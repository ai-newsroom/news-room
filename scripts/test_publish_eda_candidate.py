#!/usr/bin/env python3
"""Regression tests for the automatic EDA publication boundary."""

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

## 새로 공개된 설계 피드백

새 도구는 분석 결과를 다음 설계 행동으로 연결합니다.

## 피드백이 다음 설계로 이어지는 과정

RTL과 constraint를 받은 도구가 분석 결과를 만들고 에이전트가 다음 탐색점을 고릅니다.

### 기존 flow와 비교하면

수작업 전달 단계가 줄어들 수 있습니다.

## 설계 흐름의 의미와 남은 검증

설계 수렴을 앞당길 가능성이 있지만 전체 flow 우위는 아직 확인되지 않았습니다.

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
            "policy_id": publisher.POLICY_ID,
            "human_approval_required": False,
            "automatic_publish_allowed": True,
            "quality_gate_passed": True,
            "content_promotion_allowed": True,
            "git_write_allowed": True,
            "deploy_allowed": True,
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


class AutomaticEdaPublisherTest(unittest.TestCase):
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

    def test_validated_candidate_materializes_automatic_release_without_external_actions(self):
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
                executor="test",
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
            self.assertEqual(release["authorization"]["mode"], "automatic")
            self.assertEqual(
                release["authorization"]["policy_id"],
                publisher.POLICY_ID,
            )
            self.assertIn("artifact-hashes", release["authorization"]["checks"])

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

    def test_verification_appendix_remains_required(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            article, evidence_path = self.make_candidate(root)
            article.write_text(
                article.read_text(encoding="utf-8").replace(
                    "## 이해상충과 취재 조건",
                    "## 취재 메모",
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(publisher.PublishError, "required section"):
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

    def test_one_source_url_is_not_enough_for_automatic_analysis(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            article, evidence_path = self.make_candidate(root)
            value = json.loads(evidence_path.read_text())
            value["claims"][0]["sources"] = value["claims"][0]["sources"][:1]
            evidence_path.write_text(json.dumps(value), encoding="utf-8")
            with self.assertRaisesRegex(publisher.PublishError, "at least two source URLs"):
                publisher.validate_candidate(
                    article,
                    evidence_path,
                    "2026-08-13",
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
