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
            article, required_terms=style_v2.DEFAULT_TERM_RULES
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

    def test_prompt_config_and_release_use_approved_v2_contract(self):
        docs = (ROOT / "docs/08-ai-eda-editorial-profiles.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("AI 기술 블로그 문체 계약 (`ai-technical-blog-v2`)", docs)
        prompt = (HERE / "article-prompt.md").read_text(encoding="utf-8")
        self.assertIn("주 독자는 AI 연구자가 아니라", prompt)
        self.assertIn("AI 모델·API·SDK·오픈소스", prompt)
        self.assertIn("SW 엔지니어를 위한 판단", prompt)
        self.assertIn("이 공개의 의의와 편집 판단", prompt)
        self.assertIn("편집 판단:", prompt)
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
            release["human_approval"]["scope"],
        )
        self.assertIn(
            "the clearly labeled significance and editorial judgment section",
            release["human_approval"]["scope"],
        )
        self.assertIn(
            "approved an SW-engineer-friendly AI News tone and article publication",
            release["human_approval"]["approval_basis"],
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
