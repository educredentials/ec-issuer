#!/usr/bin/env bash
# Bump version in pyproject.toml to the next minor version.
# Usage: bump-version.sh

set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

# Current version
CURRENT=$(grep '^version = ' pyproject.toml | sed 's/version = "\(.*\)"/\1/')
read -r MAJOR MINOR PATCH <<< "${CURRENT//\./ }"
NEXT="${MAJOR}.$((MINOR + 1)).0"

echo "Bumping version: ${CURRENT} → ${NEXT}"
sed -i "s/^version = \"${CURRENT}\"/version = \"${NEXT}\"/" pyproject.toml

echo "Running uv lock..."
uv lock

echo "Committing..."
git add pyproject.toml uv.lock
git commit -m "chore: bump version to ${NEXT}"

echo "Pushing..."
git push

echo "Tagging v${NEXT}..."
git tag --sign "v${NEXT}" -m "Version ${NEXT}"

echo "Pushing tags..."
git push --tags

echo "Done: v${NEXT}"
