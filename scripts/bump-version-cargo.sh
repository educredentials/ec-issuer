#!/usr/bin/env bash
# Bump version in Cargo.toml to the next minor version.
# Usage: bump-version-cargo.sh
#
# Uses sed to edit Cargo.toml directly (no cargo-edit dependency).

set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

# Cross-platform sed -i (GNU vs BSD/macOS)
sed_i="-i"
[[ "$(uname -s)" == Darwin ]] && sed_i="-i ''"

# Current version
CURRENT=$(grep '^version = ' rust/Cargo.toml | sed 's/version = "\(.*\)"/\1/')
read -r MAJOR MINOR PATCH <<< "${CURRENT//\./ }"
NEXT="${MAJOR}.$((MINOR + 1)).0"

echo "Bumping version: ${CURRENT} → ${NEXT}"
sed ${sed_i} "s/^version = \"${CURRENT}\"/version = \"${NEXT}\"/" rust/Cargo.toml

echo "Building to update Cargo.lock..."
cd rust && cargo build --quiet 2>&1 || true

echo "Committing..."
git add rust/Cargo.toml rust/Cargo.lock
git commit -m "chore: bump version to ${NEXT}"

echo "Pushing..."
git push

echo "Tagging v${NEXT}..."
TAG_MSG="Version ${NEXT}"
if COMMITS=$(git log "v${CURRENT}"..HEAD --format='  %s'); then
  TAG_MSG+=$'\n'"Commits since v${CURRENT}:${COMMITS}"
fi
git tag "v${NEXT}" -m "${TAG_MSG}"

echo "Pushing tags..."
git push --tags

echo "Done: v${NEXT}"
