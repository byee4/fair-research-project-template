# Module: eCLIP / CLIP-seq

| Variant | Default | Notes |
|---|---|---|
| eCLIP (SE/PE) with SMInput | YeoLab/skipper (Snakemake) | Reproducible enriched windows, repeats, motifs; needs >= 2 CLIP reps |
| Antibody-barcode eCLIP | YeoLab/Mudskipper | Multiplexed RBPs; confirm manifest format with maintainers |
| ENCODE-comparable | YeoLab/eclip (CWL + CLIPper) | Only when matching ENCODE processing is required |

Skipper is not containerized; it builds conda envs on first run. Run that first build on an
interactive TSCC node, pin the Skipper commit and Snakemake version, and record both in
`workflow/pipeline.yaml`. Provenance: `scripts/build_rocrate.py` after each run.

**Mini fixture:** subsample an ENCODE eCLIP experiment for a well-characterized RBP
(2 CLIP reps + SMInput, ~200k reads each). Expected: the known motif is recovered.

**FAIR:** HGNC id + antibody (catalog, lot, validation) per row; deposit FASTQ + enriched
windows + bigWigs to GEO/SRA following ENCODE metadata conventions.

**Setup for Skipper:** add it at the pinned commit as a submodule so the exact code is recorded:
`git submodule add https://github.com/YeoLab/skipper workflow/vendor/skipper && git -C workflow/vendor/skipper checkout <commit>`.
Copy its example config to `workflow/skipper_config.py`, point it at `workflow/skipper_manifest.csv`
(from `scripts/export_samplesheet.py`), and copy its Slurm profile to `workflow/vendor/skipper/profiles/tscc`
with your TSCC account, partition, and `slurm_extra: "--qos=<qos>"`.
