---
name: project-interview
description: Set up a new research project by interviewing the user (question, assay, platform, replicates, organism, data sources, compute), choosing and pinning a community pipeline, and installing the matching assay module. Use when project.yaml has initialized false or the user says they are starting a new project.
---

# Project interview

Follow `docs/agent_playbooks/project_interview.md` step by step. Key rules:

- Ask, don't guess: assay, platform/chemistry, replicates (biological units), organism, data sources.
- Accept "I don't know" and record it as `TODO(ask PI)` instead of inventing an answer.
- Look up the pipeline's current release yourself and pin an exact version (never "latest").
- Install with `python3 scripts/init_project.py --assay … --variant … --pipeline … --version … --organism …`.
- Finish with `pytest -q` output and the three things the student should do this week.
- Do not write pipeline code during the interview.
