#!/usr/bin/env python3
"""Deterministic checks for the ai-technical-blog-v2 writing contract."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path


CONTRACT_ID = "ai-technical-blog-v2"
PLAIN_ENDING = re.compile(
    r"(?<!니)(?<!습)(?:한다|된다|있다|없다|않다|였다|했다|됐다|이다|아니다|다)\."
)
URL = re.compile(r"https://[^\s)]+")
REVISION = re.compile(r"(?<![0-9a-f])[0-9a-f]{40}(?![0-9a-f])")
NUMBER = re.compile(
    r"(?<![0-9A-Za-z])"
    r"\d[\d,]*(?:\.\d+)?"
    r"(?:\s*(?:×|~|→)\s*\d[\d,]*(?:\.\d+)?)?"
    r"(?:\s*(?:B|GB|MHz|Hz|fps|p|프레임|초|ms|req/s|tok/s|token|개|차원|단계|회|%))?"
)
PROHIBITED_METAPHORS = (
    "게임 체인저",
    "기술의 심장",
    "마법처럼",
    "새 시대의 문을 열",
    "혁신의 씨앗",
)
READER_BLAME = ("당연히", "누구나 알듯", "간단히 말해")
ENGINEER_JUDGMENT_HEADING = "## SW 엔지니어를 위한 판단"
ENGINEER_JUDGMENT_LABELS = (
    "지금 확인할 수 있는 것",
    "도입 전에 확인할 것",
    "아직 결론 내릴 수 없는 것",
)
EDITORIAL_SIGNIFICANCE_HEADING = "## 이 공개의 의의와 편집 판단"
EDITORIAL_JUDGMENT_LABEL = "편집 판단:"
COSMOS_2026_07_21_TERM_RULES = {
    "MoT": ["트랜스포머 혼합 구조", "Mixture-of-Transformers"],
    "자동회귀": ["다음 토큰"],
    "diffusion": ["확산", "노이즈"],
    "VANTAGE": ["영상 이해", "benchmark"],
    "RoboLab": ["로봇 평가"],
}
PROTECTED_FRONTMATTER = (
    "edition",
    "decision",
    "title",
    "date",
    "subject",
    "evidence_ceiling",
    "reproducibility",
    "conflicts",
)


def _frontmatter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---\n"):
        raise ValueError("frontmatter missing")
    marker = text.find("\n---\n", 4)
    if marker < 0:
        raise ValueError("frontmatter is not closed")
    values: dict[str, str] = {}
    for line in text[4:marker].splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            values[key] = value.strip()
    return values, text[marker + 5 :]


def _narrative(text: str) -> str:
    _, body = _frontmatter(text)
    return body.split("\n## 근거 원장\n", 1)[0]


def _strip_exemptions(line: str) -> str:
    line = re.sub(r"`[^`]*`", "", line)
    line = re.sub(r"“[^”]*”", "", line)
    line = re.sub(r'"[^"]*"', "", line)
    return line


def validate_text(
    text: str,
    *,
    required_terms: dict[str, list[str]] | None = None,
) -> list[dict[str, object]]:
    """Return stable validation errors; an empty list means the text passes."""
    errors: list[dict[str, object]] = []
    narrative = _narrative(text)
    lines = narrative.splitlines()
    prose_lines: list[tuple[int, str]] = []
    in_fence = False
    for number, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        if (
            in_fence
            or not stripped
            or stripped.startswith("#")
            or stripped.startswith("|")
            or stripped.startswith(">")
        ):
            continue
        prose_lines.append((number, _strip_exemptions(stripped)))

    for number, line in prose_lines:
        if PLAIN_ENDING.search(line):
            errors.append(
                {"code": "plain-style-ending", "line": number, "text": line}
            )
        for phrase in READER_BLAME:
            if phrase in line:
                errors.append(
                    {"code": "reader-blaming-language", "line": number, "term": phrase}
                )
        for phrase in PROHIBITED_METAPHORS:
            if phrase in line and not (
                "비유 대응:" in line and "비유 한계:" in line
            ):
                errors.append(
                    {"code": "unbounded-metaphor", "line": number, "term": phrase}
                )

    opening = next((line for _, line in prose_lines), "")
    if not (
        "공개" in opening
        and "중요" in opening
        and ("개발자" in opening or "SW 엔지니어" in opening)
    ):
        errors.append({"code": "opening-reader-value-missing", "line": 1})

    if ENGINEER_JUDGMENT_HEADING not in narrative:
        errors.append({"code": "engineer-judgment-heading-missing", "line": 1})
    for label in ENGINEER_JUDGMENT_LABELS:
        if label not in narrative:
            errors.append(
                {"code": "engineer-judgment-label-missing", "line": 1, "label": label}
            )
    if EDITORIAL_SIGNIFICANCE_HEADING not in narrative:
        errors.append({"code": "editorial-significance-heading-missing", "line": 1})
    if EDITORIAL_JUDGMENT_LABEL not in narrative:
        errors.append({"code": "editorial-judgment-label-missing", "line": 1})

    for term, explanations in (required_terms or {}).items():
        first = next(
            ((number, line) for number, line in prose_lines if term in line),
            None,
        )
        if first is None:
            errors.append({"code": "required-term-missing", "term": term})
            continue
        number, line = first
        missing = [value for value in explanations if value not in line]
        if missing:
            errors.append(
                {
                    "code": "first-use-explanation-missing",
                    "line": number,
                    "term": term,
                    "missing": missing,
                }
            )
    return errors


def _section(text: str, heading: str, next_heading: str | None) -> str:
    start_marker = f"\n## {heading}\n"
    start = text.index(start_marker) + 1
    if next_heading is None:
        return text[start:]
    end = text.index(f"\n## {next_heading}\n", start)
    return text[start:end]


def fact_inventory(text: str) -> dict[str, object]:
    """Extract wording-independent values that a style-only edit must preserve."""
    frontmatter, _ = _frontmatter(text)
    numeric = Counter(match.group(0).strip() for match in NUMBER.finditer(text))
    urls = Counter(match.group(0).rstrip(".,") for match in URL.finditer(text))
    revisions = Counter(REVISION.findall(text))
    ledger = _section(text, "근거 원장", "출처")
    sources = _section(text, "출처", None)
    return {
        "frontmatter": {
            key: frontmatter.get(key) for key in PROTECTED_FRONTMATTER
        },
        "numbers": sorted(numeric.items()),
        "urls": sorted(urls.items()),
        "revisions": sorted(revisions.items()),
        "ledger_sha256": hashlib.sha256(ledger.encode()).hexdigest(),
        "sources_sha256": hashlib.sha256(sources.encode()).hexdigest(),
        "license_occurrences": text.count("OpenMDW-1.1"),
        "vendor_claim_occurrences": text.count("VENDOR_CLAIM_ONLY"),
    }


def inventory_digest(inventory: dict[str, object]) -> str:
    payload = json.dumps(
        inventory, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode()
    return hashlib.sha256(payload).hexdigest()


def validation_report(text: str) -> dict[str, object]:
    """Validate the topic-neutral writing contract used by the CLI."""
    errors = validate_text(text)
    return {
        "contract_id": CONTRACT_ID,
        "status": "passed" if not errors else "failed",
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("article", type=Path)
    args = parser.parse_args()
    text = args.article.read_text(encoding="utf-8")
    report = validation_report(text)
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
