#!/usr/bin/env bash
# Wait for GitHub Pages and verify the live route for one publication.
set -euo pipefail

if [[ $# -ne 2 ]]; then
  echo "usage: $0 <current-affairs|ai|eda> <YYYY-MM-DD>" >&2
  exit 2
fi

EDITION="$1"
PUBLICATION_ID="$2"
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PUBLIC_BASE="${NEWS_ROOM_PUBLIC_BASE:-https://ai-newsroom.github.io/news-room}"
ATTEMPTS="${NEWS_ROOM_VERIFY_ATTEMPTS:-60}"
INTERVAL="${NEWS_ROOM_VERIFY_INTERVAL_SECS:-10}"

case "$EDITION" in
  current-affairs)
    ARTICLE="$REPO/content/$PUBLICATION_ID/article.md"
    URL="$PUBLIC_BASE/news/$PUBLICATION_ID/"
    ;;
  ai)
    ARTICLE="$REPO/content/ai/$PUBLICATION_ID/article.md"
    URL="$PUBLIC_BASE/ai/$PUBLICATION_ID/"
    ;;
  eda)
    ARTICLE="$REPO/content/eda/$PUBLICATION_ID/article.md"
    URL="$PUBLIC_BASE/eda/$PUBLICATION_ID/"
    ;;
  *)
    echo "Unsupported edition: $EDITION" >&2
    exit 2
    ;;
esac

if [[ ! -f "$ARTICLE" ]]; then
  echo "Cannot verify missing article: $ARTICLE" >&2
  exit 2
fi
TITLE="$(sed -n 's/^title: *"\(.*\)"$/\1/p' "$ARTICLE" | head -1)"
if [[ -z "$TITLE" ]]; then
  echo "Cannot read article title from $ARTICLE" >&2
  exit 2
fi

BODY="$(mktemp)"
trap 'rm -f "$BODY"' EXIT
for ((attempt = 1; attempt <= ATTEMPTS; attempt++)); do
  HTTP_CODE="$(curl -sS -L -o "$BODY" -w '%{http_code}' "$URL" || true)"
  if [[ "$HTTP_CODE" == 200 ]] && grep -Fq "$TITLE" "$BODY"; then
    VERIFIED=false
    if [[ "$EDITION" == current-affairs ]]; then
      VERIFIED=true
    elif grep -Fq "발행 ID $PUBLICATION_ID" "$BODY"; then
      if [[ "$EDITION" == ai ]] && grep -Fq "자동 출고 검증 완료" "$BODY"; then
        VERIFIED=true
      elif [[ "$EDITION" == eda ]] && {
        grep -Fq "사람 공개 승인 완료" "$BODY" ||
        grep -Fq "자동 출고 검증 완료" "$BODY"
      }; then
        VERIFIED=true
      fi
    fi
    if [[ "$VERIFIED" == true ]]; then
      printf '%s\n' "$URL"
      exit 0
    fi
  fi
  if (( attempt < ATTEMPTS )); then
    sleep "$INTERVAL"
  fi
done

echo "Live publication verification failed: $URL" >&2
exit 4
