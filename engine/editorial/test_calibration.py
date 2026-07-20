#!/usr/bin/env python3
"""Tests for deterministic, edition-isolated historical gate calibration."""

from __future__ import annotations

import copy
import hashlib
import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

from calibration import (
    DEFAULT_FIXTURE,
    PROFILES,
    CalibrationError,
    evaluate_case,
    evaluate_fixture,
    load_fixture,
)


ROOT = Path(__file__).resolve().parents[2]


def content_snapshot():
    snapshot = {}
    for path in sorted((ROOT / "content").rglob("*")):
        if path.is_file():
            snapshot[path.relative_to(ROOT).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return snapshot


class HistoricalCalibrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = load_fixture(DEFAULT_FIXTURE)
        cls.cases = {case["case_id"]: case for case in cls.fixture["cases"]}

    def test_each_edition_has_publish_and_no_publish_historical_cases(self):
        counts = {
            edition: {"publish-candidate": 0, "no-publish": 0} for edition in PROFILES
        }
        for case in self.fixture["cases"]:
            counts[case["edition"]][case["expected"]["decision"]] += 1
        self.assertEqual(
            counts,
            {
                "ai": {"publish-candidate": 1, "no-publish": 1},
                "eda": {"publish-candidate": 1, "no-publish": 1},
            },
        )

    def test_all_fixed_expectations_match_the_evaluator(self):
        results = evaluate_fixture(self.fixture)
        self.assertEqual(len(results), 4)
        for result in results:
            expected = self.cases[result["case_id"]]["expected"]
            self.assertEqual(result["decision"], expected["decision"])
            self.assertEqual(result["reason_codes"], expected["reason_codes"])
            self.assertEqual(result["failed_gates"], expected["failed_gates"])

    def test_every_case_has_claim_grades_reproducibility_conflict_and_expected_reasons(self):
        for case in self.fixture["cases"]:
            with self.subTest(case=case["case_id"]):
                self.assertTrue(case["claim_ledger"])
                self.assertRegex(case["reproducibility"], r"^R[0-3]$")
                self.assertIn("disclosed", case["conflict_of_interest"])
                self.assertIn("reason_codes", case["expected"])
                for claim in case["claim_ledger"]:
                    self.assertTrue(claim["evidence"])
                    for evidence in claim["evidence"]:
                        self.assertRegex(evidence["source_type"], r"^(P[0-2]|I1|S[12])$")
                        self.assertRegex(evidence["evidence_grade"], r"^E[0-4]$")

    def test_repeated_runs_are_byte_deterministic(self):
        first = json.dumps(
            evaluate_fixture(copy.deepcopy(self.fixture)),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        for _ in range(10):
            rerun = json.dumps(
                evaluate_fixture(copy.deepcopy(self.fixture)),
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
            self.assertEqual(rerun, first)

    def test_evidence_digest_and_decision_ignore_input_array_order(self):
        for original in self.fixture["cases"]:
            with self.subTest(case=original["case_id"]):
                permuted = copy.deepcopy(original)
                permuted["claim_ledger"].reverse()
                for claim in permuted["claim_ledger"]:
                    claim["evidence"].reverse()
                self.assertEqual(evaluate_case(permuted), evaluate_case(original))

    def test_cross_edition_execution_fails_instead_of_mixing_gates(self):
        for case in self.fixture["cases"]:
            other = "eda" if case["edition"] == "ai" else "ai"
            with self.subTest(case=case["case_id"]), self.assertRaisesRegex(
                CalibrationError, "cannot run as"
            ):
                evaluate_case(case, requested_edition=other)

    def test_cross_edition_role_is_rejected(self):
        case = copy.deepcopy(next(value for value in self.fixture["cases"] if value["edition"] == "ai"))
        case["roles_completed"].append("eda-desk")
        with self.assertRaisesRegex(CalibrationError, "cross-edition roles"):
            evaluate_case(case)

    def test_edition_score_contracts_are_not_interchangeable_and_roles_are_disjoint(self):
        self.assertNotEqual(
            set(PROFILES["ai"]["score_keys"]), set(PROFILES["eda"]["score_keys"])
        )
        self.assertTrue(
            PROFILES["ai"]["required_roles"].isdisjoint(PROFILES["eda"]["required_roles"])
        )
        case = copy.deepcopy(next(value for value in self.fixture["cases"] if value["edition"] == "ai"))
        case["candidate_scores"] = {
            key: 0 for key in PROFILES["eda"]["score_keys"]
        }
        with self.assertRaisesRegex(CalibrationError, "score keys are not isolated"):
            evaluate_case(case)

    def test_comparative_vendor_claims_fail_the_e3_and_reproducibility_gates(self):
        rejected = [
            evaluate_case(case)
            for case in self.fixture["cases"]
            if case["expected"]["decision"] == "no-publish"
        ]
        for result in rejected:
            with self.subTest(case=result["case_id"]):
                self.assertEqual(result["evidence_ceiling"], "E1")
                self.assertIn("VENDOR_CLAIM_ONLY", result["reason_codes"])
                self.assertIn("COMPARISON_NOT_VALID", result["reason_codes"])
                self.assertIn("REPRODUCIBILITY_TOO_LOW", result["reason_codes"])

    def test_cli_is_a_no_write_calibration_dry_run(self):
        before = content_snapshot()
        environment = dict(os.environ)
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        completed = subprocess.run(
            [sys.executable, "calibration.py"],
            cwd=Path(__file__).parent,
            env=environment,
            check=False,
            capture_output=True,
            text=True,
        )
        after = content_snapshot()
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        report = json.loads(completed.stdout)
        self.assertEqual(report["status"], "passed")
        self.assertEqual(report["mode"], "calibration-dry-run")
        self.assertEqual(report["side_effects"], [])
        self.assertEqual(after, before)


if __name__ == "__main__":
    unittest.main()
