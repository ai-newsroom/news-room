#!/usr/bin/env python3
"""Regression tests for deterministic current-affairs publication assembly."""

from __future__ import annotations

import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TRIM_FILTER = ROOT / "scripts/trim-trailing-blank-lines.awk"


def trim_trailing_blank_lines(text: str) -> str:
    return subprocess.run(
        ["awk", "-f", str(TRIM_FILTER)],
        input=text,
        check=True,
        capture_output=True,
        text=True,
    ).stdout


class PublishDailyTest(unittest.TestCase):
    def test_debate_assembly_uses_trailing_blank_line_filter(self) -> None:
        publisher = (ROOT / "scripts/publish-daily.sh").read_text()
        self.assertIn(
            'awk -f "$REPO/scripts/trim-trailing-blank-lines.awk"',
            publisher,
        )

    def test_filter_removes_only_trailing_blank_lines(self) -> None:
        source = "first paragraph\n\nsecond paragraph\n \t\n\n"
        self.assertEqual(
            trim_trailing_blank_lines(source),
            "first paragraph\n\nsecond paragraph\n",
        )

    def test_filter_preserves_clean_input(self) -> None:
        self.assertEqual(trim_trailing_blank_lines("body\n"), "body\n")


if __name__ == "__main__":
    unittest.main(verbosity=2)
