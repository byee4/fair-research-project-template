#!/usr/bin/env python3
"""Describe, in plain English, what scripts/install_agent_kit.sh just put in place.

Run by install_agent_kit.sh from the repository root (standard library only). Reads the
installed files themselves, so the summary stays true as settings, skills, workflows and
commit checks change. The installer passes its own results in environment variables:
KIT_COPIED, KIT_BACKED_UP, KIT_STAMP, KIT_HOOKS (pre-commit status), KIT_AUTOUPDATE.
"""

import json
import os
import re
import textwrap
from pathlib import Path

WIDTH = 92
CAP = 8


def say(label, text, indent=2, label_width=0):
    """Print `label  text`, wrapping text under itself."""
    first = " " * indent + (label.ljust(label_width) if label_width else label)
    if text:
        first += "  " if label else ""
    pad = " " * len(first) if label else " " * indent
    lines = textwrap.wrap(text, WIDTH, initial_indent=first, subsequent_indent=pad,
                          break_on_hyphens=False, break_long_words=False) or [first]
    print("\n".join(lines))


def capped(items, cap=CAP):
    items = list(dict.fromkeys(i for i in items if i))
    if len(items) > cap:
        return ", ".join(items[:cap]) + f", +{len(items) - cap} more"
    return ", ".join(items)


def joined(items):
    items = list(items)
    return items[0] if len(items) == 1 else ", ".join(items[:-1]) + " and " + items[-1]


# --- Claude Code settings -----------------------------------------------------------------

def _path(p):
    p = re.sub(r"^\./", "", p)
    p = re.sub(r"^\*\*/", "", p)
    return re.sub(r"/\*\*$", "", p)


def _rule(rule):
    """('reading', '.env') / ('commands', 'git push') / ('other', 'any MCP tool')."""
    if rule.startswith("mcp__"):
        return "other", "any MCP tool" if rule == "mcp__*" else rule
    m = re.fullmatch(r"(\w+)(?:\((.*)\))?", rule)
    if not m:
        return "other", rule
    tool, arg = m.group(1), m.group(2)
    if tool == "Bash" and arg:
        return "commands", re.sub(r"(:\*| \*)$", "", arg).strip()
    if tool == "Read" and arg:
        return "reading", _path(arg)
    if tool in ("Edit", "Write", "MultiEdit") and arg:
        return "editing", _path(arg)
    if tool == "WebFetch" and arg:
        return "fetching", arg.replace("domain:", "")
    return "other", rule


def describe_settings():
    path = Path(".claude/settings.json")
    if not path.is_file():
        return
    try:
        data = json.loads(path.read_text())
    except ValueError:
        print(f"Claude Code settings ({path}): could not be read as JSON.")
        return
    print(f"Claude Code settings ({path})")
    perms = data.get("permissions", {})
    for key, title in (("deny", "Blocked"), ("ask", "Asks you first"),
                       ("allow", "Allowed without asking")):
        rules = perms.get(key) or []
        if not rules:
            continue
        print(f"  {title}:")
        groups = {}
        for rule in rules:
            kind, what = _rule(rule)
            groups.setdefault(kind, []).append(what)
        for kind in ("reading", "editing", "commands", "fetching", "other"):
            if kind in groups:
                say(kind, capped(groups[kind]), indent=4, label_width=9)
    sandbox = data.get("sandbox") or {}
    if sandbox.get("enabled"):
        fs = sandbox.get("filesystem", {})
        text = "Shell commands run in an OS sandbox."
        if fs.get("denyRead"):
            text += f" They can't read {capped(_path(p) for p in fs['denyRead'])}."
        if fs.get("denyWrite"):
            text += f" They can't write to {capped(_path(p) for p in fs['denyWrite'])}."
        domains = (sandbox.get("network") or {}).get("allowedDomains") or []
        if domains:
            text += f" They can only reach {len(domains)} listed sites."
        if sandbox.get("failIfUnavailable"):
            text += " If the sandbox can't start on a machine, commands don't run there."
        say("Sandbox:", text)
    if perms.get("disableBypassPermissionsMode") == "disable":
        say("", "Bypass-permissions mode is turned off.")
    if data.get("hooks"):
        say("", "Turns on the agent hooks below.")
    print()


def describe_codex():
    path = Path(".codex/hooks.json")
    if not path.is_file():
        return
    try:
        events = json.loads(path.read_text()).get("hooks", {})
    except ValueError:
        events = {}
    when = {"PreToolUse": "before each command", "PostToolUse": "after each edit",
            "Stop": "before finishing"}
    named = [when[e] for e in when if e in events]
    print(f"Codex ({path})")
    say("", "Turns on the same agent hooks for Codex" + (f" ({joined(named)})." if named else "."))
    print()


