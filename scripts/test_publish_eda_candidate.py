#!/usr/bin/env python3
"""Regression tests for the human-approved EDA publication boundary."""

from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "publish_eda_candidate",
    ROOT / "scripts/publish-eda-candidate.py",
)
assert SPEC and SPEC.loader
publisher = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(publisher)


ARTICLE = """---
edition: eda
decision: publish-candidate
title: "검증 가능한 EDA 피드백"
date: 2026-08-13
subject: "EDA agent feedback loop"
summary: "도구 피드백의 의미와 검증 범위를 나눴습니다."
evidence_ceiling: E2
reproducibility: R1
conflicts: ["당사자 발표가 중심 자료입니다."]
---

도구 피드백이 설계 에이전트의 다음 행동을 바꿉니다.

## 세 줄 요약

- 확인된 사실입니다.
- 저자 보고 결과입니다.
- 독립 비교는 아직 없습니다.

## EDA 엔지니어를 위한 판단

- **지금 할 일:** 피드백 인터페이스를 확인합니다.
- **아직 미룰 일:** 제품 우위를 단정하지 않습니다.
- **다음 신호:** 공개 benchmark를 기다립니다.

## 확인된 것과 확인되지 않은 것

도구가 구조 정보를 제공하는 것은 확인했지만 전체 flow 우위는 확인하지 못했습니다.

## 이 공개의 의의와 편집 판단

**편집 판단:** 두 원문이 지지하는 범위에서만 판단합니다.

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
        "edition": "eda",
        "publication_id": "2026-08-13",
        "date": "2026-08-13",
        "decision": "publish-candidate",
        "selection": {"total": 8, "threshold": 7},
        "evidence_ceiling": level,
        "reproducibility": "R1",
        "release_gate": {
            "human_approval_required": True,
            "automatic_publish_allowed": False,
            "quality_gate_passed": True,
            "content_promotion_allowed": False,
            "git_write_allowed": False,
            "deploy_allowed": False,
        },
        "conflicts": ["당사자 발표가 중심 자료입니다."],
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


class HumanEdaPublisherTest(unittest.TestCase):
    def make_candidate(self, root: Path, level: str = "E2") -> tuple[Path, Path]:
        run = root / "var/runs/eda/test/staged-content"
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

    def test_validated_candidate_materializes_human_release_without_external_actions(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            article, evidence_path = self.make_candidate(root)
            candidate = publisher.validate_candidate(
                article,
                evidence_path,
                "2026-08-13",
                repo_root=root,
                require_today=False,
            )
            result = publisher.materialize(
                candidate,
                approved_by="test owner",
                approval_basis="test approval",
                approval_scope=["first EDA article"],
                repo_root=root,
            )
            self.assertEqual(result["status"], "materialized")
            self.assertEqual(
                result["external_actions"],
                {"commit": False, "push": False, "deploy": False},
            )
            release = json.loads(
                (root / "decisions/eda/2026-08-13/release.json").read_text()
            )
            self.assertEqual(release["authorization"]["mode"], "human")
            self.assertEqual(release["authorization"]["approved_by"], "test owner")

    def test_e1_candidate_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            article, evidence_path = self.make_candidate(root, "E1")
            with self.assertRaisesRegex(publisher.PublishError, "E2 or higher"):
                publisher.validate_candidate(
                    article,
                    evidence_path,
                    "2026-08-13",
                    repo_root=root,
                    require_today=False,
                )

    def test_source_type_alias_is_accepted(self):
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
                "2026-08-13",
                repo_root=root,
                require_today=False,
            )
            self.assertEqual(candidate["publication_id"], "2026-08-13")

    def test_conflicting_source_grade_aliases_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            article, evidence_path = self.make_candidate(root)
            value = json.loads(evidence_path.read_text())
            value["claims"][0]["sources"][0]["source_type"] = "P2"
            evidence_path.write_text(json.dumps(value), encoding="utf-8")
            with self.assertRaisesRegex(publisher.PublishError, "fields conflict"):
                publisher.validate_candidate(
                    article,
                    evidence_path,
                    "2026-08-13",
                    repo_root=root,
                    require_today=False,
                )

    def test_automatic_gate_cannot_enter_human_path(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            article, evidence_path = self.make_candidate(root)
            value = json.loads(evidence_path.read_text())
            value["release_gate"]["automatic_publish_allowed"] = True
            evidence_path.write_text(json.dumps(value), encoding="utf-8")
            with self.assertRaisesRegex(publisher.PublishError, "not authorized"):
                publisher.validate_candidate(
                    article,
                    evidence_path,
                    "2026-08-13",
                    repo_root=root,
                    require_today=False,
                )

    def test_unexpected_frontmatter_field_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            article, evidence_path = self.make_candidate(root)
            article.write_text(
                article.read_text(encoding="utf-8").replace(
                    "date: 2026-08-13\n",
                    'date: 2026-08-13\npublication_id: "2026-08-13"\n',
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
                    "2026-08-13",
                    repo_root=root,
                    require_today=False,
                )
            self.assertFalse((root / "content/eda/2026-08-13").exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
