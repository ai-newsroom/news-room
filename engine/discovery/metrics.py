"""Channel-neutral discovery metrics and retrospective decisions.

The module has no network, browser, credential, publication, or git behavior.
Collectors finish first; instrumentation is then run through a best-effort hook.
"""

from __future__ import annotations

import json
import math
import os
import re
import tempfile
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from statistics import median
from typing import Any, Callable, Iterable, Mapping, Optional, Sequence


class ContractError(ValueError):
    """Raised when a discovery record or retrospective violates the contract."""


SCHEMA_VERSION = 1
CHANNEL_TYPES = {
    "x",
    "official-blog",
    "paper-feed",
    "repository-release",
    "standards-conference",
    "other",
}
COLLECTION_STATUSES = {"completed", "failed", "skipped"}
EDITORIAL_DISPOSITIONS = {"publish-candidate", "no-publish", "unreviewed"}
RETROSPECTIVE_DECISIONS = {"retain", "adjust", "rollback"}

RUN_FIELDS = {
    "schema_version",
    "run_id",
    "edition",
    "started_at",
    "ended_at",
    "channels",
}
CHANNEL_FIELDS = {
    "channel_id",
    "channel_type",
    "configuration_id",
    "collection_status",
    "execution_time_seconds",
    "direct_cost_usd",
    "candidates",
}
CANDIDATE_FIELDS = {
    "candidate_id",
    "canonical_candidate_id",
    "source_published_at",
    "discovered_at",
    "duplicate_of",
    "primary_evidence_promoted",
    "editorial_disposition",
    "false_positive",
    "false_positive_reason",
}
WINDOW_FIELDS = {"window_id", "configuration_id", "records"}
POLICY_FIELDS = {
    "min_runs",
    "min_span_days",
    "min_primary_promotion_rate_improvement",
    "max_false_positive_rate_regression",
    "max_cost_per_unique_candidate_usd",
    "max_median_latency_regression_seconds",
}
EXPERIMENT_FIELDS = {
    "capability",
    "hypothesis",
    "scope",
    "success_measure",
    "rollback_plan",
    "max_runs",
    "max_days",
}
FORBIDDEN_KEYS = {
    "authorization",
    "bearer_token",
    "api_key",
    "client_secret",
    "credential",
    "credentials",
}
IDENTIFIER_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._:-]*$")
EDITION_RE = re.compile(r"^[a-z][a-z0-9-]*$")


