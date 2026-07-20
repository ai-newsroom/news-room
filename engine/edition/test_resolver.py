#!/usr/bin/env python3
"""Stage-0/1 regression tests for runtime resolution and route baselines."""

from __future__ import annotations

import copy
import hashlib
import html
import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

import resolver

from tools.worktree_manifest import capture, compare


ROOT = Path(__file__).resolve().parents[2]
FIXTURE_ROOT = Path(__file__).parent / "fixtures"
INVALID_FIXTURE = json.loads(
    (FIXTURE_ROOT / "invalid-runtime-configs.json").read_text(
        encoding="utf-8"
    )
)
LEGACY_ROUTES = json.loads(
    (ROOT / "tests/fixtures/legacy-routes.json").read_text(
        encoding="utf-8"
    )
)
EXCLUDED_CONTENT = json.loads(
    (ROOT / "tests/fixtures/excluded-content.json").read_text(
        encoding="utf-8"
    )
)
SCHEMA = resolver.load_json(resolver.RUNTIME_SCHEMA)


def load_configs():
    return {
        edition: resolver.load_json(path)
        for edition, path in resolver.CONFIG_PATHS.items()
    }


def mutate(config, path, value):
    target = config
    for part in path[:-1]:
        target = target[part]
    target[path[-1]] = value


def content_snapshot():
    return {
        path.relative_to(ROOT).as_posix(): hashlib.sha256(
            path.read_bytes()
        ).hexdigest()
        for path in sorted((ROOT / "content").rglob("*"))
        if path.is_file()
    }


def frontmatter_value(path, key):
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0] != "---":
        raise AssertionError(f"frontmatter missing: {path}")
    for line in lines[1:]:
        if line == "---":
            break
        if line.startswith(f"{key}:"):
            value = line.split(":", 1)[1].strip()
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
    return None


def frontmatter_title(path):
    title = frontmatter_value(path, "title")
    if title is None:
        raise AssertionError(f"title missing: {path}")
    return title


