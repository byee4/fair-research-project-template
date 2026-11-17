## Assay notes: single-cell RNA-seq (modules/scrnaseq)
- Rows are FASTQ pairs; lanes of one library share `sample_id`. Replicates are distinct `donor`s.
- Differential expression between conditions = pseudobulk by donor (never cells as replicates).
- Record aligner, chemistry/protocol, and cells vs nuclei; changing any of them is a decision.
- QC thresholds (min genes, max % mito, doublet calls, ambient removal) are scientific parameters:
  propose them with plots, a human approves (policy: change_filter_thresholds).
- Cell-type labels are claims: cite the marker evidence or reference used; label EXPLORATORY by default.