def build_run_record(raw: Mapping[str, Any]) -> Mapping[str, Any]:
    """Validate one collection run and add deterministic channel metrics."""

    _mapping(raw, "run")
    _reject_secret_keys(raw)
    _require_exact_fields(raw, RUN_FIELDS, "run")
    if raw["schema_version"] != SCHEMA_VERSION:
        raise ContractError("unsupported_schema_version")

    run_id = _identifier(raw["run_id"], "run_id")
    edition = _string(raw["edition"], "edition")
    if not EDITION_RE.fullmatch(edition):
        raise ContractError("invalid_edition")
    started_at = _timestamp(raw["started_at"])
    ended_at = _timestamp(raw["ended_at"])
    if ended_at < started_at:
        raise ContractError("run_ended_before_start")

    channels = _sequence(raw["channels"], "channels")
    channel_ids = set()
    output_channels = []
    total_candidates = 0
    total_unique = 0
    total_execution = Decimal("0")
    total_cost = Decimal("0")

    for value in channels:
        channel = _mapping(value, "channel")
        _require_exact_fields(channel, CHANNEL_FIELDS, "channel")
        channel_id = _identifier(channel["channel_id"], "channel_id")
        if channel_id in channel_ids:
            raise ContractError("duplicate_channel_id")
        channel_ids.add(channel_id)

        channel_type = _string(channel["channel_type"], "channel_type")
        if channel_type not in CHANNEL_TYPES:
            raise ContractError("invalid_channel_type")
        configuration_id = _identifier(
            channel["configuration_id"], "configuration_id"
        )
        collection_status = _string(
            channel["collection_status"], "collection_status"
        )
        if collection_status not in COLLECTION_STATUSES:
            raise ContractError("invalid_collection_status")
        execution_time = _non_negative_decimal(
            channel["execution_time_seconds"], "execution_time_seconds"
        )
        direct_cost = _non_negative_decimal(
            channel["direct_cost_usd"], "direct_cost_usd"
        )

        candidates = [
            _validated_candidate(item)
            for item in _sequence(channel["candidates"], "candidates")
        ]
        candidate_ids = [item["candidate_id"] for item in candidates]
        if len(candidate_ids) != len(set(candidate_ids)):
            raise ContractError("duplicate_candidate_id")
        if collection_status in {"failed", "skipped"} and candidates:
            raise ContractError("incomplete_channel_cannot_emit_candidates")

        metrics = _channel_metrics(candidates, execution_time, direct_cost)
        total_candidates += metrics["candidate_count"]
        total_unique += metrics["unique_candidate_count"]
        total_execution += execution_time
        total_cost += direct_cost
        output_channels.append(
            {
                "channel_id": channel_id,
                "channel_type": channel_type,
                "configuration_id": configuration_id,
                "collection_status": collection_status,
                "execution_time_seconds": _number(execution_time),
                "direct_cost_usd": _money(direct_cost),
                "candidates": candidates,
                "metrics": metrics,
            }
        )

    return {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "edition": edition,
        "started_at": raw["started_at"],
        "ended_at": raw["ended_at"],
        "channels": output_channels,
        "run_metrics": {
            "channel_count": len(output_channels),
            "candidate_count": total_candidates,
            "unique_candidate_count": total_unique,
            "execution_time_seconds": _number(total_execution),
            "direct_cost_usd": _money(total_cost),
        },
    }


def collect_with_optional_metrics(
    collector: Callable[[], Any],
    payload_builder: Callable[[Any], Mapping[str, Any]],
    sink: Callable[[Mapping[str, Any]], Any],
    *,
    enabled: bool,
) -> tuple[Any, Mapping[str, Any]]:
    """Run collection first, then record metrics without failing collection.

    Collector exceptions remain collector failures and are not hidden. Every exception
    after collection is reduced to its type so logs cannot leak credential values.
    """

    collected = collector()
    if not enabled:
        return collected, {"status": "disabled"}
    try:
        record = build_run_record(payload_builder(collected))
        sink_result = sink(record)
    except Exception as error:  # instrumentation must be fail-open
        return collected, {
            "status": "failed",
            "error_type": type(error).__name__,
        }
    return collected, {
        "status": "recorded",
        "run_id": record["run_id"],
        "sink_result": None if sink_result is None else str(sink_result),
    }


def write_json_record(directory: Path | str, record: Mapping[str, Any]) -> str:
    """Atomically create one JSON file per run without overwriting prior evidence."""

    run_id = _identifier(record.get("run_id"), "run_id")
    target_directory = Path(directory)
    target_directory.mkdir(parents=True, exist_ok=True)
    target = target_directory / "{}.json".format(run_id)
    serialized = json.dumps(
        record, ensure_ascii=False, indent=2, sort_keys=True
    ) + "\n"

    if target.exists():
        if target.read_text(encoding="utf-8") == serialized:
            return str(target)
        raise ContractError("run_record_conflict")

    temporary_path: Optional[Path] = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=target_directory,
            prefix=".discovery-metrics-",
            delete=False,
        ) as temporary:
            temporary.write(serialized)
            temporary.flush()
            os.fsync(temporary.fileno())
            temporary_path = Path(temporary.name)
        os.link(temporary_path, target)
    except FileExistsError:
        if target.read_text(encoding="utf-8") != serialized:
            raise ContractError("run_record_conflict")
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
    return str(target)


