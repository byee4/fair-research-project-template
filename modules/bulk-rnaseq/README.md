# Module: bulk RNA-seq

**Default:** [nf-core/rnaseq](https://nf-co.re/rnaseq) pinned to an exact release (check the
releases page during the interview). **Fallback:** `skeleton/` — a custom Snakemake/Nextflow pipeline
with lineage sidecars, only if nf-core/rnaseq cannot handle the design.

What gets installed by `init_project.py --assay bulk-rnaseq`:
`samplesheet.schema.json` (FASTQ, lane, strandedness), `rules.yaml` (lanes, paired consistency),
`contracts/<pipeline>.yaml`, `tests/` (pitfall tests), agent notes, eval cases.

**Mini fixture:** 10–50k read pairs per sample from a public run of the same kit on a ~1 Mb
chr22 slice. First, run nf-core/rnaseq's own `-profile test` to prove the install works on TSCC.
Then run your fixture, inspect outputs by hand, and record expected values.

**FAIR:** MINSEQE metadata; deposit FASTQ to SRA and counts + sample sheet to GEO
(dbGaP if controlled-access human data).
