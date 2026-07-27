#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel)"
SITE_DIR="$SCRIPT_DIR/site"
BUILD_DIR="$(mktemp -d "${TMPDIR:-/tmp}/nexusflow-build.XXXXXX")"
PUBLISH_DIR="$(mktemp -d "${TMPDIR:-/tmp}/nexusflow-pages.XXXXXX")"
WORKTREE_ADDED=false

cleanup() {
  if [[ "$WORKTREE_ADDED" == true ]]; then
    git -C "$REPO_ROOT" worktree remove --force "$PUBLISH_DIR" >/dev/null 2>&1 || true
  fi
  rm -rf -- "$BUILD_DIR" "$PUBLISH_DIR"
}
trap cleanup EXIT

required_files=(
  index.html
  about.html
  products.html
  pricing.html
  contact.html
  robots.txt
  sitemap.xml
  .env
  assets/css/style.css
  assets/js/app.js
)

for relative_path in "${required_files[@]}"; do
  if [[ ! -f "$SITE_DIR/$relative_path" ]]; then
    echo "Missing required site file: $relative_path" >&2
    exit 1
  fi
done

cp -R "$SITE_DIR"/. "$BUILD_DIR"/
touch "$BUILD_DIR/.nojekyll"

if git -C "$REPO_ROOT" ls-remote --exit-code --heads origin gh-pages >/dev/null 2>&1; then
  git -C "$REPO_ROOT" fetch origin gh-pages
  git -C "$REPO_ROOT" worktree add --detach "$PUBLISH_DIR" origin/gh-pages
else
  git -C "$REPO_ROOT" worktree add --detach "$PUBLISH_DIR" HEAD
  git -C "$PUBLISH_DIR" switch --orphan "gh-pages-build-$$"
fi
WORKTREE_ADDED=true

find "$PUBLISH_DIR" -mindepth 1 -maxdepth 1 ! -name .git -exec rm -rf -- {} +
cp -R "$BUILD_DIR"/. "$PUBLISH_DIR"/

git -C "$PUBLISH_DIR" add --all
if git -C "$PUBLISH_DIR" diff --cached --quiet; then
  echo "GitHub Pages is already up to date."
  exit 0
fi

git -C "$PUBLISH_DIR" commit -m "deploy: publish NexusFlow site"
git -C "$PUBLISH_DIR" push origin HEAD:gh-pages

echo "Published NexusFlow to the gh-pages branch."