def summarize_channel(
    records: Sequence[Mapping[str, Any]], channel_id: str
) -> Mapping[str, Any]:
    """Aggregate one channel without averaging already-rounded rates."""

    _identifier(channel_id, "channel_id")
    if not records:
        raise ContractError("empty_observation_window")

    run_ids = set()
    configurations = set()
    starts = []
    candidate_count = 0
    unique_count = 0
    duplicate_count = 0
    primary_count = 0
    publish_count = 0
    false_positive_count = 0
    false_positive_reviewed_count = 0
    latencies = []
    execution_time = Decimal("0")
    direct_cost = Decimal("0")

    for record in records:
        run_id = _identifier(record.get("run_id"), "run_id")
        if run_id in run_ids:
            raise ContractError("duplicate_run_id_in_window")
        run_ids.add(run_id)
        starts.append(_timestamp(record.get("started_at")))
        channel = _find_channel(record, channel_id)
        configurations.add(channel["configuration_id"])
        metrics = channel["metrics"]
        candidate_count += int(metrics["candidate_count"])
        unique_count += int(metrics["unique_candidate_count"])
        duplicate_count += int(metrics["duplicate_count"])
        primary_count += int(metrics["primary_evidence_promoted_count"])
        publish_count += int(metrics["publish_candidate_contribution_count"])
        false_positive_count += int(metrics["false_positive_count"])
        false_positive_reviewed_count += int(
            metrics["false_positive_reviewed_count"]
        )
        execution_time += _non_negative_decimal(
            metrics["execution_time_seconds"], "execution_time_seconds"
        )
        direct_cost += _non_negative_decimal(
            metrics["direct_cost_usd"], "direct_cost_usd"
        )
        for candidate in channel["candidates"]:
            if candidate["duplicate_of"] is None:
                latency = _candidate_latency(candidate)
                if latency is not None:
                    latencies.append(latency)

    if len(configurations) != 1:
        raise ContractError("mixed_channel_configurations")
    starts.sort()
    span_days = (starts[-1] - starts[0]).total_seconds() / 86400
    cost_per_unique = None if unique_count == 0 else direct_cost / unique_count

    return {
        "channel_id": channel_id,
        "configuration_id": next(iter(configurations)),
        "run_count": len(records),
        "span_days": round(span_days, 6),
        "candidate_count": candidate_count,
        "unique_candidate_count": unique_count,
        "duplicate_count": duplicate_count,
        "duplicate_rate": _rate(duplicate_count, candidate_count),
        "primary_evidence_promoted_count": primary_count,
        "primary_evidence_promotion_rate": _rate(primary_count, unique_count),
        "publish_candidate_contribution_count": publish_count,
        "publish_candidate_contribution_rate": _rate(publish_count, unique_count),
        "false_positive_count": false_positive_count,
        "false_positive_reviewed_count": false_positive_reviewed_count,
        "false_positive_rate": _rate(
            false_positive_count, false_positive_reviewed_count
        ),
        "discovery_latency_seconds": _latency_summary(latencies),
        "execution_time_seconds": _number(execution_time),
        "direct_cost_usd": _money(direct_cost),
        "direct_cost_per_unique_candidate_usd": (
            None if cost_per_unique is None else _money(cost_per_unique)
        ),
    }


