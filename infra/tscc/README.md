# TSCC notes

- Where agents run: on your laptop or an AWS dev instance against a git clone — **not** on TSCC
  login nodes (policy forbids running programs there). Code reaches TSCC via `git pull`.
- Where pipelines run: `sbatch infra/tscc/run_pipeline.sbatch` (controller job) → Slurm executor.
- Storage: code in `$HOME`; raw data on `/tscc/projects/...` (read-only, backed up);
  work dirs on `/tscc/lustre/ddn/scratch/$USER` (purged after 90 days — never the only copy);
  per-job temp on `/scratch/$USER/job_$SLURM_JOBID`.
- Containers: build `containers/analysis.def` → `.sif` (on AWS/laptop with apptainer or via
  `apptainer build --remote`), copy to project storage, record sha256 in `containers/SIF_SHA256`.
- Every job needs partition + QOS + account.
