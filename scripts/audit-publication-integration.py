#!/usr/bin/env python3
"""Audit done improvement items against publication-facing integration state."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


PUBLICATION_PATH_PREFIXES = (
    "prompts/",
    "workflows/",
    "newsroom/",
    "editions/",
    "engine/edition/",
    "scripts/publish",
    "scripts/finalize-publication",
    "scripts/publication-git",
    "scripts/verify-publication",
    "site/",
    "docs/",
)
DEFAULT_INBOX = ".coco-agents/inbox/items"


def run_git(repo: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        check=False,
        capture_output=True,
        text=True,
    )


def dirty_paths(repo: Path) -> set[str]:
    completed = run_git(repo, ["status", "--porcelain=v1", "-z"])
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or "git status failed")
    entries = completed.stdout.split("\0")
    paths: set[str] = set()
    index = 0
    while index < len(entries):
        entry = entries[index]
        index += 1
        if not entry:
            continue
        status = entry[:2]
        path = entry[3:]
        if status.startswith("R") or status.startswith("C"):
            if index < len(entries):
                path = entries[index]
                index += 1
        paths.add(path)
    return paths


def normalize_changed_path(raw: str) -> str:
    path = raw.strip().lstrip("-").strip()
    if " (" in path:
        path = path.split(" (", 1)[0]
    return path


def result_changed_paths(item: dict[str, Any]) -> set[str]:
    result = item.get("result") or {}
    summary = result.get("summary") or ""
    paths: set[str] = set()
    in_changed = False
    for line in summary.splitlines():
        stripped = line.strip()
        if stripped.lower().startswith("changed paths"):
            in_changed = True
            continue
        if in_changed and stripped.startswith("- "):
            path = normalize_changed_path(stripped)
            if path:
                paths.add(path)
            continue
        if in_changed and stripped and not stripped.startswith("- "):
            break
    return paths


def is_publication_affecting(paths: set[str]) -> bool:
    return any(
        path.startswith(PUBLICATION_PATH_PREFIXES) for path in paths
    )


def integration_state(item: dict[str, Any]) -> str:
    text = " ".join(
        str(value)
        for value in (
            item.get("description", ""),
            (item.get("result") or {}).get("summary", ""),
            item.get("blocked_reason", ""),
        )
    ).lower()
    if "no publication effect" in text or "publication effect: none" in text:
        return "no-publication-effect"
    if "editor-deferred" in text or "editor deferred" in text or "편집자 보류" in text:
        return "editor-deferred"
    if "origin/main" in text and "commit" in text and "push" in text:
        return "landed-on-origin-main"
    return "unrecorded"


def load_done_items(inbox: Path) -> list[dict[str, Any]]:
    items = []
    for path in sorted(inbox.glob("*.json")):
        item = json.loads(path.read_text(encoding="utf-8"))
        if item.get("status") == "done":
            item["_record_path"] = str(path)
            items.append(item)
    return items


def release_checks(
    repo: Path, ref: str, release_path: str
) -> tuple[list[str], str | None]:
    completed = run_git(repo, ["show", f"{ref}:{release_path}"])
    if completed.returncode != 0:
        return [], completed.stderr.strip() or f"missing {ref}:{release_path}"
    release = json.loads(completed.stdout)
    checks = release.get("authorization", {}).get("checks", [])
    return [str(check) for check in checks], None


def audit(args: argparse.Namespace) -> dict[str, Any]:
    repo = args.repo.resolve()
    dirty = dirty_paths(repo)
    items = load_done_items(repo / args.inbox)
    publication_items = []
    for item in items:
        paths = result_changed_paths(item)
        if not paths or not is_publication_affecting(paths):
            continue
        item_id = item["id"]
        state = integration_state(item)
        dirty_overlap = sorted(paths & dirty)
        publication_items.append(
            {
                "id": item_id,
                "record": item["_record_path"],
                "integration_state": state,
                "changed_paths": sorted(paths),
                "dirty_overlap": dirty_overlap,
            }
        )

    findings = []
    unintegrated = [
        item
        for item in publication_items
        if item["integration_state"] == "unrecorded" and item["dirty_overlap"]
    ]
    if unintegrated:
        findings.append(
            {
                "code": "done-publication-affecting-item-still-dirty",
                "severity": "error",
                "items": [
                    {
                        "id": item["id"],
                        "dirty_overlap": item["dirty_overlap"],
                    }
                    for item in unintegrated
                ],
            }
        )

    expected = args.expected_release_check
    stale = args.stale_release_check
    if args.release_path and expected:
        checks, error = release_checks(repo, args.ref, args.release_path)
        if error:
            findings.append(
                {
                    "code": "release-metadata-unavailable",
                    "severity": "error",
                    "release_path": args.release_path,
                    "ref": args.ref,
                    "error": error,
                }
            )
        elif expected not in checks and (not stale or stale in checks):
            findings.append(
                {
                    "code": "release-contract-behind-done-item",
                    "severity": "error",
                    "release_path": args.release_path,
                    "ref": args.ref,
                    "expected_check": expected,
                    "stale_check": stale,
                    "observed_checks": checks,
                }
            )

    return {
        "status": "failed" if findings else "passed",
        "repo": str(repo),
        "ref": args.ref,
        "publication_items_checked": publication_items,
        "dirty_paths": sorted(dirty),
        "findings": findings,
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--inbox", default=DEFAULT_INBOX)
    parser.add_argument("--ref", default="origin/main")
    parser.add_argument("--release-path")
    parser.add_argument("--expected-release-check")
    parser.add_argument("--stale-release-check")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    try:
        report = audit(parse_args(argv or []))
    except Exception as error:
        report = {"status": "error", "error": str(error)}
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
