# Agent evaluations

| Layer | Tool | When | What it catches |
|---|---|---|---|
| Unit | `pytest` (tests/) | every edit (stop hook), every commit, CI | broken code, contract violations, regressions |
| Agent behavior | Inspect AI (`evals/inspect/`) | model/AGENTS.md/policy/hook change; weekly | agent ignores rules, touches protected files, declares done early |
| Prose | promptfoo (`evals/promptfoo/`) | before committee updates / manuscripts | overclaiming, missing uncertainty |
| Traces | OpenTelemetry → Langfuse (self-hosted) or CloudWatch | always on | drift after model updates, cost, failure clusters |

Grow `evals/cases/lab_tasks.jsonl` by one case each time you catch an agent mistake in review.
