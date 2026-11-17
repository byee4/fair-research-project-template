# .agent — the agent control plane (agent kit, Sept 2026)

Enforcement for every coding agent (Claude Code, Codex, any wrapper) and for humans, so that
rules in `AGENTS.md` are not just advice.

| Piece | What it does | Wired into |
|---|---|---|
| `hooks/pre_tool_guard.py` | Blocks/asks on risky shell commands and file access using `policy.yaml` | Claude Code + Codex `PreToolUse` |
| `hooks/post_edit_check.sh` | Fast lint/parse of the file just edited; problems go back to the agent | `PostToolUse` |
| `hooks/stop_gate.sh` | The agent can't finish while `done.sh` fails | `Stop` |
| `policy.yaml` | deny / ask rules (paths, commands) | the guard |
| `done.sh` | Definition of done: the same checks run by the Stop hook, CI, and humans | Stop hook, CI |
| `install/` | Protected config copied into place by `scripts/install_agent_kit.sh` | — |

`install/` holds (dot-less, mapped by the installer) `claude/settings.json` (permission rules, Bash sandbox, hooks, bypass mode
disabled, project MCP servers not auto-enabled), `codex/hooks.json` (same hooks; asks become
denies because Codex hooks can't ask), `pre-commit-config.yaml` (ruff, gitleaks, hygiene, skills
sync), and `github/` (CI, Dependabot with cooldown, CODEOWNERS for the control plane, PR template
with AI-authorship disclosure). Install with `bash scripts/install_agent_kit.sh`.

Layers, fastest first: post-edit hook (ms) → guard (ms) → pre-commit (s) → Stop gate / CI (min) →
human review. Every agent mistake you catch should become a test or a policy rule, not only a
new line in `AGENTS.md`. Tune the policy from `python3 scripts/agent_audit_report.py`.

Audit log: denied/asked tool calls are appended to `logs/agent/audit.jsonl` (git-ignored).
