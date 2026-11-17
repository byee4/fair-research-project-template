---
name: ship-change
description: Make a feature or bug-fix change end to end in this repo — spec, branch, failing test first, implement, run the definition of done, update docs, open a PR with evidence. Use for any non-trivial code change.
---

# Ship a change

1. **Understand.** Read `AGENTS.md`, `docs/codemap.md`, and any related `docs/specs/*.md`.
   Ask the user about anything ambiguous before editing.
2. **Spec (non-trivial work).** Interview the user until you could write the spec, then write it
   to `docs/specs/YYYY-MM-DD-<topic>.md`: goal, non-goals, acceptance checks, failure modes.
   Keep it short. If the interview ran long, suggest building from the spec in a fresh session.
3. **Branch.** `git switch -c <agent-or-user>/<short-desc>`. Never work on `main`.
4. **Test first.** Write a test that fails now and will pass when the change is right.
   For a bug, reproduce it as a regression test before fixing.
5. **Implement** the smallest change that makes the test pass. Touch only what the task needs.
6. **Definition of done.** Run `bash .agent/done.sh` and fix everything it reports. Paste its output.
7. **Docs.** Update `README.md` / `docs/codemap.md` if a public surface or layout changed.
8. **PR.** Commit as `<area>: <imperative summary>`, push the branch (a human approves the push),
   and open a PR using the template: what/why, spec link, agent + model used, pasted evidence, risks.

Never: push to `main`, force-push, skip hooks (`--no-verify`), edit the agent control plane
(`.agent/`, `.agents/`, `.claude/`, `.codex/`, `AGENTS.md`, `.github/`) without the user asking.
