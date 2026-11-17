#!/usr/bin/env bash
# Research-template extra post-edit checks (called by .agent/hooks/post_edit_check.sh).
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
case "$1" in
  *samples*.tsv|*samplesheet*.tsv|*samplesheet*.csv) python3 "$ROOT/scripts/validate_samplesheet.py" "$1" 2>&1 >/dev/null ;;
  */claims/*.yaml|claims/*.yaml) python3 "$ROOT/scripts/check_claims.py" 2>&1 >/dev/null ;;
  */contracts/*.yaml|contracts/*.yaml) python3 "$ROOT/scripts/check_contracts.py" 2>&1 >/dev/null ;;
esac
exit 0
