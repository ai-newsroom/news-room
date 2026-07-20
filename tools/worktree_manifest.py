#!/usr/bin/env python3
"""Read-only Git worktree preservation manifest and comparison helper."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Mapping, Optional, Sequence


SCHEMA_VERSION = 1
TOOL_NAME = "worktree-preservation-manifest"
TOOL_VERSION = 1


class ManifestError(RuntimeError):
    """Raised when capture is unsafe or a manifest violates the contract."""


def capture(repo: Path | str) -> Mapping[str, Any]:
    """Capture every changed tracked and untracked, non-ignored Git path."""

    started = time.monotonic()
    requested = Path(repo).resolve()
    root_text = _git_text(requested, "rev-parse", "--show-toplevel").strip()
    root = Path(root_text).resolve()
    head_result = _git(
        root, "rev-parse", "--verify", "HEAD", check=False, text=True
    )
    head_oid = head_result.stdout.strip() if head_result.returncode == 0 else None
    index = _index_entries(root)
    status_data = _git(
        root,
        "status",
        "--porcelain=v1",
        "-z",
        "--untracked-files=all",
        "--ignore-submodules=none",
        text=False,
    ).stdout
    status_entries = _parse_status(status_data)

    entries = []
    tracked_count = 0
    untracked_count = 0
    for status_entry in status_entries:
        path_bytes = status_entry["path_bytes"]
        path = _decode_path(path_bytes)
        status_code = status_entry["status"]
        tracked = status_code != "??"
        fingerprint = _fingerprint(root, path_bytes, status_code)
        entries.append(
            {
                "path": path,
                "status": status_code,
                "tracked": tracked,
                "original_path": (
                    None
                    if status_entry["original_path_bytes"] is None
                    else _decode_path(status_entry["original_path_bytes"])
                ),
                "index": index.get(path_bytes, []),
                "worktree": fingerprint,
            }
        )
        if tracked:
            tracked_count += 1
        else:
            untracked_count += 1

    entries.sort(key=lambda item: item["path"])
    duration_ms = round((time.monotonic() - started) * 1000, 3)
    return {
        "schema_version": SCHEMA_VERSION,
        "tool": TOOL_NAME,
        "tool_version": TOOL_VERSION,
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "repository": {
            "root": str(root),
            "head_oid": head_oid,
        },
        "scope": {
            "tracked": "git-status-changed-only",
            "untracked": "all-non-ignored-files",
            "ignored": "excluded",
            "symlinks": "link-target-hash-only",
            "submodules": "gitlink-and-directory-metadata-only",
        },
        "entries": entries,
        "summary": {
            "entry_count": len(entries),
            "tracked_changed_count": tracked_count,
            "untracked_count": untracked_count,
        },
        "instrumentation": {
            "capture_duration_ms": duration_ms,
            "external_invocation_count": 1,
            "git_read_command_count": 4,
        },
    }


def compare(
    before: Mapping[str, Any],
    after: Mapping[str, Any],
    *,
    allowed_new: Sequence[str] = (),
) -> Mapping[str, Any]:
    """Compare two manifests and distinguish authorized newly changed paths."""

    _validate_manifest(before, "before")
    _validate_manifest(after, "after")
    before_repo = before["repository"]
    after_repo = after["repository"]
    if before_repo["root"] != after_repo["root"]:
        raise ManifestError("repository_root_mismatch")

    allowances = [_normalize_allowance(value) for value in allowed_new]
    before_entries = _entries_by_path(before)
    after_entries = _entries_by_path(after)
    before_paths = set(before_entries)
    after_paths = set(after_entries)

    preserved = []
    changed = []
    missing = []
    allowed = []
    unexpected = []
    used_allowances = set()

    for path in sorted(before_paths):
        if path not in after_entries:
            missing.append({"path": path, "before": before_entries[path]})
        elif before_entries[path] == after_entries[path]:
            preserved.append(path)
        else:
            changed.append(
                {
                    "path": path,
                    "changed_fields": _changed_fields(
                        before_entries[path], after_entries[path]
                    ),
                    "before": before_entries[path],
                    "after": after_entries[path],
                }
            )

    for path in sorted(after_paths - before_paths):
        matched = _matching_allowance(path, allowances)
        item = {"path": path, "after": after_entries[path]}
        if matched is None:
            unexpected.append(item)
        else:
            item["allowance"] = matched["raw"]
            allowed.append(item)
            used_allowances.add(matched["raw"])

    head_changed = before_repo["head_oid"] != after_repo["head_oid"]
    violation_count = (
        len(changed) + len(missing) + len(unexpected) + int(head_changed)
    )
    accounted = len(preserved) + len(changed) + len(missing)
    before_count = len(before_entries)
    return {
        "schema_version": SCHEMA_VERSION,
        "tool": TOOL_NAME,
        "tool_version": TOOL_VERSION,
        "status": "pass" if violation_count == 0 else "fail",
        "repository_root": before_repo["root"],
        "before_captured_at": before["captured_at"],
        "after_captured_at": after["captured_at"],
        "head_changed": head_changed,
        "allowed_new": allowed,
        "unexpected_new": unexpected,
        "preexisting_changed": changed,
        "preexisting_missing": missing,
        "preexisting_preserved": preserved,
        "unused_allowances": sorted(
            item["raw"] for item in allowances if item["raw"] not in used_allowances
        ),
        "coverage": {
            "before_entry_count": before_count,
            "accounted_preexisting_count": accounted,
            "explanation_rate": (
                1.0 if before_count == 0 else round(accounted / before_count, 6)
            ),
            "preserved_count": len(preserved),
            "violation_count": violation_count,
        },
        "instrumentation": {
            "recommended_manual_invocations_per_turn": 2,
            "workflow": ["capture", "compare-live"],
        },
    }


def _git(
    repo: Path,
    *args: str,
    check: bool = True,
    text: bool = False,
) -> subprocess.CompletedProcess:
    environment = os.environ.copy()
    environment["GIT_OPTIONAL_LOCKS"] = "0"
    result = subprocess.run(
        ["git", "--no-optional-locks", "-C", str(repo), *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        text=text,
        env=environment,
    )
    if check and result.returncode != 0:
        stderr = result.stderr if text else result.stderr.decode("utf-8", "replace")
        raise ManifestError("git_read_failed:{}".format(stderr.strip()))
    return result


def _git_text(repo: Path, *args: str) -> str:
    return _git(repo, *args, text=True).stdout


def _parse_status(data: bytes) -> list[Mapping[str, Any]]:
    fields = data.split(b"\0")
    result = []
    index = 0
    while index < len(fields):
        record = fields[index]
        index += 1
        if not record:
            continue
        if len(record) < 4 or record[2:3] != b" ":
            raise ManifestError("unexpected_porcelain_record")
        try:
            status_code = record[:2].decode("ascii")
        except UnicodeDecodeError as error:
            raise ManifestError("invalid_porcelain_status") from error
        path_bytes = record[3:]
        if not path_bytes:
            raise ManifestError("empty_status_path")
        original = None
        if "R" in status_code or "C" in status_code:
            if index >= len(fields) or not fields[index]:
                raise ManifestError("rename_source_missing")
            original = fields[index]
            index += 1
        result.append(
            {
                "status": status_code,
                "path_bytes": path_bytes,
                "original_path_bytes": original,
            }
        )
    return result


def _index_entries(repo: Path) -> Mapping[bytes, list[Mapping[str, Any]]]:
    data = _git(repo, "ls-files", "--stage", "-z", text=False).stdout
    result: dict[bytes, list[Mapping[str, Any]]] = {}
    for record in data.split(b"\0"):
        if not record:
            continue
        header, separator, path = record.partition(b"\t")
        parts = header.split(b" ")
        if not separator or len(parts) != 3 or not path:
            raise ManifestError("unexpected_index_record")
        mode, object_id, stage = parts
        result.setdefault(path, []).append(
            {
                "mode": mode.decode("ascii"),
                "object_id": object_id.decode("ascii"),
                "stage": int(stage),
            }
        )
    for values in result.values():
        values.sort(key=lambda item: item["stage"])
    return result


def _fingerprint(
    root: Path, path_bytes: bytes, status_code: str
) -> Mapping[str, Any]:
    relative = Path(_decode_path(path_bytes))
    full_path = root / relative
    try:
        before = os.lstat(full_path)
    except FileNotFoundError as error:
        if "D" in status_code:
            return {
                "kind": "missing",
                "mode": None,
                "size": None,
                "mtime_ns": None,
                "sha256": None,
            }
        raise ManifestError("path_changed_during_capture:{}".format(relative)) from error

    mode = stat.S_IMODE(before.st_mode)
    digest = None
    if stat.S_ISREG(before.st_mode):
        kind = "file"
        digest = _file_sha256(full_path)
    elif stat.S_ISLNK(before.st_mode):
        kind = "symlink"
        digest = hashlib.sha256(os.fsencode(os.readlink(full_path))).hexdigest()
    elif stat.S_ISDIR(before.st_mode):
        kind = "directory"
    else:
        kind = "special"

    after = os.lstat(full_path)
    before_state = (
        before.st_dev,
        before.st_ino,
        before.st_mode,
        before.st_size,
        before.st_mtime_ns,
    )
    after_state = (
        after.st_dev,
        after.st_ino,
        after.st_mode,
        after.st_size,
        after.st_mtime_ns,
    )
    if before_state != after_state:
        raise ManifestError("path_changed_during_capture:{}".format(relative))
    return {
        "kind": kind,
        "mode": mode,
        "size": before.st_size,
        "mtime_ns": before.st_mtime_ns,
        "sha256": digest,
    }


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while True:
            chunk = stream.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _decode_path(value: bytes) -> str:
    return os.fsdecode(value)


def _validate_manifest(value: Mapping[str, Any], label: str) -> None:
    if not isinstance(value, Mapping):
        raise ManifestError("{}_manifest_must_be_mapping".format(label))
    required = {
        "schema_version",
        "tool",
        "tool_version",
        "captured_at",
        "repository",
        "scope",
        "entries",
        "summary",
        "instrumentation",
    }
    if set(value) != required:
        raise ManifestError("{}_manifest_fields_invalid".format(label))
    if value["schema_version"] != SCHEMA_VERSION or value["tool"] != TOOL_NAME:
        raise ManifestError("{}_manifest_version_invalid".format(label))
    if not isinstance(value["entries"], list):
        raise ManifestError("{}_entries_must_be_list".format(label))


def _entries_by_path(manifest: Mapping[str, Any]) -> Mapping[str, Mapping[str, Any]]:
    result = {}
    for entry in manifest["entries"]:
        path = entry.get("path") if isinstance(entry, Mapping) else None
        if not isinstance(path, str) or not path:
            raise ManifestError("manifest_entry_path_invalid")
        if path in result:
            raise ManifestError("manifest_entry_path_duplicated")
        result[path] = entry
    return result


def _normalize_allowance(raw: str) -> Mapping[str, Any]:
    if not isinstance(raw, str) or not raw.strip():
        raise ManifestError("allowance_must_be_nonempty")
    normalized = raw.replace(os.sep, "/")
    prefix = normalized.endswith("/")
    candidate = normalized[:-1] if prefix else normalized
    path = PurePosixPath(candidate)
    if path.is_absolute() or ".." in path.parts or ".git" in path.parts:
        raise ManifestError("unsafe_allowance:{}".format(raw))
    clean = path.as_posix()
    if clean in {"", "."}:
        raise ManifestError("unsafe_allowance:{}".format(raw))
    return {"raw": raw, "path": clean, "prefix": prefix}


def _matching_allowance(
    path: str, allowances: Sequence[Mapping[str, Any]]
) -> Optional[Mapping[str, Any]]:
    for allowance in allowances:
        if allowance["prefix"]:
            if path.startswith(allowance["path"] + "/"):
                return allowance
        elif path == allowance["path"]:
            return allowance
    return None


def _changed_fields(
    before: Mapping[str, Any], after: Mapping[str, Any]
) -> list[str]:
    keys = sorted(set(before) | set(after))
    return [key for key in keys if before.get(key) != after.get(key)]


def _read_manifest(path: str) -> Mapping[str, Any]:
    if path == "-":
        return json.load(sys.stdin)
    with Path(path).open("r", encoding="utf-8") as stream:
        return json.load(stream)


def _write_json(value: Mapping[str, Any]) -> None:
    json.dump(value, sys.stdout, ensure_ascii=True, indent=2, sort_keys=True)
    sys.stdout.write("\n")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    capture_parser = subparsers.add_parser("capture")
    capture_parser.add_argument("--repo", default=".")

    compare_parser = subparsers.add_parser("compare")
    compare_parser.add_argument("--before", required=True)
    compare_parser.add_argument("--after", required=True)
    compare_parser.add_argument("--allow-new", action="append", default=[])

    live_parser = subparsers.add_parser("compare-live")
    live_parser.add_argument("--repo", default=".")
    live_parser.add_argument("--before", required=True)
    live_parser.add_argument("--allow-new", action="append", default=[])
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    arguments = _parser().parse_args(argv)
    try:
        if arguments.command == "capture":
            _write_json(capture(arguments.repo))
            return 0
        before = _read_manifest(arguments.before)
        if arguments.command == "compare":
            after = _read_manifest(arguments.after)
            report = compare(before, after, allowed_new=arguments.allow_new)
            _write_json(report)
        else:
            after = capture(arguments.repo)
            report = compare(before, after, allowed_new=arguments.allow_new)
            _write_json({"comparison": report, "after_manifest": after})
        return 0 if report["status"] == "pass" else 2
    except (ManifestError, OSError, json.JSONDecodeError) as error:
        _write_json(
            {
                "schema_version": SCHEMA_VERSION,
                "tool": TOOL_NAME,
                "status": "error",
                "error_type": type(error).__name__,
                "error": str(error),
            }
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
