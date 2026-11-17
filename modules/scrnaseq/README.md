# Module: single-cell / single-nucleus RNA-seq

**Default:** [nf-core/scrnaseq](https://nf-co.re/scrnaseq) pinned to a release; choose the
aligner deliberately (simpleaf default; Cell Ranger when numbers must match 10x; STARsolo).
Downstream analysis (QC, integration, annotation) lives in parameterized notebooks or scripts
that read the pipeline's h5ad and write to `results/analysis/`.

One sample-sheet row = one FASTQ pair; lanes share `sample_id`. Replicates are counted by `donor`.

**Mini fixture:** a few hundred cells subsampled from a public demo dataset of the same chemistry;
run the pipeline's `-profile test` first.

**FAIR:** CELLxGENE/HCA-style ontology metadata (assay, tissue, cell type, donor, development stage).
Deposit FASTQ + matrices to GEO/SRA; curated h5ad to CELLxGENE Discover when appropriate.
