#!/usr/bin/env python3
"""Pure, deterministic AI/EDA publish-gate calibration evaluator."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence, Tuple
from urllib.parse import urlparse


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_FIXTURE = Path(__file__).parent / "fixtures/historical-calibration-cases.json"

REASON_ORDER = (
    "NO_MATERIAL_CHANGE",
    "PRIMARY_SOURCE_MISSING",
    "VENDOR_CLAIM_ONLY",
    "COMPARISON_NOT_VALID",
    "REPRODUCIBILITY_TOO_LOW",
    "CONFLICT_UNRESOLVED",
    "SECURITY_OR_LICENSE_RISK",
)
GATE_ORDER = (
    "selection-score",
    "edition-roles",
    "material-change",
    "primary-source",
    "core-evidence-ceiling",
    "vendor-claim-only",
    "comparison-conditions",
    "reproducibility",
    "conflict-disclosure",
    "rights-and-security",
)
PROFILES = {
    "ai": {
        "score_keys": (
            "importance",
            "novelty",
            "verifiability",
            "decision_usefulness",
            "korean_relevance",
        ),
        "required_roles": {
            "ai-primary-evidence-reporter",
            "ai-evaluation-method-reviewer",
            "ai-desk",
        },
    },
    "eda": {
        "score_keys": (
            "flow_impact",
            "novelty",
            "condition_disclosure",
            "reproducibility",
            "practice_usefulness",
        ),
        "required_roles": {
            "eda-primary-evidence-reporter",
            "eda-repro-license-reviewer",
            "eda-desk",
        },
    },
}
EVIDENCE_RANK = {f"E{rank}": rank for rank in range(5)}
REPRODUCIBILITY_RANK = {f"R{rank}": rank for rank in range(4)}
MINIMUM_CORE_EVIDENCE = {
    "release-fact": "E1",
    "technical-change": "E2",
    "standard-change": "E2",
    "comparative-performance": "E3",
    "safety-superiority": "E3",
}
SOURCE_TYPES = {"P0", "P1", "P2", "I1", "S1", "S2"}
SOURCE_ORIGINS = {
    "vendor",
    "standards-body",
    "open-source-project",
    "independent",
    "academic",
}
COMPARISON_CONDITIONS = {
    "baseline",
    "workload",
    "hardware",
    "quality_equivalence",
    "statistical_scope",
}


class CalibrationError(ValueError):
    """Raised when a fixture violates the calibration contract."""


def load_fixture(path: Path = DEFAULT_FIXTURE) -> Mapping[str, Any]:
    try:
        with path.open(encoding="utf-8") as stream:
            value = json.load(stream)
    except (OSError, json.JSONDecodeError) as exc:
        raise CalibrationError(f"cannot load fixture {path}: {exc}") from exc
    if value.get("schema_version") != 1 or not isinstance(value.get("cases"), list):
        raise CalibrationError("fixture must have schema_version=1 and a cases array")
    return value


def _require(mapping: Mapping[str, Any], fields: Iterable[str], location: str) -> None:
    missing = sorted(set(fields) - set(mapping))
    if missing:
        raise CalibrationError(f"{location}: missing fields: {', '.join(missing)}")


def validate_case(case: Mapping[str, Any], requested_edition: str | None = None) -> None:
    _require(
        case,
        {
            "case_id",
            "edition",
            "historical_cutoff",
            "subject_ko",
            "candidate_scores",
            "roles_completed",
            "material_change",
            "reproducibility",
            "conflict_of_interest",
            "rights_and_security",
            "evidence_ceiling",
            "claim_ledger",
            "expected",
        },
        "case",
    )
    edition = case["edition"]
    if edition not in PROFILES:
        raise CalibrationError(f"{case['case_id']}: unknown edition {edition!r}")
    if requested_edition is not None and edition != requested_edition:
        raise CalibrationError(
            f"{case['case_id']}: fixture edition {edition!r} cannot run as {requested_edition!r}"
        )

    profile = PROFILES[edition]
    scores = case["candidate_scores"]
    if set(scores) != set(profile["score_keys"]):
        raise CalibrationError(f"{case['case_id']}: {edition} score keys are not isolated")
    if any(isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 2 for value in scores.values()):
        raise CalibrationError(f"{case['case_id']}: every score must be an integer from 0 to 2")

    roles = case["roles_completed"]
    if not isinstance(roles, list) or len(roles) != len(set(roles)):
        raise CalibrationError(f"{case['case_id']}: roles must be a unique list")
    wrong_prefix = sorted(role for role in roles if not role.startswith(f"{edition}-"))
    if wrong_prefix:
        raise CalibrationError(
            f"{case['case_id']}: cross-edition roles are forbidden: {', '.join(wrong_prefix)}"
        )

    if not isinstance(case["material_change"], bool):
        raise CalibrationError(f"{case['case_id']}: material_change must be boolean")
    if case["reproducibility"] not in REPRODUCIBILITY_RANK:
        raise CalibrationError(f"{case['case_id']}: invalid reproducibility")
    if case["evidence_ceiling"] not in EVIDENCE_RANK:
        raise CalibrationError(f"{case['case_id']}: invalid evidence_ceiling")

    conflict = case["conflict_of_interest"]
    rights = case["rights_and_security"]
    _require(conflict, {"disclosed", "notes_ko"}, f"{case['case_id']}.conflict")
    _require(rights, {"risks_resolved", "notes_ko"}, f"{case['case_id']}.rights")
    if not isinstance(conflict["disclosed"], bool) or not conflict["notes_ko"]:
        raise CalibrationError(f"{case['case_id']}: conflict disclosure is incomplete")
    if not isinstance(rights["risks_resolved"], bool) or not rights["notes_ko"]:
        raise CalibrationError(f"{case['case_id']}: rights/security review is incomplete")

    claims = case["claim_ledger"]
    if not isinstance(claims, list) or not claims:
        raise CalibrationError(f"{case['case_id']}: claim ledger must not be empty")
    claim_ids = [claim.get("claim_id") for claim in claims]
    if len(claim_ids) != len(set(claim_ids)):
        raise CalibrationError(f"{case['case_id']}: claim ids must be unique")
    if not any(claim.get("is_core") is True for claim in claims):
        raise CalibrationError(f"{case['case_id']}: at least one core claim is required")

    for claim in claims:
        _validate_claim(case["case_id"], claim)

    expected = case["expected"]
    _require(expected, {"decision", "score_total", "reason_codes", "failed_gates"}, "expected")
    if expected["decision"] not in {"publish-candidate", "no-publish"}:
        raise CalibrationError(f"{case['case_id']}: invalid expected decision")
    if any(reason not in REASON_ORDER for reason in expected["reason_codes"]):
        raise CalibrationError(f"{case['case_id']}: invalid expected reason code")


def _validate_claim(case_id: str, claim: Mapping[str, Any]) -> None:
    _require(
        claim,
        {"claim_id", "is_core", "claim_kind", "statement_ko", "evidence", "comparison"},
        f"{case_id}.claim",
    )
    if not isinstance(claim["is_core"], bool):
        raise CalibrationError(f"{case_id}.{claim['claim_id']}: is_core must be boolean")
    if claim["claim_kind"] not in MINIMUM_CORE_EVIDENCE:
        raise CalibrationError(f"{case_id}.{claim['claim_id']}: unknown claim kind")
    if not isinstance(claim["statement_ko"], str) or len(claim["statement_ko"]) < 10:
        raise CalibrationError(f"{case_id}.{claim['claim_id']}: statement is too short")
    if not isinstance(claim["evidence"], list) or not claim["evidence"]:
        raise CalibrationError(f"{case_id}.{claim['claim_id']}: evidence must not be empty")

    for source in claim["evidence"]:
        _require(
            source,
            {
                "source_url",
                "source_type",
                "evidence_grade",
                "origin",
                "version",
                "direct_or_derived",
                "limitations_ko",
                "conflicts_ko",
            },
            f"{case_id}.{claim['claim_id']}.evidence",
        )
        parsed = urlparse(source["source_url"])
        if parsed.scheme != "https" or not parsed.netloc:
            raise CalibrationError(f"{case_id}.{claim['claim_id']}: source URL must be HTTPS")
        if source["source_type"] not in SOURCE_TYPES:
            raise CalibrationError(f"{case_id}.{claim['claim_id']}: invalid source type")
        if source["evidence_grade"] not in EVIDENCE_RANK:
            raise CalibrationError(f"{case_id}.{claim['claim_id']}: invalid evidence grade")
        if source["origin"] not in SOURCE_ORIGINS:
            raise CalibrationError(f"{case_id}.{claim['claim_id']}: invalid source origin")
        if source["direct_or_derived"] not in {"direct", "derived"}:
            raise CalibrationError(f"{case_id}.{claim['claim_id']}: invalid derivation state")
        if not source["limitations_ko"] or not source["conflicts_ko"]:
            raise CalibrationError(f"{case_id}.{claim['claim_id']}: limits/conflicts are required")

    comparison = claim["comparison"]
    _require(comparison, {"required", "conditions"}, f"{case_id}.{claim['claim_id']}.comparison")
    if not isinstance(comparison["required"], bool):
        raise CalibrationError(f"{case_id}.{claim['claim_id']}: comparison.required must be boolean")
    conditions = comparison["conditions"]
    if comparison["required"] and set(conditions) != COMPARISON_CONDITIONS:
        raise CalibrationError(f"{case_id}.{claim['claim_id']}: comparison conditions incomplete")
    if not comparison["required"] and conditions:
        raise CalibrationError(f"{case_id}.{claim['claim_id']}: non-comparison claim has conditions")
    if any(not isinstance(value, bool) for value in conditions.values()):
        raise CalibrationError(f"{case_id}.{claim['claim_id']}: comparison conditions must be boolean")


def _claim_assessment(claim: Mapping[str, Any]) -> Dict[str, Any]:
    evidence = claim["evidence"]
    ceiling = max((source["evidence_grade"] for source in evidence), key=EVIDENCE_RANK.get)
    primary_present = any(source["source_type"] in {"P1", "P2"} for source in evidence)
    comparison = claim["comparison"]
    comparison_complete = (
        None if not comparison["required"] else all(comparison["conditions"].values())
    )
    vendor_only = bool(evidence) and all(source["origin"] == "vendor" for source in evidence)
    return {
        "claim_id": claim["claim_id"],
        "is_core": claim["is_core"],
        "claim_kind": claim["claim_kind"],
        "evidence_ceiling": ceiling,
        "minimum_evidence": MINIMUM_CORE_EVIDENCE[claim["claim_kind"]],
        "primary_present": primary_present,
        "source_types": sorted({source["source_type"] for source in evidence}),
        "comparison_complete": comparison_complete,
        "vendor_only": vendor_only,
    }


def _canonical_evidence_payload(case: Mapping[str, Any]) -> List[Mapping[str, Any]]:
    normalized = []
    for claim in sorted(case["claim_ledger"], key=lambda value: value["claim_id"]):
        evidence = []
        for source in sorted(
            claim["evidence"],
            key=lambda value: (value["source_url"], value["version"], value["source_type"]),
        ):
            item = dict(source)
            item["limitations_ko"] = sorted(item["limitations_ko"])
            item["conflicts_ko"] = sorted(item["conflicts_ko"])
            evidence.append(item)
        normalized.append(
            {
                "claim_id": claim["claim_id"],
                "is_core": claim["is_core"],
                "claim_kind": claim["claim_kind"],
                "statement_ko": claim["statement_ko"],
                "evidence": evidence,
                "comparison": claim["comparison"],
            }
        )
    return normalized


def _digest(value: Any) -> str:
    canonical = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def evaluate_case(
    case: Mapping[str, Any],
    requested_edition: str | None = None,
) -> Dict[str, Any]:
    validate_case(case, requested_edition)
    edition = case["edition"]
    profile = PROFILES[edition]
    score_total = sum(case["candidate_scores"].values())
    missing_roles = sorted(profile["required_roles"] - set(case["roles_completed"]))
    assessments = sorted(
        (_claim_assessment(claim) for claim in case["claim_ledger"]),
        key=lambda value: value["claim_id"],
    )
    core = [assessment for assessment in assessments if assessment["is_core"]]
    calculated_ceiling = min(core, key=lambda value: EVIDENCE_RANK[value["evidence_ceiling"]])[
        "evidence_ceiling"
    ]
    if calculated_ceiling != case["evidence_ceiling"]:
        raise CalibrationError(
            f"{case['case_id']}: declared evidence ceiling {case['evidence_ceiling']} "
            f"does not match core claims {calculated_ceiling}"
        )

    comparative = [
        assessment
        for assessment in core
        if assessment["claim_kind"] in {"comparative-performance", "safety-superiority"}
    ]
    primary_missing = any(not assessment["primary_present"] for assessment in core)
    core_grade_failed = any(
        EVIDENCE_RANK[assessment["evidence_ceiling"]]
        < EVIDENCE_RANK[assessment["minimum_evidence"]]
        for assessment in core
    )
    vendor_only = any(
        assessment["vendor_only"]
        and EVIDENCE_RANK[assessment["evidence_ceiling"]] < EVIDENCE_RANK["E3"]
        for assessment in comparative
    )
    comparison_failed = any(assessment["comparison_complete"] is False for assessment in comparative)
    reproducibility_failed = bool(comparative) and (
        REPRODUCIBILITY_RANK[case["reproducibility"]] < REPRODUCIBILITY_RANK["R2"]
    )

    failed_flags = {
        "selection-score": score_total < 7,
        "edition-roles": bool(missing_roles),
        "material-change": not case["material_change"],
        "primary-source": primary_missing,
        "core-evidence-ceiling": core_grade_failed,
        "vendor-claim-only": vendor_only,
        "comparison-conditions": comparison_failed,
        "reproducibility": reproducibility_failed,
        "conflict-disclosure": not case["conflict_of_interest"]["disclosed"],
        "rights-and-security": not case["rights_and_security"]["risks_resolved"],
    }
    reason_flags = {
        "NO_MATERIAL_CHANGE": not case["material_change"],
        "PRIMARY_SOURCE_MISSING": primary_missing,
        "VENDOR_CLAIM_ONLY": vendor_only,
        "COMPARISON_NOT_VALID": comparison_failed,
        "REPRODUCIBILITY_TOO_LOW": reproducibility_failed,
        "CONFLICT_UNRESOLVED": not case["conflict_of_interest"]["disclosed"],
        "SECURITY_OR_LICENSE_RISK": not case["rights_and_security"]["risks_resolved"],
    }
    failed_gates = [gate for gate in GATE_ORDER if failed_flags[gate]]
    reasons = [reason for reason in REASON_ORDER if reason_flags[reason]]
    decision = "publish-candidate" if not failed_gates else "no-publish"

    result = {
        "case_id": case["case_id"],
        "edition": edition,
        "decision": decision,
        "score_total": score_total,
        "score_breakdown": {
            key: case["candidate_scores"][key] for key in profile["score_keys"]
        },
        "evidence_ceiling": calculated_ceiling,
        "reproducibility": case["reproducibility"],
        "reason_codes": reasons,
        "failed_gates": failed_gates,
        "missing_roles": missing_roles,
        "claim_assessments": assessments,
        "evidence_digest": _digest(_canonical_evidence_payload(case)),
    }
    result["evaluation_digest"] = _digest(result)
    return result


def evaluate_fixture(fixture: Mapping[str, Any]) -> List[Dict[str, Any]]:
    case_ids = [case.get("case_id") for case in fixture["cases"]]
    if len(case_ids) != len(set(case_ids)):
        raise CalibrationError("fixture case ids must be unique")
    results = []
    for case in sorted(fixture["cases"], key=lambda value: value["case_id"]):
        result = evaluate_case(case)
        expected = case["expected"]
        observed = {
            "decision": result["decision"],
            "score_total": result["score_total"],
            "reason_codes": result["reason_codes"],
            "failed_gates": result["failed_gates"],
        }
        if observed != expected:
            raise CalibrationError(
                f"{case['case_id']}: calibration drift; expected {expected!r}, got {observed!r}"
            )
        results.append(result)
    return results


def _parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", type=Path, default=DEFAULT_FIXTURE)
    return parser.parse_args(argv)


def main(argv: Sequence[str] = ()) -> int:
    args = _parse_args(argv)
    try:
        fixture = load_fixture(args.fixture)
        results = evaluate_fixture(fixture)
    except CalibrationError as exc:
        print(json.dumps({"status": "failed", "error": str(exc)}, ensure_ascii=False))
        return 2

    print(
        json.dumps(
            {
                "status": "passed",
                "mode": "calibration-dry-run",
                "fixture_id": fixture["fixture_id"],
                "case_count": len(results),
                "results": results,
                "side_effects": [],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
