#!/usr/bin/env python3
"""Validate and materialize one public AI no-publish status record."""

from __future__ import annotations

import argparse
import json
import os
import re
from collections.abc import Mapping
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]
POLICY_ID = "ai-no-publish-status-v1"
SEOUL = ZoneInfo("Asia/Seoul")
PUBLICATION_ID = re.compile(r"^\d{4}-\d{2}-\d{2}$")
DECISION_KEYS = frozenset({
    "schema_version",
    "publication_id",
    "decision",
    "reason",
    "discovery_review",
})
DISCOVERY_REVIEW_KEYS = frozenset({"signals", "alternatives"})


class NoPublishError(ValueError):
    """Raised when a no-publish status cannot cross the public boundary."""


def validate_record_list(value: Any, *, field: str) -> None:
    if not isinstance(value, list):
        raise NoPublishError(f"no-publish {field} must be a list")
    if any(not isinstance(item, Mapping) or not item for item in value):
        raise NoPublishError(f"no-publish {field} entries must be non-empty objects")


def validate_decision(
    decision_path: Path,
    publication_id: str,
    *,
    repo_root: Path = ROOT,
    require_today: bool = True,
) -> dict[str, Any]:
    if not PUBLICATION_ID.fullmatch(publication_id):
        raise NoPublishError("invalid AI no-publish publication id")
    if require_today and publication_id != datetime.now(SEOUL).date().isoformat():
        raise NoPublishError("AI no-publish publication id is not today's Seoul date")

    root = repo_root.resolve()
    allowed = (root / "var/runs").resolve()
    resolved = decision_path.resolve()
    try:
        resolved.relative_to(allowed)
    except ValueError as error:
        raise NoPublishError("no-publish decision must be below var/runs") from error
    if decision_path.is_symlink() or not decision_path.is_file():
        raise NoPublishError("no-publish decision must be a regular file")

    decision_bytes = decision_path.read_bytes()
    try:
        value = json.loads(decision_bytes)
    except json.JSONDecodeError as error:
        raise NoPublishError("no-publish decision is not valid JSON") from error
    if not isinstance(value, dict) or set(value) != DECISION_KEYS:
        raise NoPublishError("no-publish decision fields do not match the public contract")
    if value.get("schema_version") != 1:
        raise NoPublishError("unsupported no-publish schema version")
    if value.get("publication_id") != publication_id:
        raise NoPublishError("no-publish publication id mismatch")
    if value.get("decision") != "no-publish":
        raise NoPublishError("AI status record must contain a no-publish decision")
    reason = value.get("reason")
    if not isinstance(reason, str) or len(reason.strip()) < 12:
        raise NoPublishError("no-publish reason must contain a meaningful explanation")

    discovery_review = value.get("discovery_review")
    if (
        not isinstance(discovery_review, dict)
        or set(discovery_review) != DISCOVERY_REVIEW_KEYS
    ):
        raise NoPublishError("no-publish discovery review fields are invalid")
    validate_record_list(discovery_review.get("signals"), field="signals")
    validate_record_list(discovery_review.get("alternatives"), field="alternatives")

    if (root / f"content/ai/{publication_id}").exists():
        raise NoPublishError("AI article and no-publish status cannot share a date")
    if (root / f"decisions/ai/{publication_id}").exists():
        raise NoPublishError("AI decision path already exists")

    return {
        "publication_id": publication_id,
        "decision_bytes": decision_bytes,
        "decision_path": decision_path,
    }


def materialize(
    candidate: Mapping[str, Any],
    *,
    repo_root: Path = ROOT,
) -> dict[str, Any]:
    publication_id = str(candidate["publication_id"])
    decision_root = repo_root / f"decisions/ai/{publication_id}"
    target = decision_root / "no-publish.json"
    created_root = False
    try:
        decision_root.mkdir(parents=True)
        created_root = True
        temporary = target.with_suffix(".json.tmp")
        temporary.write_bytes(bytes(candidate["decision_bytes"]))
        os.replace(temporary, target)
    except Exception:
        target.unlink(missing_ok=True)
        temporary = target.with_suffix(".json.tmp")
        temporary.unlink(missing_ok=True)
        if created_root:
            try:
                decision_root.rmdir()
            except OSError:
                pass
        raise

    return {
        "status": "materialized",
        "policy_id": POLICY_ID,
        "publication_id": publication_id,
        "decision_path": str(target.relative_to(repo_root)),
        "route": "/ai/",
        "external_actions": {"commit": False, "push": False, "deploy": False},
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate and materialize one public AI no-publish status.",
    )
    parser.add_argument("--decision", required=True, type=Path)
    parser.add_argument("--publication-id", required=True)
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args()

    try:
        candidate = validate_decision(args.decision, args.publication_id)
        if args.check_only:
            result = {
                "status": "validated",
                "policy_id": POLICY_ID,
                "publication_id": args.publication_id,
                "external_actions": {
                    "content": False,
                    "commit": False,
                    "push": False,
                    "deploy": False,
                },
            }
        else:
            result = materialize(candidate)
    except (NoPublishError, OSError) as error:
        print(json.dumps({"status": "rejected", "error": str(error)}, ensure_ascii=False))
        return 2

    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
