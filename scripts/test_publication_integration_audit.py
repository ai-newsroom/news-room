#!/usr/bin/env python3
"""Regression tests for publication-affecting improvement integration audit."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "audit_publication_integration",
    ROOT / "scripts/audit-publication-integration.py",
)
assert SPEC and SPEC.loader
audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)


def git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )


class PublicationIntegrationAuditTest(unittest.TestCase):
    def test_flags_done_dirty_v3_item_when_origin_release_still_v2(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            git(repo, "init", "-q")
            (repo / ".coco-agents/inbox/items").mkdir(parents=True)
            (repo / "docs").mkdir()
            (repo / "editions/ai").mkdir(parents=True)
            (repo / "decisions/ai/2026-08-04").mkdir(parents=True)
            (repo / "docs/11-ai-auto-publishing.md").write_text(
                "release gate: ai-technical-blog-v2\n",
                encoding="utf-8",
            )
            (repo / "editions/ai/edition.json").write_text(
                '{"contract": "ai-technical-blog-v2"}\n',
                encoding="utf-8",
            )
            release = {
                "authorization": {
                    "checks": ["ai-technical-blog-v2"],
                },
            }
            (repo / "decisions/ai/2026-08-04/release.json").write_text(
                json.dumps(release),
                encoding="utf-8",
            )
            git(repo, "add", ".")
            git(
                repo,
                "-c",
                "user.email=test@example.invalid",
                "-c",
                "user.name=Test",
                "commit",
                "-q",
                "-m",
                "base",
            )
            git(repo, "branch", "-M", "main")
            git(repo, "update-ref", "refs/remotes/origin/main", "HEAD")

            item = {
                "id": "item_88cd52eaed7143c6a0002dd6ddd96208",
                "status": "done",
                "risk": "medium",
                "kind": "capability",
                "description": "accepted AI accessibility v3",
                "result": {
                    "summary": (
                        "Changed paths:\n"
                        "- docs/11-ai-auto-publishing.md\n"
                        "- editions/ai/edition.json\n"
                    )
                },
            }
            item_path = (
                repo
                / ".coco-agents/inbox/items/"
                / "item_88cd52eaed7143c6a0002dd6ddd96208.json"
            )
            item_path.write_text(json.dumps(item), encoding="utf-8")
            (repo / "docs/11-ai-auto-publishing.md").write_text(
                "release gate: ai-technical-blog-v3\n",
                encoding="utf-8",
            )

            args = audit.parse_args(
                [
                    "--repo",
                    str(repo),
                    "--release-path",
                    "decisions/ai/2026-08-04/release.json",
                    "--expected-release-check",
                    "ai-technical-blog-v3",
                    "--stale-release-check",
                    "ai-technical-blog-v2",
                ]
            )
            report = audit.audit(args)

            self.assertEqual(report["status"], "failed")
            self.assertEqual(
                {
                    finding["code"]
                    for finding in report["findings"]
                },
                {
                    "done-publication-affecting-item-still-dirty",
                    "release-contract-behind-done-item",
                },
            )

    def test_landed_item_with_current_release_passes(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            git(repo, "init", "-q")
            (repo / ".coco-agents/inbox/items").mkdir(parents=True)
            (repo / "decisions/ai/2026-08-05").mkdir(parents=True)
            release = {
                "authorization": {
                    "checks": ["ai-technical-blog-v3"],
                },
            }
            (repo / "decisions/ai/2026-08-05/release.json").write_text(
                json.dumps(release),
                encoding="utf-8",
            )
            item = {
                "id": "item_landed",
                "status": "done",
                "risk": "medium",
                "kind": "capability",
                "result": {
                    "summary": (
                        "Changed paths:\n"
                        "- editions/ai/edition.json\n\n"
                        "HEAD and origin/main both equal abc. "
                        "Commit abc was pushed."
                    )
                },
            }
            (repo / ".coco-agents/inbox/items/item_landed.json").write_text(
                json.dumps(item),
                encoding="utf-8",
            )
            git(repo, "add", ".")
            git(
                repo,
                "-c",
                "user.email=test@example.invalid",
                "-c",
                "user.name=Test",
                "commit",
                "-q",
                "-m",
                "base",
            )
            git(repo, "branch", "-M", "main")
            git(repo, "update-ref", "refs/remotes/origin/main", "HEAD")

            args = audit.parse_args(
                [
                    "--repo",
                    str(repo),
                    "--release-path",
                    "decisions/ai/2026-08-05/release.json",
                    "--expected-release-check",
                    "ai-technical-blog-v3",
                    "--stale-release-check",
                    "ai-technical-blog-v2",
                ]
            )
            report = audit.audit(args)

            self.assertEqual(report["status"], "passed")
            self.assertEqual(report["findings"], [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
