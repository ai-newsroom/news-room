#!/usr/bin/env python3
"""Regression tests for the edition-isolated technical source registries."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

from editions.validate_editions import EditionValidationError, load_json
from editions.validate_source_registries import (
    REQUIRED_SOURCE_TYPES,
    validate_registry,
)


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = load_json(ROOT / "editions/_schema/source-registry.schema.json")
REGISTRY_PATHS = {
    edition: ROOT / f"editions/{edition}/sources/primary-sources.json"
    for edition in ("ai", "eda")
}


class SourceRegistryTests(unittest.TestCase):
    def registry(self, edition: str = "ai"):
        return load_json(REGISTRY_PATHS[edition])

    def assert_rejected(self, registry, phrase: str | None = None):
        with self.assertRaises(EditionValidationError) as caught:
            validate_registry(registry, SCHEMA)
        if phrase:
            self.assertIn(phrase, str(caught.exception))

    def test_ai_and_eda_cover_their_required_technical_source_types(self):
        for edition in ("ai", "eda"):
            with self.subTest(edition=edition):
                result = validate_registry(self.registry(edition), SCHEMA, edition)
                self.assertTrue(REQUIRED_SOURCE_TYPES[edition].issubset(result["source_types"]))
                self.assertGreaterEqual(result["source_count"], 9)
                self.assertFalse(result["current_affairs_imported"])

    def test_ai_has_primary_artifacts_and_independent_secondary_evaluation(self):
        result = validate_registry(self.registry("ai"), SCHEMA, "ai")
        self.assertGreater(result["primary_count"], 0)
        self.assertGreater(result["secondary_count"], 0)

    def test_every_source_records_url_owner_relation_access_and_conflict(self):
        required = {
            "canonical_url",
            "owner",
            "default_relation",
            "access",
            "conflict_of_interest",
        }
        for edition in ("ai", "eda"):
            for source in self.registry(edition)["sources"]:
                with self.subTest(edition=edition, source=source["id"]):
                    self.assertTrue(required.issubset(source))
                    self.assertTrue(source["canonical_url"].startswith("https://"))
                    self.assertIn(source["default_relation"], {"primary", "secondary"})

    def test_each_required_acceptance_field_is_schema_required(self):
        for field in (
            "canonical_url",
            "owner",
            "default_relation",
            "access",
            "conflict_of_interest",
        ):
            with self.subTest(field=field):
                registry = self.registry()
                del registry["sources"][0][field]
                self.assert_rejected(registry, "missing required property")

    def test_missing_required_source_type_fails_closed(self):
        for edition, required_types in REQUIRED_SOURCE_TYPES.items():
            missing_type = sorted(required_types)[0]
            with self.subTest(edition=edition, source_type=missing_type):
                registry = self.registry(edition)
                registry["sources"] = [
                    source for source in registry["sources"] if source["source_type"] != missing_type
                ]
                self.assert_rejected(registry, "missing required source types")

    def test_duplicate_source_id_is_rejected(self):
        registry = self.registry()
        registry["sources"][1]["id"] = registry["sources"][0]["id"]
        self.assert_rejected(registry, "duplicate source ids")

    def test_secondary_source_requires_independent_or_professional_semantics(self):
        registry = self.registry()
        source = next(item for item in registry["sources"] if item["default_relation"] == "secondary")
        source["evidence_codes"] = ["P1"]
        self.assert_rejected(registry, "secondary source needs I1 or S1")

    def test_current_affairs_import_and_popularity_cannot_be_enabled(self):
        for key in ("imports_current_affairs_sources", "popularity_used"):
            with self.subTest(key=key):
                registry = self.registry()
                registry["selection_policy"][key] = True
                self.assert_rejected(registry, "must equal False")

    def test_newsroom_source_list_must_remain_forbidden(self):
        registry = self.registry()
        registry["forbidden_imports"] = []
        self.assert_rejected(registry)

    def test_registry_types_cannot_express_political_media_or_community_feeds(self):
        allowed_types = set(SCHEMA["$defs"]["source"]["properties"]["source_type"]["enum"])
        self.assertTrue({"news-media", "community", "social-trend"}.isdisjoint(allowed_types))

    def test_cli_validates_both_registries_without_network(self):
        environment = dict(os.environ)
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        completed = subprocess.run(
            [sys.executable, "editions/validate_source_registries.py"],
            cwd=ROOT,
            env=environment,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        report = json.loads(completed.stdout)
        self.assertEqual(report["status"], "passed")
        self.assertEqual(
            [registry["edition"] for registry in report["registries"]],
            ["ai", "eda"],
        )


if __name__ == "__main__":
    unittest.main()