def evaluate_retrospective(
    baseline: Optional[Mapping[str, Any]],
    experiment: Mapping[str, Any],
    *,
    channel_id: str,
    policy: Mapping[str, Any],
    next_experiment: Optional[Mapping[str, Any]],
) -> Mapping[str, Any]:
    """Compare mature baseline/experiment windows and return a bounded decision."""

    _require_exact_fields(policy, POLICY_FIELDS, "policy")
    checked_policy = _validated_policy(policy)
    experiment_window = _validated_window(experiment, "experiment")
    experiment_summary = summarize_channel(
        experiment_window["records"], channel_id
    )
    _match_configuration(experiment_window, experiment_summary)

    if baseline is None:
        return _deferred_retrospective(
            "baseline-missing", None, experiment_window, None, experiment_summary
        )

    baseline_window = _validated_window(baseline, "baseline")
    if baseline_window["window_id"] == experiment_window["window_id"]:
        raise ContractError("baseline_and_experiment_window_must_differ")
    if baseline_window["configuration_id"] == experiment_window["configuration_id"]:
        raise ContractError("baseline_and_experiment_configuration_must_differ")
    baseline_summary = summarize_channel(baseline_window["records"], channel_id)
    _match_configuration(baseline_window, baseline_summary)
    incomplete = []
    if not _window_ready(baseline_summary, checked_policy):
        incomplete.append("BASELINE_WINDOW_INCOMPLETE")
    if not _window_ready(experiment_summary, checked_policy):
        incomplete.append("EXPERIMENT_WINDOW_INCOMPLETE")
    if incomplete:
        result = _deferred_retrospective(
            "collecting",
            baseline_window,
            experiment_window,
            baseline_summary,
            experiment_summary,
        )
        result["reason_codes"] = incomplete
        return result

    proposal = _validated_experiment(next_experiment)
    comparison = _comparison(baseline_summary, experiment_summary)
    reasons = []

    false_positive_delta = comparison["false_positive_rate_delta"]
    if (
        false_positive_delta is None
        or false_positive_delta
        > checked_policy["max_false_positive_rate_regression"]
    ):
        reasons.append("FALSE_POSITIVE_GUARDRAIL_BREACHED")

    experiment_cost = experiment_summary[
        "direct_cost_per_unique_candidate_usd"
    ]
    if experiment_cost is None or Decimal(experiment_cost) > checked_policy[
        "max_cost_per_unique_candidate_usd"
    ]:
        reasons.append("DIRECT_COST_GUARDRAIL_BREACHED")

    latency_delta = comparison["median_discovery_latency_delta_seconds"]
    if (
        latency_delta is None
        or latency_delta
        > checked_policy["max_median_latency_regression_seconds"]
    ):
        reasons.append("DISCOVERY_LATENCY_GUARDRAIL_BREACHED")

    if reasons:
        decision = "rollback"
    elif (
        comparison["primary_evidence_promotion_rate_delta"]
        >= checked_policy["min_primary_promotion_rate_improvement"]
    ):
        decision = "retain"
        reasons.append("PROMOTION_IMPROVEMENT_AND_GUARDRAILS_PASS")
    else:
        decision = "adjust"
        reasons.append("IMPROVEMENT_BELOW_THRESHOLD")

    if decision not in RETROSPECTIVE_DECISIONS:
        raise ContractError("invalid_retrospective_decision")
    return {
        "status": "evaluated",
        "comparison_ready": True,
        "improvement_claim": (
            "supported-within-observed-window"
            if decision == "retain"
            else "not-supported"
        ),
        "decision": decision,
        "reason_codes": reasons,
        "baseline": {
            "window_id": baseline_window["window_id"],
            "summary": baseline_summary,
        },
        "experiment": {
            "window_id": experiment_window["window_id"],
            "summary": experiment_summary,
        },
        "comparison": comparison,
        "next_bounded_experiment": proposal,
    }


