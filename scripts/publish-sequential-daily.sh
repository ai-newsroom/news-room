#!/usr/bin/env bash
# Own one daily publication sequence: current affairs, then AI, then live proof.
set -euo pipefail

export PATH="$HOME/.cargo/bin:$HOME/.local/bin:$PATH"
NEWS_ROOM_TZ="${NEWS_ROOM_TZ:-Asia/Seoul}"
PUBLICATION_ID="${NEWS_ROOM_PUBLICATION_ID:-$(TZ="$NEWS_ROOM_TZ" date +%F)}"
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUN_DIR="$REPO/var/runs/publications/$PUBLICATION_ID"
STATE_FILE="$RUN_DIR/run.json"
LOCK_FILE="${XDG_RUNTIME_DIR:-/tmp}/news-room-publications.lock"
PHASE="starting"

mkdir -p "$RUN_DIR"

write_state() {
  local phase="$1"
  local status="$2"
  local detail="${3:-}"
  python3 - "$STATE_FILE" "$PUBLICATION_ID" "$phase" "$status" "$detail" <<'PY'
import datetime as dt
import json
import os
import sys

path, publication_id, phase, status, detail = sys.argv[1:]
try:
    with open(path, encoding="utf-8") as source:
        value = json.load(source)
except FileNotFoundError:
    value = {"schema_version": 1, "publication_id": publication_id, "events": []}
value["phase"] = phase
value["status"] = status
value["updated_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
value["events"].append({
    "phase": phase,
    "status": status,
    "detail": detail or None,
    "timestamp": value["updated_at"],
})
temporary = path + ".tmp"
with open(temporary, "w", encoding="utf-8") as target:
    json.dump(value, target, ensure_ascii=False, indent=2)
    target.write("\n")
os.replace(temporary, path)
PY
}

on_error() {
  local exit_code=$?
  trap - ERR
  write_state "$PHASE" failed "exit_code=$exit_code"
  exit "$exit_code"
}
trap on_error ERR

exec 9>"$LOCK_FILE"
if ! flock -n 9; then
  echo "Another daily publication run already owns $LOCK_FILE" >&2
  exit 5
fi

cd "$REPO"
write_state starting running

PHASE="preflight"
"$REPO/scripts/publication-git-preflight.sh" >/dev/null
write_state "$PHASE" succeeded

PHASE="current-affairs"
"$REPO/scripts/publish-daily.sh"
write_state "$PHASE" succeeded

PHASE="verify-current-affairs"
CURRENT_URL="$("$REPO/scripts/verify-publication.sh" current-affairs "$PUBLICATION_ID")"
write_state "$PHASE" succeeded "$CURRENT_URL"

PHASE="ai"
NEWS_ROOM_PUBLICATION_RUN_DIR="$RUN_DIR" "$REPO/scripts/publish-ai-daily.sh"
if [[ -f "$RUN_DIR/ai-decision.json" ]]; then
  write_state "$PHASE" succeeded "no-publish"
else
  write_state "$PHASE" succeeded
fi

if git cat-file -e "HEAD:content/ai/$PUBLICATION_ID/article.md" 2>/dev/null; then
  PHASE="verify-ai"
  AI_URL="$("$REPO/scripts/verify-publication.sh" ai "$PUBLICATION_ID")"
  write_state "$PHASE" succeeded "$AI_URL"
fi

PHASE="complete"
write_state "$PHASE" succeeded
printf 'Daily publication sequence completed for %s\n' "$PUBLICATION_ID"
