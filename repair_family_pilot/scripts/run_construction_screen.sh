#!/bin/bash
# Construction screen for case 76906469.
#
# Cost estimate for gpt-6-luna at $0.10 / 1M input tokens and $0.50 / 1M output tokens.
# One technical conversation on each of 4 configurations, then 3 repeats of those 4:
#   expected, a few cents
#   the cap of 200 model calls stops a looping agent near $0.30
# The model is gpt-6-luna with reasoning_effort none on every configuration, including llm-math.
#
# Usage, from anywhere:
#   export OPENAI_API_KEY=...
#   bash scripts/run_construction_screen.sh
# The key is not printed and is not written to a file.

set -euo pipefail
cd "$(dirname "$0")/.."

if [ -z "${OPENAI_API_KEY:-}" ]; then
  echo "OPENAI_API_KEY is not set. Export it in this shell, then run the script again."
  exit 1
fi

PYTHON="/data/wang/junh/envs/harnessfix/bin/python"

echo "Full collection: 12 task groups, 4 configurations, 20 repeats. No smoke step. Expected spend is about \$1. The cap stops the run near \$2."
"$PYTHON" -m repair_family_pilot collect --config configs/pilot.yaml
