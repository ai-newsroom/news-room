#!/usr/bin/env bash
# Publish one editor-requested AI special without consuming the regular daily slot.
set -euo pipefail

export PATH="$HOME/.cargo/bin:$HOME/.local/bin:$PATH"
if [[ $# -ne 4 ]]; then
  echo "usage: $0 <slug> <brief-file> <approved-by> <approval-basis>" >&2
  exit 2
fi

SLUG="$1"
BRIEF_INPUT="$2"
APPROVED_BY="$3"
APPROVAL_BASIS="$4"
if [[ ! "$SLUG" =~ ^[a-z0-9]+(-[a-z0-9]+)*$ ]]; then
  echo "Special slug must contain lowercase letters, digits, and single hyphens" >&2
  exit 2
fi
if [[ -z "$APPROVED_BY" || -z "$APPROVAL_BASIS" ]]; then
  echo "Special publication requires explicit approval metadata" >&2
  exit 2
fi

NEWS_ROOM_TZ="${NEWS_ROOM_TZ:-Asia/Seoul}"
PUBLICATION_DATE="${NEWS_ROOM_PUBLICATION_DATE:-$(TZ="$NEWS_ROOM_TZ" date +%F)}"
PUBLICATION_ID="$PUBLICATION_DATE--$SLUG"
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROMPT_FILE="$REPO/prompts/special-ai-codex.md"
REPAIR_PROMPT_FILE="$REPO/prompts/repair-ai-candidate.md"
RUN_ROOT="$REPO/var/runs/ai/special/$PUBLICATION_ID"
ATTEMPT_ID="$(date -u +%Y%m%dT%H%M%SZ)-$$"
RUN_DIR="$RUN_ROOT/$ATTEMPT_ID"
STAGED_DIR="$RUN_DIR/staged-content"
REQUEST="$RUN_DIR/request.json"
NO_PUBLISH="$RUN_DIR/no-publish.json"
ARTICLE="$STAGED_DIR/article.md"
EVIDENCE="$RUN_DIR/evidence.json"
SESSION_RUN_JSON="$RUN_DIR/session-run.jsonl"
LAST_MESSAGE="$RUN_DIR/session-last-message.txt"
NEWS_ROOM_CODEX_SANDBOX="${NEWS_ROOM_CODEX_SANDBOX:-danger-full-access}"
MAX_VALIDATION_ATTEMPTS="${NEWS_ROOM_AI_MAX_VALIDATION_ATTEMPTS:-2}"

cd "$REPO"
"$REPO/scripts/publication-git-preflight.sh" >/dev/null

BRIEF_FILE="$(python3 - "$REPO" "$BRIEF_INPUT" <<'PY'
import pathlib, sys
root = pathlib.Path(sys.argv[1]).resolve()
brief = pathlib.Path(sys.argv[2])
if not brief.is_absolute():
    brief = root / brief
brief = brief.resolve()
allowed = (root / "prompts/ai-special-briefs").resolve()
try:
    brief.relative_to(allowed)
except ValueError:
    raise SystemExit("special brief must be below prompts/ai-special-briefs")
if brief.is_symlink() or not brief.is_file():
    raise SystemExit("special brief must be a regular file")
print(brief)
PY
)"

if git cat-file -e "HEAD:content/ai/$PUBLICATION_ID/article.md" 2>/dev/null; then
  echo "AI special publication already exists for $PUBLICATION_ID" >&2
  exit 2
fi
if [[ ! -f "$PROMPT_FILE" || ! -f "$REPAIR_PROMPT_FILE" ]]; then
  echo "AI special publication or repair prompt is missing" >&2
  exit 2
fi
if [[ ! "$MAX_VALIDATION_ATTEMPTS" =~ ^[12]$ ]]; then
  echo "NEWS_ROOM_AI_MAX_VALIDATION_ATTEMPTS must be 1 or 2" >&2
  exit 2
fi

mkdir -p "$STAGED_DIR"
python3 - "$REQUEST" "$PUBLICATION_ID" "$PUBLICATION_DATE" "$ARTICLE" "$EVIDENCE" "$NO_PUBLISH" "$REPO" <<'PY'
import json, pathlib, sys
path, publication_id, publication_date, article, evidence, no_publish, repo = sys.argv[1:]
root = pathlib.Path(repo)
relative = lambda value: str(pathlib.Path(value).relative_to(root))
value = {
    "schema_version": 1,
    "publication_id": publication_id,
    "publication_date": publication_date,
    "publication_kind": "special",
    "article_path": relative(article),
    "evidence_path": relative(evidence),
    "no_publish_path": relative(no_publish),
}
pathlib.Path(path).write_text(
    json.dumps(value, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)
PY

set +e
{
  cat "$PROMPT_FILE"
  printf '\n## 이번 실행 요청\n\n`%s`를 먼저 읽고 경로, 발행일, 특별판 식별자를 정확히 사용하라.\n' "${REQUEST#$REPO/}"
  printf '\n## 편집자 지정 브리프\n\n'
  cat "$BRIEF_FILE"
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
  echo "AI special editorial turn failed with exit code $SESSION_EXIT" >&2
  exit "$SESSION_EXIT"
fi

if [[ -f "$NO_PUBLISH" ]]; then
  if [[ -f "$ARTICLE" || -f "$EVIDENCE" ]]; then
    echo "AI special turn produced both no-publish and publication artifacts" >&2
    exit 2
  fi
  python3 - "$NO_PUBLISH" "$PUBLICATION_ID" <<'PY'
import json, sys
value = json.load(open(sys.argv[1], encoding="utf-8"))
if value.get("decision") != "no-publish" or value.get("publication_id") != sys.argv[2]:
    raise SystemExit("invalid special no-publish decision")
  if value.get("publication_kind") != "special":
    raise SystemExit("invalid special no-publish kind")
if not isinstance(value.get("reason"), str) or not value["reason"].strip():
    raise SystemExit("no-publish reason is required")
PY
  if [[ -n "$(git status --porcelain=v1 --untracked-files=all)" ]]; then
    echo "AI special no-publish turn modified tracked publication files" >&2
    git status --short >&2
    exit 2
  fi
  echo "AI special edition: no-publish for $PUBLICATION_ID"
  exit 0
fi
if [[ ! -f "$ARTICLE" || ! -f "$EVIDENCE" ]]; then
  echo "AI special turn produced neither a complete candidate nor no-publish" >&2
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
    --publication-kind special \
    --approved-by "$APPROVED_BY" \
    --approval-basis "$APPROVAL_BASIS" \
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
    echo "AI special candidate repair failed with exit code $repair_exit" >&2
    return "$repair_exit"
  fi
}

VALIDATION_ATTEMPT=1
while ! run_candidate_validation "$VALIDATION_ATTEMPT"; do
  if (( VALIDATION_ATTEMPT >= MAX_VALIDATION_ATTEMPTS )); then
    echo "AI special candidate remained invalid after $VALIDATION_ATTEMPT attempt(s)" >&2
    exit 2
  fi
  repair_candidate "$VALIDATION_ATTEMPT"
  VALIDATION_ATTEMPT=$((VALIDATION_ATTEMPT + 1))
done

if [[ -n "$(git status --porcelain=v1 --untracked-files=all)" ]]; then
  echo "AI special turn modified files outside the ignored run directory" >&2
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
  --publication-kind special \
  --approved-by "$APPROVED_BY" \
  --approval-basis "$APPROVAL_BASIS" \
  --executor "news-room-special-publisher"

npm --prefix site test
npm --prefix site run build
"$REPO/scripts/finalize-publication.sh" ai "$PUBLICATION_ID"
LIVE_URL="$("$REPO/scripts/verify-publication.sh" ai "$PUBLICATION_ID")"
printf '%s\n' "$LIVE_URL"

RETROSPECTIVE_WORKSPACE="${NEWS_ROOM_RETROSPECTIVE_WORKSPACE:-/home/pys/repositories/news-room}"
CONDUCTOR_STATE="$RETROSPECTIVE_WORKSPACE/.coco-agents/conductor-loop.json"
COCO_AGENTS="$(command -v coco-agents || true)"
if [[ -n "$COCO_AGENTS" && -d "$RETROSPECTIVE_WORKSPACE" && -f "$CONDUCTOR_STATE" ]]; then
  CONDUCTOR_SESSION="$(python3 - "$CONDUCTOR_STATE" <<'PY' || true
import json, sys
value = json.load(open(sys.argv[1], encoding="utf-8"))
session_id = value.get("conductor_session_id")
if not isinstance(session_id, str) or not session_id:
    raise SystemExit("conductor session id is missing")
print(session_id)
PY
)"
  if [[ -z "$CONDUCTOR_SESSION" ]]; then
    echo "Special article is live; conductor session metadata is invalid" >&2
  else
    RETROSPECTIVE_PROMPT="Fetch origin main, then read the complete retrospective contract with git show origin/main:prompts/post-publish-retrospective.md and execute that origin/main contract for publication $PUBLICATION_ID. Preserve the dirty local working tree and read tracked inputs with git show origin/main. Use this completed deterministic publisher proof instead of making another network request: $LIVE_URL returned HTTP 200 and contained the expected title, publication id $PUBLICATION_ID, and human-approval label. This is read-only: create at most one evidence-based proposal and do not approve, dispatch, edit, commit, push, publish, deploy, change routines, or request network approval."
    if ! "$COCO_AGENTS" session run \
      --session "$CONDUCTOR_SESSION" \
      --workspace "$RETROSPECTIVE_WORKSPACE" \
      --turn-timeout 1800 \
      --poll-interval-ms 1000 \
      --json \
      "$RETROSPECTIVE_PROMPT" > "$RUN_DIR/retrospective-run.json"
    then
      echo "Special article is live, but its retrospective turn did not complete" >&2
    fi
  fi
else
  echo "Special article is live; its retrospective turn must be started separately" >&2
fi
