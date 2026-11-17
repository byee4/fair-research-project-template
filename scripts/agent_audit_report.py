#!/usr/bin/env python3
"""Summarize logs/agent/audit.jsonl to tune .agent/policy.yaml.
A rule that fires constantly and is always approved is friction to relax; a deny that keeps
recurring is a behavior to address in AGENTS.md, a skill, or a test."""
import collections
import json
import sys
from pathlib import Path

log = Path(sys.argv[1] if len(sys.argv) > 1 else "logs/agent/audit.jsonl")
if not log.exists():
    sys.exit(f"no audit log at {log}")
recs = [json.loads(x) for x in log.read_text().splitlines() if x.strip()]
by = collections.Counter((r["decision"], r.get("reason", "")[:100]) for r in recs)
print(f"{len(recs)} denied/asked tool calls\n")
for (d, reason), n in by.most_common(30):
    print(f"{n:5d}  {d:5s}  {reason}")
