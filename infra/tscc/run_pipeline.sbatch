#!/bin/bash
# Launch the pinned pipeline's CONTROLLER as a small long-running job (TSCC forbids compute on
# login nodes). A human submits this; agents may only propose it (policy: submit_slurm_job = ask).
#SBATCH --job-name=pipeline-controller
#SBATCH --account=<your_allocation>
#SBATCH --partition=condo
#SBATCH --qos=condo
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=7-00:00:00
#SBATCH --output=logs/controller_%j.out
set -euo pipefail
cd "$SLURM_SUBMIT_DIR"
module load singularitypro 2>/dev/null || module load apptainer 2>/dev/null || true

# Refuse to run on changed inputs or an invalid sheet.
python3 scripts/make_manifest.py verify data/raw/MANIFEST.tsv
python3 scripts/validate_samplesheet.py config/samples.tsv --check-files
python3 scripts/export_samplesheet.py || true     # no-op for pipelines that read config/samples.tsv

# The launch command comes from workflow/pipeline.yaml (set by init_project.py from the assay module).
# Fill the {placeholders} in workflow/pipeline.yaml once (site_profile, fasta, gtf, ...), then:
LAUNCH=$(python3 -c "import yaml;p=yaml.safe_load(open('workflow/pipeline.yaml'));print(p['launch'].replace('{version}', p['version']))")
if [[ "$LAUNCH" == *"{"* ]]; then echo "Unfilled placeholder in workflow/pipeline.yaml launch: $LAUNCH" >&2; exit 1; fi
echo "Running: $LAUNCH"
eval "$LAUNCH"

OUTDIR=$(python3 -c "import yaml;print(yaml.safe_load(open('workflow/pipeline.yaml')).get('outdir','results'))")
python3 scripts/check_contracts.py --results "$OUTDIR" --samplesheet config/samples.tsv
ENGINE=$(python3 -c "import yaml;print(yaml.safe_load(open('workflow/pipeline.yaml'))['engine'])")
if [[ "$ENGINE" != nextflow ]]; then        # Nextflow runs get an RO-Crate from nf-prov
  python3 scripts/build_rocrate.py --results "$OUTDIR" --name "$(basename "$PWD") $(date +%F)" \
      --author "<Your Name>" --orcid "https://orcid.org/0000-0000-0000-0000"
fi