# --- Agent hooks and skills ---------------------------------------------------------------

HOOKS = [
    ("before each command", "pre_tool_guard.py",
     "blocks risky commands or asks you first, following the repository's policy file"),
    ("after each edit", "post_edit_check.sh",
     "quick checks on the file just edited, so the agent fixes problems straight away"),
    ("before finishing", "stop_gate.sh",
     "runs .agent/done.sh; the agent can't report \"done\" while it fails"),
]


def describe_hooks():
    present = [h for h in HOOKS if Path(".agent/hooks", h[1]).is_file()]
    if not present:
        return
    print("Agent hooks (run automatically while Claude Code or Codex works)")
    for when, name, what in present:
        say(when.ljust(21) + name.ljust(19), what)
    print()


def _skill_summary(text):
    m = re.search(r"^description:\s*(.+)$", text, re.MULTILINE)
    if not m:
        return ""
    desc = m.group(1).strip().strip("\"'")
    return re.split(r"(?<=[.!?])\s+Use\b", desc)[0].strip()


def describe_skills():
    root = Path(".agents/skills")
    skills = sorted(p for p in root.glob("*/SKILL.md")) if root.is_dir() else []
    if not skills:
        return
    print("Skills (playbooks the agent follows when a task matches; copied to .claude/skills)")
    width = max(len(p.parent.name) for p in skills)
    for p in skills:
        say(p.parent.name.ljust(width), _skill_summary(p.read_text()) or "(no description)")
    print()


# --- GitHub -------------------------------------------------------------------------------

TRIGGERS = {"push": "every push", "pull_request": "every PR", "release": "each release",
            "schedule": "a schedule", "workflow_dispatch": "by hand"}
JOBS = {
    "test": "tests", "checks": "tests and project checks", "validate": "workflow validation",
    "pre-commit": "all commit checks", "workflow-security": "a security scan of the workflow files",
    "custom-snakemake": "Snakemake lint", "custom-nextflow": "Nextflow lint",
    "agent-evals": "agent evals", "image": "builds and pushes the container image",
    "build": "builds the package", "publish": "publishes it",
}
ECOSYSTEMS = {"github-actions": "GitHub Actions", "pip": "pip packages", "uv": "uv packages",
              "npm": "npm packages", "docker": "Docker images"}


def _top_keys(text, block):
    """Keys indented two spaces under a top-level `block:` line."""
    keys, inside = [], False
    for line in text.splitlines():
        if re.match(rf"^['\"]?{block}['\"]?:\s*$", line):
            inside = True
            continue
        inline = re.match(rf"^['\"]?{block}['\"]?:\s*\[(.*)\]", line)
        if inline:
            return [k.strip() for k in inline.group(1).split(",")]
        if inside:
            if re.match(r"^\S", line):
                break
            m = re.match(r"^  ([A-Za-z0-9_-]+):", line)
            if m:
                keys.append(m.group(1))
    return keys


def _workflow(path):
    text = path.read_text()
    triggers = [TRIGGERS.get(k, k) for k in _top_keys(text, "on")]
    jobs = [JOBS.get(k, k) for k in _top_keys(text, "jobs")]
    when = f"On {joined(triggers)}" if triggers else "Runs"
    return f"{when}: {', '.join(jobs)}." if jobs else f"{when}."


def _dependabot(path):
    text = path.read_text()
    kinds = [ECOSYSTEMS.get(k, k) for k in re.findall(r"package-ecosystem:\s*([\w-]+)", text)]
    interval = re.search(r"interval:\s*(\w+)", text)
    cooldown = re.search(r"default-days:\s*(\d+)", text)
    text = f"{(interval.group(1) if interval else 'Regular').capitalize()} PRs to update "
    text += joined(list(dict.fromkeys(kinds))) if kinds else "dependencies"
    if cooldown:
        text += f", waiting {cooldown.group(1)} days after each new release"
    return text + "."


def _codeowners(path):
    owners = {}
    for line in path.read_text().splitlines():
        parts = line.split("#", 1)[0].split()
        if len(parts) >= 2:
            for owner in parts[1:]:
                owners.setdefault(owner, []).append(parts[0].strip("/"))
    if not owners:
        return "Lists no owners."
    return "Changes need review from " + "; ".join(
        f"{o} ({capped(paths, 4)})" for o, paths in owners.items()) + "."


