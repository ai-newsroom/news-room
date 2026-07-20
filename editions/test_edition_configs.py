#!/usr/bin/env python3
"""Regression tests for isolated AI/EDA editorial configuration."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

from editions.validate_editions import (
    CURRENT_AFFAIRS_FALLBACKS,
    EDITORIAL_REFERENCE_KEYS,
    EditionValidationError,
    load_json,
    validate_config,
)


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = load_json(ROOT / "editions/_schema/edition.schema.json")
CONFIG_PATHS = {
    edition: ROOT / f"editions/{edition}/edition.json" for edition in ("ai", "eda")
}


class EditionConfigTests(unittest.TestCase):
    def config(self, edition: str = "ai"):
        return load_json(CONFIG_PATHS[edition])

    def assert_rejected(self, config, phrase: str | None = None):
        with self.assertRaises(EditionValidationError) as caught:
            validate_config(config, SCHEMA, ROOT)
        if phrase:
            self.assertIn(phrase, str(caught.exception))

    def test_ai_and_eda_configs_resolve_every_explicit_contract_section(self):
        for edition in ("ai", "eda"):
            with self.subTest(edition=edition):
                config = self.config(edition)
                result = validate_config(config, SCHEMA, ROOT)
                self.assertEqual(set(config["editorial"]), set(EDITORIAL_REFERENCE_KEYS) | {"release_gates"})
                self.assertEqual(result["resolved_section_references"], 9)
                self.assertTrue(result["publish_requires_human_approval"])
                self.assertEqual(result["fallback_policy"], "explicit-failure")

    def test_every_missing_editorial_setting_fails_instead_of_falling_back(self):
        for key in (*EDITORIAL_REFERENCE_KEYS, "release_gates"):
            with self.subTest(key=key):
                config = self.config()
                del config["editorial"][key]
                self.assert_rejected(config, "missing required property")

    def test_human_approval_cannot_be_disabled(self):
        config = self.config()
        config["publication"]["publish_requires_human_approval"] = False
        self.assert_rejected(config, "must equal True")

        config = self.config()
        config["publication"]["publish_requires_human_approval"] = 1
        self.assert_rejected(config, "expected boolean")

    def test_automatic_publish_cannot_be_enabled(self):
        config = self.config()
        config["publication"]["automatic_publish"] = True
        self.assert_rejected(config, "must equal False")

    def test_each_current_affairs_fallback_must_be_forbidden(self):
        for fallback in CURRENT_AFFAIRS_FALLBACKS:
            with self.subTest(fallback=fallback):
                config = self.config()
                config["forbidden_fallbacks"].remove(fallback)
                config["forbidden_fallbacks"].append("unused/fallback")
                self.assert_rejected(config, "does not contain the required value")

    def test_current_affairs_paths_are_rejected_as_section_references(self):
        fallback_refs = {
            "charter": "newsroom/charter.md",
            "roles": "newsroom/personas/lighthouse.md",
            "sources": "newsroom/sources.md",
        }
        for key, path in fallback_refs.items():
            with self.subTest(key=key):
                config = self.config()
                config["editorial"][key]["path"] = path
                self.assert_rejected(config)

    def test_missing_file_fails_without_fallback(self):
        config = self.config()
        config["editorial"]["charter"]["path"] = "docs/does-not-exist.md"
        self.assert_rejected(config, "no fallback attempted")

    def test_missing_technical_config_fails_without_loading_newsroom_defaults(self):
        with self.assertRaisesRegex(EditionValidationError, "cannot load"):
            load_json(ROOT / "editions/missing/edition.json")

    def test_missing_heading_fails_without_fallback(self):
        config = self.config()
        config["editorial"]["charter"]["heading"] = "### Missing technical charter"
        self.assert_rejected(config, "no fallback attempted")

    def test_cross_edition_reference_is_rejected(self):
        config = self.config()
        config["editorial"]["charter"] = {
            "path": "editions/eda/charter.md",
            "heading": "### 6.1 EDA판 강령과 주제 선정",
        }
        self.assert_rejected(config, "cross-edition fallback")

    def test_unknown_config_keys_are_rejected(self):
        config = self.config()
        config["fallback"] = "newsroom"
        self.assert_rejected(config, "unexpected property")

    def test_cli_validates_both_editions_without_writing_state(self):
        environment = dict(os.environ)
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        completed = subprocess.run(
            [sys.executable, "editions/validate_editions.py"],
            cwd=ROOT,
            env=environment,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        report = json.loads(completed.stdout)
        self.assertEqual(report["status"], "passed")
        self.assertEqual([item["id"] for item in report["editions"]], ["ai", "eda"])


if __name__ == "__main__":
    unittest.main()