def _validated_candidate(raw: Any) -> Mapping[str, Any]:
    candidate = _mapping(raw, "candidate")
    _require_exact_fields(candidate, CANDIDATE_FIELDS, "candidate")
    candidate_id = _identifier(candidate["candidate_id"], "candidate_id")
    canonical_id = _identifier(
        candidate["canonical_candidate_id"], "canonical_candidate_id"
    )
    discovered_at = _timestamp(candidate["discovered_at"])
    published_at = candidate["source_published_at"]
    if published_at is not None and _timestamp(published_at) > discovered_at:
        raise ContractError("candidate_discovered_before_publication")
    duplicate_of = candidate["duplicate_of"]
    if duplicate_of is not None:
        duplicate_of = _identifier(duplicate_of, "duplicate_of")
    primary = candidate["primary_evidence_promoted"]
    if not isinstance(primary, bool):
        raise ContractError("primary_evidence_promoted_must_be_boolean")
    disposition = _string(
        candidate["editorial_disposition"], "editorial_disposition"
    )
    if disposition not in EDITORIAL_DISPOSITIONS:
        raise ContractError("invalid_editorial_disposition")
    false_positive = candidate["false_positive"]
    if false_positive is not None and not isinstance(false_positive, bool):
        raise ContractError("false_positive_must_be_boolean_or_null")
    reason = candidate["false_positive_reason"]
    if false_positive is True and not _optional_nonempty_string(reason):
        raise ContractError("false_positive_reason_required")
    if false_positive is not True and reason is not None:
        raise ContractError("false_positive_reason_without_false_positive")
    if false_positive is True and disposition != "no-publish":
        raise ContractError("false_positive_must_be_no_publish")
    if disposition == "publish-candidate" and false_positive is not False:
        raise ContractError("publish_candidate_must_be_reviewed_not_false_positive")
    if duplicate_of is not None and (
        primary or disposition != "unreviewed" or false_positive is not None
    ):
        raise ContractError("duplicate_observation_cannot_claim_outcome")
    return {
        "candidate_id": candidate_id,
        "canonical_candidate_id": canonical_id,
        "source_published_at": published_at,
        "discovered_at": candidate["discovered_at"],
        "duplicate_of": duplicate_of,
        "primary_evidence_promoted": primary,
        "editorial_disposition": disposition,
        "false_positive": false_positive,
        "false_positive_reason": reason,
    }


def _channel_metrics(
    candidates: Sequence[Mapping[str, Any]],
    execution_time: Decimal,
    direct_cost: Decimal,
) -> Mapping[str, Any]:
    unique = [item for item in candidates if item["duplicate_of"] is None]
    reviewed = [item for item in unique if item["false_positive"] is not None]
    duplicate_count = len(candidates) - len(unique)
    primary_count = sum(item["primary_evidence_promoted"] for item in unique)
    publish_count = sum(
        item["editorial_disposition"] == "publish-candidate" for item in unique
    )
    false_positive_count = sum(item["false_positive"] is True for item in reviewed)
    latencies = [
        latency
        for latency in (_candidate_latency(item) for item in unique)
        if latency is not None
    ]
    return {
        "candidate_count": len(candidates),
        "unique_candidate_count": len(unique),
        "duplicate_count": duplicate_count,
        "duplicate_rate": _rate(duplicate_count, len(candidates)),
        "primary_evidence_promoted_count": primary_count,
        "primary_evidence_promotion_rate": _rate(primary_count, len(unique)),
        "publish_candidate_contribution_count": publish_count,
        "publish_candidate_contribution_rate": _rate(publish_count, len(unique)),
        "false_positive_count": false_positive_count,
        "false_positive_reviewed_count": len(reviewed),
        "false_positive_rate": _rate(false_positive_count, len(reviewed)),
        "discovery_latency_seconds": _latency_summary(latencies),
        "execution_time_seconds": _number(execution_time),
        "direct_cost_usd": _money(direct_cost),
    }


def _candidate_latency(candidate: Mapping[str, Any]) -> Optional[int]:
    if candidate["source_published_at"] is None:
        return None
    return int(
        (
            _timestamp(candidate["discovered_at"])
            - _timestamp(candidate["source_published_at"])
        ).total_seconds()
    )


def _latency_summary(values: Iterable[int]) -> Mapping[str, Any]:
    ordered = sorted(values)
    if not ordered:
        return {"count": 0, "min": None, "median": None, "p95": None, "max": None}
    p95_index = max(0, math.ceil(len(ordered) * 0.95) - 1)
    return {
        "count": len(ordered),
        "min": ordered[0],
        "median": _number(Decimal(str(median(ordered)))),
        "p95": ordered[p95_index],
        "max": ordered[-1],
    }


