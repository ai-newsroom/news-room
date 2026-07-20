import json
import unittest
from dataclasses import fields
from decimal import Decimal
from pathlib import Path

import adapter


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "acquisition-cases.json"


class XAdapterContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
        cls.budget_policy = adapter.BudgetPolicy(
            max_calls_per_run=20,
            max_post_reads_per_run=200,
            monthly_post_read_limit=1000,
            monthly_cost_limit_usd=Decimal("10.00"),
            post_read_unit_cost_usd=Decimal("0.005"),
        )

    def scenario(self, name):
        return next(
            value for value in self.fixture["scenarios"] if value["name"] == name
        )

    def test_route_request_contracts(self):
        for case in self.fixture["route_requests"]:
            with self.subTest(case=case["name"]):
                config = adapter.AdapterConfig.from_mapping(case["config"])
                checkpoint = adapter.Checkpoint.from_mapping(case["checkpoint"])
                request = adapter.plan_request(
                    config,
                    checkpoint,
                    adapter.BudgetMeter(self.budget_policy),
                )
                self.assertEqual(request.method, "GET")
                self.assertEqual(request.path, case["expected_path"])
                for key, value in case["expected_params"].items():
                    self.assertEqual(request.params[key], value)
                self.assertIn("edit_history_tweet_ids", request.params["tweet.fields"])

    def test_webhook_is_push_only(self):
        config = adapter.AdapterConfig(
            route=adapter.FILTERED_STREAM_WEBHOOK,
            scope_key="mock-webhook",
            max_results=100,
        )
        checkpoint = adapter.Checkpoint(
            route=config.route,
            scope_key=config.scope_key,
            complete=False,
        )
        with self.assertRaises(adapter.PushDeliveryOnly):
            adapter.plan_request(
                config,
                checkpoint,
                adapter.BudgetMeter(self.budget_policy),
            )

    def test_pagination_since_edit_dedupe_and_metrics(self):
        case = self.scenario("pagination-since-edit-and-dedupe")
        result = adapter.run_fixture_scenario(case)
        expected = case["expected_result"]

        self.assertEqual(
            [event["kind"] for event in result["events"]], expected["event_kinds"]
        )
        self.assertEqual(
            [event["current_post_id"] for event in result["events"]],
            expected["event_current_ids"],
        )
        self.assertEqual(result["checkpoint"]["since_id"], expected["since_id"])
        self.assertEqual(
            result["checkpoint"]["pagination_token"], expected["pagination_token"]
        )
        self.assertEqual(result["checkpoint"]["complete"], expected["complete"])

        for key in (
            "calls",
            "post_reads_gross",
            "estimated_cost_usd",
            "duplicate_reads",
            "edits",
            "deletes",
            "lead_time_seconds",
            "recall",
            "circuit_breaker",
        ):
            self.assertEqual(result["metrics"][key], expected[key], key)
        self.assertAlmostEqual(result["metrics"]["duplicate_rate"], 0.25)
        self.assertEqual(result["request_trace"][0]["params"]["since_id"], "100")
        self.assertNotIn("pagination_token", result["request_trace"][0]["params"])
        self.assertEqual(
            result["request_trace"][1]["params"]["pagination_token"], "page-2"
        )

    def test_delete_tombstones_entire_edit_chain_idempotently(self):
        case = self.scenario("delete-edit-chain-tombstone")
        result = adapter.run_fixture_scenario(case)
        expected = case["expected_result"]

        self.assertEqual(
            [event["kind"] for event in result["events"]], expected["event_kinds"]
        )
        self.assertEqual(
            result["events"][0]["canonical_post_id"], expected["canonical_post_id"]
        )
        record = result["records"][0]
        self.assertEqual(record["deleted"], expected["record_deleted"])
        self.assertEqual(record["content"], expected["record_content"])
        self.assertEqual(result["metrics"]["deletes"], expected["deletes"])
        self.assertEqual(
            result["metrics"]["post_reads_gross"], expected["post_reads_gross"]
        )
        self.assertEqual(
            result["metrics"]["estimated_cost_usd"],
            expected["estimated_cost_usd"],
        )

    def test_recent_search_dedupes_a_timeline_record(self):
        case = self.scenario("recent-search-dedupes-timeline-record")
        result = adapter.run_fixture_scenario(case)
        expected = case["expected_result"]

        self.assertEqual(
            [event["current_post_id"] for event in result["events"]],
            expected["event_current_ids"],
        )
        self.assertEqual(result["checkpoint"]["since_id"], expected["since_id"])
        for key in (
            "calls",
            "post_reads_gross",
            "estimated_cost_usd",
            "duplicate_reads",
            "recall",
        ):
            self.assertEqual(result["metrics"][key], expected[key], key)
        self.assertEqual(result["request_trace"][0]["path"], "/2/tweets/search/recent")

    def test_circuit_breaker_preserves_mid_page_checkpoint(self):
        case = self.scenario("call-budget-stops-mid-pagination")
        result = adapter.run_fixture_scenario(case)
        expected = case["expected_result"]

        self.assertEqual(
            [event["current_post_id"] for event in result["events"]],
            expected["event_current_ids"],
        )
        for key in ("since_id", "pagination_token", "complete"):
            self.assertEqual(result["checkpoint"][key], expected[key], key)
        for key in (
            "calls",
            "post_reads_gross",
            "estimated_cost_usd",
            "circuit_breaker",
        ):
            self.assertEqual(result["metrics"][key], expected[key], key)

    def test_live_gate_keeps_user_decisions_independent(self):
        self.assertEqual(
            adapter.live_gate(None, False)["blockers"],
            ["monthly_cost_cap_required", "credential_provider_required"],
        )
        self.assertEqual(
            adapter.live_gate("5.00", False)["blockers"],
            ["credential_provider_required"],
        )
        self.assertEqual(
            adapter.live_gate(None, True)["blockers"],
            ["monthly_cost_cap_required"],
        )
        self.assertTrue(adapter.live_gate("5.00", True)["live_allowed"])

    def test_contract_objects_cannot_store_secret_material(self):
        forbidden = {"authorization", "bearer_token", "api_key", "client_secret"}
        for contract_type in (
            adapter.AdapterConfig,
            adapter.Checkpoint,
            adapter.BudgetPolicy,
            adapter.FetchRequest,
            adapter.RunMetrics,
        ):
            with self.subTest(contract_type=contract_type.__name__):
                names = {field.name.lower() for field in fields(contract_type)}
                self.assertTrue(names.isdisjoint(forbidden))

        def keys(value):
            if isinstance(value, dict):
                for key, child in value.items():
                    yield str(key).lower()
                    yield from keys(child)
            elif isinstance(value, list):
                for child in value:
                    yield from keys(child)

        self.assertTrue(set(keys(self.fixture)).isdisjoint(forbidden))

    def test_pricing_snapshot_is_explicit_and_not_a_hidden_default(self):
        snapshot = self.fixture["pricing_snapshot"]
        self.assertEqual(snapshot["checked_at"], "2026-07-20")
        self.assertEqual(snapshot["post_read_unit_cost_usd"], "0.005")
        with self.assertRaises(KeyError):
            adapter.BudgetPolicy.from_mapping(
                {
                    "max_calls_per_run": 1,
                    "max_post_reads_per_run": 10,
                    "monthly_post_read_limit": 100,
                    "monthly_cost_limit_usd": "1.00"
                }
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
