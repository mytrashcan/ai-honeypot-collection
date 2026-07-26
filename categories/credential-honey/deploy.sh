#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$script_dir"

if ! command -v docker >/dev/null 2>&1; then
  echo "docker is required" >&2
  exit 1
fi

if ! grep -q '^TRACKING_TOKEN=EXAMPLE-' .env; then
  echo "Refusing to deploy: .env is not the repository's synthetic decoy." >&2
  exit 1
fi

umask 077
docker compose config --quiet
docker compose up --detach --build
docker compose ps
