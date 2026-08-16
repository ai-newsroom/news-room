#!/usr/bin/env python3
"""Regression tests for the public AI no-publish status boundary."""

from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "publish_ai_no_publish",
    ROOT / "scripts/publish-ai-no-publish.py",
)
assert SPEC and SPEC.loader
publisher = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(publisher)


def decision(publication_id: str = "2026-08-16") -> dict:
    return {
        "schema_version": 1,
        "publication_id": publication_id,
        "decision": "no-publish",
        "reason": "새롭고 중복되지 않은 후보 중 오늘의 근거 기준을 충족한 주제가 없었습니다.",
        "discovery_review": {
            "signals": [{"channel": "official-release-notes", "note": "확인함"}],
            "alternatives": [{"subject": "candidate", "decision": "not-selected"}],
        },
    }


class AiNoPublishStatusTest(unittest.TestCase):
    def make_decision(self, root: Path, value: dict | None = None) -> Path:
        path = root / "var/runs/ai/test/no-publish.json"
        path.parent.mkdir(parents=True)
        path.write_text(
            json.dumps(value or decision(), ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        return path

    def test_valid_decision_materializes_without_article_route(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = self.make_decision(root)
            candidate = publisher.validate_decision(
                source,
                "2026-08-16",
                repo_root=root,
                require_today=False,
            )
            result = publisher.materialize(candidate, repo_root=root)

            target = root / "decisions/ai/2026-08-16/no-publish.json"
            self.assertEqual(target.read_bytes(), source.read_bytes())
            self.assertFalse((root / "content/ai/2026-08-16").exists())
            self.assertEqual(result["route"], "/ai/")
            self.assertEqual(
                result["external_actions"],
                {"commit": False, "push": False, "deploy": False},
            )

    def test_unexpected_fields_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            value = decision()
            value["article_path"] = "content/ai/2026-08-16/article.md"
            source = self.make_decision(root, value)
            with self.assertRaisesRegex(publisher.NoPublishError, "fields"):
                publisher.validate_decision(
                    source,
                    "2026-08-16",
                    repo_root=root,
                    require_today=False,
                )

    def test_article_conflict_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = self.make_decision(root)
            article_root = root / "content/ai/2026-08-16"
            article_root.mkdir(parents=True)
            (article_root / "article.md").write_text("article", encoding="utf-8")
            with self.assertRaisesRegex(publisher.NoPublishError, "cannot share"):
                publisher.validate_decision(
                    source,
                    "2026-08-16",
                    repo_root=root,
                    require_today=False,
                )

    def test_invalid_discovery_review_entry_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            value = decision()
            value["discovery_review"]["alternatives"] = [{}]
            source = self.make_decision(root, value)
            with self.assertRaisesRegex(publisher.NoPublishError, "entries"):
                publisher.validate_decision(
                    source,
                    "2026-08-16",
                    repo_root=root,
                    require_today=False,
                )

    def test_publication_id_mismatch_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = self.make_decision(root)
            with self.assertRaisesRegex(publisher.NoPublishError, "mismatch"):
                publisher.validate_decision(
                    source,
                    "2026-08-17",
                    repo_root=root,
                    require_today=False,
                )


if __name__ == "__main__":
    unittest.main(verbosity=2)
