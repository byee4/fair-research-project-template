#!/usr/bin/env bash
# "Definition of done" gate: the agent cannot finish while .agent/done.sh fails.
# Claude Code / Codex: Stop hook (exit 2 => keep working). Humans/CI: run directly.
set -uo pipefail
ROOT="${PROJECT_ROOT:-$(cd "$(dirname "$0")/../.." && pwd)}"
cd "$ROOT"
if [[ ! -t 0 ]]; then
  active=$(python3 -c 'import json,sys
try: print(bool(json.load(sys.stdin).get("stop_hook_active")))
except Exception: print(False)' 2>/dev/null)
  [[ "$active" == "True" ]] && exit 0        # avoid infinite loops on re-entry
fi
# Nothing changed since the last commit? Nothing to gate.
if git rev-parse --git-dir >/dev/null 2>&1 && [[ -z "$(git status --porcelain 2>/dev/null)" ]]; then exit 0; fi
if ! res=$(bash .agent/done.sh 2>&1); then
  printf "Not done yet: .agent/done.sh failed. 'It ran' is not 'it is correct'.\n%s\n" "$(echo "$res" | tail -n 40)" >&2
  exit 2
fi
exit 0
