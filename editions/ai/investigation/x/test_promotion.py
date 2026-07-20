import json
import unittest
from copy import deepcopy
from pathlib import Path

import promotion


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "promotion-cases.json"


class XSignalPromotionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
        cls.cases = {case["name"]: case for case in cls.fixture["cases"]}

    def evaluate(self, name):
        return promotion.evaluate_signal(self.cases[name]["signal"])

    def test_all_fixture_cases_match_expected_promotion(self):
        for name, case in self.cases.items():
            with self.subTest(case=name):
                result = promotion.evaluate_signal(case["signal"])
                expected = case["expected"]
                self.assertEqual(
                    result["promotion_status"], expected["promotion_status"]
                )
                self.assertEqual(
                    result["promotion_mapping"]["evidence_grade"],
                    expected["evidence_grade"],
                )
                self.assertEqual(
                    result["promotion_mapping"]["reproducibility"],
                    expected["reproducibility"],
                )
                self.assertEqual(
                    result["editorial_disposition"],
                    expected["editorial_disposition"],
                )
                self.assertEqual(result["reason_codes"], expected["reason_codes"])
                if "retention_action" in expected:
                    self.assertEqual(
                        result["retention_action"], expected["retention_action"]
                    )
                if "text_excerpt" in expected:
                    self.assertEqual(
                        result["post"]["text_excerpt"], expected["text_excerpt"]
                    )
                promotion.validate_signal(result)

    def test_fixture_covers_all_five_promotion_states(self):
        states = {
            promotion.evaluate_signal(case["signal"])["promotion_status"]
            for case in self.fixture["cases"]
        }
        self.assertEqual(states, promotion.PROMOTION_STATUSES)

    def test_x_signal_stays_s2_at_every_promotion_level(self):
        for name, case in self.cases.items():
            with self.subTest(case=name):
                result = promotion.evaluate_signal(case["signal"])
                self.assertEqual(
                    result["promotion_mapping"]["signal_source_type"], "S2"
                )
                for claim in result["extracted_claims"]:
                    self.assertEqual(
                        claim["promotion_mapping"]["signal_source_type"], "S2"
                    )

    def test_thread_quote_reply_and_outbound_links_are_preserved(self):
        case = self.cases["paper-and-code-primary-linked"]
        before_thread = deepcopy(case["signal"]["thread_context"])
        before_links = deepcopy(case["signal"]["outbound_links"])
        result = promotion.evaluate_signal(case["signal"])

        self.assertEqual(result["thread_context"], before_thread)
        self.assertEqual(result["outbound_links"], before_links)
        self.assertEqual(result["thread_context"]["reply_to_post_id"], "998")
        self.assertEqual(result["thread_context"]["quoted_post_id"], "997")

    def test_performance_text_without_sources_cannot_be_promoted(self):
        result = self.evaluate("missing-primary-source")
        claim = result["extracted_claims"][0]
        self.assertEqual(claim["promotion_status"], promotion.SIGNAL_ONLY)
        self.assertEqual(claim["promotion_mapping"]["evidence_grade"], "E0")
        self.assertEqual(result["editorial_disposition"], "no-publish")

    def test_deleted_edit_nda_opinion_and_conflict_boundaries(self):
        deleted = self.evaluate("deleted-post-rejected")
        self.assertIsNone(deleted["post"]["text_excerpt"])
        self.assertEqual(deleted["retention_action"], "tombstone-purge-content")

        edited = self.evaluate("material-edit-not-reverified")
        self.assertEqual(edited["promotion_status"], promotion.REJECTED)
        self.assertIn("latest-post-version-rehydrated", edited["recheck_triggers"])

        nda = self.evaluate("nda-implied-source-rejected")
        self.assertEqual(nda["retention_action"], "discard-restricted-material")

        opinion = self.evaluate("personal-opinion-signal-only")
        self.assertEqual(opinion["reason_codes"], ["OPINION_ONLY"])

        conflict = self.evaluate("conflicted-performance-awaits-independent-source")
        self.assertEqual(
            conflict["promotion_status"], promotion.PRIMARY_SOURCE_LINKED
        )
        self.assertEqual(conflict["editorial_disposition"], "no-publish")
        self.assertEqual(conflict["reason_codes"], ["CONFLICT_UNRESOLVED"])

    def test_independent_reproduction_maps_to_e4_r3(self):
        result = self.evaluate("independent-reproduction-verified")
        claim = result["extracted_claims"][0]
        self.assertEqual(
            claim["promotion_status"], promotion.INDEPENDENTLY_VERIFIED
        )
        self.assertEqual(
            claim["promotion_mapping"]["evidence_source_types"],
            ["P1", "P2", "I1"],
        )
        self.assertEqual(claim["promotion_mapping"]["evidence_grade"], "E4")
        self.assertEqual(claim["promotion_mapping"]["reproducibility"], "R3")

    def test_material_claims_use_the_most_conservative_status(self):
        signal = deepcopy(self.cases["official-announcement-confirmed"]["signal"])
        signal["extracted_claims"].append(
            {
                "claim_id": "C2",
                "claim_kind": "opinion",
                "claim_text_ko": "작성자의 개인 전망이다.",
                "material": True,
                "subject_version": "Model-B-v2",
                "claim_date": "2026-07-20",
                "source_refs": [],
            }
        )
        result = promotion.evaluate_signal(signal)
        self.assertEqual(
            [claim["promotion_status"] for claim in result["extracted_claims"]],
            [promotion.ANNOUNCEMENT_CONFIRMED, promotion.SIGNAL_ONLY],
        )
        self.assertEqual(result["promotion_status"], promotion.SIGNAL_ONLY)
        self.assertEqual(result["promotion_mapping"]["evidence_grade"], "E0")
        self.assertEqual(result["editorial_disposition"], "no-publish")

    def test_version_mismatch_stays_signal_only(self):
        signal = deepcopy(self.cases["paper-and-code-primary-linked"]["signal"])
        signal["extracted_claims"][0]["subject_version"] = "Runtime-C-v2"
        result = promotion.evaluate_signal(signal)
        self.assertEqual(result["promotion_status"], promotion.SIGNAL_ONLY)
        self.assertEqual(result["reason_codes"], ["VERSION_OR_DATE_MISMATCH"])

        signal = deepcopy(self.cases["paper-and-code-primary-linked"]["signal"])
        signal["extracted_claims"][0]["claim_date"] = "2026-07-19"
        result = promotion.evaluate_signal(signal)
        self.assertEqual(result["promotion_status"], promotion.SIGNAL_ONLY)
        self.assertEqual(result["reason_codes"], ["VERSION_OR_DATE_MISMATCH"])

    def test_unknown_source_reference_fails_closed(self):
        signal = deepcopy(self.cases["missing-primary-source"]["signal"])
        signal["extracted_claims"][0]["source_refs"] = ["DOES_NOT_EXIST"]
        with self.assertRaises(promotion.ContractError):
            promotion.evaluate_signal(signal)


if __name__ == "__main__":
    unittest.main(verbosity=2)
