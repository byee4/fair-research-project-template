#!/usr/bin/env bash
# Agent-agnostic post-edit feedback: fast checks on the file just edited; problems go to
# stderr with exit 2 so the agent (Claude Code / Codex PostToolUse) fixes them next.
# Usage: post_edit_check.sh <file>   or   hook JSON on stdin (tool_input.file_path / apply_patch).
set -uo pipefail
ROOT="${PROJECT_ROOT:-$(cd "$(dirname "$0")/../.." && pwd)}"
files=("$@")
if [[ ${#files[@]} -eq 0 && ! -t 0 ]]; then
  mapfile -t files < <(python3 -c '
import json, re, sys
try: d = json.load(sys.stdin)
except Exception: sys.exit(0)
ti = d.get("tool_input") or {}
for k in ("file_path", "notebook_path"):
    if ti.get(k): print(ti[k])
for k in ("patch", "input"):
    if isinstance(ti.get(k), str):
        for m in re.findall(r"^\*\*\* (?:Add|Update) File: (.+)$", ti[k], re.M): print(m.strip())
' 2>/dev/null)
fi
out=""
for f in "${files[@]}"; do
  [[ -f "$f" ]] || continue
  case "$f" in
    *.py)  command -v ruff >/dev/null && { ruff format -q "$f" 2>/dev/null; out+=$(ruff check --fix -q "$f" 2>&1); } ;;
    *Snakefile|*.smk) command -v snakefmt >/dev/null && out+=$(snakefmt -q "$f" 2>&1) ;;
    *.nf)  command -v nextflow >/dev/null && out+=$(nextflow lint "$f" 2>&1 | grep -iE "error" ) ;;
    *.sh)  out+=$(bash -n "$f" 2>&1); command -v shellcheck >/dev/null && out+=$(shellcheck -S warning "$f" 2>&1) ;;
    *.yaml|*.yml) out+=$(python3 -c 'import sys,yaml; yaml.safe_load(open(sys.argv[1]))' "$f" 2>&1) ;;
    *.json) python3 -m json.tool "$f" >/dev/null 2>&1 || out+="invalid JSON: $f" ;;
    *.toml) out+=$(python3 -c 'import sys,tomllib; tomllib.load(open(sys.argv[1],"rb"))' "$f" 2>&1) ;;
  esac
  [[ -x "$ROOT/.agent/post_edit_extra.sh" ]] && out+=$("$ROOT/.agent/post_edit_extra.sh" "$f" 2>&1)
done
if [[ -n "${out//[[:space:]]/}" ]]; then
  printf 'Post-edit checks found problems — fix before continuing:\n%s\n' "$out" >&2
  exit 2
fi
exit 0