def _validated_window(raw: Mapping[str, Any], label: str) -> Mapping[str, Any]:
    value = _mapping(raw, label)
    _require_exact_fields(value, WINDOW_FIELDS, label)
    return {
        "window_id": _identifier(value["window_id"], "window_id"),
        "configuration_id": _identifier(
            value["configuration_id"], "configuration_id"
        ),
        "records": list(_sequence(value["records"], "records")),
    }


def _match_configuration(
    window: Mapping[str, Any], summary: Mapping[str, Any]
) -> None:
    if window["configuration_id"] != summary["configuration_id"]:
        raise ContractError("window_configuration_mismatch")


def _validated_policy(raw: Mapping[str, Any]) -> Mapping[str, Any]:
    min_runs = _positive_integer(raw["min_runs"], "min_runs")
    min_span_days = _non_negative_decimal(raw["min_span_days"], "min_span_days")
    if min_span_days <= 0:
        raise ContractError("observation_window_must_be_positive")
    result = {
        "min_runs": min_runs,
        "min_span_days": float(min_span_days),
        "min_primary_promotion_rate_improvement": float(
            _non_negative_decimal(
                raw["min_primary_promotion_rate_improvement"],
                "min_primary_promotion_rate_improvement",
            )
        ),
        "max_false_positive_rate_regression": float(
            _non_negative_decimal(
                raw["max_false_positive_rate_regression"],
                "max_false_positive_rate_regression",
            )
        ),
        "max_cost_per_unique_candidate_usd": _non_negative_decimal(
            raw["max_cost_per_unique_candidate_usd"],
            "max_cost_per_unique_candidate_usd",
        ),
        "max_median_latency_regression_seconds": float(
            _non_negative_decimal(
                raw["max_median_latency_regression_seconds"],
                "max_median_latency_regression_seconds",
            )
        ),
    }
    for key in (
        "min_primary_promotion_rate_improvement",
        "max_false_positive_rate_regression",
    ):
        if result[key] > 1:
            raise ContractError("{}_must_be_rate".format(key))
    return result


def _validated_experiment(
    raw: Optional[Mapping[str, Any]],
) -> Mapping[str, Any]:
    if raw is None:
        raise ContractError("next_bounded_experiment_required")
    value = _mapping(raw, "next_experiment")
    _require_exact_fields(value, EXPERIMENT_FIELDS, "next_experiment")
    result = {
        key: _string(value[key], key)
        for key in (
            "capability",
            "hypothesis",
            "scope",
            "success_measure",
            "rollback_plan",
        )
    }
    result["max_runs"] = _positive_integer(value["max_runs"], "max_runs")
    result["max_days"] = _positive_integer(value["max_days"], "max_days")
    return result


def _window_ready(
    summary: Mapping[str, Any], policy: Mapping[str, Any]
) -> bool:
    return (
        summary["run_count"] >= policy["min_runs"]
        and summary["span_days"] >= policy["min_span_days"]
    )


def _comparison(
    baseline: Mapping[str, Any], experiment: Mapping[str, Any]
) -> Mapping[str, Any]:
    promotion_delta = _optional_delta(
        baseline["primary_evidence_promotion_rate"],
        experiment["primary_evidence_promotion_rate"],
    )
    false_positive_delta = _optional_delta(
        baseline["false_positive_rate"], experiment["false_positive_rate"]
    )
    baseline_latency = baseline["discovery_latency_seconds"]["median"]
    experiment_latency = experiment["discovery_latency_seconds"]["median"]
    latency_delta = _optional_delta(baseline_latency, experiment_latency)
    baseline_cost = baseline["direct_cost_per_unique_candidate_usd"]
    experiment_cost = experiment["direct_cost_per_unique_candidate_usd"]
    cost_delta = None
    if baseline_cost is not None and experiment_cost is not None:
        cost_delta = _money(Decimal(experiment_cost) - Decimal(baseline_cost))
    return {
        "primary_evidence_promotion_rate_delta": promotion_delta,
        "false_positive_rate_delta": false_positive_delta,
        "median_discovery_latency_delta_seconds": latency_delta,
        "direct_cost_per_unique_candidate_usd_delta": cost_delta,
    }


