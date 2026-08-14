#!/usr/bin/env python3
"""Regression tests for the automatic AI publication boundary."""

from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "publish_ai_candidate",
    ROOT / "scripts/publish-ai-candidate.py",
)
assert SPEC and SPEC.loader
publisher = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(publisher)


ARTICLE = """---
edition: ai
decision: publish-candidate
title: "검증된 새 AI 사건"
date: 2026-07-26
subject: "새 AI 사건"
summary: "두 공식 기술 원문을 대조했습니다."
evidence_ceiling: E2
reproducibility: R1
conflicts: ["당사자 발표입니다."]
---

공개된 새 AI 사건은 SW 엔지니어에게 중요한 운영 변경을 보여 줍니다.

## 이번 뉴스가 바꾼 것

새 공개는 모델의 실행 방식을 바꿉니다.

## 요청이 처리되는 방식

입력은 새 실행 단계를 지나 결과가 됩니다.

### 이전 방식과 비교하면

이전에는 한 단계에서 처리하던 일을 나눠 처리합니다.

## 개발 흐름에 갖는 의미와 남은 검증

이 변화는 운영 선택지를 넓히지만 비공개 조건은 더 확인해야 합니다.

## 이해상충과 취재 조건

당사자가 발표한 자료이며 지원은 받지 않았습니다.

## 근거 원장

| Claim | 판정 |
|---|---|
| C1 | E2 |

## 출처

1. https://example.com/one
2. https://example.org/two
"""


def evidence(level: str = "E2") -> dict:
    return {
        "schema_version": 1,
        "edition": "ai",
        "date": "2026-07-26",
        "decision": "publish-candidate",
        "selection": {"total": 9, "threshold": 7},
        "evidence_ceiling": level,
        "reproducibility": "R1",
        "release_gate": {
            "policy_id": publisher.POLICY_ID,
            "human_approval_required": False,
            "automatic_publish_allowed": True,
            "quality_gate_passed": True,
            "content_promotion_allowed": True,
            "git_write_allowed": True,
            "deploy_allowed": True,
        },
        "conflicts": ["당사자 발표입니다."],
        "claims": [{
            "claim_id": "C1",
            "central": True,
            "evidence_level": level,
            "sources": [
                {"url": "https://example.com/one", "source_grade": "P1"},
                {"url": "https://example.org/two", "source_grade": "P2"},
            ],
        }],
    }