def describe_github():
    root = Path(".github")
    files = sorted(p for p in root.rglob("*") if p.is_file() and ".bak-" not in p.name) \
        if root.is_dir() else []
    if not files:
        return
    print("GitHub (takes effect once committed and pushed)")
    width = max(len(str(p.relative_to(root))) for p in files)
    for p in files:  # no zip(strict=): this must run on older system python3 (e.g. on HPC)
        r = str(p.relative_to(root))
        if r.startswith("workflows/") and p.suffix in (".yml", ".yaml"):
            what = _workflow(p)
        elif p.name == "dependabot.yml":
            what = _dependabot(p)
        elif p.name == "CODEOWNERS":
            what = _codeowners(p)
        elif p.name.lower() == "pull_request_template.md":
            what = "Checklist shown on every new PR."
        else:
            what = ""
        say(r.ljust(width), what)
    print()


# --- Commit checks ------------------------------------------------------------------------

CHECKS = {
    "check-yaml": ("files", "valid YAML"), "check-toml": ("files", "valid TOML"),
    "check-json": ("files", "valid JSON"),
    "check-added-large-files": ("files", "no files over {size}"),
    "check-merge-conflict": ("files", "no leftover merge-conflict markers"),
    "end-of-file-fixer": ("files", "missing final newlines added"),
    "trailing-whitespace": ("files", "trailing spaces removed"),
    "mixed-line-ending": ("files", "consistent line endings"),
    "check-case-conflict": ("files", "no file names that differ only by case"),
    "detect-private-key": ("secrets", "private keys"),
    "gitleaks": ("secrets", "API tokens and passwords (gitleaks)"),
    "gitleaks-docker": ("secrets", "API tokens and passwords (gitleaks)"),
    "gitleaks-system": ("secrets", "API tokens and passwords (gitleaks)"),
    "detect-secrets": ("secrets", "API tokens and passwords (detect-secrets)"),
    "ruff-check": ("style", "ruff for Python"), "ruff": ("style", "ruff for Python"),
    "ruff-format": ("style", "ruff formatting for Python"),
    "black": ("style", "black formatting for Python"), "mypy": ("style", "mypy type checks"),
    "snakefmt": ("style", "snakefmt for Snakemake"),
    "validate-samplesheet": ("project", "sample sheet is valid"),
    "check-contracts": ("project", "data contracts are well-formed"),
    "check-claims": ("project", "claims are backed by validation"),
    "agent-skills-in-sync": ("project", ".claude/skills matches .agents/skills"),
}


def _hooks_in(text):
    """(id, name, args) for each hook in a .pre-commit-config.yaml."""
    hooks = []
    for block in re.split(r"\n(?=\s*- id:)", text):
        m = re.search(r"- id:\s*([\w.-]+)", block)
        if not m:
            continue
        name = re.search(r"\n\s*name:\s*(.+)", block)
        args = re.search(r"\n\s*args:\s*(.+)", block)
        hooks.append((m.group(1), name.group(1).strip().strip("\"'") if name else "",
                      args.group(1) if args else ""))
    return hooks


def describe_precommit():
    path = Path(".pre-commit-config.yaml")
    status = os.environ.get("KIT_HOOKS", "")
    if not path.is_file() and not status:
        return
    print(f"Commit checks ({path})")
    if status:
        first, *rest = status.splitlines()
        say("Status:", first.strip())
        for line in rest:  # keep the installer's line breaks: some lines are commands to copy
            print("  " + line)
    if path.is_file():
        groups = {}
        for hook_id, name, args in _hooks_in(path.read_text()):
            kind, what = CHECKS.get(hook_id, ("other", name or hook_id))
            if "{size}" in what:
                kb = re.search(r"maxkb=(\d+)", args)
                size = f"{int(kb.group(1)) // 1000} MB" if kb else "500 KB"
                what = what.format(size=size)
            groups.setdefault(kind, []).append(what)
        for kind in ("files", "secrets", "style", "project", "other"):
            if kind in groups:
                say(kind, capped(groups[kind], 12), indent=2, label_width=8)
    if os.environ.get("KIT_AUTOUPDATE") == "ok":
        say("", "Check versions were updated to the latest releases.")
    print()


def main():
    print()
    print("What this installed")
    print("-------------------")
    copied = os.environ.get("KIT_COPIED", "?")
    backed_up = int(os.environ.get("KIT_BACKED_UP", "0") or 0)
    describe_settings()
    describe_codex()
    describe_hooks()
    describe_skills()
    describe_github()
    describe_precommit()
    text = f"Copied {copied} files from .agent/install/. "
    if backed_up:
        stamp = os.environ.get("KIT_STAMP", "")
        files = "file differed and was" if backed_up == 1 else "files differed and were"
        text += f"{backed_up} existing {files} saved as *.bak-{stamp}; review or delete them."
    else:
        text += "No existing files were replaced."
    say("", text, indent=0)


if __name__ == "__main__":
    main()