def _deferred_retrospective(
    status: str,
    baseline_window: Optional[Mapping[str, Any]],
    experiment_window: Mapping[str, Any],
    baseline_summary: Optional[Mapping[str, Any]],
    experiment_summary: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "status": status,
        "comparison_ready": False,
        "improvement_claim": None,
        "decision": None,
        "reason_codes": [
            "BASELINE_REQUIRED" if baseline_window is None else "OBSERVATION_INCOMPLETE"
        ],
        "baseline": (
            None
            if baseline_window is None
            else {
                "window_id": baseline_window["window_id"],
                "summary": baseline_summary,
            }
        ),
        "experiment": {
            "window_id": experiment_window["window_id"],
            "summary": experiment_summary,
        },
        "comparison": None,
        "next_bounded_experiment": None,
    }


def _find_channel(
    record: Mapping[str, Any], channel_id: str
) -> Mapping[str, Any]:
    matches = [
        item for item in record.get("channels", []) if item.get("channel_id") == channel_id
    ]
    if len(matches) != 1:
        raise ContractError("channel_missing_or_duplicated_in_run")
    return matches[0]


def _rate(numerator: int, denominator: int) -> Optional[float]:
    if denominator == 0:
        return None
    return round(numerator / denominator, 6)


def _optional_delta(baseline: Any, experiment: Any) -> Optional[float]:
    if baseline is None or experiment is None:
        return None
    return round(float(experiment) - float(baseline), 6)


def _money(value: Decimal) -> str:
    return format(value.quantize(Decimal("0.000001")), "f")


def _number(value: Decimal) -> int | float:
    if value == value.to_integral_value():
        return int(value)
    return float(value)


def _non_negative_decimal(value: Any, label: str) -> Decimal:
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise ContractError("invalid_{}".format(label))
    if not result.is_finite() or result < 0:
        raise ContractError("invalid_{}".format(label))
    return result


def _positive_integer(value: Any, label: str) -> int:
    if isinstance(value, bool):
        raise ContractError("invalid_{}".format(label))
    result = _non_negative_decimal(value, label)
    if result <= 0 or result != result.to_integral_value():
        raise ContractError("invalid_{}".format(label))
    return int(result)


def _timestamp(value: Any) -> datetime:
    if not isinstance(value, str):
        raise ContractError("timestamp_must_be_string")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ContractError("invalid_timestamp") from error
    if parsed.tzinfo is None:
        raise ContractError("timestamp_timezone_required")
    return parsed


def _identifier(value: Any, label: str) -> str:
    result = _string(value, label)
    if not IDENTIFIER_RE.fullmatch(result):
        raise ContractError("invalid_{}".format(label))
    return result


def _string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ContractError("{}_must_be_nonempty_string".format(label))
    return value


def _optional_nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ContractError("{}_must_be_mapping".format(label))
    return value


def _sequence(value: Any, label: str) -> Sequence[Any]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise ContractError("{}_must_be_sequence".format(label))
    return value


def _require_exact_fields(
    value: Mapping[str, Any], expected: set[str], label: str
) -> None:
    missing = expected - set(value)
    unknown = set(value) - expected
    if missing:
        raise ContractError("{}_missing:{}".format(label, ",".join(sorted(missing))))
    if unknown:
        raise ContractError("{}_unknown:{}".format(label, ",".join(sorted(unknown))))


def _reject_secret_keys(value: Any) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if str(key).lower() in FORBIDDEN_KEYS:
                raise ContractError("secret_material_forbidden")
            _reject_secret_keys(child)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        for child in value:
            _reject_secret_keys(child)
