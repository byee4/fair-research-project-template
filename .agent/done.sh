#!/usr/bin/env bash
# Definition of done for this repo. Run by the Stop hook, by CI, and by humans.
# Every command must pass before an agent may report a task complete.
set -uo pipefail
cd "$(dirname "$0")/.."
fail=0
run() { echo "+ $*"; "$@" || { echo "FAILED: $*"; fail=1; }; }
run python3 -m pytest -q -x -p no:cacheprovider
run python3 scripts/check_contracts.py
run python3 scripts/check_claims.py
python3 -m pytest -q -p no:cacheprovider tests/test_agent_kit.py >/dev/null 2>&1 || { echo 'FAILED: agent kit self-test (tests/test_agent_kit.py)'; fail=1; }
exit $fail
