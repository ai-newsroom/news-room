#!/usr/bin/env python3
"""Static contracts tying the sequential runner, schedules, and safety gates together."""

from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class SequentialPublicationContractTest(unittest.TestCase):
    def test_ai_discovery_prompt_uses_global_sources_without_fixed_checklist(self) -> None:
        prompt = (ROOT / "prompts/daily-ai-codex.md").read_text()
        self.assertIn("강제 순회 목록이 아니라 발견 출발점", prompt)
        for provider in ("Qwen", "DeepSeek", "Mistral"):
            self.assertIn(provider, prompt)
        self.assertIn("discovery_review", prompt)
        self.assertIn("선택하지 않은 실질적 발표", prompt)

    def test_runner_orders_current_affairs_ai_and_eda(self) -> None:
        runner = (ROOT / "scripts/publish-sequential-daily.sh").read_text()
        current = runner.index('"$REPO/scripts/publish-daily.sh"')
        live_current = runner.index(
            '"$REPO/scripts/verify-publication.sh" current-affairs'
        )
        ai = runner.index('"$REPO/scripts/publish-ai-daily.sh"')
        live_ai = runner.index(
            '"$REPO/scripts/verify-publication.sh" ai'
        )
        eda = runner.index('"$REPO/scripts/publish-eda-daily.sh"')
        live_eda = runner.index(
            '"$REPO/scripts/verify-publication.sh" eda'
        )
        self.assertLess(current, live_current)
        self.assertLess(live_current, ai)
        self.assertLess(ai, live_ai)
        self.assertLess(live_ai, eda)
        self.assertLess(eda, live_eda)

    def test_ai_entrypoint_rechecks_live_current_affairs(self) -> None:
        publisher = (ROOT / "scripts/publish-ai-daily.sh").read_text()
        current_guard = publisher.index(
            'HEAD:content/$PUBLICATION_ID/article.md'
        )
        live_guard = publisher.index(
            '"$REPO/scripts/verify-publication.sh" current-affairs'
        )
        codex = publisher.index("codex exec")
        self.assertLess(current_guard, live_guard)
        self.assertLess(live_guard, codex)

    def test_ai_entrypoint_loads_only_the_matching_date_brief(self) -> None:
        publisher = (ROOT / "scripts/publish-ai-daily.sh").read_text()
        self.assertIn(
            'BRIEF_FILE="$REPO/prompts/ai-briefs/$PUBLICATION_ID.md"',
            publisher,
        )
        brief_guard = publisher.index('if [[ -f "$BRIEF_FILE" ]]')
        brief_read = publisher.index('cat "$BRIEF_FILE"')
        codex = publisher.index("codex exec")
        self.assertLess(brief_guard, brief_read)
        self.assertLess(brief_read, codex)

        brief = (ROOT / "prompts/ai-briefs/2026-08-11.md").read_text()
        self.assertIn("Muse Glimmer 30B", brief)
        self.assertIn("https://research.meta.ai/blog/introducing-muse-glimmer-open-agentic-model", brief)
        self.assertIn("https://huggingface.co/meta-models/Muse-Glimmer-30B", brief)

    def test_ai_no_publish_is_durable_for_same_date_replay(self) -> None:
        publisher = (ROOT / "scripts/publish-ai-daily.sh").read_text()
        self.assertIn('DECISION_FILE="$PUBLICATION_RUN_DIR/ai-decision.json"', publisher)
        self.assertIn('"decision") == "no-publish"', publisher)
        self.assertIn('mv "$DECISION_FILE.tmp" "$DECISION_FILE"', publisher)
        self.assertIn(
            'HEAD:decisions/ai/$PUBLICATION_ID/no-publish.json',
            publisher,
        )
        self.assertEqual(publisher.count("scripts/publish-ai-no-publish.py"), 2)
        status_validation = publisher.index("scripts/publish-ai-no-publish.py")
        status_finalize = publisher.index(
            '"$REPO/scripts/finalize-publication.sh" ai-status'
        )
        status_verify = publisher.index(
            '"$REPO/scripts/verify-publication.sh" ai-status'
        )
        self.assertLess(status_validation, status_finalize)
        self.assertLess(status_finalize, status_verify)

    def test_ai_validation_failure_gets_one_bounded_repair_before_materialization(self) -> None:
        publisher = (ROOT / "scripts/publish-ai-daily.sh").read_text()
        self.assertIn(
            'MAX_VALIDATION_ATTEMPTS="${NEWS_ROOM_AI_MAX_VALIDATION_ATTEMPTS:-2}"',
            publisher,
        )
        self.assertIn('REPAIR_PROMPT_FILE="$REPO/prompts/repair-ai-candidate.md"', publisher)
        validation = publisher.index('while ! run_candidate_validation')
        repair = publisher.index('repair_candidate "$VALIDATION_ATTEMPT"')
        materialize = publisher.index('--executor "news-room-sequential-publisher"')
        self.assertLess(validation, repair)
        self.assertLess(repair, materialize)

        repair_prompt = (ROOT / "prompts/repair-ai-candidate.md").read_text()
        self.assertIn("기사 frontmatter에 `publication_id`를 넣지 않는다", repair_prompt)
        self.assertIn("새 주제를 조사하지 않는다", repair_prompt)

    def test_ai_special_entrypoint_is_human_gated_and_preserves_daily_slot(self) -> None:
        publisher = (ROOT / "scripts/publish-ai-special.sh").read_text()
        self.assertIn('PUBLICATION_ID="$PUBLICATION_DATE--$SLUG"', publisher)
        self.assertIn("special brief must be below prompts/ai-special-briefs", publisher)
        self.assertIn('--publication-kind special', publisher)
        self.assertIn('--approved-by "$APPROVED_BY"', publisher)
        self.assertIn('--approval-basis "$APPROVAL_BASIS"', publisher)
        self.assertNotIn('"$REPO/scripts/publish-daily.sh"', publisher)
        live = publisher.index('"$REPO/scripts/verify-publication.sh" ai')
        retrospective = publisher.index(
            '"$COCO_AGENTS" session run'
        )
        self.assertLess(live, retrospective)
        self.assertIn("git show origin/main:prompts/post-publish-retrospective.md", publisher)
        self.assertIn("completed deterministic publisher proof", publisher)

        prompt = (ROOT / "prompts/special-ai-codex.md").read_text()
        self.assertIn("ai-special-publish-v1", prompt)
        self.assertIn("publication_kind: special", prompt)
        self.assertIn("정규 일일판의 주제 선정이나", prompt)

    def test_eda_entrypoint_rechecks_prior_stages_and_uses_bounded_repair(self) -> None:
        publisher = (ROOT / "scripts/publish-eda-daily.sh").read_text()
        current_guard = publisher.index(
            'HEAD:content/$PUBLICATION_ID/article.md'
        )
        ai_guard = publisher.index(
            'HEAD:content/ai/$PUBLICATION_ID/article.md'
        )
        codex = publisher.index("codex exec")
        self.assertLess(current_guard, ai_guard)
        self.assertLess(ai_guard, codex)
        self.assertIn('DECISION_FILE="$PUBLICATION_RUN_DIR/eda-decision.json"', publisher)
        self.assertIn(
            'MAX_VALIDATION_ATTEMPTS="${NEWS_ROOM_EDA_MAX_VALIDATION_ATTEMPTS:-2}"',
            publisher,
        )
        validation = publisher.index('while ! run_candidate_validation')
        repair = publisher.index('repair_candidate "$VALIDATION_ATTEMPT"')
        materialize = publisher.index('--executor "news-room-sequential-publisher"')
        self.assertLess(validation, repair)
        self.assertLess(repair, materialize)

        prompt = (ROOT / "prompts/daily-eda-codex.md").read_text()
        self.assertIn("강제 순회 목록이 아니라 발견 출발점", prompt)
        self.assertIn("원문을 최소 두 개", prompt)
        self.assertIn("eda-auto-publish-v1", prompt)
        repair_prompt = (ROOT / "prompts/repair-eda-candidate.md").read_text()
        self.assertIn("기사 frontmatter에 `publication_id`를 넣지 않는다", repair_prompt)
        self.assertIn("새 주제를 조사하지 않는다", repair_prompt)

    def test_all_editions_are_owned_by_one_timer(self) -> None:
        current = json.loads(
            (ROOT / "editions/current-affairs/runtime.json").read_text()
        )
        ai = json.loads((ROOT / "editions/ai/runtime.json").read_text())
        eda = json.loads((ROOT / "editions/eda/runtime.json").read_text())
        self.assertEqual(
            current["schedule"]["managed_by"], ai["schedule"]["managed_by"]
        )
        self.assertEqual(
            current["schedule"]["managed_by"], "systemd:news-room-daily.timer"
        )
        self.assertEqual(
            eda["schedule"]["managed_by"], current["schedule"]["managed_by"]
        )

    def test_retrospective_reads_eda_release_and_measures_its_next_three_runs(self) -> None:
        prompt = (ROOT / "prompts/post-publish-retrospective.md").read_text()
        self.assertIn("content/eda/YYYY-MM-DD/article.md", prompt)
        self.assertIn("/eda/YYYY-MM-DD/", prompt)
        self.assertIn("docs/14-eda-auto-publishing.md", prompt)
        self.assertIn("해당 판의 이후 발행 3회", prompt)
        self.assertIn("원문 두 개의 역할 중복", prompt)
        self.assertIn("content/ai/YYYY-MM-DD--*/article.md", prompt)
        self.assertIn("/ai/YYYY-MM-DD/<slug>/", prompt)


if __name__ == "__main__":
    unittest.main(verbosity=2)
