#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 2 || ! $1 =~ ^[0-9a-f]{40}$ || ! $2 =~ ^https?:// ]]; then
  echo "Usage: scripts/deploy_staging.sh <40-character release SHA> <staging URL>" >&2
  exit 2
fi
if [[ ! -f .env.staging ]]; then
  echo "Create .env.staging from .env.staging.example before deploying." >&2
  exit 2
fi

export IMAGE_TAG="$1"
staging_url="${2%/}"
compose=(docker compose --env-file .env.staging -f compose.staging.yml)

"${compose[@]}" config --quiet
"${compose[@]}" pull
"${compose[@]}" up -d --wait --wait-timeout 180
curl --fail --silent --show-error --retry 8 --retry-delay 5 --retry-all-errors \
  "${staging_url}/health"
curl --fail --silent --show-error --retry 8 --retry-delay 5 --retry-all-errors \
  "${staging_url}/api/v1/events" > /dev/null
curl --fail --silent --show-error --retry 8 --retry-delay 5 --retry-all-errors \
  "${staging_url}/api/v1/risk-profile/clusters" > /dev/null
