#!/usr/bin/env python3
"""Reject a Korean copy edit that changes evidence-bearing article facts."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path


URL = re.compile(r"https://[^\s)]+")
NUMBER = re.compile(
    r"(?<![0-9A-Za-z])"
    r"\d[\d,]*(?:\.\d+)?"
    r"(?:\s*(?:×|~|→)\s*\d[\d,]*(?:\.\d+)?)?"
    r"(?:\s*(?:B|GB|MHz|Hz|fps|p|프레임|초|ms|req/s|tok/s|token|개|차원|단계|회|%|배|쪽))?"
)
INLINE_CODE = re.compile(r"`([^`\n]+)`")
APPENDIX_MARKER = "\n## 이해상충과 취재 조건\n"
FIXED_FRONTMATTER = (
    "edition",
    "decision",
    "date",
    "subject",
    "evidence_ceiling",
    "reproducibility",
    "conflicts",
    "publication_kind",
)


def frontmatter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---\n"):
        raise ValueError("frontmatter missing")
    marker = text.find("\n---\n", 4)
    if marker < 0:
        raise ValueError("frontmatter is not closed")
    values: dict[str, str] = {}
    for line in text[4:marker].splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        if key in values:
            raise ValueError(f"duplicate frontmatter field: {key}")
        values[key] = value.strip()
    return values, text[marker + 5 :]


def inventory(text: str) -> dict[str, object]:
    values, body = frontmatter(text)
    if APPENDIX_MARKER not in body:
        raise ValueError("verification appendix missing")
    appendix = APPENDIX_MARKER + body.split(APPENDIX_MARKER, 1)[1]
    return {
        "frontmatter_keys": sorted(values),
        "fixed_frontmatter": {
            key: values.get(key) for key in FIXED_FRONTMATTER
        },
        "numbers": sorted(Counter(NUMBER.findall(text)).items()),
        "urls": sorted(
            Counter(match.group(0).rstrip(".,") for match in URL.finditer(text)).items()
        ),
        "inline_code": sorted(set(INLINE_CODE.findall(text))),
        "appendix_sha256": hashlib.sha256(appendix.encode()).hexdigest(),
    }


def compare(before: str, after: str) -> list[str]:
    before_inventory = inventory(before)
    after_inventory = inventory(after)
    return [
        key
        for key in before_inventory
        if before_inventory[key] != after_inventory[key]
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("before", type=Path)
    parser.add_argument("after", type=Path)
    args = parser.parse_args()
    try:
        changed = compare(
            args.before.read_text(encoding="utf-8"),
            args.after.read_text(encoding="utf-8"),
        )
    except (OSError, ValueError) as error:
        print(json.dumps({"status": "failed", "error": str(error)}, ensure_ascii=False))
        return 1
    report = {
        "status": "passed" if not changed else "failed",
        "changed_invariants": changed,
    }
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0 if not changed else 1


if __name__ == "__main__":
    raise SystemExit(main())
