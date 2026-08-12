#!/usr/bin/env bash
# Commit and fast-forward-push only the files authorized for one edition.
set -euo pipefail

if [[ $# -ne 2 ]]; then
  echo "usage: $0 <current-affairs|ai|eda> <YYYY-MM-DD>" >&2
  exit 2
fi

EDITION="$1"
PUBLICATION_ID="$2"
if [[ ! "$PUBLICATION_ID" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]]; then
  echo "Invalid publication id: $PUBLICATION_ID" >&2
  exit 2
fi

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO"

case "$EDITION" in
  current-affairs)
    ALLOWED_ROOTS=("content/$PUBLICATION_ID")
    REQUIRED_PATHS=("content/$PUBLICATION_ID/article.md")
    COMMIT_MESSAGE="publish: $PUBLICATION_ID"
    ;;
  ai)
    ALLOWED_ROOTS=("content/ai/$PUBLICATION_ID" "decisions/ai/$PUBLICATION_ID")
    REQUIRED_PATHS=(
      "content/ai/$PUBLICATION_ID/article.md"
      "decisions/ai/$PUBLICATION_ID/evidence.json"
      "decisions/ai/$PUBLICATION_ID/release.json"
    )
    COMMIT_MESSAGE="publish(ai): $PUBLICATION_ID"
    ;;
  eda)
    ALLOWED_ROOTS=("content/eda/$PUBLICATION_ID" "decisions/eda/$PUBLICATION_ID")
    REQUIRED_PATHS=(
      "content/eda/$PUBLICATION_ID/article.md"
      "decisions/eda/$PUBLICATION_ID/evidence.json"
      "decisions/eda/$PUBLICATION_ID/release.json"
    )
    COMMIT_MESSAGE="publish(eda): $PUBLICATION_ID"
    ;;
  *)
    echo "Unsupported edition: $EDITION" >&2
    exit 2
    ;;
esac

for path in "${REQUIRED_PATHS[@]}"; do
  if [[ ! -f "$path" ]]; then
    echo "Required publication file is missing: $path" >&2
    exit 2
  fi
done

is_allowed_path() {
  local candidate="$1"
  local root
  for root in "${ALLOWED_ROOTS[@]}"; do
    if [[ "$candidate" == "$root" || "$candidate" == "$root/"* ]]; then
      return 0
    fi
  done
  return 1
}

while IFS= read -r status_line; do
  [[ -z "$status_line" ]] && continue
  changed_path="${status_line:3}"
  if [[ "$changed_path" == *" -> "* ]]; then
    changed_path="${changed_path##* -> }"
  fi
  if ! is_allowed_path "$changed_path"; then
    echo "Refusing to finalize unrelated change: $changed_path" >&2
    exit 2
  fi
done < <(git status --porcelain=v1 --untracked-files=all)

git add -- "${ALLOWED_ROOTS[@]}"
if git diff --cached --quiet; then
  echo "No publication changes to finalize for $EDITION $PUBLICATION_ID" >&2
  exit 2
fi

while IFS= read -r staged_path; do
  if ! is_allowed_path "$staged_path"; then
    echo "Refusing staged path outside publication scope: $staged_path" >&2
    exit 2
  fi
done < <(git diff --cached --name-only)

if [[ "$EDITION" == ai || "$EDITION" == eda ]]; then
  ACTUAL_TECHNICAL_PATHS="$(git diff --cached --name-only | LC_ALL=C sort)"
  EXPECTED_TECHNICAL_PATHS="$(printf '%s\n' "${REQUIRED_PATHS[@]}" | LC_ALL=C sort)"
  if [[ "$ACTUAL_TECHNICAL_PATHS" != "$EXPECTED_TECHNICAL_PATHS" ]]; then
    echo "Technical publication must stage exactly its article, evidence, and release files" >&2
    printf 'expected:\n%s\nactual:\n%s\n' "$EXPECTED_TECHNICAL_PATHS" "$ACTUAL_TECHNICAL_PATHS" >&2
    exit 2
  fi
fi

git diff --cached --check
git commit --quiet -m "$COMMIT_MESSAGE"

COMMIT_SHA="$(git rev-parse HEAD)"
PARENT_SHA="$(git rev-parse HEAD^)"
git fetch --quiet origin main
REMOTE_SHA="$(git rev-parse origin/main)"
if [[ "$PARENT_SHA" != "$REMOTE_SHA" ]]; then
  echo "origin/main changed during publication; refusing non-fast-forward push" >&2
  echo "parent=$PARENT_SHA origin/main=$REMOTE_SHA commit=$COMMIT_SHA" >&2
  exit 3
fi

git push --quiet origin HEAD:main
git fetch --quiet origin main
if [[ "$(git rev-parse origin/main)" != "$COMMIT_SHA" ]]; then
  echo "Remote verification failed after publication push" >&2
  exit 3
fi
if [[ -n "$(git status --porcelain=v1 --untracked-files=all)" ]]; then
  echo "Publication checkout is dirty after finalization" >&2
  git status --short >&2
  exit 3
fi

printf '%s\n' "$COMMIT_SHA"
