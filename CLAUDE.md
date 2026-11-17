@AGENTS.md

## Claude Code specifics
- Hooks, permission rules and the Bash sandbox are in `.claude/settings.json`
  (installed from `.agent/install/` by `scripts/install_agent_kit.sh`). Check with `/hooks`.
- Skills are mirrored from `.agents/skills/` into `.claude/skills/`; edit the canonical copy.
