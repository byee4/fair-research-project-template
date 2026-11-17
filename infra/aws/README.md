# AWS notes

- Bucket layout: `s3://<lab-bucket>/<project>/{raw,external,work,results,crates}/`.
  Enable versioning; apply `s3-raw-protect-policy.json` (or S3 Object Lock) to `raw/`.
- IAM: a separate `<project>-agent` role with read-only raw access, write only to `work/` and
  `results/`, no IAM/Batch-admin permissions; short-lived credentials via SSO.
- Compute: Nextflow `-profile awsbatch` or Snakemake on AWS ParallelCluster (Slurm) for parity with TSCC.
- Agent sandbox (optional, for unattended agents): Bedrock AgentCore Runtime + Code Interpreter in a VPC
  with gateway-only ingress, Guardrails in Policy, and AgentCore Evaluations on traces.
- Observability: export agent OpenTelemetry to CloudWatch or a self-hosted Langfuse (see `.agent/telemetry.env.example`).
- Budgets: AWS Budgets alert at 50/80/100% of monthly project budget.
