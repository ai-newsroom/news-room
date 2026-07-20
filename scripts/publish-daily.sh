#!/usr/bin/env bash
# news-room 일일 발행 래퍼.
# cron이 매일 1회 호출한다. LLM과 무관한 결정적 스크립트이므로
# 파이프라인이 실패해도 휴간 공지는 거의 항상 발행된다 (강령 7).
set -uo pipefail

export PATH="$HOME/.cargo/bin:$HOME/.local/bin:$PATH"
NEWS_ROOM_TZ="${NEWS_ROOM_TZ:-Asia/Seoul}"
NEWS_ROOM_BACKEND="${NEWS_ROOM_BACKEND:-claude}"

case "$NEWS_ROOM_BACKEND" in
  claude|codex) ;;
  *)
    echo "Unsupported NEWS_ROOM_BACKEND: $NEWS_ROOM_BACKEND" >&2
    exit 2
    ;;
esac

if [[ "$NEWS_ROOM_BACKEND" == "claude" ]]; then
  NEWS_ROOM_RUNTIME="${NEWS_ROOM_RUNTIME:-rust-pty-attached}"
  export COCO_AGENTS_CLAUDE_EFFORT="${COCO_AGENTS_CLAUDE_EFFORT:-medium}"
  export COCO_AGENTS_CLAUDE_ALLOWED_TOOLS="${COCO_AGENTS_CLAUDE_ALLOWED_TOOLS:-WebSearch,WebFetch,Task,Read,Write,Edit,MultiEdit}"
else
  NEWS_ROOM_RUNTIME="${NEWS_ROOM_RUNTIME:-codex-exec}"
fi
NEWS_ROOM_MODEL="${NEWS_ROOM_MODEL:-not-pinned-by-publish-daily.sh}"
NEWS_ROOM_EFFORT="${COCO_AGENTS_CLAUDE_EFFORT:-backend-default}"
NEWS_ROOM_ALLOWED_TOOLS="${COCO_AGENTS_CLAUDE_ALLOWED_TOOLS:-backend-default}"

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATE="$(TZ="$NEWS_ROOM_TZ" date +%F)"
WS="$REPO"
ART="$REPO/newsroom/artifacts"
OUT="$REPO/content/$DATE"
DEFAULT_PROMPT_FILE="$REPO/prompts/daily-newsroom-single-$NEWS_ROOM_BACKEND.md"
PROMPT_FILE="${NEWS_ROOM_PROMPT_FILE:-$DEFAULT_PROMPT_FILE}"
SESSION_STARTUP_TIMEOUT_SECS="${NEWS_ROOM_SESSION_STARTUP_TIMEOUT_SECS:-60}"
SESSION_TURN_TIMEOUT_SECS="${NEWS_ROOM_SESSION_TURN_TIMEOUT_SECS:-7200}"
SESSION_RUN_JSON="$ART/session-run.json"
CODEX_LAST_MESSAGE="$ART/session-last-message.txt"
NEWS_ROOM_CODEX_SANDBOX="${NEWS_ROOM_CODEX_SANDBOX:-danger-full-access}"

cd "$REPO"
git pull --rebase --quiet || true

if [[ ! -f "$PROMPT_FILE" ]]; then
  echo "Prompt file not found: $PROMPT_FILE" >&2
  exit 2
fi

PROMPT_DIR="$(cd "$(dirname "$PROMPT_FILE")" && pwd -P)"
PROMPT_BASENAME="$(basename "$PROMPT_FILE")"
PROMPT_REAL="$PROMPT_DIR/$PROMPT_BASENAME"
case "$PROMPT_REAL" in
  "$REPO"/prompts/*.md) ;;
  *)
    echo "Refusing to publish prompt outside repo prompts/: $PROMPT_REAL" >&2
    exit 2
    ;;
esac
PROMPT="$(cat "$PROMPT_FILE")"

# 작업대 초기화
rm -rf "$ART"
mkdir -p "$ART"
echo "$DATE" > "$ART/today.txt"

# 편집국 소집: Claude는 PTY 세션, Codex는 batch-friendly exec 경로를 사용한다.
case "$NEWS_ROOM_BACKEND" in
  claude)
    coco-agents session run \
      --backend claude \
      --runtime "$NEWS_ROOM_RUNTIME" \
      --workspace "$WS" \
      --name "news-room-claude-$DATE" \
      --startup-timeout "$SESSION_STARTUP_TIMEOUT_SECS" \
      --turn-timeout "$SESSION_TURN_TIMEOUT_SECS" \
      --json \
      "$PROMPT" > "$SESSION_RUN_JSON"
    ;;
  codex)
    codex exec \
      --cd "$WS" \
      --sandbox "$NEWS_ROOM_CODEX_SANDBOX" \
      --json \
      --output-last-message "$CODEX_LAST_MESSAGE" \
      - < "$PROMPT_FILE" > "$SESSION_RUN_JSON"
    ;;
esac
SESSION_EXIT=$?
echo "$SESSION_EXIT" > "$ART/session-exit-code.txt"
echo "$NEWS_ROOM_BACKEND" > "$ART/session-backend.txt"

public_value() {
  case "$1" in
    *[!A-Za-z0-9._,=:/+-]*)
      printf 'redacted-unsafe-value'
      ;;
    *)
      printf '%s' "$1"
      ;;
  esac
}

mkdir -p "$OUT"
printf '%s\n' "$PROMPT" > "$OUT/prompt.md"
[[ -s "$ART/article-draft.md" ]] && cp "$ART/article-draft.md" "$OUT/draft.md"
cat > "$OUT/run.md" <<EOF
# 발행 실행 정보 — $DATE

- backend: $(public_value "$NEWS_ROOM_BACKEND")
- runtime: $(public_value "$NEWS_ROOM_RUNTIME")
- model: $(public_value "$NEWS_ROOM_MODEL")
- effort: $(public_value "$NEWS_ROOM_EFFORT")
- allowed_tools: $(public_value "$NEWS_ROOM_ALLOWED_TOOLS")
- prompt_file: prompts/$PROMPT_BASENAME
- session_exit_code: $SESSION_EXIT

model 값이 "not-pinned-by-publish-daily.sh"이면, 이 발행 스크립트가 모델명을 직접 고정하지 않았다는 뜻이다.
실제 모델 선택은 실행 백엔드의 기본 설정이나 상위 환경에 의해 결정될 수 있다.
EOF

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
