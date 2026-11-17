#!/usr/bin/env bash
# Install the agent kit's protected config into place (run once after creating a project from
# this template, and again after updating .agent/install/). Idempotent. (The config is stored
# without leading dots because some file-sync tools refuse to write .claude/.github paths.)
#   .agent/install/claude/                 -> .claude/                 (Claude Code permissions/sandbox/hooks)
#   .agent/install/codex/                  -> .codex/                  (Codex hooks)
#   .agent/install/github/                 -> .github/                 (CI, Dependabot, CODEOWNERS, PR template)
#   .agent/install/pre-commit-config.yaml  -> .pre-commit-config.yaml
#   .agents/skills/  (canonical)           -> .claude/skills/          (mirror for Claude Code)
# Existing files that differ are backed up to <file>.bak-<date> before being replaced.
# Ends with a summary of what it did and what is left to commit.
set -euo pipefail
cd "$(dirname "$0")/.."
stamp=$(date +%Y%m%d%H%M%S)
src=.agent/install
dest_for() {
  case "$1" in
    claude/*) echo ".claude/${1#claude/}" ;;
    codex/*) echo ".codex/${1#codex/}" ;;
    github/*) echo ".github/${1#github/}" ;;
    pre-commit-config.yaml) echo ".pre-commit-config.yaml" ;;
    *) echo "$1" ;;
  esac
}
copied=0
backed_up=0
while IFS= read -r -d '' f; do
  rel=$(dest_for "${f#"$src"/}")
  if [[ -f "$rel" ]] && ! cmp -s "$f" "$rel"; then
    cp "$rel" "$rel.bak-$stamp"; echo "backed up $rel -> $rel.bak-$stamp"; backed_up=$((backed_up + 1))
  fi
  mkdir -p "$(dirname "$rel")"; cp "$f" "$rel"; echo "installed $rel"; copied=$((copied + 1))
done < <(find "$src" -type f -print0)
skills="no .agents/skills to mirror"
if [[ -d .agents/skills ]]; then
  rm -rf .claude/skills && mkdir -p .claude && cp -R .agents/skills .claude/skills && echo "synced .claude/skills"
  skills=".agents/skills -> .claude/skills"
fi
chmod +x .agent/hooks/* .agent/done.sh 2>/dev/null || true
mkdir -p logs/agent

# pre-commit runs the checks in .pre-commit-config.yaml on every commit. `pre-commit install`
# refuses to run when git's core.hooksPath is set, so check that first and say so plainly.
hooks="not installed: pre-commit not found (install it with 'uv tool install pre-commit' or
    'pip install --user pre-commit', then re-run this script)"
in_git=false
autoupdate=""
git rev-parse --git-dir >/dev/null 2>&1 && in_git=true
if command -v pre-commit >/dev/null 2>&1 || command -v uvx >/dev/null 2>&1; then
  PC="pre-commit"; command -v pre-commit >/dev/null 2>&1 || PC="uvx pre-commit"
  if ! $in_git; then
    hooks="not installed: this folder is not a git repository yet (run 'git init', then re-run)"
  else
    if $PC autoupdate >/dev/null 2>&1; then
      echo "pre-commit revs updated"; autoupdate=ok
    else
      echo "pre-commit autoupdate skipped (offline?)"
    fi
    hooks_path=$(git config --get core.hooksPath || true)
    if [[ -n "$hooks_path" ]]; then
      origin=$(git config --show-origin --get core.hooksPath | cut -f1)
      hooks="not installed: git's core.hooksPath is set to $hooks_path ($origin),
    and pre-commit won't install a hook while it is. Either run the checks by hand with
    '$PC run --all-files', or, if the hooks in that folder chain to .git/hooks/pre-commit,
    unset it in this repo (if set here) and hide the global one (needs git 2.32+):
      git config --local --unset-all core.hooksPath
      GIT_CONFIG_GLOBAL=/dev/null $PC install"
    elif $PC install; then
      hooks="installed: .git/hooks/pre-commit runs the checks on every commit"
    else
      hooks="not installed: '$PC install' failed (see the error above)"
    fi
  fi
fi

to_commit=""
if $in_git; then
  to_commit=$(git status --porcelain --untracked-files=all -- \
    .claude .codex .github .pre-commit-config.yaml .agent logs/agent 2>/dev/null || true)
fi

# Describe each installed setting, hook, skill, GitHub file and commit check in plain English,
# read from the files themselves; fall back to a short summary if python3 isn't available.
if ! { command -v python3 >/dev/null 2>&1 && \
  KIT_COPIED=$copied KIT_BACKED_UP=$backed_up KIT_STAMP=$stamp KIT_HOOKS="$hooks" \
  KIT_AUTOUPDATE=$autoupdate python3 scripts/describe_agent_kit.py; }; then
  echo
  echo "Summary"
  echo "  Config:     copied $copied files from $src/ into .claude/, .codex/, .github/ and"
  echo "              .pre-commit-config.yaml ($backed_up existing files backed up as *.bak-$stamp)"
  echo "  Skills:     $skills"
  echo "  Hooks:      made .agent/hooks/* and .agent/done.sh executable; created logs/agent/"
  echo "  pre-commit: $hooks"
fi
if [[ -n "$to_commit" ]]; then
  echo
  echo "Not committed yet (GitHub CI and the agent hooks only apply once these are in the repo):"
  echo "$to_commit" | sed 's/^/  /'
  if ((backed_up > 0)); then
    echo "  Review or delete the *.bak-$stamp files before committing."
  fi
  echo "  Commit them with:"
  echo "    git add .claude .codex .github .pre-commit-config.yaml .agent logs/agent"
  echo "    git commit -m \"Install agent kit\""
fi
cat <<'MSG'

Next:
  - Codex: open the repo and trust the project hooks with /hooks.
  - Claude Code: hooks load from .claude/settings.json; check with /hooks.
  - GitHub: protect main (require PRs, CI, and CODEOWNERS review).
  - Workflow actions are pinned to commit SHAs (version in a comment); Dependabot updates them
    weekly after a 7-day cooldown. Re-pin any action you add (e.g. `pinact run`).
MSG
