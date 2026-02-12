#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="/Users/ellisbot/.openclaw/workspace"
cd "$REPO_DIR"

# Ensure auth for git-over-https is wired through gh
if ! gh auth status >/dev/null 2>&1; then
  echo "ERROR: gh auth is not valid" >&2
  exit 1
fi

gh auth setup-git >/dev/null 2>&1 || true

# Commit if needed
if git diff --quiet && git diff --cached --quiet; then
  echo "No changes to commit"
  exit 0
fi

git add -A
if git diff --cached --quiet; then
  echo "No staged changes"
  exit 0
fi

git commit -m "daily backup $(date +%Y-%m-%d_%H%M%S)" >/dev/null 2>&1 || true

# Push with retry
if git push origin main; then
  echo "Push succeeded"
  exit 0
fi

echo "First push attempt failed. Re-applying gh auth and retrying..." >&2
gh auth setup-git >/dev/null 2>&1 || true
sleep 2
git push origin main

echo "Push succeeded on retry"
