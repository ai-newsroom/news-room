#!/usr/bin/env bash
# news-room 일일 발행 래퍼.
# cron이 매일 1회 호출한다. LLM과 무관한 결정적 스크립트이므로
# 파이프라인이 실패해도 휴간 공지는 거의 항상 발행된다 (강령 7).
set -uo pipefail

export PATH="$HOME/.cargo/bin:$HOME/.local/bin:$PATH"
NEWS_ROOM_TZ="${NEWS_ROOM_TZ:-Asia/Seoul}"

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATE="$(TZ="$NEWS_ROOM_TZ" date +%F)"
WS="$REPO/newsroom"
ART="$WS/artifacts"
OUT="$REPO/content/$DATE"
PROMPT_FILE="${NEWS_ROOM_PROMPT_FILE:-$REPO/prompts/daily-newsroom-single-claude.md}"
SESSION_STARTUP_TIMEOUT_SECS="${NEWS_ROOM_SESSION_STARTUP_TIMEOUT_SECS:-60}"
SESSION_TURN_TIMEOUT_SECS="${NEWS_ROOM_SESSION_TURN_TIMEOUT_SECS:-3600}"
SESSION_RUN_JSON="$ART/session-run.json"

cd "$REPO"
git pull --rebase --quiet || true

# 작업대 초기화
rm -rf "$ART"
mkdir -p "$ART"
echo "$DATE" > "$ART/today.txt"

# 편집국 소집: 서버 배치에서는 workflow가 아니라 단일 Claude Code PTY 세션을 실행한다.
PROMPT="$(cat "$PROMPT_FILE")"
coco-agents session run \
  --backend claude \
  --runtime rust-pty-attached \
  --workspace "$WS" \
  --name "news-room-$DATE" \
  --startup-timeout "$SESSION_STARTUP_TIMEOUT_SECS" \
  --turn-timeout "$SESSION_TURN_TIMEOUT_SECS" \
  --json \
  "$PROMPT" > "$SESSION_RUN_JSON"
SESSION_EXIT=$?
echo "$SESSION_EXIT" > "$ART/session-exit-code.txt"

mkdir -p "$OUT"

if [[ -s "$ART/article.md" ]]; then
  cp "$ART/article.md" "$OUT/article.md"
  [[ -s "$ART/guest.md" ]] && cp "$ART/guest.md" "$OUT/guest.md"

  # 토론 전문을 결정적으로 조립 (라운드 순서 = 토론의 시간 순서)
  MEMBERS=(
    "zelkova:느티나무 (논설위원·중도 보수)"
    "waterway:물길 (논설위원·중도 진보)"
    "gadfly:등에 (철학)"
    "stethoscope:청진기 (심리)"
    "weft:씨줄 (사회)"
    "balance:저울 (경제)"
    "guest:객원"
  )
  {
    echo "# 편집국 토론 전문 — $DATE"
    echo
    echo "> 이 문서는 기사가 만들어진 과정의 기록이다. 가공 없이 그대로 공개한다."
    echo
    if [[ -s "$ART/topic.md" ]]; then
      echo "## 데스크의 주제 선정 (등대)"
      echo
      cat "$ART/topic.md"
      echo
    fi
    for round in 1 2 3; do
      if [[ $round -eq 3 ]]; then
        echo "## 3라운드 — 최종 변론 (논설위원)"
      else
        echo "## ${round}라운드"
      fi
      echo
      for entry in "${MEMBERS[@]}"; do
        key="${entry%%:*}"; label="${entry#*:}"
        f="$ART/round${round}-${key}.md"
        if [[ -s "$f" ]]; then
          echo "### $label"
          echo
          cat "$f"
          echo
        fi
      done
    done
  } > "$OUT/debate.md"
else
  # 휴간 공지 — 실패도 뉴스로 알린다
  cat > "$OUT/article.md" <<EOF
---
title: "휴간 공지"
date: $DATE
topic: "발행 실패"
summary: "오늘 편집국 파이프라인이 실패해 기사를 내지 못했습니다."
holiday: true
---

오늘은 기사를 내지 못했습니다. 편집국(자동화 파이프라인)이 도중에 실패했습니다.

실패를 숨기지 않는 것도 이 매체의 투명성입니다. 원인을 확인하는 대로
강령과 시스템을 다듬어 내일 다시 발행하겠습니다. — 편집자
EOF
fi

git add "content/$DATE"
if git diff --cached --quiet; then
  echo "No content changes for $DATE"
else
  git commit -m "publish: $DATE" --quiet && git push --quiet
fi
