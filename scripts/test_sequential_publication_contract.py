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

    def test_runner_orders_live_current_affairs_before_ai(self) -> None:
        runner = (ROOT / "scripts/publish-sequential-daily.sh").read_text()
        current = runner.index('"$REPO/scripts/publish-daily.sh"')
        live_current = runner.index(
            '"$REPO/scripts/verify-publication.sh" current-affairs'
        )
        ai = runner.index('"$REPO/scripts/publish-ai-daily.sh"')
        self.assertLess(current, live_current)
        self.assertLess(live_current, ai)

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

    def test_ai_no_publish_is_durable_for_same_date_replay(self) -> None:
        publisher = (ROOT / "scripts/publish-ai-daily.sh").read_text()
        self.assertIn('DECISION_FILE="$PUBLICATION_RUN_DIR/ai-decision.json"', publisher)
        self.assertIn('"decision") == "no-publish"', publisher)
        self.assertIn('mv "$DECISION_FILE.tmp" "$DECISION_FILE"', publisher)

    def test_both_editions_are_owned_by_one_timer(self) -> None:
        current = json.loads(
            (ROOT / "editions/current-affairs/runtime.json").read_text()
        )
        ai = json.loads((ROOT / "editions/ai/runtime.json").read_text())
        self.assertEqual(
            current["schedule"]["managed_by"], ai["schedule"]["managed_by"]
        )
        self.assertEqual(
            current["schedule"]["managed_by"], "systemd:news-room-daily.timer"
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
