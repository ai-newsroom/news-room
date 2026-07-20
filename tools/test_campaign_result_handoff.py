#!/usr/bin/env python3
"""Fixture tests for the single-path campaign result handoff."""

from __future__ import annotations

import copy
import hashlib
import json
import os
import statistics
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

import campaign_result_handoff as handoff


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "campaign-result-handoff-cases.json"
)
TOOL_PATH = Path(handoff.__file__)


class CampaignResultHandoffTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads(
            FIXTURE_PATH.read_text(encoding="utf-8")
        )

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.repo = Path(self.temporary.name) / "fixture repo with spaces"
        self.run_id = self.fixture["run_id"]
        self.run_dir = (
            self.repo
            / ".coco-agents"
            / "campaigns"
            / "runs"
            / self.run_id
        )
        self.run_dir.mkdir(parents=True)
        self.target = self.run_dir / "result.json"

        self.sibling_state = (
            self.repo
            / ".coco-agents"
            / "campaigns"
            / "inbox-state.json"
        )
        self.sibling_state.parent.mkdir(parents=True, exist_ok=True)
        self.sibling_state.write_text(
            "do not read or change\n", encoding="utf-8"
        )
        other_run = (
            self.repo
            / ".coco-agents"
            / "campaigns"
            / "runs"
            / "campaign_run_ffffffffffffffffffffffffffffffff"
        )
        other_run.mkdir()
        (other_run / "result.json").write_text(
            "other run sentinel\n", encoding="utf-8"
        )

    def tearDown(self):
        self.temporary.cleanup()

    def invoke(self, command, *, path=None, contract=None):
        result_path = self.target if path is None else path
        payload = None
        if contract is not None:
            payload = json.dumps(
                contract, ensure_ascii=False
            ).encode("utf-8")
        completed = subprocess.run(
            [
                sys.executable,
                str(TOOL_PATH),
                command,
                "--repo",
                str(self.repo),
                "--run-id",
                self.run_id,
                "--result-path",
                str(result_path),
            ],
            input=payload,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        )
        report = json.loads(completed.stdout)
        return completed, report

    def other_campaign_state_snapshot(self):
        result = {}
        campaign_root = self.repo / ".coco-agents"
        for path in sorted(campaign_root.rglob("*")):
            if not path.is_file() or path == self.target:
                continue
            relative = path.relative_to(campaign_root).as_posix()
            result[relative] = hashlib.sha256(
                path.read_bytes()
            ).hexdigest()
        return result

    def materialize_failure_case(self, case):
        if case["path"] == "expected":
            path = self.target
        else:
            path = (
                self.repo
                / ".coco-agents"
                / "campaigns"
                / "runs"
                / case["path"]
            )
        if case["materialization"] == "raw":
            path.write_text(case["content"], encoding="utf-8")
        elif case["materialization"] == "json":
            path.write_text(
                json.dumps(case["content"]), encoding="utf-8"
            )
        return path

    def test_fixed_failure_cases_are_detected_without_touching_other_state(
        self,
    ):
        for case in self.fixture["failure_cases"]:
            with self.subTest(case=case["case_id"]):
                path = self.materialize_failure_case(case)
                before = self.other_campaign_state_snapshot()
                completed, report = self.invoke("verify", path=path)
                after = self.other_campaign_state_snapshot()
                self.assertEqual(completed.returncode, 2)
                self.assertEqual(report["status"], "failed")
                self.assertEqual(
                    report["error"], case["expected_error"]
                )
                self.assertEqual(
                    report["instrumentation"][
                        "other_campaign_state_files_read"
                    ],
                    0,
                )
                self.assertEqual(
                    report["instrumentation"][
                        "other_campaign_state_files_written"
                    ],
                    0,
                )
                self.assertEqual(after, before)
                if self.target.exists():
                    self.target.unlink()

    def test_valid_contract_is_atomically_written_and_reparsed(self):
        before = self.other_campaign_state_snapshot()
        completed, written = self.invoke(
            "write",
            contract=copy.deepcopy(self.fixture["valid_contract"]),
        )
        after = self.other_campaign_state_snapshot()
        self.assertEqual(
            completed.returncode, 0, completed.stderr.decode()
        )
        self.assertEqual(written["status"], "passed")
        self.assertEqual(written["mode"], "write-and-verify")
        self.assertTrue(
            written["checks"]["same_directory_atomic_replace"]
        )
        self.assertTrue(
            written["checks"]["read_back_parse_confirmed"]
        )
        self.assertEqual(
            json.loads(self.target.read_text(encoding="utf-8")),
            self.fixture["valid_contract"],
        )
        self.assertEqual(after, before)
        self.assertEqual(
            list(self.run_dir.glob(".result.json.*.tmp")), []
        )

        completed, verified = self.invoke("verify")
        self.assertEqual(
            completed.returncode, 0, completed.stderr.decode()
        )
        self.assertEqual(
            verified["result_sha256"], written["result_sha256"]
        )
        self.assertEqual(verified["result_path"], str(self.target))

    def test_invalid_stdin_is_rejected_before_any_result_write(self):
        completed = subprocess.run(
            [
                sys.executable,
                str(TOOL_PATH),
                "write",
                "--repo",
                str(self.repo),
                "--run-id",
                self.run_id,
                "--result-path",
                str(self.target),
            ],
            input=b"{invalid",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        )
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 2)
        self.assertEqual(report["error"], "invalid_json")
        self.assertFalse(self.target.exists())
        self.assertEqual(
            list(self.run_dir.glob(".result.json.*.tmp")), []
        )

    def test_verify_subprocess_overhead_is_below_budget_in_fixture(
        self,
    ):
        completed, _ = self.invoke(
            "write",
            contract=copy.deepcopy(self.fixture["valid_contract"]),
        )
        self.assertEqual(completed.returncode, 0)
        durations = []
        for _ in range(11):
            started = time.monotonic()
            completed, report = self.invoke("verify")
            durations.append(
                (time.monotonic() - started) * 1_000
            )
            self.assertEqual(completed.returncode, 0)
            self.assertLessEqual(
                report["instrumentation"]["duration_ms"],
                handoff.OVERHEAD_BUDGET_MS,
            )
        self.assertLess(
            statistics.median(durations),
            handoff.OVERHEAD_BUDGET_MS,
        )

    def test_nested_contract_fields_are_strict(self):
        contract = copy.deepcopy(self.fixture["valid_contract"])
        del contract["follow_ups"][0]["capability_experiment"][
            "rollback_plan"
        ]
        with self.assertRaisesRegex(
            handoff.HandoffError, "fields do not match"
        ):
            handoff.validate_contract(contract)


if __name__ == "__main__":
    unittest.main(verbosity=2)
