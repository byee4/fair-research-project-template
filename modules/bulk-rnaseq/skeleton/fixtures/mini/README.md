# Mini fixture

Tiny dataset the agent must pass before declaring any pipeline change "done".

Replace the synthetic FASTQs with a **real** down-sampled subset as soon as possible:
- While waiting for your own data: subsample a public dataset with the same assay
  (e.g. 10–50k read pairs from an ENCODE/GEO run on a ~1 Mb slice of chr22), so
  reads actually align and counts are non-trivial.
- When your data arrive: replace with 10k read pairs per sample from your own runs.

Then run the pipeline once, **inspect the outputs by hand**, and record the
expected values in `tests/expected/mini_expected.yaml`. From then on any drift fails tests.

Reference slice: `ref/` (FASTA slice, matching GTF subset, chrom.sizes, STAR index built in a Slurm job).
