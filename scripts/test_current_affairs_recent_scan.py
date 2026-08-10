#!/usr/bin/env python3
"""Regression tests for current-affairs recent article scan paths."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/check-current-affairs-recent-scan.py"
SPEC = importlib.util.spec_from_file_location(
    "check_current_affairs_recent_scan",
    SCRIPT,
)
assert SPEC and SPEC.loader
scanner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(scanner)


class CurrentAffairsRecentScanTest(unittest.TestCase):
    def test_20260803_publish_cwd_finds_recent_article_and_requires_delta(self):
        completed = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--today",
                "2026-08-03",
                "--candidate-topic",
                "검사의 보완수사권 폐지 형사소송법 개정안 후속 보도",
                "--overlap-keyword",
                "보완수사권",
                "--overlap-keyword",
                "형사소송법",
            ],
            cwd=ROOT / "newsroom",
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 1, completed.stdout)
        report = json.loads(completed.stdout)
        self.assertEqual(report["status"], "delta-required")
        self.assertIn(
            "content/2026-08-01/article.md",
            report["checked_paths"],
        )
        self.assertIn(
            "content/2026-08-01/article.md",
            report["comparison_required_paths"],
        )

    def test_populated_repo_with_zero_recent_articles_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            (repo / ".git").mkdir()
            article = repo / "content/2026-07-20/article.md"
            article.parent.mkdir(parents=True)
            article.write_text("old article", encoding="utf-8")
            workdir = repo / "newsroom"
            workdir.mkdir()

            args = scanner.parse_args(
                [
                    "--cwd",
                    str(workdir),
                    "--today",
                    "2026-08-03",
                ]
            )
            report = scanner.audit(args)

            self.assertEqual(report["status"], "blocked")
            self.assertEqual(
                report["reason"],
                "recent scan found zero articles in a populated repository",
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
