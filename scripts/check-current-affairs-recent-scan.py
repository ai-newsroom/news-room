#!/usr/bin/env python3
"""Check current-affairs recent article paths before accepting a follow-up."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any


DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def find_repo_root(start: Path) -> Path:
    current = start.resolve()
    for candidate in (current, *current.parents):
        if (candidate / ".git").exists() and (candidate / "content").is_dir():
            return candidate
    raise RuntimeError(f"cannot find repository root from {start}")


def parse_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def dated_article_paths(repo_root: Path) -> list[tuple[date, Path]]:
    paths: list[tuple[date, Path]] = []
    for article in sorted((repo_root / "content").glob("*/article.md")):
        content_id = article.parent.name
        if not DATE_RE.match(content_id):
            continue
        paths.append((parse_date(content_id), article))
    return paths


def recent_articles(
    repo_root: Path, today: date, days: int
) -> list[tuple[date, Path]]:
    start = today - timedelta(days=days)
    return [
        (article_date, path)
        for article_date, path in dated_article_paths(repo_root)
        if start <= article_date < today
    ]


def relative(path: Path, repo_root: Path) -> str:
    return path.relative_to(repo_root).as_posix()


def overlapping_paths(
    repo_root: Path,
    recent: list[tuple[date, Path]],
    candidate_topic: str,
    keywords: list[str],
) -> list[str]:
    if not candidate_topic or not keywords:
        return []
    normalized_candidate = candidate_topic.casefold()
    required = [
        keyword
        for keyword in keywords
        if keyword.casefold() in normalized_candidate
    ]
    if not required:
        return []
    matches = []
    for _, path in recent:
        text = path.read_text(encoding="utf-8").casefold()
        if any(keyword.casefold() in text for keyword in required):
            matches.append(relative(path, repo_root))
    return matches


def audit(args: argparse.Namespace) -> dict[str, Any]:
    repo_root = find_repo_root(args.cwd or Path.cwd())
    today = parse_date(args.today)
    all_articles = dated_article_paths(repo_root)
    recent = recent_articles(repo_root, today, args.days)
    checked_paths = [relative(path, repo_root) for _, path in recent]
    report: dict[str, Any] = {
        "status": "passed",
        "repo_root": str(repo_root),
        "today": args.today,
        "days": args.days,
        "checked_paths": checked_paths,
        "followup_delta_required": False,
        "comparison_required_paths": [],
    }

    if not recent and all_articles:
        report.update(
            {
                "status": "blocked",
                "reason": "recent scan found zero articles in a populated repository",
                "all_article_count": len(all_articles),
            }
        )
        return report

    matches = overlapping_paths(
        repo_root, recent, args.candidate_topic, args.overlap_keyword
    )
    if matches:
        report.update(
            {
                "status": "delta-required",
                "followup_delta_required": True,
                "comparison_required_paths": matches,
                "reason": (
                    "candidate overlaps recent current-affairs coverage; "
                    "topic.md must record checked paths and concrete deltas"
                ),
            }
        )
    return report


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cwd", type=Path)
    parser.add_argument("--today", required=True)
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--candidate-topic", default="")
    parser.add_argument("--overlap-keyword", action="append", default=[])
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
