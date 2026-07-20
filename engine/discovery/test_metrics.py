import copy
import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

import metrics


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "discovery-metrics-cases.json"


class DiscoveryMetricsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
        cls.run_case = cls.fixture["multi_channel_run"]
        cls.retrospective = cls.fixture["retrospective"]

    def channel(self, record, channel_id):
        return next(
            channel
            for channel in record["channels"]
            if channel["channel_id"] == channel_id
        )

    def make_window(self, variant_name, offsets=None):
        variant = self.retrospective[variant_name]
        offsets = self.retrospective["offset_days"] if offsets is None else offsets
        base = datetime(2026, 7, 1, 10, 0, tzinfo=timezone.utc)
        records = []
        for run_index, day_offset in enumerate(offsets):
            discovered_at = base + timedelta(days=day_offset)
            candidates = []
            for candidate_index, spec in enumerate(variant["candidates"]):
                published_at = discovered_at - timedelta(
                    seconds=spec["latency_seconds"]
                )
                candidates.append(
                    {
                        "candidate_id": "{}:{}:{}".format(
                            variant_name, run_index, candidate_index
                        ),
                        "canonical_candidate_id": "topic:{}:{}:{}".format(
                            variant_name, run_index, candidate_index
                        ),
                        "source_published_at": published_at.isoformat(),
                        "discovered_at": discovered_at.isoformat(),
                        "duplicate_of": None,
                        "primary_evidence_promoted": spec["primary"],
                        "editorial_disposition": spec["disposition"],
                        "false_positive": spec["false_positive"],
                        "false_positive_reason": spec.get("reason"),
                    }
                )
            raw = {
                "schema_version": 1,
                "run_id": "{}-run-{}".format(variant_name, run_index),
                "edition": "ai",
                "started_at": discovered_at.isoformat(),
                "ended_at": (discovered_at + timedelta(minutes=1)).isoformat(),
                "channels": [
                    {
                        "channel_id": self.retrospective["channel_id"],
                        "channel_type": "paper-feed",
                        "configuration_id": variant["configuration_id"],
                        "collection_status": "completed",
                        "execution_time_seconds": variant[
                            "execution_time_seconds"
                        ],
                        "direct_cost_usd": variant["direct_cost_usd"],
                        "candidates": candidates,
                    }
                ],
            }
            records.append(metrics.build_run_record(raw))
        return {
            "window_id": variant["window_id"],
            "configuration_id": variant["configuration_id"],
            "records": records,
        }

    def evaluate(self, variant_name, offsets=None, next_experiment=True):
        return metrics.evaluate_retrospective(
            self.make_window("baseline"),
            self.make_window(variant_name, offsets),
            channel_id=self.retrospective["channel_id"],
            policy=self.retrospective["policy"],
            next_experiment=(
                self.retrospective["next_experiment"] if next_experiment else None
            ),
        )

    def test_multi_channel_run_records_all_required_metrics(self):
        record = metrics.build_run_record(self.run_case["input"])
        expected = self.run_case["expected"]
        self.assertEqual(
            record["run_metrics"]["candidate_count"],
            expected["run_candidate_count"],
        )
        self.assertEqual(
            record["run_metrics"]["unique_candidate_count"],
            expected["run_unique_candidate_count"],
        )
        self.assertEqual(
            record["run_metrics"]["execution_time_seconds"],
            expected["run_execution_time_seconds"],
        )
        self.assertEqual(
            record["run_metrics"]["direct_cost_usd"],
            expected["run_direct_cost_usd"],
        )
        for channel_id, expected_metrics in expected["channels"].items():
            with self.subTest(channel=channel_id):
                actual = self.channel(record, channel_id)["metrics"]
                for key, value in expected_metrics.items():
                    self.assertEqual(actual[key], value, key)

    def test_no_publish_is_not_automatically_a_false_positive(self):
        record = metrics.build_run_record(self.run_case["input"])
        paper = self.channel(record, "ml-paper-feed")["metrics"]
        self.assertEqual(paper["publish_candidate_contribution_count"], 1)
        self.assertEqual(paper["false_positive_reviewed_count"], 2)
        self.assertEqual(paper["false_positive_count"], 0)

    def test_duplicate_observation_cannot_claim_editorial_outcome(self):
        raw = copy.deepcopy(self.run_case["input"])
        duplicate = raw["channels"][0]["candidates"][1]
        duplicate["editorial_disposition"] = "publish-candidate"
        duplicate["false_positive"] = False
        with self.assertRaisesRegex(
            metrics.ContractError, "duplicate_observation_cannot_claim_outcome"
        ):
            metrics.build_run_record(raw)

    def test_secret_material_is_rejected(self):
        raw = copy.deepcopy(self.run_case["input"])
        raw["api_key"] = "must-not-be-recorded"
        with self.assertRaisesRegex(
            metrics.ContractError, "secret_material_forbidden"
        ):
            metrics.build_run_record(raw)

    def test_enabled_hook_writes_atomic_idempotent_record(self):
        collected = {"unchanged": True}
        with tempfile.TemporaryDirectory() as directory:
            result, hook = metrics.collect_with_optional_metrics(
                lambda: collected,
                lambda _: self.run_case["input"],
                lambda record: metrics.write_json_record(directory, record),
                enabled=True,
            )
            self.assertIs(result, collected)
            self.assertEqual(hook["status"], "recorded")
            target = Path(directory) / "fixture-run-001.json"
            saved = json.loads(target.read_text(encoding="utf-8"))
            self.assertEqual(saved["run_id"], "fixture-run-001")

            same_result, same_hook = metrics.collect_with_optional_metrics(
                lambda: collected,
                lambda _: self.run_case["input"],
                lambda record: metrics.write_json_record(directory, record),
                enabled=True,
            )
            self.assertIs(same_result, collected)
            self.assertEqual(same_hook["status"], "recorded")

    def test_disabled_hook_bypasses_builder_and_sink(self):
        collected = object()

        def should_not_run(_):
            raise AssertionError("disabled instrumentation executed")

        result, hook = metrics.collect_with_optional_metrics(
            lambda: collected,
            should_not_run,
            should_not_run,
            enabled=False,
        )
        self.assertIs(result, collected)
        self.assertEqual(hook, {"status": "disabled"})

    def test_instrumentation_failure_does_not_fail_collection(self):
        collected = ["candidate-a"]

        def failing_sink(_):
            raise OSError("fixture sink unavailable")

        result, hook = metrics.collect_with_optional_metrics(
            lambda: collected,
            lambda _: self.run_case["input"],
            failing_sink,
            enabled=True,
        )
        self.assertIs(result, collected)
        self.assertEqual(hook["status"], "failed")
        self.assertEqual(hook["error_type"], "OSError")
        self.assertNotIn("fixture sink unavailable", json.dumps(hook))

    def test_collector_failure_remains_a_collection_failure(self):
        def failing_collector():
            raise RuntimeError("collector failed")

        with self.assertRaisesRegex(RuntimeError, "collector failed"):
            metrics.collect_with_optional_metrics(
                failing_collector,
                lambda _: self.run_case["input"],
                lambda _: None,
                enabled=True,
            )

    def test_missing_baseline_forbids_comparison_and_improvement_claim(self):
        experiment = self.make_window("retain")
        result = metrics.evaluate_retrospective(
            None,
            experiment,
            channel_id=self.retrospective["channel_id"],
            policy=self.retrospective["policy"],
            next_experiment=None,
        )
        self.assertEqual(result["status"], "baseline-missing")
        self.assertFalse(result["comparison_ready"])
        self.assertIsNone(result["improvement_claim"])
        self.assertIsNone(result["decision"])

    def test_later_of_run_count_and_days_controls_observation_window(self):
        ten_runs_only_eight_days = [0, 1, 2, 3, 4, 5, 6, 7, 8, 8]
        result = self.evaluate("retain", offsets=ten_runs_only_eight_days)
        self.assertEqual(result["status"], "collecting")
        self.assertFalse(result["comparison_ready"])
        self.assertIn(
            "EXPERIMENT_WINDOW_INCOMPLETE", result["reason_codes"]
        )
        self.assertIsNone(result["decision"])
        self.assertIsNone(result["next_bounded_experiment"])

    def test_mature_comparison_records_retain_and_bounded_next_experiment(self):
        result = self.evaluate("retain")
        self.assertEqual(result["status"], "evaluated")
        self.assertEqual(result["decision"], "retain")
        self.assertEqual(
            result["improvement_claim"], "supported-within-observed-window"
        )
        self.assertEqual(
            result["comparison"]["primary_evidence_promotion_rate_delta"],
            0.25,
        )
        self.assertEqual(
            result["comparison"]["false_positive_rate_delta"], -0.25
        )
        self.assertEqual(
            result["next_bounded_experiment"],
            self.retrospective["next_experiment"],
        )

    def test_mature_comparison_records_adjust(self):
        result = self.evaluate("adjust")
        self.assertEqual(result["decision"], "adjust")
        self.assertEqual(result["improvement_claim"], "not-supported")
        self.assertIn("IMPROVEMENT_BELOW_THRESHOLD", result["reason_codes"])
        self.assertEqual(
            result["next_bounded_experiment"],
            self.retrospective["next_experiment"],
        )

    def test_mature_comparison_records_rollback_on_guardrails(self):
        result = self.evaluate("rollback")
        self.assertEqual(result["decision"], "rollback")
        self.assertEqual(result["improvement_claim"], "not-supported")
        self.assertIn(
            "FALSE_POSITIVE_GUARDRAIL_BREACHED", result["reason_codes"]
        )
        self.assertIn("DIRECT_COST_GUARDRAIL_BREACHED", result["reason_codes"])
        self.assertIn(
            "DISCOVERY_LATENCY_GUARDRAIL_BREACHED", result["reason_codes"]
        )
        self.assertEqual(
            result["next_bounded_experiment"],
            self.retrospective["next_experiment"],
        )

    def test_mature_window_requires_bounded_next_experiment(self):
        with self.assertRaisesRegex(
            metrics.ContractError, "next_bounded_experiment_required"
        ):
            self.evaluate("retain", next_experiment=False)


if __name__ == "__main__":
    unittest.main(verbosity=2)
