#!/usr/bin/env python3
"""Agent-agnostic pre-tool guard (Claude Code, Codex, or any agent/wrapper).

Reads JSON on stdin in the PreToolUse format shared by Claude Code and Codex:
    {"tool_name": "...", "tool_input": {...}}
or CLI flags:  --command "<shell>" | --write <path> | --read <path>

Rules come from the first policy file found: policy/authority.yaml, then .agent/policy.yaml
(key `enforcement`: deny_write_paths, ask_write_paths, deny_read_paths, deny_commands, ask_commands).

Exit 0 = allow, 2 = deny (reason on stderr). "ask" prints a permissionDecision JSON (exit 0),
or, when GUARD_ASK_MODE=deny (agents without an ask decision), denies with a "ask the human" reason.
CLI mode: ask exits 3. Every non-allow decision is appended to logs/agent/audit.jsonl.
"""

from __future__ import annotations

import argparse
import datetime as dt
import fnmatch
import json
import os
import re
import shlex
import sys
from pathlib import Path

ROOT = Path(os.environ.get("PROJECT_ROOT") or Path(__file__).resolve().parents[2])
POLICIES = [ROOT / "policy" / "authority.yaml", ROOT / ".agent" / "policy.yaml"]
AUDIT = Path(os.environ.get("GUARD_AUDIT_LOG") or ROOT / "logs" / "agent" / "audit.jsonl")
PATCH_FILE = re.compile(r"^\*\*\* (?:Add|Update|Delete) File: (.+)$", re.MULTILINE)  # Codex apply_patch


def load_policy() -> dict:
    import yaml

    for p in POLICIES:
        if p.exists():
            return (yaml.safe_load(p.read_text()) or {}).get("enforcement", {})
    return {}


def rel(path: str) -> str:
    p = Path(os.path.expanduser(path))
    p = (p if p.is_absolute() else Path.cwd() / p).resolve()
    try:
        return str(p.relative_to(ROOT))
    except ValueError:
        return str(p)


def match(path: str, patterns: list[str]) -> str | None:
    for pat in patterns:
        pat_x = os.path.expanduser(pat)
        if fnmatch.fnmatch(path, pat_x) or fnmatch.fnmatch(path, pat_x.rstrip("*").rstrip("/")):
            return pat
    return None


def decide(kind: str, value: str, pol: dict) -> tuple[str, str]:
    if kind == "command":
        for rx in pol.get("deny_commands", []):
            if re.search(rx, value):
                return "deny", f"command matches deny rule {rx!r}"
        for rx in pol.get("ask_commands", []):
            if re.search(rx, value):
                return "ask", f"command matches ask rule {rx!r}: a human must approve"
        return "allow", ""
    path = rel(value)
    if kind == "write":
        if m := match(path, pol.get("deny_write_paths", [])):
            return "deny", f"writing {path} is forbidden ({m!r})"
        if m := match(path, pol.get("ask_write_paths", [])):
            return "ask", f"{path} is a protected file ({m!r}): a human must approve"
    if kind == "read" and (m := match(path, pol.get("deny_read_paths", []))):
        return "deny", f"reading {path} is forbidden ({m!r})"
    return "allow", ""


def checks_from_payload(data: dict) -> list[tuple[str, str]]:
    tool = str(data.get("tool_name", ""))
    ti = data.get("tool_input") or {}
    out: list[tuple[str, str]] = []
    cmd = ti.get("command") or ti.get("cmd")
    if isinstance(cmd, list):
        cmd = " ".join(shlex.quote(str(c)) for c in cmd)
    if cmd:
        out.append(("command", str(cmd)))
    for key in ("file_path", "notebook_path"):
        if ti.get(key):
            out.append(("read" if tool in {"Read", "Grep", "Glob"} else "write", ti[key]))
    if tool in {"Grep", "Glob"} and ti.get("path"):
        out.append(("read", ti["path"]))
    for key in ("patch", "input"):
        if isinstance(ti.get(key), str):
            out += [("write", p.strip()) for p in PATCH_FILE.findall(ti[key])]
    return out


def audit(rec: dict) -> None:
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    rec["ts"] = dt.datetime.now(dt.timezone.utc).isoformat()  # noqa: UP017 (py3.10 compatible)
    with open(AUDIT, "a") as fh:
        fh.write(json.dumps(rec) + "\n")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--command")
    ap.add_argument("--write")
    ap.add_argument("--read")
    a = ap.parse_args()
    cli = any([a.command, a.write, a.read])
    if cli:
        checks = [(k, v) for k, v in (("command", a.command), ("write", a.write), ("read", a.read)) if v]
    else:
        raw = sys.stdin.read()
        checks = checks_from_payload(json.loads(raw)) if raw.strip() else []
    pol = load_policy()
    final, reason = "allow", ""
    for kind, value in checks:
        d, r = decide(kind, value, pol)
        if d != "allow":
            audit(
                {
                    "hook": "pre_tool_guard",
                    "kind": kind,
                    "value": value,
                    "decision": d,
                    "reason": r,
                }
            )
        if d == "deny":
            final, reason = d, r
            break
        if d == "ask":
            final, reason = d, r
    if final == "ask" and not cli and os.environ.get("GUARD_ASK_MODE") == "deny":
        final, reason = (
            "deny",
            reason + " — stop and ask the user to run or approve this",
        )
    if final == "deny":
        print(f"BLOCKED by .agent/hooks/pre_tool_guard.py: {reason}", file=sys.stderr)
        return 2
    if final == "ask":
        if cli:
            print(f"ASK: {reason}")
            return 3
        print(
            json.dumps(
                {
                    "hookSpecificOutput": {
                        "hookEventName": "PreToolUse",
                        "permissionDecision": "ask",
                        "permissionDecisionReason": reason,
                    }
                }
            )
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