class RuntimeEditionResolverTest(unittest.TestCase):
    def test_three_configs_resolve_with_isolated_routes_and_write_roots(self):
        resolved = resolver.validate_and_resolve_all(
            load_configs(), SCHEMA, ROOT
        )
        self.assertEqual(
            set(resolved), {"current-affairs", "ai", "eda"}
        )
        self.assertEqual(
            {
                edition: value["site"]["route_prefix"]
                for edition, value in resolved.items()
            },
            {
                "current-affairs": "/news",
                "ai": "/ai",
                "eda": "/eda",
            },
        )
        technical_roots = {
            edition: {
                key: resolved[edition]["normalized_paths"][key][
                    "relative"
                ]
                for key in (
                    "content_root",
                    "run_root",
                    "decision_root",
                )
            }
            for edition in ("ai", "eda")
        }
        self.assertTrue(
            set(technical_roots["ai"].values()).isdisjoint(
                technical_roots["eda"].values()
            )
        )

    def test_current_affairs_points_to_current_legacy_contract(self):
        current = resolver.resolve_requested("current-affairs")[
            "resolution"
        ]
        paths = current["normalized_paths"]
        self.assertEqual(paths["workspace"]["relative"], "newsroom")
        self.assertEqual(
            paths["prompt"]["relative"],
            "prompts/daily-newsroom-single-claude.md",
        )
        self.assertEqual(
            paths["workflow"]["relative"],
            "workflows/daily-newsroom-single-claude.json",
        )
        self.assertEqual(
            paths["legacy_entrypoint"]["relative"],
            "scripts/publish-daily.sh",
        )
        self.assertTrue(current["schedule"]["enabled"])
        self.assertEqual(
            current["schedule"]["managed_by"], "external-cron"
        )
        self.assertEqual(
            current["release"]["mode"], "legacy-wrapper"
        )

    def test_technical_editions_are_disabled_prepare_only_and_human_gated(
        self,
    ):
        for edition in ("ai", "eda"):
            with self.subTest(edition=edition):
                report = resolver.resolve_requested(edition)
                resolved = report["resolution"]
                self.assertFalse(resolved["schedule"]["enabled"])
                self.assertEqual(
                    resolved["schedule"]["managed_by"], "none"
                )
                self.assertEqual(
                    resolved["release"],
                    {
                        "mode": "prepare-only",
                        "requires_human_approval": True,
                        "git_write": False,
                        "deploy": False,
                    },
                )
                self.assertEqual(
                    resolved["fallback_policy"],
                    "technical-explicit-failure",
                )
                self.assertNotIn(
                    "prompt", resolved["normalized_paths"]
                )
                self.assertNotIn(
                    "workflow", resolved["normalized_paths"]
                )

    def test_resolver_cli_only_outputs_paths_and_a_nonexecuting_phase_plan(
        self,
    ):
        before_manifest = capture(ROOT)
        before_content = content_snapshot()
        reports = []
        environment = {
            **os.environ,
            "PYTHONDONTWRITEBYTECODE": "1",
        }
        for edition in ("current-affairs", "ai", "eda"):
            completed = subprocess.run(
                [
                    sys.executable,
                    "engine/edition/resolver.py",
                    "--edition",
                    edition,
                ],
                cwd=ROOT,
                env=environment,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(
                completed.returncode,
                0,
                completed.stdout + completed.stderr,
            )
            report = json.loads(completed.stdout)
            reports.append(report)
            self.assertEqual(report["status"], "passed")
            self.assertEqual(report["mode"], "resolve-only")
            self.assertEqual(report["side_effects"], [])
            self.assertFalse(report["workflow_executed"])
            self.assertFalse(report["content_written"])
            self.assertFalse(report["git_written"])
            phases = report["resolution"]["phase_plan"]
            self.assertEqual(
                [phase["phase"] for phase in phases],
                [
                    "resolve",
                    "acquire",
                    "analyze",
                    "decide",
                    "validate",
                    "stage",
                ],
            )
            self.assertTrue(phases[0]["executed"])
            self.assertTrue(
                all(
                    not phase["executed"] and phase["writes"] == []
                    for phase in phases[1:]
                )
            )
            for path in report["resolution"][
                "normalized_paths"
            ].values():
                self.assertTrue(Path(path["absolute"]).is_absolute())

        after_manifest = capture(ROOT)
        preservation = compare(before_manifest, after_manifest)
        self.assertEqual(
            preservation["status"], "pass", preservation
        )
        self.assertEqual(content_snapshot(), before_content)
        self.assertEqual(len(reports), 3)

    def test_fixed_invalid_configs_fail_closed(self):
        for case in INVALID_FIXTURE["cases"]:
            with self.subTest(case=case["case_id"]):
                configs = copy.deepcopy(load_configs())
                mutate(
                    configs[case["edition"]],
                    case["mutation"]["path"],
                    case["mutation"]["value"],
                )
                with self.assertRaises(resolver.ResolutionError) as caught:
                    resolver.validate_and_resolve_all(
                        configs, SCHEMA, ROOT
                    )
                self.assertIn(
                    case["expected_error"], str(caught.exception)
                )

    def test_unknown_edition_is_rejected_as_json_without_side_effects(
        self,
    ):
        completed = subprocess.run(
            [
                sys.executable,
                "engine/edition/resolver.py",
                "--edition",
                "unknown",
            ],
            cwd=ROOT,
            env={
                **os.environ,
                "PYTHONDONTWRITEBYTECODE": "1",
            },
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 2)
        report = json.loads(completed.stdout)
        self.assertEqual(report["status"], "failed")
        self.assertIn("unknown edition", report["error"])
        self.assertEqual(report["side_effects"], [])

    def test_route_manifests_partition_every_current_depth_one_article(
        self,
    ):
        legacy = LEGACY_ROUTES["routes"]
        excluded = EXCLUDED_CONTENT["content"]
        legacy_ids = {item["content_id"] for item in legacy}
        excluded_ids = {item["content_id"] for item in excluded}
        self.assertTrue(legacy_ids.isdisjoint(excluded_ids))
        self.assertEqual(
            excluded_ids,
            {
                "2026-06-14-codex-high-test",
                "2026-06-14-codex-high-workflow-test",
            },
        )
        article_ids = {
            path.parent.name
            for path in (ROOT / "content").glob("*/article.md")
        }
        published_ids = {
            path.parent.name
            for path in (ROOT / "content").glob("*/article.md")
            if frontmatter_value(path, "publication") != "experiment"
        }
        self.assertEqual(article_ids, published_ids | excluded_ids)
        self.assertTrue(legacy_ids.issubset(published_ids))
        post_baseline_ids = published_ids - legacy_ids
        baseline_through = LEGACY_ROUTES["baseline_through"]
        self.assertTrue(post_baseline_ids)
        for content_id in post_baseline_ids:
            self.assertRegex(content_id, r"^\d{4}-\d{2}-\d{2}$")
            self.assertGreater(content_id, baseline_through)
        self.assertEqual(
            {item["content_id"] for item in legacy if "-prep" in item["content_id"]},
            {"2026-06-11-prep"},
        )
        for item in legacy:
            if item["content_id"] != "2026-06-11-prep":
                self.assertRegex(
                    item["content_id"], r"^\d{4}-\d{2}-\d{2}$"
                )
            self.assertEqual(
                frontmatter_title(ROOT / item["source"]),
                item["title"],
            )
        for item in excluded:
            self.assertEqual(
                frontmatter_title(ROOT / item["source"]),
                item["title"],
            )

    def test_current_site_build_matches_route_title_and_home_baseline(
        self,
    ):
        completed = subprocess.run(
            ["npm", "--prefix", "site", "run", "build"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(
            completed.returncode,
            0,
            completed.stdout + completed.stderr,
        )
        legacy = LEGACY_ROUTES["routes"]
        excluded = EXCLUDED_CONTENT["content"]
        published_ids = {
            path.parent.name
            for path in (ROOT / "content").glob("*/article.md")
            if frontmatter_value(path, "publication") != "experiment"
        }
        expected_routes = {
            f"/news/{content_id}/" for content_id in published_ids
        }
        built_routes = {
            f"/news/{path.parent.name}/"
            for path in (ROOT / "site/dist/news").glob("*/index.html")
        }
        self.assertEqual(built_routes, expected_routes)

        home = html.unescape(
            (ROOT / "site/dist/index.html").read_text(
                encoding="utf-8"
            )
        )
        for item in legacy:
            route_file = (
                ROOT
                / "site/dist"
                / item["route"].lstrip("/")
                / "index.html"
            )
            rendered = html.unescape(
                route_file.read_text(encoding="utf-8")
            )
            self.assertIn(item["title"], rendered)
            self.assertIn(
                f'href="{item["home_href"]}"', home
            )
        for item in excluded:
            route_file = (
                ROOT
                / "site/dist"
                / item["current_route"].lstrip("/")
                / "index.html"
            )
            self.assertFalse(route_file.exists())
            self.assertNotIn(
                f'href="{item["current_home_href"]}"', home
            )
        legacy_ids = {item["content_id"] for item in legacy}
        for content_id in published_ids - legacy_ids:
            self.assertIn(
                f'href="/news-room/news/{content_id}/"', home
            )
        self.assertEqual(
            EXCLUDED_CONTENT["migration_target"],
            "remain-outside-published-routes",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
