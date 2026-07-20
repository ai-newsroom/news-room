"""Credential-free X acquisition normalization contract.

This module intentionally contains no HTTP client or credential value.  A future,
approved transport may attach authentication outside this boundary and pass only
decoded API pages/events into ``run_fixture_scenario`` or equivalent ingestion.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from decimal import Decimal, ROUND_FLOOR
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple


USER_TIMELINE = "user_timeline"
RECENT_SEARCH = "recent_search"
FILTERED_STREAM = "filtered_stream"
FILTERED_STREAM_WEBHOOK = "filtered_stream_webhook"

POLLING_ROUTES = {USER_TIMELINE, RECENT_SEARCH}
SUPPORTED_ROUTES = POLLING_ROUTES | {FILTERED_STREAM, FILTERED_STREAM_WEBHOOK}
ROUTE_MIN_RESULTS = {USER_TIMELINE: 5, RECENT_SEARCH: 10}


class ContractError(ValueError):
    """The fixture or adapter state violates the acquisition contract."""


class CircuitOpen(RuntimeError):
    """A local budget or safety gate prevented another provider request."""

    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason


class PushDeliveryOnly(ContractError):
    """Webhook delivery is ingested as a push event, not planned as a GET."""


@dataclass(frozen=True)
class AdapterConfig:
    route: str
    scope_key: str
    max_results: int
    query: Optional[str] = None
    tweet_fields: Tuple[str, ...] = (
        "id",
        "text",
        "author_id",
        "created_at",
        "conversation_id",
        "edit_history_tweet_ids",
        "entities",
        "referenced_tweets",
    )

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any]) -> "AdapterConfig":
        config = cls(
            route=str(raw["route"]),
            scope_key=str(raw["scope_key"]),
            max_results=int(raw.get("max_results", 100)),
            query=raw.get("query"),
            tweet_fields=tuple(raw.get("tweet_fields", cls.tweet_fields)),
        )
        config.validate()
        return config

    def validate(self) -> None:
        if self.route not in SUPPORTED_ROUTES:
            raise ContractError("unsupported_route")
        if not self.scope_key:
            raise ContractError("scope_key_required")
        if not 1 <= self.max_results <= 100:
            raise ContractError("max_results_out_of_range")
        if self.route == RECENT_SEARCH and not self.query:
            raise ContractError("recent_search_query_required")


@dataclass
class Checkpoint:
    route: str
    scope_key: str
    since_id: Optional[str] = None
    pagination_token: Optional[str] = None
    high_watermark_id: Optional[str] = None
    complete: bool = True

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any]) -> "Checkpoint":
        return cls(
            route=str(raw["route"]),
            scope_key=str(raw["scope_key"]),
            since_id=_optional_string(raw.get("since_id")),
            pagination_token=_optional_string(raw.get("pagination_token")),
            high_watermark_id=_optional_string(raw.get("high_watermark_id")),
            complete=bool(raw.get("complete", True)),
        )

    def validate_for(self, config: AdapterConfig) -> None:
        if self.route != config.route or self.scope_key != config.scope_key:
            raise ContractError("checkpoint_scope_mismatch")
        for value in (self.since_id, self.high_watermark_id):
            if value is not None and not value.isdigit():
                raise ContractError("checkpoint_post_id_must_be_numeric")


@dataclass(frozen=True)
class BudgetPolicy:
    max_calls_per_run: int
    max_post_reads_per_run: int
    monthly_post_read_limit: int
    monthly_cost_limit_usd: Decimal
    post_read_unit_cost_usd: Decimal

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any]) -> "BudgetPolicy":
        policy = cls(
            max_calls_per_run=int(raw["max_calls_per_run"]),
            max_post_reads_per_run=int(raw["max_post_reads_per_run"]),
            monthly_post_read_limit=int(raw["monthly_post_read_limit"]),
            monthly_cost_limit_usd=Decimal(str(raw["monthly_cost_limit_usd"])),
            post_read_unit_cost_usd=Decimal(str(raw["post_read_unit_cost_usd"])),
        )
        if min(
            policy.max_calls_per_run,
            policy.max_post_reads_per_run,
            policy.monthly_post_read_limit,
        ) <= 0:
            raise ContractError("budget_limits_must_be_positive")
        if policy.monthly_cost_limit_usd <= 0 or policy.post_read_unit_cost_usd <= 0:
            raise ContractError("budget_costs_must_be_positive")
        return policy


@dataclass
class BudgetMeter:
    policy: BudgetPolicy
    monthly_post_reads_before: int = 0
    monthly_spend_before_usd: Decimal = Decimal("0")
    calls: int = 0
    post_reads: int = 0

    @classmethod
    def from_mapping(
        cls, policy: BudgetPolicy, raw: Optional[Mapping[str, Any]] = None
    ) -> "BudgetMeter":
        raw = raw or {}
        return cls(
            policy=policy,
            monthly_post_reads_before=int(raw.get("monthly_post_reads_before", 0)),
            monthly_spend_before_usd=Decimal(
                str(raw.get("monthly_spend_before_usd", "0"))
            ),
        )

    def blocker_for_next_call(self) -> Optional[str]:
        if self.calls >= self.policy.max_calls_per_run:
            return "max_calls_per_run"
        if self.post_reads >= self.policy.max_post_reads_per_run:
            return "max_post_reads_per_run"
        if (
            self.monthly_post_reads_before + self.post_reads
            >= self.policy.monthly_post_read_limit
        ):
            return "monthly_post_read_limit"
        if (
            self.monthly_spend_before_usd + self.estimated_cost_usd
            + self.policy.post_read_unit_cost_usd
            > self.policy.monthly_cost_limit_usd
        ):
            return "monthly_cost_limit_usd"
        return None

    @property
    def estimated_cost_usd(self) -> Decimal:
        return self.policy.post_read_unit_cost_usd * self.post_reads

    def remaining_post_capacity(self) -> int:
        run_remaining = self.policy.max_post_reads_per_run - self.post_reads
        month_remaining = (
            self.policy.monthly_post_read_limit
            - self.monthly_post_reads_before
            - self.post_reads
        )
        cost_remaining = (
            self.policy.monthly_cost_limit_usd
            - self.monthly_spend_before_usd
            - self.estimated_cost_usd
        )
        cost_capacity = int(
            (cost_remaining / self.policy.post_read_unit_cost_usd).to_integral_value(
                rounding=ROUND_FLOOR
            )
        )
        return max(0, min(run_remaining, month_remaining, cost_capacity))

    def charge(self, post_reads: int, *, count_call: bool) -> None:
        if post_reads < 0 or post_reads > self.remaining_post_capacity():
            raise CircuitOpen("response_exceeds_remaining_post_budget")
        if count_call:
            blocker = self.blocker_for_next_call()
            if blocker:
                raise CircuitOpen(blocker)
            self.calls += 1
        self.post_reads += post_reads


@dataclass(frozen=True)
class FetchRequest:
    method: str
    path: str
    params: Mapping[str, str]


@dataclass
class PostRecord:
    canonical_post_id: str
    current_post_id: str
    version_ids: List[str]
    content: Optional[Mapping[str, Any]]
    deleted: bool = False

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any]) -> "PostRecord":
        versions = [str(value) for value in raw.get("version_ids", [])]
        current = str(raw["current_post_id"])
        if not versions:
            versions = [current]
        return cls(
            canonical_post_id=str(raw["canonical_post_id"]),
            current_post_id=current,
            version_ids=versions,
            content=raw.get("content"),
            deleted=bool(raw.get("deleted", False)),
        )


@dataclass
class RunMetrics:
    route: str
    calls: int = 0
    post_reads_gross: int = 0
    estimated_cost_usd: str = "0.000"
    emitted_events: int = 0
    duplicate_reads: int = 0
    duplicate_rate: float = 0.0
    edits: int = 0
    deletes: int = 0
    lead_time_seconds: List[int] = field(default_factory=list)
    expected_posts: int = 0
    observed_expected_posts: int = 0
    recall: Optional[float] = None
    circuit_breaker: Optional[str] = None


def plan_request(
    config: AdapterConfig, checkpoint: Checkpoint, meter: BudgetMeter
) -> FetchRequest:
    """Return an auth-free request description for an approved outer transport."""

    config.validate()
    checkpoint.validate_for(config)
    if config.route == FILTERED_STREAM_WEBHOOK:
        raise PushDeliveryOnly("webhook_is_push_delivery")

    blocker = meter.blocker_for_next_call()
    if blocker:
        raise CircuitOpen(blocker)

    params: Dict[str, str] = {"tweet.fields": ",".join(config.tweet_fields)}

    if config.route == USER_TIMELINE:
        capacity = meter.remaining_post_capacity()
        if capacity < ROUTE_MIN_RESULTS[USER_TIMELINE]:
            raise CircuitOpen("remaining_post_budget_below_endpoint_minimum")
        params["max_results"] = str(min(config.max_results, capacity))
        params["exclude"] = "retweets"
        if checkpoint.since_id:
            params["since_id"] = checkpoint.since_id
        if checkpoint.pagination_token:
            params["pagination_token"] = checkpoint.pagination_token
        path = "/2/users/{}/tweets".format(config.scope_key)
    elif config.route == RECENT_SEARCH:
        capacity = meter.remaining_post_capacity()
        if capacity < ROUTE_MIN_RESULTS[RECENT_SEARCH]:
            raise CircuitOpen("remaining_post_budget_below_endpoint_minimum")
        params["max_results"] = str(min(config.max_results, capacity))
        params["query"] = str(config.query)
        if checkpoint.since_id:
            params["since_id"] = checkpoint.since_id
        if checkpoint.pagination_token:
            params["next_token"] = checkpoint.pagination_token
        path = "/2/tweets/search/recent"
    else:
        path = "/2/tweets/search/stream"

    return FetchRequest(method="GET", path=path, params=params)


def live_gate(
    monthly_cost_limit_usd: Optional[str], credential_available: bool
) -> Mapping[str, Any]:
    """Keep the two user decisions independent without accepting credential material."""

    blockers: List[str] = []
    try:
        cap = (
            None
            if monthly_cost_limit_usd is None
            else Decimal(str(monthly_cost_limit_usd))
        )
    except Exception:
        cap = None
    if cap is None or cap <= 0:
        blockers.append("monthly_cost_cap_required")
    if not credential_available:
        blockers.append("credential_provider_required")
    return {"live_allowed": not blockers, "blockers": blockers}


def run_fixture_scenario(scenario: Mapping[str, Any]) -> Mapping[str, Any]:
    """Process deterministic fixture pages without performing network or file writes."""

    config = AdapterConfig.from_mapping(scenario["config"])
    checkpoint = Checkpoint.from_mapping(scenario["checkpoint"])
    checkpoint.validate_for(config)
    policy = BudgetPolicy.from_mapping(scenario["budget"])
    meter = BudgetMeter.from_mapping(policy, scenario.get("budget_state"))
    records = _load_records(scenario.get("known_records", []))
    version_index = _version_index(records.values())

    events: List[Mapping[str, Any]] = []
    request_trace: List[Mapping[str, Any]] = []
    seen_post_ids = set()
    lead_times: List[int] = []
    duplicate_reads = 0
    edits = 0
    deletes = 0
    circuit_reason: Optional[str] = None

    for envelope in scenario.get("pages", []):
        response = envelope.get("response", {})
        posts = list(response.get("data") or [])

        if config.route == FILTERED_STREAM_WEBHOOK:
            try:
                meter.charge(len(posts), count_call=False)
            except CircuitOpen as error:
                circuit_reason = error.reason
                break
        else:
            try:
                request = plan_request(config, checkpoint, meter)
            except CircuitOpen as error:
                circuit_reason = error.reason
                break

            request_token = request.params.get(
                "next_token" if config.route == RECENT_SEARCH else "pagination_token"
            )
            if _optional_string(envelope.get("request_token")) != request_token:
                raise ContractError("fixture_request_token_mismatch")
            planned_max = int(request.params.get("max_results", len(posts) or 1))
            if len(posts) > planned_max:
                raise ContractError("response_exceeds_planned_max_results")
            meter.charge(len(posts), count_call=True)
            request_trace.append(asdict(request))

        observed_at = str(envelope["observed_at"])
        source_route = str(envelope.get("source_route", config.route))
        for post in posts:
            post_id = str(post["id"])
            seen_post_ids.add(post_id)
            checkpoint.high_watermark_id = _max_post_id(
                checkpoint.high_watermark_id, post_id
            )
            event = _ingest_post(
                post=post,
                observed_at=observed_at,
                source_route=source_route,
                records=records,
                version_index=version_index,
            )
            if event is None:
                duplicate_reads += 1
                continue
            events.append(event)
            if event["kind"] == "edit":
                edits += 1
            lead_time = _lead_time_seconds(post.get("created_at"), observed_at)
            if lead_time is not None:
                lead_times.append(lead_time)

        for compliance in response.get("compliance_events", []):
            event = _ingest_compliance_event(
                compliance,
                observed_at=observed_at,
                source_route=source_route,
                records=records,
                version_index=version_index,
            )
            if event is not None:
                events.append(event)
                if event["kind"] == "delete":
                    deletes += 1

        if config.route in POLLING_ROUTES:
            next_token = _optional_string(response.get("meta", {}).get("next_token"))
            if next_token:
                checkpoint.pagination_token = next_token
                checkpoint.complete = False
            else:
                checkpoint.pagination_token = None
                checkpoint.complete = True
                checkpoint.since_id = _max_post_id(
                    checkpoint.since_id, checkpoint.high_watermark_id
                )
        else:
            checkpoint.complete = False

    expected = {str(value) for value in scenario.get("expected_post_ids", [])}
    observed_expected = len(expected & seen_post_ids)
    recall = None if not expected else observed_expected / len(expected)
    duplicate_rate = 0.0 if meter.post_reads == 0 else duplicate_reads / meter.post_reads

    metrics = RunMetrics(
        route=config.route,
        calls=meter.calls,
        post_reads_gross=meter.post_reads,
        estimated_cost_usd=_money(meter.estimated_cost_usd),
        emitted_events=len(events),
        duplicate_reads=duplicate_reads,
        duplicate_rate=duplicate_rate,
        edits=edits,
        deletes=deletes,
        lead_time_seconds=lead_times,
        expected_posts=len(expected),
        observed_expected_posts=observed_expected,
        recall=recall,
        circuit_breaker=circuit_reason,
    )

    return {
        "events": events,
        "checkpoint": asdict(checkpoint),
        "records": [
            asdict(records[key])
            for key in sorted(records, key=lambda value: int(value))
        ],
        "metrics": asdict(metrics),
        "request_trace": request_trace,
    }


def _load_records(raw_records: Iterable[Mapping[str, Any]]) -> Dict[str, PostRecord]:
    records: Dict[str, PostRecord] = {}
    for raw in raw_records:
        record = PostRecord.from_mapping(raw)
        records[record.canonical_post_id] = record
    return records


def _version_index(records: Iterable[PostRecord]) -> Dict[str, str]:
    index: Dict[str, str] = {}
    for record in records:
        for version in record.version_ids:
            index[version] = record.canonical_post_id
    return index


def _ingest_post(
    *,
    post: Mapping[str, Any],
    observed_at: str,
    source_route: str,
    records: Dict[str, PostRecord],
    version_index: Dict[str, str],
) -> Optional[Mapping[str, Any]]:
    current_id = str(post["id"])
    versions = [str(value) for value in post.get("edit_history_tweet_ids") or []]
    if not versions:
        versions = [current_id]
    if versions[-1] != current_id:
        raise ContractError("post_id_must_be_latest_edit_version")
    canonical_id = versions[0]
    record = records.get(canonical_id)

    if record is None:
        record = PostRecord(
            canonical_post_id=canonical_id,
            current_post_id=current_id,
            version_ids=versions,
            content=dict(post),
            deleted=False,
        )
        records[canonical_id] = record
        for version in versions:
            version_index[version] = canonical_id
        return {
            "kind": "upsert",
            "canonical_post_id": canonical_id,
            "current_post_id": current_id,
            "supersedes_post_id": None,
            "version_ids": versions,
            "source_route": source_route,
            "observed_at": observed_at,
        }

    if current_id == record.current_post_id or current_id in record.version_ids:
        return None
    if record.current_post_id not in versions or len(versions) <= len(record.version_ids):
        return None

    previous_id = record.current_post_id
    record.current_post_id = current_id
    record.version_ids = versions
    record.content = dict(post)
    record.deleted = False
    for version in versions:
        version_index[version] = canonical_id
    return {
        "kind": "edit",
        "canonical_post_id": canonical_id,
        "current_post_id": current_id,
        "supersedes_post_id": previous_id,
        "version_ids": versions,
        "source_route": source_route,
        "observed_at": observed_at,
    }


def _ingest_compliance_event(
    event: Mapping[str, Any],
    *,
    observed_at: str,
    source_route: str,
    records: Dict[str, PostRecord],
    version_index: Dict[str, str],
) -> Optional[Mapping[str, Any]]:
    if event.get("type") != "delete":
        raise ContractError("unsupported_compliance_event")
    post_id = str(event["post_id"])
    canonical_id = version_index.get(post_id, post_id)
    record = records.get(canonical_id)
    if record is None:
        record = PostRecord(
            canonical_post_id=canonical_id,
            current_post_id=post_id,
            version_ids=[post_id],
            content=None,
            deleted=True,
        )
        records[canonical_id] = record
        version_index[post_id] = canonical_id
    elif record.deleted:
        return None
    else:
        record.content = None
        record.deleted = True
    return {
        "kind": "delete",
        "canonical_post_id": canonical_id,
        "current_post_id": record.current_post_id,
        "deleted_version_id": post_id,
        "source_route": source_route,
        "observed_at": observed_at,
    }


def _max_post_id(left: Optional[str], right: Optional[str]) -> Optional[str]:
    values = [value for value in (left, right) if value is not None]
    if not values:
        return None
    if not all(value.isdigit() for value in values):
        raise ContractError("post_id_must_be_numeric")
    return max(values, key=int)


def _lead_time_seconds(created_at: Any, observed_at: str) -> Optional[int]:
    if not created_at:
        return None
    created = _parse_timestamp(str(created_at))
    observed = _parse_timestamp(observed_at)
    return max(0, int((observed - created).total_seconds()))


def _parse_timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _optional_string(value: Any) -> Optional[str]:
    return None if value is None else str(value)


def _money(value: Decimal) -> str:
    return str(value.quantize(Decimal("0.001")))
