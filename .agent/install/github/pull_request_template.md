## What and why

## Spec / issue
docs/specs/… (or n/a for trivial changes)

## Author
- [ ] Human  - [ ] Coding agent — tool + model: ______  (session/trace link if available)

## Evidence (paste output; don't summarize)
- `bash .agent/done.sh`:

## Risk
- [ ] Touches agent control plane (.agent, .agents, .claude, .codex, AGENTS.md, CLAUDE.md, .github)
- [ ] Touches deployment, secrets handling, auth, or data
- Rollback plan:

## Reviewer checklist
- [ ] A test would fail if this regressed
- [ ] Docs/codemap updated if a public surface changed
- [ ] New mistake found in review? Added a regression test (and an AGENTS.md line only if a test can't catch it)
