#!/usr/bin/env bash
# Run one evidence-preserving Korean copy edit before deterministic validation.
set -euo pipefail

if [[ $# -ne 6 ]]; then
  echo "usage: $0 <ai|eda> <request> <article> <evidence> <run-dir> <sandbox>" >&2
  exit 2
fi
EDITION="$1"
REQUEST="$2"
ARTICLE="$3"
EVIDENCE="$4"
RUN_DIR="$5"
CODEX_SANDBOX="$6"
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROMPT="$REPO/prompts/copyedit-technical-korean.md"
BEFORE_ARTICLE="$RUN_DIR/pre-copyedit-article.md"
BEFORE_EVIDENCE="$RUN_DIR/pre-copyedit-evidence.json"
SESSION_RUN="$RUN_DIR/copyedit-session-run.jsonl"
LAST_MESSAGE="$RUN_DIR/copyedit-last-message.txt"

case "$EDITION" in
  ai|eda) ;;
  *) echo "copy edit edition must be ai or eda" >&2; exit 2 ;;
esac
for path in "$PROMPT" "$REQUEST" "$ARTICLE" "$EVIDENCE"; do
  if [[ ! -f "$path" ]]; then
    echo "copy edit input is missing: $path" >&2
    exit 2
  fi
done

cp "$ARTICLE" "$BEFORE_ARTICLE"
cp "$EVIDENCE" "$BEFORE_EVIDENCE"

set +e
{
  cat "$PROMPT"
  printf '\n## 이번 편집 요청\n\nedition은 `%s`다. `%s`를 읽고 지정된 기사만 편집하라.\n' \
    "$EDITION" "${REQUEST#$REPO/}"
} | codex exec \
  --cd "$REPO" \
  --sandbox "$CODEX_SANDBOX" \
  --json \
  --output-last-message "$LAST_MESSAGE" \
  - > "$SESSION_RUN"
COPYEDIT_EXIT=$?
set -e
printf '%s\n' "$COPYEDIT_EXIT" > "$RUN_DIR/copyedit-exit-code.txt"

if [[ $COPYEDIT_EXIT -ne 0 ]]; then
  cp "$BEFORE_ARTICLE" "$ARTICLE"
  cp "$BEFORE_EVIDENCE" "$EVIDENCE"
  echo "technical Korean copy edit failed with exit code $COPYEDIT_EXIT" >&2
  exit "$COPYEDIT_EXIT"
fi

if ! cmp -s "$BEFORE_EVIDENCE" "$EVIDENCE"; then
  cp "$BEFORE_ARTICLE" "$ARTICLE"
  cp "$BEFORE_EVIDENCE" "$EVIDENCE"
  echo "technical Korean copy edit changed evidence; restored original candidate" >&2
  exit 2
fi

if ! python3 "$REPO/scripts/validate-technical-copyedit.py" \
  "$BEFORE_ARTICLE" "$ARTICLE" > "$RUN_DIR/copyedit-invariants.json"
then
  cp "$BEFORE_ARTICLE" "$ARTICLE"
  cp "$BEFORE_EVIDENCE" "$EVIDENCE"
  cat "$RUN_DIR/copyedit-invariants.json" >&2
  echo "technical Korean copy edit changed protected facts; restored original candidate" >&2
  exit 2
fi
