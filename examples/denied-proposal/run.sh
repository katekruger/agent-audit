#!/usr/bin/env bash
# The one-command version: starts a local OTel Collector, runs the
# flagship example against it, and shows what actually landed.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"

docker compose up -d --wait
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318
uv run --project ../../py --group examples python run.py

echo
echo "--- what the collector received (docker compose logs collector) ---"
docker compose logs collector --no-log-prefix | grep -A 40 "EventName: agent_audit" || true
