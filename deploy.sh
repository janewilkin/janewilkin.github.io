#!/usr/bin/env bash
#
# deploy.sh - Deploy janewilkin.github.io to GitHub Pages
#
# Usage:
#   ./deploy.sh                  # Deploy with auto-generated commit message
#   ./deploy.sh "commit message" # Deploy with custom commit message
#
# This script stages all changes, commits, and pushes to the main branch.
# GitHub Pages automatically deploys from the main branch.
#

set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$REPO_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Deploying janewilkin.github.io${NC}"
echo "=================================="

# Check for uncommitted changes
if git diff --quiet && git diff --cached --quiet && [ -z "$(git ls-files --others --exclude-standard)" ]; then
  echo -e "${YELLOW}No changes to deploy.${NC}"
  exit 0
fi

# Show what will be deployed
echo ""
echo "Changes to deploy:"
echo "------------------"
git status --short
echo ""

# Build commit message
if [ $# -gt 0 ]; then
  COMMIT_MSG="$1"
else
  COMMIT_MSG="Update site - $(date '+%Y-%m-%d %H:%M')"
fi

# Stage, commit, and push
git add -A
git commit -m "$COMMIT_MSG"
git push origin main

echo ""
echo -e "${GREEN}Deployed successfully!${NC}"
echo -e "Site will be live at ${GREEN}https://janewilkin.github.io/${NC} in a few moments."
