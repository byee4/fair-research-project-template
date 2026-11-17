#!/usr/bin/env bash
# One-time setup after cloning the template.
set -euo pipefail
cd "$(dirname "$0")/.."
chmod +x scripts/*.py .agent/hooks/* 2>/dev/null || true
python3 -m pip install --user pre-commit ruff snakefmt pyyaml jsonschema pandas pytest rocrate
bash scripts/install_agent_kit.sh      # Claude Code/Codex config, CI, Dependabot, pre-commit
# Custom Nextflow skeleton only: Nextflow adds workflow/nextflow/bin to PATH.
if [[ -d workflow/nextflow ]]; then
  mkdir -p workflow/nextflow/bin
  for f in write_lineage.py tidy_featurecounts.py qc_summary.py diff.R; do
    [[ -f scripts/$f ]] && ln -sf ../../../scripts/$f workflow/nextflow/bin/$f
  done
fi
if grep -q "initialized: false" project.yaml; then
  echo
  echo "Next: start your coding agent in this folder and say: 'I'm starting a new project.'"
  echo "It will run the project interview (docs/agent_playbooks/project_interview.md)."
  echo "No agent? Run: python3 scripts/init_project.py --list"
fi
