#!/usr/bin/env bash
# Synchronize the dedicated publication checkout before any model work starts.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO"

if [[ -n "$(git status --porcelain=v1 --untracked-files=all)" ]]; then
  echo "Refusing publication from a dirty checkout: $REPO" >&2
  git status --short >&2
  exit 2
fi

git fetch --quiet origin main
git merge --ff-only --quiet origin/main

HEAD_SHA="$(git rev-parse HEAD)"
REMOTE_SHA="$(git rev-parse origin/main)"
if [[ "$HEAD_SHA" != "$REMOTE_SHA" ]]; then
  echo "Publication checkout is not synchronized with origin/main" >&2
  echo "HEAD=$HEAD_SHA origin/main=$REMOTE_SHA" >&2
  exit 2
fi

if [[ -n "$(git status --porcelain=v1 --untracked-files=all)" ]]; then
  echo "Publication checkout became dirty during preflight" >&2
  exit 2
fi

printf '%s\n' "$HEAD_SHA"
