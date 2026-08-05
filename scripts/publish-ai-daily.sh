#!/usr/bin/env bash
# Generate, validate, materialize, and publish at most one AI edition article.
set -euo pipefail

export PATH="$HOME/.cargo/bin:$HOME/.local/bin:$PATH"
NEWS_ROOM_TZ="${NEWS_ROOM_TZ:-Asia/Seoul}"
PUBLICATION_ID="${NEWS_ROOM_PUBLICATION_ID:-$(TZ="$NEWS_ROOM_TZ" date +%F)}"
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUN_ROOT="$REPO/var/runs/ai/$PUBLICATION_ID-sequential"
PUBLICATION_RUN_DIR="${NEWS_ROOM_PUBLICATION_RUN_DIR:-$REPO/var/runs/publications/$PUBLICATION_ID}"
DECISION_FILE="$PUBLICATION_RUN_DIR/ai-decision.json"
ATTEMPT_ID="$(date -u +%Y%m%dT%H%M%SZ)-$$"
RUN_DIR="$RUN_ROOT/$ATTEMPT_ID"
STAGED_DIR="$RUN_DIR/staged-content"
REQUEST="$RUN_DIR/request.json"
NO_PUBLISH="$RUN_DIR/no-publish.json"
ARTICLE="$STAGED_DIR/article.md"
EVIDENCE="$RUN_DIR/evidence.json"
PROMPT_FILE="$REPO/prompts/daily-ai-codex.md"
REPAIR_PROMPT_FILE="$REPO/prompts/repair-ai-candidate.md"
SESSION_RUN_JSON="$RUN_DIR/session-run.jsonl"
LAST_MESSAGE="$RUN_DIR/session-last-message.txt"
NEWS_ROOM_CODEX_SANDBOX="${NEWS_ROOM_CODEX_SANDBOX:-danger-full-access}"
MAX_VALIDATION_ATTEMPTS="${NEWS_ROOM_AI_MAX_VALIDATION_ATTEMPTS:-2}"

cd "$REPO"
"$REPO/scripts/publication-git-preflight.sh" >/dev/null

if ! git cat-file -e "HEAD:content/$PUBLICATION_ID/article.md" 2>/dev/null; then
  echo "AI publication requires the current-affairs publication for $PUBLICATION_ID" >&2
  exit 2
fi
"$REPO/scripts/verify-publication.sh" current-affairs "$PUBLICATION_ID" >/dev/null

if [[ -f "$DECISION_FILE" ]] && python3 - "$DECISION_FILE" "$PUBLICATION_ID" <<'PY'
import json, sys
value = json.load(open(sys.argv[1], encoding="utf-8"))
raise SystemExit(0 if value.get("publication_id") == sys.argv[2] and value.get("decision") == "no-publish" else 1)
PY
then
  echo "AI no-publish decision already exists for $PUBLICATION_ID"
  exit 0
fi

if git cat-file -e "HEAD:content/ai/$PUBLICATION_ID/article.md" 2>/dev/null; then
  echo "AI publication already exists for $PUBLICATION_ID"
  exit 0
fi
if [[ ! -f "$PROMPT_FILE" || ! -f "$REPAIR_PROMPT_FILE" ]]; then
  echo "AI publication or repair prompt is missing" >&2
  exit 2
fi
if [[ ! "$MAX_VALIDATION_ATTEMPTS" =~ ^[12]$ ]]; then
  echo "NEWS_ROOM_AI_MAX_VALIDATION_ATTEMPTS must be 1 or 2" >&2
  exit 2
fi

mkdir -p "$STAGED_DIR"
mkdir -p "$PUBLICATION_RUN_DIR"
cat > "$REQUEST" <<EOF
{
  "schema_version": 1,
  "publication_id": "$PUBLICATION_ID",
  "article_path": "${ARTICLE#$REPO/}",
  "evidence_path": "${EVIDENCE#$REPO/}",
  "no_publish_path": "${NO_PUBLISH#$REPO/}"
}
EOF

set +e
{
  cat "$PROMPT_FILE"
  printf '\n## 이번 실행 요청\n\n`%s`를 읽고 그 경로와 발행일을 정확히 사용하라.\n' "${REQUEST#$REPO/}"
} | codex exec \
  --cd "$REPO" \
  --sandbox "$NEWS_ROOM_CODEX_SANDBOX" \
  --json \
  --output-last-message "$LAST_MESSAGE" \
  - > "$SESSION_RUN_JSON"
SESSION_EXIT=$?
set -e
printf '%s\n' "$SESSION_EXIT" > "$RUN_DIR/session-exit-code.txt"
if [[ $SESSION_EXIT -ne 0 ]]; then
  echo "AI editorial turn failed with exit code $SESSION_EXIT" >&2
  exit "$SESSION_EXIT"
