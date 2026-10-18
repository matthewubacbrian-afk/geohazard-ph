#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 || $# -gt 3 || ! $1 =~ ^[0-9a-f]{40}$ || ! $2 =~ ^https?:// ]] \
  || [[ $# -eq 3 && $3 != --with-profile ]]; then
  echo "Usage: scripts/deploy_staging.sh <40-character release SHA> <staging URL> [--with-profile]" >&2
  exit 2
fi
if [[ ! -f .env.staging ]]; then
  echo "Create .env.staging from .env.staging.example before deploying." >&2
  exit 2
fi

export IMAGE_TAG="$1"
staging_url="${2%/}"
compose=(docker compose --env-file .env.staging -f compose.staging.yml)
profile_mode=held
if [[ $# -eq 3 ]]; then
  compose+=(-f compose.staging.profile.yml)
  profile_mode=reviewed
fi

"${compose[@]}" config --quiet
"${compose[@]}" pull
"${compose[@]}" up -d --wait --wait-timeout 180
curl --fail --silent --show-error --retry 8 --retry-delay 5 --retry-all-errors \
  "${staging_url}/health"
curl --fail --silent --show-error --retry 8 --retry-delay 5 --retry-all-errors \
  "${staging_url}/api/v1/events" > /dev/null
curl --fail --silent --show-error --retry 8 --retry-delay 5 --retry-all-errors \
  "${staging_url}/api/v1/risk-profile/clusters" | python3 -c '
import json
import sys

try:
    profiles = json.load(sys.stdin)
except json.JSONDecodeError:
    raise SystemExit("risk-profile endpoint returned invalid JSON")

reviewed = sys.argv[1] == "reviewed"
if not isinstance(profiles, list) or bool(profiles) != reviewed:
    expected = "a non-empty list" if reviewed else "an empty list"
    raise SystemExit(f"risk-profile endpoint must return {expected} in this staging mode")
' "$profile_mode"
