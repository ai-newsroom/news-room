"""Deterministic promotion evaluator for already-extracted X signal claims.

The X signal itself always remains S2.  This module evaluates only the external
evidence bundle linked to each claim and performs no network, browser, or LLM work.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import date, datetime
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple


SIGNAL_ONLY = "signal-only"
ANNOUNCEMENT_CONFIRMED = "announcement-confirmed"
PRIMARY_SOURCE_LINKED = "primary-source-linked"
INDEPENDENTLY_VERIFIED = "independently-verified"
REJECTED = "rejected"

PROMOTION_STATUSES = {
    SIGNAL_ONLY,
    ANNOUNCEMENT_CONFIRMED,
    PRIMARY_SOURCE_LINKED,
    INDEPENDENTLY_VERIFIED,
    REJECTED,
}
STATUS_RANK = {
    SIGNAL_ONLY: 0,
    ANNOUNCEMENT_CONFIRMED: 1,
    PRIMARY_SOURCE_LINKED: 2,
    INDEPENDENTLY_VERIFIED: 3,
}
SOURCE_TYPES = {"P0", "P1", "P2", "I1", "S1", "S2", "unavailable"}
SOURCE_ORDER = {value: index for index, value in enumerate(("P0", "P1", "P2", "I1", "S1", "S2", "unavailable"))}
REPRO_RANK = {"R0": 0, "R1": 1, "R2": 2, "R3": 3}
EVIDENCE_RANK = {"E0": 0, "E1": 1, "E2": 2, "E3": 3, "E4": 4}

CLAIM_KINDS = {"speech-act", "announcement", "technical", "performance", "opinion"}

REQUIRED_SIGNAL_FIELDS = {
    "signal_id",
    "edition",
    "author",
    "post",
    "observed_at",
    "edit_state",
    "thread_context",
    "outbound_links",
    "source_evidence",
    "extracted_claims",
    "promotion_status",
    "access_constraints",
}
REQUIRED_AUTHOR_FIELDS = {
    "registry_account_id",
    "real_name",
    "x_handle",
    "affiliation_snapshot",
    "conflicts",
}
REQUIRED_POST_FIELDS = {"post_id", "url", "posted_at", "text_excerpt"}
REQUIRED_EDIT_FIELDS = {
    "canonical_post_id",
    "current_post_id",
    "version_ids",
    "is_deleted",
    "material_change",
    "latest_version_verified_at",
}
REQUIRED_THREAD_FIELDS = {
    "conversation_id",
    "reply_to_post_id",
    "quoted_post_id",
    "thread_post_ids",
    "completeness",
}
REQUIRED_LINK_FIELDS = {
    "link_id",
    "original_url",
    "resolved_url",
    "artifact_kind",
    "status",
    "accessed_at",
    "version",
    "published_at",
}
REQUIRED_SOURCE_FIELDS = {
    "source_id",
    "url",
    "source_type",
    "discovered_via",
    "relation",
    "accessible",
    "public",
    "version",
    "published_at",
    "conditions_complete",
    "independent",
    "reproduction_state",
    "reproduction_log_url",
}
REQUIRED_CLAIM_FIELDS = {
    "claim_id",
    "claim_kind",
    "claim_text_ko",
    "material",
    "subject_version",
    "claim_date",
    "source_refs",
}


class ContractError(ValueError):
    """A signal record does not meet the investigation contract."""


def evaluate_signal(raw_signal: Mapping[str, Any]) -> Mapping[str, Any]:
    """Validate and return a new signal with claim and aggregate promotion results."""

    validate_signal(raw_signal)
    signal: Dict[str, Any] = deepcopy(dict(raw_signal))
    sources = {item["source_id"]: item for item in signal["source_evidence"]}

    evaluated_claims = [
        _evaluate_claim(signal, claim, sources)
        for claim in signal["extracted_claims"]
    ]
    signal["extracted_claims"] = evaluated_claims

    material_claims = [claim for claim in evaluated_claims if claim["material"]]
    considered = material_claims or evaluated_claims
    aggregate_status = _aggregate_status(considered)
    aggregate_mapping = _aggregate_mapping(aggregate_status, considered)
    reason_codes = _ordered_unique(
        reason
        for claim in considered
        for reason in claim["reason_codes"]
    )

    signal["promotion_status"] = aggregate_status
    signal["promotion_mapping"] = aggregate_mapping
    signal["reason_codes"] = reason_codes
    signal["editorial_disposition"] = (
        "review-ready"
        if considered and all(claim["review_ready"] for claim in considered)
        else "no-publish"
    )
    signal["retention_action"] = _retention_action(signal, reason_codes)
    signal["recheck_triggers"] = _recheck_triggers(reason_codes)

    if signal["edit_state"]["is_deleted"]:
        signal["post"]["text_excerpt"] = None

    return signal


def validate_signal(signal: Mapping[str, Any]) -> None:
    _require_fields(signal, REQUIRED_SIGNAL_FIELDS, "signal")
    if signal["edition"] != "ai":
        raise ContractError("edition_must_be_ai")
    if signal["promotion_status"] not in PROMOTION_STATUSES:
        raise ContractError("invalid_initial_promotion_status")
    _parse_timestamp(str(signal["observed_at"]))

    author = _mapping(signal["author"], "author")
    _require_fields(author, REQUIRED_AUTHOR_FIELDS, "author")
    if not str(author["x_handle"]).startswith("@"):
        raise ContractError("author_handle_must_start_with_at")
    if not isinstance(author["conflicts"], list):
        raise ContractError("author_conflicts_must_be_list")

    post = _mapping(signal["post"], "post")
    _require_fields(post, REQUIRED_POST_FIELDS, "post")
    _parse_timestamp(str(post["posted_at"]))
    if str(post["post_id"]) not in str(post["url"]):
        raise ContractError("post_url_must_contain_post_id")

    edit = _mapping(signal["edit_state"], "edit_state")
    _require_fields(edit, REQUIRED_EDIT_FIELDS, "edit_state")
    versions = [str(value) for value in edit["version_ids"]]
    if not versions or versions[0] != str(edit["canonical_post_id"]):
        raise ContractError("edit_chain_must_start_with_canonical_id")
    if versions[-1] != str(edit["current_post_id"]):
        raise ContractError("edit_chain_must_end_with_current_id")
    if str(post["post_id"]) != str(edit["current_post_id"]):
        raise ContractError("post_id_must_match_current_edit_id")
    if signal["signal_id"] != "x:{}".format(edit["canonical_post_id"]):
        raise ContractError("signal_id_must_use_canonical_post_id")
    if edit["latest_version_verified_at"] is not None:
        _parse_timestamp(str(edit["latest_version_verified_at"]))

    thread = _mapping(signal["thread_context"], "thread_context")
    _require_fields(thread, REQUIRED_THREAD_FIELDS, "thread_context")
    if thread["completeness"] not in {"complete", "partial", "unknown"}:
        raise ContractError("invalid_thread_completeness")
    if not isinstance(thread["thread_post_ids"], list):
        raise ContractError("thread_post_ids_must_be_list")

    links = _sequence(signal["outbound_links"], "outbound_links")
    link_ids = set()
    resolved_urls = set()
    for link in links:
        item = _mapping(link, "outbound_link")
        _require_fields(item, REQUIRED_LINK_FIELDS, "outbound_link")
        if item["link_id"] in link_ids:
            raise ContractError("duplicate_link_id")
        link_ids.add(item["link_id"])
        resolved_urls.add(item["resolved_url"])
        _parse_date(str(item["accessed_at"]))
        if item["published_at"] is not None:
            _parse_date(str(item["published_at"]))

    evidence = _sequence(signal["source_evidence"], "source_evidence")
    source_ids = set()
    for source in evidence:
        item = _mapping(source, "source_evidence_item")
        _require_fields(item, REQUIRED_SOURCE_FIELDS, "source_evidence_item")
        if item["source_id"] in source_ids:
            raise ContractError("duplicate_source_id")
        source_ids.add(item["source_id"])
        if item["source_type"] not in SOURCE_TYPES:
            raise ContractError("invalid_source_type")
        if item["relation"] not in {"supports", "contradicts", "context"}:
            raise ContractError("invalid_source_relation")
        if item["reproduction_state"] not in REPRO_RANK:
            raise ContractError("invalid_reproduction_state")
        if item["published_at"] is not None:
            _parse_date(str(item["published_at"]))
        if item["discovered_via"] == "outbound" and item["url"] not in resolved_urls:
            raise ContractError("outbound_source_url_not_preserved")

    claims = _sequence(signal["extracted_claims"], "extracted_claims")
    if not claims:
        raise ContractError("at_least_one_claim_required")
    claim_ids = set()
    for claim in claims:
        item = _mapping(claim, "claim")
        _require_fields(item, REQUIRED_CLAIM_FIELDS, "claim")
        if item["claim_id"] in claim_ids:
            raise ContractError("duplicate_claim_id")
        claim_ids.add(item["claim_id"])
        if item["claim_kind"] not in CLAIM_KINDS:
            raise ContractError("invalid_claim_kind")
        if item["claim_date"] is not None:
            _parse_date(str(item["claim_date"]))
        unknown_sources = set(item["source_refs"]) - source_ids
        if unknown_sources:
            raise ContractError("unknown_claim_source_ref:{}".format(sorted(unknown_sources)))

    constraints = _mapping(signal["access_constraints"], "access_constraints")
    if "embargo_or_nda_implied" not in constraints or "notes" not in constraints:
        raise ContractError("access_constraints_fields_missing")


def _evaluate_claim(
    signal: Mapping[str, Any],
    raw_claim: Mapping[str, Any],
    source_index: Mapping[str, Mapping[str, Any]],
) -> Mapping[str, Any]:
    claim = deepcopy(dict(raw_claim))
    sources = [source_index[source_id] for source_id in claim["source_refs"]]

    hard_rejection = _hard_rejection(signal, sources)
    if hard_rejection:
        return _finish_claim(
            claim,
            REJECTED,
            sources,
            "E0",
            "R0",
            [hard_rejection],
            review_ready=False,
        )

    contradictory = [
        source
        for source in sources
        if source["relation"] == "contradicts"
        and source["source_type"] in {"P1", "P2", "I1"}
        and source["accessible"]
        and source["public"]
    ]
    if contradictory:
        return _finish_claim(
            claim,
            REJECTED,
            contradictory,
            "E0",
            "R0",
            ["CLAIM_CONTRADICTED"],
            review_ready=False,
        )

    if claim["claim_kind"] == "opinion":
        return _finish_claim(
            claim,
            SIGNAL_ONLY,
            [],
            "E0",
            "R0",
            ["OPINION_ONLY"],
            review_ready=False,
        )

    if not sources:
        return _finish_claim(
            claim,
            SIGNAL_ONLY,
            [],
            "E0",
            "R0",
            ["PRIMARY_SOURCE_MISSING"],
            review_ready=False,
        )

    public_support = [
        source
        for source in sources
        if source["relation"] == "supports"
        and source["accessible"]
        and source["public"]
    ]
    if not public_support:
        return _finish_claim(
            claim,
            SIGNAL_ONLY,
            sources,
            "E0",
            "R0",
            ["PRIMARY_SOURCE_UNAVAILABLE"],
            review_ready=False,
        )

    matching = [
        source for source in public_support if _version_and_date_match(claim, source)
    ]
    if not matching:
        return _finish_claim(
            claim,
            SIGNAL_ONLY,
            public_support,
            "E0",
            "R0",
            ["VERSION_OR_DATE_MISMATCH"],
            review_ready=False,
        )

    if claim["claim_kind"] == "speech-act":
        return _finish_claim(
            claim,
            SIGNAL_ONLY,
            matching,
            "E0",
            "R0",
            ["SPEECH_ACT_ONLY"],
            review_ready=False,
        )

    official = [source for source in matching if source["source_type"] in {"P0", "P1"}]
    if claim["claim_kind"] == "announcement":
        if official:
            return _finish_claim(
                claim,
                ANNOUNCEMENT_CONFIRMED,
                official,
                "E1",
                "R0",
                [],
                review_ready=True,
            )
        return _finish_claim(
            claim,
            SIGNAL_ONLY,
            matching,
            "E0",
            "R0",
            ["PRIMARY_SOURCE_MISSING"],
            review_ready=False,
        )

    primary = [
        source
        for source in matching
        if source["source_type"] == "P1" and source["conditions_complete"]
    ]
    executable = [
        source
        for source in matching
        if source["source_type"] == "P2" and source["conditions_complete"]
    ]

    if claim["claim_kind"] == "performance" and (not primary or not executable):
        return _finish_claim(
            claim,
            SIGNAL_ONLY,
            matching,
            "E0",
            "R0",
            ["PERFORMANCE_CONDITIONS_MISSING"],
            review_ready=False,
        )
    if claim["claim_kind"] == "technical" and not primary:
        reason = "VENDOR_CLAIM_ONLY" if any(
            source["source_type"] == "P0" for source in matching
        ) else "PRIMARY_SOURCE_MISSING"
        return _finish_claim(
            claim,
            SIGNAL_ONLY,
            matching,
            "E0",
            "R0",
            [reason],
            review_ready=False,
        )

    evidence_bundle = primary + executable
    independent = [
        source
        for source in matching
        if source["source_type"] == "I1" and source["independent"]
    ]

    if independent:
        evidence_bundle += independent
        reproduced = any(
            source["reproduction_state"] == "R3"
            and source["reproduction_log_url"]
            for source in independent
        )
        evidence_grade = "E4" if reproduced else "E3"
        reproducibility = "R3" if reproduced else _bundle_reproducibility(evidence_bundle)
        status = INDEPENDENTLY_VERIFIED
    else:
        evidence_grade = "E2"
        reproducibility = _bundle_reproducibility(evidence_bundle)
        status = PRIMARY_SOURCE_LINKED

    reasons: List[str] = []
    review_ready = True
    if _has_conflict(signal) and claim["claim_kind"] in {"technical", "performance"}:
        if status != INDEPENDENTLY_VERIFIED:
            reasons.append("CONFLICT_UNRESOLVED")
            review_ready = False

    return _finish_claim(
        claim,
        status,
        evidence_bundle,
        evidence_grade,
        reproducibility,
        reasons,
        review_ready=review_ready,
    )


def _hard_rejection(
    signal: Mapping[str, Any], sources: Sequence[Mapping[str, Any]]
) -> Optional[str]:
    edit = signal["edit_state"]
    if edit["is_deleted"]:
        return "POST_DELETED"
    if edit["material_change"] and not edit["latest_version_verified_at"]:
        return "EDIT_NOT_REVERIFIED"
    if signal["access_constraints"]["embargo_or_nda_implied"]:
        return "SECURITY_OR_LICENSE_RISK"
    if any(not source["public"] and source["accessible"] for source in sources):
        return "SECURITY_OR_LICENSE_RISK"
    return None


def _version_and_date_match(
    claim: Mapping[str, Any], source: Mapping[str, Any]
) -> bool:
    if not claim["subject_version"] or not claim["claim_date"]:
        return False
    if source["version"] != claim["subject_version"] or not source["published_at"]:
        return False
    if (
        source["source_type"] in {"P0", "P1", "P2"}
        and source["published_at"] != claim["claim_date"]
    ):
        return False
    return True


def _finish_claim(
    claim: Dict[str, Any],
    status: str,
    evidence_sources: Sequence[Mapping[str, Any]],
    evidence_grade: str,
    reproducibility: str,
    reason_codes: Sequence[str],
    *,
    review_ready: bool,
) -> Mapping[str, Any]:
    claim["promotion_status"] = status
    claim["promotion_mapping"] = {
        "signal_source_type": "S2",
        "evidence_source_types": _source_types(evidence_sources),
        "evidence_grade": evidence_grade,
        "reproducibility": reproducibility,
    }
    claim["reason_codes"] = list(reason_codes)
    claim["review_ready"] = review_ready
    return claim


def _aggregate_status(claims: Sequence[Mapping[str, Any]]) -> str:
    statuses = [claim["promotion_status"] for claim in claims]
    if REJECTED in statuses:
        return REJECTED
    return min(statuses, key=lambda status: STATUS_RANK[status])


def _aggregate_mapping(
    status: str, claims: Sequence[Mapping[str, Any]]
) -> Mapping[str, Any]:
    source_types = _ordered_unique(
        source_type
        for claim in claims
        for source_type in claim["promotion_mapping"]["evidence_source_types"]
    )
    source_types.sort(key=lambda value: SOURCE_ORDER[value])
    if status in {SIGNAL_ONLY, REJECTED}:
        evidence_grade = "E0"
        reproducibility = "R0"
    else:
        evidence_grade = min(
            (claim["promotion_mapping"]["evidence_grade"] for claim in claims),
            key=lambda value: EVIDENCE_RANK[value],
        )
        reproducibility = min(
            (claim["promotion_mapping"]["reproducibility"] for claim in claims),
            key=lambda value: REPRO_RANK[value],
        )
    return {
        "signal_source_type": "S2",
        "evidence_source_types": source_types,
        "evidence_grade": evidence_grade,
        "reproducibility": reproducibility,
    }


def _bundle_reproducibility(sources: Sequence[Mapping[str, Any]]) -> str:
    states = [source["reproduction_state"] for source in sources]
    if any(state in {"R2", "R3"} for state in states):
        return "R2"
    return "R1"


def _source_types(sources: Sequence[Mapping[str, Any]]) -> List[str]:
    values = _ordered_unique(source["source_type"] for source in sources)
    return sorted(values, key=lambda value: SOURCE_ORDER[value])


def _has_conflict(signal: Mapping[str, Any]) -> bool:
    return any(
        str(value).strip() and str(value).strip() != "없음"
        for value in signal["author"]["conflicts"]
    )


def _retention_action(signal: Mapping[str, Any], reasons: Sequence[str]) -> str:
    if "POST_DELETED" in reasons:
        return "tombstone-purge-content"
    if "EDIT_NOT_REVERIFIED" in reasons:
        return "rehydrate-latest-version"
    if "SECURITY_OR_LICENSE_RISK" in reasons:
        return "discard-restricted-material"
    return "retain-investigation-record"


def _recheck_triggers(reason_codes: Sequence[str]) -> List[str]:
    trigger_map = {
        "PRIMARY_SOURCE_MISSING": "public-primary-source-published",
        "PRIMARY_SOURCE_UNAVAILABLE": "primary-source-becomes-public",
        "VERSION_OR_DATE_MISMATCH": "matching-version-and-date-confirmed",
        "POST_DELETED": "none-deleted-post-is-not-restored-by-assumption",
        "EDIT_NOT_REVERIFIED": "latest-post-version-rehydrated",
        "OPINION_ONLY": "public-technical-artifact-published",
        "SECURITY_OR_LICENSE_RISK": "same-evidence-published-without-restriction",
        "CONFLICT_UNRESOLVED": "independent-I1-published",
        "CLAIM_CONTRADICTED": "contradiction-resolved-with-comparable-conditions",
        "PERFORMANCE_CONDITIONS_MISSING": "benchmark-conditions-and-P2-published",
        "VENDOR_CLAIM_ONLY": "technical-P1-or-independent-I1-published",
        "SPEECH_ACT_ONLY": "technical-primary-source-published",
    }
    return _ordered_unique(
        trigger_map[reason]
        for reason in reason_codes
        if reason in trigger_map
    )


def _require_fields(
    value: Mapping[str, Any], required: Iterable[str], label: str
) -> None:
    missing = set(required) - set(value)
    if missing:
        raise ContractError("{} missing {}".format(label, sorted(missing)))


def _mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ContractError("{}_must_be_mapping".format(label))
    return value


def _sequence(value: Any, label: str) -> Sequence[Any]:
    if not isinstance(value, list):
        raise ContractError("{}_must_be_list".format(label))
    return value


def _ordered_unique(values: Iterable[str]) -> List[str]:
    result: List[str] = []
    seen = set()
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


def _parse_timestamp(value: str) -> datetime:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ContractError("invalid_timestamp:{}".format(value)) from error


def _parse_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as error:
        raise ContractError("invalid_date:{}".format(value)) from error