fi

if [[ -f "$NO_PUBLISH" ]]; then
  if [[ -f "$ARTICLE" || -f "$EVIDENCE" ]]; then
    echo "AI turn produced both no-publish and publication artifacts" >&2
    exit 2
  fi
  python3 - "$NO_PUBLISH" "$PUBLICATION_ID" <<'PY'
import json, sys
path, publication_id = sys.argv[1:]
value = json.load(open(path, encoding="utf-8"))
if value.get("decision") != "no-publish" or value.get("publication_id") != publication_id:
    raise SystemExit("invalid no-publish decision")
if not isinstance(value.get("reason"), str) or not value["reason"].strip():
    raise SystemExit("no-publish reason is required")
PY
  if [[ -n "$(git status --porcelain=v1 --untracked-files=all)" ]]; then
    echo "AI no-publish turn modified tracked publication files" >&2
    git status --short >&2
    exit 2
  fi
  cp "$NO_PUBLISH" "$DECISION_FILE.tmp"
  mv "$DECISION_FILE.tmp" "$DECISION_FILE"
  echo "AI edition: no-publish for $PUBLICATION_ID"
  exit 0
fi

if [[ ! -f "$ARTICLE" || ! -f "$EVIDENCE" ]]; then
  echo "AI turn produced neither a complete candidate nor no-publish decision" >&2
  exit 2
fi

run_candidate_validation() {
  local attempt="$1"
  local log="$RUN_DIR/validation-$attempt.log"
  : > "$log"
  if ! python3 editions/ai/editorial/style_v2.py "$ARTICLE" >> "$log" 2>&1; then
    cat "$log" >&2
    return 1
  fi
  if ! python3 scripts/publish-ai-candidate.py \
    --article "$ARTICLE" \
    --evidence "$EVIDENCE" \
    --publication-id "$PUBLICATION_ID" \
    --check-only >> "$log" 2>&1
  then
    cat "$log" >&2
    return 1
  fi
  cat "$log"
}

repair_candidate() {
  local failed_attempt="$1"
  local validation_log="$RUN_DIR/validation-$failed_attempt.log"
  local repair_run="$RUN_DIR/repair-$failed_attempt-session-run.jsonl"
  local repair_last="$RUN_DIR/repair-$failed_attempt-last-message.txt"
  local repair_exit

  set +e
  {
    cat "$REPAIR_PROMPT_FILE"
    printf '\n## 이번 복구 요청\n\n`%s`의 기존 후보를 최소 수정하라. 아래 결정적 검증 오류만 고친다.\n\n```text\n' "${REQUEST#$REPO/}"
    cat "$validation_log"
    printf '\n```\n'
  } | codex exec \
    --cd "$REPO" \
    --sandbox "$NEWS_ROOM_CODEX_SANDBOX" \
    --json \
    --output-last-message "$repair_last" \
    - > "$repair_run"
  repair_exit=$?
  set -e
  printf '%s\n' "$repair_exit" > "$RUN_DIR/repair-$failed_attempt-exit-code.txt"
  if [[ $repair_exit -ne 0 ]]; then
    echo "AI candidate repair turn failed with exit code $repair_exit" >&2
    return "$repair_exit"
  fi
}

VALIDATION_ATTEMPT=1
while ! run_candidate_validation "$VALIDATION_ATTEMPT"; do
  if (( VALIDATION_ATTEMPT >= MAX_VALIDATION_ATTEMPTS )); then
    echo "AI candidate remained invalid after $VALIDATION_ATTEMPT validation attempt(s)" >&2
    exit 2
  fi
  repair_candidate "$VALIDATION_ATTEMPT"
  VALIDATION_ATTEMPT=$((VALIDATION_ATTEMPT + 1))
done

if [[ -n "$(git status --porcelain=v1 --untracked-files=all)" ]]; then
  echo "AI candidate turn modified files outside the ignored run directory" >&2
  git status --short >&2
  exit 2
fi

PYTHONDONTWRITEBYTECODE=1 python3 editions/validate_editions.py
PYTHONDONTWRITEBYTECODE=1 python3 editions/validate_source_registries.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover editions
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover scripts

python3 scripts/publish-ai-candidate.py \
  --article "$ARTICLE" \
  --evidence "$EVIDENCE" \
  --publication-id "$PUBLICATION_ID" \
  --executor "news-room-sequential-publisher"

npm --prefix site test
npm --prefix site run build
"$REPO/scripts/finalize-publication.sh" ai "$PUBLICATION_ID"
"$REPO/scripts/verify-publication.sh" ai "$PUBLICATION_ID"