class AutomaticAiPublisherTest(unittest.TestCase):
    def make_candidate(self, root: Path, level: str = "E2") -> tuple[Path, Path]:
        run = root / "var/runs/ai/test/staged-content"
        run.mkdir(parents=True)
        article = run / "article.md"
        evidence_path = run.parent / "evidence.json"
        article.write_text(
            ARTICLE.replace("evidence_ceiling: E2", f"evidence_ceiling: {level}"),
            encoding="utf-8",
        )
        evidence_path.write_text(
            json.dumps(evidence(level), ensure_ascii=False),
            encoding="utf-8",
        )
        return article, evidence_path

    def test_validated_candidate_materializes_release_without_external_actions(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            article, evidence_path = self.make_candidate(root)
            candidate = publisher.validate_candidate(
                article,
                evidence_path,
                "2026-07-26",
                repo_root=root,
                require_today=False,
            )
            result = publisher.materialize(
                candidate,
                executor="test",
                repo_root=root,
            )
            self.assertEqual(result["status"], "materialized")
            self.assertEqual(
                result["external_actions"],
                {"commit": False, "push": False, "deploy": False},
            )
            release = json.loads(
                (root / "decisions/ai/2026-07-26/release.json").read_text()
            )
            self.assertEqual(release["authorization"]["mode"], "automatic")
            self.assertEqual(
                release["authorization"]["policy_id"],
                publisher.POLICY_ID,
            )

    def test_e1_candidate_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            article, evidence_path = self.make_candidate(root, "E1")
            with self.assertRaisesRegex(publisher.PublishError, "E2 or higher"):
                publisher.validate_candidate(
                    article,
                    evidence_path,
                    "2026-07-26",
                    repo_root=root,
                    require_today=False,
                )

    def test_verification_appendix_remains_required(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            article, evidence_path = self.make_candidate(root)
            article.write_text(
                article.read_text(encoding="utf-8").replace(
                    "## 근거 원장",
                    "## 검증 자료",
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(publisher.PublishError, "required section"):
                publisher.validate_candidate(
                    article,
                    evidence_path,
                    "2026-07-26",
                    repo_root=root,
                    require_today=False,
                )

    def test_source_type_alias_matches_editorial_contract(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            article, evidence_path = self.make_candidate(root)
            value = json.loads(evidence_path.read_text())
            for source in value["claims"][0]["sources"]:
                source["source_type"] = source.pop("source_grade")
            evidence_path.write_text(json.dumps(value), encoding="utf-8")

            candidate = publisher.validate_candidate(
                article,
                evidence_path,
                "2026-07-26",
                repo_root=root,
                require_today=False,
            )
            self.assertEqual(candidate["publication_id"], "2026-07-26")

    def test_conflicting_source_grade_aliases_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            article, evidence_path = self.make_candidate(root)
            value = json.loads(evidence_path.read_text())
            value["claims"][0]["sources"][0]["source_type"] = "P2"
            evidence_path.write_text(json.dumps(value), encoding="utf-8")

            with self.assertRaisesRegex(
                publisher.PublishError,
                "source grade fields conflict",
            ):
                publisher.validate_candidate(
                    article,
                    evidence_path,
                    "2026-07-26",
                    repo_root=root,
                    require_today=False,
                )

    def test_human_gate_cannot_enter_automatic_path(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            article, evidence_path = self.make_candidate(root)
            value = json.loads(evidence_path.read_text())
            value["release_gate"]["human_approval_required"] = True
            evidence_path.write_text(json.dumps(value), encoding="utf-8")
            with self.assertRaisesRegex(publisher.PublishError, "not authorized"):
                publisher.validate_candidate(
                    article,
                    evidence_path,
                    "2026-07-26",
                    repo_root=root,
                    require_today=False,
                )

    def test_unexpected_frontmatter_field_is_rejected_before_materialization(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            article, evidence_path = self.make_candidate(root)
            article.write_text(
                article.read_text(encoding="utf-8").replace(
                    "date: 2026-07-26\n",
                    'date: 2026-07-26\npublication_id: "2026-07-26"\n',
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(
                publisher.PublishError,
                r"unexpected article frontmatter field.*publication_id",
            ):
                publisher.validate_candidate(
                    article,
                    evidence_path,
                    "2026-07-26",
                    repo_root=root,
                    require_today=False,
                )
            self.assertFalse((root / "content/ai/2026-07-26").exists())
            self.assertFalse((root / "decisions/ai/2026-07-26").exists())

    def test_same_day_special_candidate_gets_nested_route_and_human_authorization(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            article, evidence_path = self.make_candidate(root)
            article.write_text(
                article.read_text(encoding="utf-8").replace(
                    "date: 2026-07-26\n",
                    "date: 2026-07-26\npublication_kind: special\n",
                ).replace(
                    'title: "검증된 새 AI 사건"',
                    'title: "검증된 AI 운영 변경"',
                ).replace(
                    'summary: "두 공식 기술 원문을 대조했습니다."',
                    'summary: "운영 변경의 기술 원리를 두 공식 원문으로 확인했습니다."',
                ),
                encoding="utf-8",
            )
            value = json.loads(evidence_path.read_text())
            value.update({
                "publication_id": "2026-07-26--cordis",
                "publication_kind": "special",
                "central_claim": "운영 변경의 기술 원리가 배포 판단을 바꿉니다.",
                "editorial_brief_alignment": {
                    "requested_angle": "운영 변경의 기술 원리와 배포 의의를 설명합니다.",
                    "required_focus_terms": ["운영 변경", "기술 원리"],
                    "secondary_terms": ["가격", "버전"],
                },
            })
            value["release_gate"].update({
                "policy_id": publisher.SPECIAL_POLICY_ID,
                "human_approval_required": True,
                "automatic_publish_allowed": False,
            })
            evidence_path.write_text(json.dumps(value), encoding="utf-8")

            (root / "content/ai/2026-07-26").mkdir(parents=True)
            candidate = publisher.validate_candidate(
                article,
                evidence_path,
                "2026-07-26--cordis",
                repo_root=root,
                require_today=False,
                publication_kind="special",
                approved_by="편집자",
                approval_basis="대화에서 Cordis 특별판 발행을 승인함",
            )
            result = publisher.materialize(candidate, executor="test", repo_root=root)

            self.assertEqual(result["route"], "/ai/2026-07-26/cordis/")
            release = json.loads(
                (root / "decisions/ai/2026-07-26--cordis/release.json").read_text()
            )
            self.assertEqual(release["publication_kind"], "special")
            self.assertEqual(release["authorization"]["mode"], "human")
            self.assertEqual(release["authorization"]["approved_by"], "편집자")
            self.assertEqual(
                release["editorial_brief_alignment"]["status"],
                "passed",
            )
            self.assertEqual(
                release["editorial_brief_alignment"]["checked_targets"],
                ["title", "summary", "lead", "central_claim"],
            )

    def test_special_candidate_rejects_caution_dominated_editorial_angle(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            article, evidence_path = self.make_candidate(root)
            article.write_text(
                article.read_text(encoding="utf-8").replace(
                    "date: 2026-07-26\n",
                    "date: 2026-07-26\npublication_kind: special\n",
                ).replace(
                    'title: "검증된 새 AI 사건"',
                    'title: "새 모델 버전과 가격은 주의해서 봐야 합니다"',
                ),
                encoding="utf-8",
            )
            value = json.loads(evidence_path.read_text())
            value.update({
                "publication_id": "2026-07-26--deep-analysis",
                "publication_kind": "special",
                "central_claim": "버전과 가격, 주의사항을 먼저 기록해야 합니다.",
                "editorial_brief_alignment": {
                    "requested_angle": "기술의 작동 원리를 쉽게 설명하고 기술적 의의를 분석합니다.",
                    "required_focus_terms": ["작동 원리", "기술적 의의"],
                    "secondary_terms": ["버전", "가격", "주의사항"],
                },
            })
            value["release_gate"].update({
                "policy_id": publisher.SPECIAL_POLICY_ID,
                "human_approval_required": True,
                "automatic_publish_allowed": False,
            })
            evidence_path.write_text(json.dumps(value), encoding="utf-8")

            with self.assertRaisesRegex(
                publisher.PublishError,
                "special brief alignment focus is missing from title",
            ):
                publisher.validate_candidate(
                    article,
                    evidence_path,
                    "2026-07-26--deep-analysis",
                    repo_root=root,
                    require_today=False,
                    publication_kind="special",
                    approved_by="편집자",
                    approval_basis="기술 설명 중심 특별판을 승인함",
                )

    def test_special_candidate_requires_matching_id_kind_and_approval(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            article, evidence_path = self.make_candidate(root)
            with self.assertRaisesRegex(publisher.PublishError, "do not match"):
                publisher.validate_candidate(
                    article,
                    evidence_path,
                    "2026-07-26--cordis",
                    repo_root=root,
                    require_today=False,
                )
            with self.assertRaisesRegex(publisher.PublishError, "lowercase-slug"):
                publisher.validate_candidate(
                    article,
                    evidence_path,
                    "2026-07-26--Cordis",
                    repo_root=root,
                    require_today=False,
                    publication_kind="special",
                )


if __name__ == "__main__":
    unittest.main(verbosity=2)
