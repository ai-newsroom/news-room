#!/usr/bin/env python3
"""Regression tests for ai-technical-blog-v2 and the first issue."""

from __future__ import annotations

import hashlib
import json
import sys
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))

import style_v2  # noqa: E402


class AiTechnicalBlogV2Test(unittest.TestCase):
    def test_positive_and_negative_fixtures(self):
        fixture = json.loads(
            (HERE / "fixtures/style-v2-cases.json").read_text(encoding="utf-8")
        )
        self.assertEqual(fixture["contract_id"], style_v2.CONTRACT_ID)
        for case in fixture["cases"]:
            with self.subTest(case=case["case_id"]):
                errors = style_v2.validate_text(
                    case["markdown"], required_terms=case["required_terms"]
                )
                self.assertEqual(not errors, case["valid"], errors)
                if not case["valid"]:
                    self.assertIn(
                        case["expected_code"],
                        {error["code"] for error in errors},
                    )

    def test_first_issue_uses_v2_and_preserves_fact_inventory(self):
        article = (ROOT / "content/ai/2026-07-21/article.md").read_text(
            encoding="utf-8"
        )
        errors = style_v2.validate_text(
            article, required_terms=style_v2.COSMOS_2026_07_21_TERM_RULES
        )
        self.assertEqual(errors, [])

        baseline = json.loads(
            (HERE / "fixtures/cosmos-style-v2-invariants.json").read_text(
                encoding="utf-8"
            )
        )
        inventory = style_v2.fact_inventory(article)
        self.assertEqual(
            style_v2.inventory_digest(inventory),
            baseline["fact_inventory_sha256"],
        )
        self.assertEqual(len(inventory["numbers"]), baseline["number_token_kinds"])
        self.assertEqual(len(inventory["urls"]), baseline["url_count"])
        self.assertEqual(len(inventory["revisions"]), baseline["revision_count"])
        self.assertEqual(inventory["ledger_sha256"], baseline["ledger_sha256"])
        self.assertEqual(inventory["sources_sha256"], baseline["sources_sha256"])
        self.assertEqual(
            inventory["license_occurrences"], baseline["license_occurrences"]
        )
        self.assertEqual(
            inventory["vendor_claim_occurrences"],
            baseline["vendor_claim_occurrences"],
        )

        evidence = ROOT / "decisions/ai/2026-07-21/evidence.json"
        self.assertEqual(
            hashlib.sha256(evidence.read_bytes()).hexdigest(),
            baseline["evidence_sha256"],
        )

    def test_cli_contract_is_topic_neutral(self):
        article = """---
edition: ai
decision: publish-candidate
title: "새 주제"
date: 2026-07-26
subject: "새 사건"
summary: "새 사건을 설명합니다."
evidence_ceiling: E1
reproducibility: R1
conflicts: ["없음"]
---

새 사건은 기존 요청 처리 방식을 두 단계로 나눕니다.

## 이번 변경의 핵심

요청 처리 경로가 달라집니다.

## 내부에서 작동하는 방식

입력은 두 구성 요소를 지나 출력이 됩니다.

## 기술적 의미와 남은 검증

개발 흐름의 선택지가 늘지만 배포 조건은 확인해야 합니다.

## 근거 원장

| Claim | 판정 |
|---|---|
| C1 | 확인 |

## 출처

1. https://example.com/source
"""
        report = style_v2.validation_report(article)
        self.assertEqual(report["status"], "passed", report["errors"])
        self.assertNotIn(
            "required-term-missing",
            {error["code"] for error in report["errors"]},
        )

    def test_prompt_config_and_release_use_approved_v2_contract(self):
        docs = (ROOT / "docs/08-ai-eda-editorial-profiles.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("AI 기술 블로그 문체 계약 (`ai-technical-blog-v2`)", docs)
        prompt = (HERE / "article-prompt.md").read_text(encoding="utf-8")
        self.assertIn("주 독자는 AI 연구자가 아니라", prompt)
        self.assertIn("AI 모델·API·SDK·오픈소스", prompt)
        self.assertIn("뉴스 설명", prompt)
        self.assertIn("기술 이해", prompt)
        self.assertIn("기술적 의미와 검증 과제", prompt)
        self.assertIn("고정 골격으로 사용하지 않습니다", prompt)
        config = json.loads(
            (ROOT / "editions/ai/edition.json").read_text(encoding="utf-8")
        )
        self.assertEqual(
            config["editorial"]["style_contract"]["heading"],
            "#### AI 기술 블로그 문체 계약 (`ai-technical-blog-v2`)",
        )
        self.assertEqual(
            config["editorial"]["article_prompt"]["path"],
            "editions/ai/editorial/article-prompt.md",
        )
        release = json.loads(
            (ROOT / "decisions/ai/2026-07-21/release.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertIn(
            "the evidence-preserving ai-technical-blog-v2 SW-engineer editorial revision",
            release["authorization"]["scope"],
        )
        self.assertIn(
            "the clearly labeled significance and editorial judgment section",
            release["authorization"]["scope"],
        )
        self.assertIn(
            "approved an SW-engineer-friendly AI News tone and article publication",
            release["authorization"]["approval_basis"],
        )
        article_path = ROOT / release["article_path"]
        evidence_path = ROOT / release["evidence_path"]
        self.assertEqual(
            hashlib.sha256(article_path.read_bytes()).hexdigest(),
            release["artifact_hashes"]["article_sha256"],
        )
        self.assertEqual(
            hashlib.sha256(evidence_path.read_bytes()).hexdigest(),
            release["artifact_hashes"]["evidence_sha256"],
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
