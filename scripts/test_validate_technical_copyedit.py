#!/usr/bin/env python3
"""Tests for the evidence-preserving Korean copy-edit boundary."""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "validate_technical_copyedit",
    ROOT / "scripts/validate-technical-copyedit.py",
)
assert SPEC and SPEC.loader
validator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validator)


ARTICLE = """---
edition: ai
decision: publish-candidate
title: "어색한 제목"
date: 2026-08-22
subject: "Example 1.2"
summary: "초고입니다."
evidence_ceiling: E2
reproducibility: R1
conflicts: ["없음"]
---

`search`는 문서 3개를 찾습니다.

## 결론의 천장

자세한 설명은 https://example.com/docs 에 있습니다.

## 이해상충과 취재 조건

없습니다.

## 근거 원장

| Claim | 근거 |
|---|---|
| C1 | 문서 3개 |

## 출처

1. https://example.com/docs
"""


class TechnicalCopyeditValidationTest(unittest.TestCase):
    def test_natural_korean_edits_may_change_title_summary_headings_and_prose(self) -> None:
        edited = (
            ARTICLE.replace('title: "어색한 제목"', 'title: "문서를 다시 찾는 검색"')
            .replace('summary: "초고입니다."', 'summary: "검색 방식을 설명합니다."')
            .replace("`search`는 문서 3개를 찾습니다.", "문서 3개는 `search`로 찾습니다.")
            .replace("## 결론의 천장", "## 실제 환경 검증은 남았습니다")
        )
        self.assertEqual(validator.compare(ARTICLE, edited), [])

    def test_number_code_url_frontmatter_and_appendix_are_protected(self) -> None:
        cases = {
            "numbers": ARTICLE.replace("문서 3개를 찾습니다", "문서 4개를 찾습니다", 1),
            "inline_code": ARTICLE.replace("`search`는", "`open`은", 1),
            "urls": ARTICLE.replace("https://example.com/docs", "https://example.com/api", 1),
            "fixed_frontmatter": ARTICLE.replace("evidence_ceiling: E2", "evidence_ceiling: E3"),
            "appendix_sha256": ARTICLE.replace("없습니다.", "광고가 없습니다.", 1),
        }
        for expected, edited in cases.items():
            with self.subTest(expected=expected):
                self.assertIn(expected, validator.compare(ARTICLE, edited))


if __name__ == "__main__":
    unittest.main(verbosity=2)
