#!/usr/bin/env python3
"""Atomically write and re-parse exactly one designated campaign result."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence


SCHEMA_VERSION = 1
TOOL_NAME = "campaign-result-handoff"
TOOL_VERSION = 1
OVERHEAD_BUDGET_MS = 2_000
RUN_ID_PATTERN = re.compile(r"campaign_run_[0-9a-f]{32}")
RESULT_FIELDS = ("status", "summary", "evidence", "follow_ups")
FOLLOW_UP_FIELDS = (
    "title",
    "description",
    "acceptance_criteria",
    "priority",
    "risk",
    "kind",
    "objective_id",
    "capability_experiment",
)
EXPERIMENT_FIELDS = (
    "capability",
    "hypothesis",
    "success_measure",
    "rollback_plan",
)


class HandoffError(RuntimeError):
    """A stable, machine-readable result handoff failure."""

    def __init__(self, code: str, detail: str):
        super().__init__(detail)
        self.code = code
        self.detail = detail


def expected_result_path(repo: Path | str, run_id: str) -> Path:
    """Return the only result path authorized for a run."""

    if RUN_ID_PATTERN.fullmatch(run_id) is None:
        raise HandoffError(
            "invalid_run_id",
            "run_id must be campaign_run_ plus 32 lowercase hex digits",
        )
    root = Path(os.path.abspath(os.fspath(repo)))
    return root / ".coco-agents" / "campaigns" / "runs" / run_id / "result.json"


def validate_target(
    repo: Path | str, run_id: str, result_path: Path | str
) -> Path:
    """Reject any target other than the exact result path for run_id."""

    expected = expected_result_path(repo, run_id)
    supplied = Path(os.path.abspath(os.fspath(result_path)))
    if supplied != expected:
        raise HandoffError(
            "result_path_mismatch",
            f"expected {expected}, received {supplied}",
        )

    root = Path(os.path.abspath(os.fspath(repo)))
    current = root
    for component in (".coco-agents", "campaigns", "runs", run_id):
        current = current / component
        if current.is_symlink():
            raise HandoffError(
                "symlinked_result_parent",
                f"result parent must not be a symlink: {current}",
            )
    if supplied.is_symlink():
        raise HandoffError(
            "symlinked_result_file", "result.json must not be a symlink"
        )
    return supplied


def validate_contract(value: Any) -> Mapping[str, Any]:
    """Validate the complete result contract, including nested follow-ups."""

    if not isinstance(value, dict):
        raise HandoffError(
            "contract_not_object", "result contract must be a JSON object"
        )
    _require_exact_fields(value, RESULT_FIELDS, "result")
    if value["status"] not in {"completed", "blocked"}:
        raise HandoffError(
            "invalid_status", "status must be completed or blocked"
        )
    if not _nonempty_string(value["summary"]):
        raise HandoffError(
            "invalid_summary", "summary must be a non-empty string"
        )
    if not isinstance(value["evidence"], list) or any(
        not _nonempty_string(item) for item in value["evidence"]
    ):
        raise HandoffError(
            "invalid_evidence",
            "evidence must be an array of non-empty strings",
        )
    if not isinstance(value["follow_ups"], list):
        raise HandoffError(
            "invalid_follow_ups", "follow_ups must be an array"
        )

    for index, follow_up in enumerate(value["follow_ups"]):
        location = f"follow_ups[{index}]"
        if not isinstance(follow_up, dict):
            raise HandoffError(
                "invalid_follow_up", f"{location} must be an object"
            )
        _require_exact_fields(follow_up, FOLLOW_UP_FIELDS, location)
        for field in ("title", "description"):
            if not _nonempty_string(follow_up[field]):
                raise HandoffError(
                    "invalid_follow_up",
                    f"{location}.{field} must be a non-empty string",
                )
        criteria = follow_up["acceptance_criteria"]
        if not isinstance(criteria, list) or any(
            not _nonempty_string(item) for item in criteria
        ):
            raise HandoffError(
                "invalid_follow_up",
                f"{location}.acceptance_criteria must be an array of non-empty strings",
            )
        priority = follow_up["priority"]
        if (
            isinstance(priority, bool)
            or not isinstance(priority, int)
            or priority < 0
        ):
            raise HandoffError(
                "invalid_follow_up",
                f"{location}.priority must be a non-negative integer",
            )
        if follow_up["risk"] not in {"low", "medium", "high"}:
            raise HandoffError(
                "invalid_follow_up", f"{location}.risk is invalid"
            )
        if follow_up["kind"] not in {"product", "capability"}:
            raise HandoffError(
                "invalid_follow_up", f"{location}.kind is invalid"
            )
        objective_id = follow_up["objective_id"]
        if objective_id is not None and not _nonempty_string(objective_id):
            raise HandoffError(
                "invalid_follow_up",
                f"{location}.objective_id must be null or a string",
            )
        experiment = follow_up["capability_experiment"]
        if experiment is not None:
            if not isinstance(experiment, dict):
                raise HandoffError(
                    "invalid_capability_experiment",
                    f"{location}.capability_experiment must be null or an object",
                )
            _require_exact_fields(
                experiment,
                EXPERIMENT_FIELDS,
                f"{location}.capability_experiment",
            )
            if any(
                not _nonempty_string(experiment[field])
                for field in EXPERIMENT_FIELDS
            ):
                raise HandoffError(
                    "invalid_capability_experiment",
                    f"{location}.capability_experiment fields must be non-empty strings",
                )
    return value


def parse_contract_bytes(payload: bytes) -> Mapping[str, Any]:
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as error:
        raise HandoffError("invalid_utf8", "result must be UTF-8") from error
    try:
        value = json.loads(text)
    except json.JSONDecodeError as error:
        raise HandoffError(
            "invalid_json",
            f"JSON parse failed at line {error.lineno}, column {error.colno}",
        ) from error
    return validate_contract(value)


def verify_result(
    repo: Path | str,
    run_id: str,
    result_path: Path | str,
    *,
    started: Optional[float] = None,
) -> Mapping[str, Any]:
    """Read only the designated result and return re-parse evidence."""

    began = time.monotonic() if started is None else started
    target = validate_target(repo, run_id, result_path)
    try:
        metadata = target.lstat()
    except FileNotFoundError as error:
        raise HandoffError(
            "result_missing", f"result file does not exist: {target}"
        ) from error
    if not stat.S_ISREG(metadata.st_mode):
        raise HandoffError(
            "result_not_regular_file", "result path must be a regular file"
        )
    try:
        payload = target.read_bytes()
    except OSError as error:
        raise HandoffError("result_read_failed", str(error)) from error
    contract = parse_contract_bytes(payload)
    duration_ms = round((time.monotonic() - began) * 1_000, 3)
    return {
        "schema_version": SCHEMA_VERSION,
        "tool": TOOL_NAME,
        "tool_version": TOOL_VERSION,
        "status": "passed",
        "mode": "verify",
        "run_id": run_id,
        "result_path": str(target),
        "result_sha256": hashlib.sha256(payload).hexdigest(),
        "result_bytes": len(payload),
        "contract_status": contract["status"],
        "checks": {
            "exact_run_path": True,
            "file_exists": True,
            "regular_file": True,
            "utf8": True,
            "json_parsed": True,
            "contract_valid": True,
            "read_back_parse_confirmed": True,
        },
        "instrumentation": {
            "duration_ms": duration_ms,
            "overhead_budget_ms": OVERHEAD_BUDGET_MS,
            "other_campaign_state_files_read": 0,
            "other_campaign_state_files_written": 0,
        },
    }


def write_result(
    repo: Path | str,
    run_id: str,
    result_path: Path | str,
    payload: bytes,
) -> Mapping[str, Any]:
    """Validate, atomically replace the target, and immediately re-parse it."""

    started = time.monotonic()
    target = validate_target(repo, run_id, result_path)
    contract = parse_contract_bytes(payload)
    parent = target.parent
    if not parent.is_dir():
        raise HandoffError(
            "result_parent_missing", f"run directory does not exist: {parent}"
        )

    serialized = (
        json.dumps(
            contract, ensure_ascii=False, indent=2, sort_keys=False
        )
        + "\n"
    ).encode("utf-8")
    descriptor = None
    temporary_path = None
    try:
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=".result.json.",
            suffix=".tmp",
            dir=str(parent),
        )
        temporary_path = Path(temporary_name)
        with os.fdopen(descriptor, "wb") as stream:
            descriptor = None
            stream.write(serialized)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_path, target)
        temporary_path = None
    except OSError as error:
        raise HandoffError("atomic_write_failed", str(error)) from error
    finally:
        if descriptor is not None:
            os.close(descriptor)
        if temporary_path is not None:
            try:
                temporary_path.unlink()
            except FileNotFoundError:
                pass

    report = dict(
        verify_result(repo, run_id, target, started=started)
    )
    report["mode"] = "write-and-verify"
    report["checks"] = {
        **report["checks"],
        "validated_before_write": True,
        "same_directory_atomic_replace": True,
    }
    return report


def _require_exact_fields(
    value: Mapping[str, Any], expected: Sequence[str], location: str
) -> None:
    actual = set(value)
    required = set(expected)
    if actual != required:
        missing = sorted(required - actual)
        unknown = sorted(actual - required)
        details = []
        if missing:
            details.append("missing=" + ",".join(missing))
        if unknown:
            details.append("unknown=" + ",".join(unknown))
        raise HandoffError(
            "contract_fields_mismatch",
            f"{location} fields do not match contract ({'; '.join(details)})",
        )


def _nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Atomically write or verify exactly one campaign result.json."
        )
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("write", "verify"):
        subparser = subparsers.add_parser(command)
        subparser.add_argument("--repo", required=True)
        subparser.add_argument("--run-id", required=True)
        subparser.add_argument("--result-path", required=True)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    started = time.monotonic()
    arguments = _parser().parse_args(argv)
    try:
        if arguments.command == "write":
            report = write_result(
                arguments.repo,
                arguments.run_id,
                arguments.result_path,
                sys.stdin.buffer.read(),
            )
        else:
            report = verify_result(
                arguments.repo,
                arguments.run_id,
                arguments.result_path,
                started=started,
            )
    except HandoffError as error:
        report = {
            "schema_version": SCHEMA_VERSION,
            "tool": TOOL_NAME,
            "tool_version": TOOL_VERSION,
            "status": "failed",
            "mode": arguments.command,
            "run_id": arguments.run_id,
            "result_path": arguments.result_path,
            "error": error.code,
            "detail": error.detail,
            "instrumentation": {
                "duration_ms": round(
                    (time.monotonic() - started) * 1_000, 3
                ),
                "overhead_budget_ms": OVERHEAD_BUDGET_MS,
                "other_campaign_state_files_read": 0,
                "other_campaign_state_files_written": 0,
            },
        }
        print(json.dumps(report, ensure_ascii=False, sort_keys=True))
        return 2
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
