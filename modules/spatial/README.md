# Module: spatial transcriptomics

| Variant | Default pipeline | Why |
|---|---|---|
| Visium | nf-core/spatialvi (pre-release: pin a commit) | Space Ranger + QC + SVGs + reports |
| Visium HD, Xenium, MERSCOPE, CosMx | nf-core/sopa | Segmentation + SpatialData output, many technologies |
| Any (exploratory) | vendor output + SpatialData/squidpy notebooks | Lightweight; parameterized notebooks |

One sample-sheet row = one tissue section. Replicates are counted by `donor`.
Vendor bundles (Xenium/MERSCOPE/CosMx output folders, Space Ranger outs) are raw data:
make them read-only and checksum every file (`make_manifest.py create ... --glob "**/*"`).

**Mini fixture:** a small public demo dataset for your platform, cropped to a small region
with spatialdata; run the pipeline's own `-profile test` first.

**FAIR:** GEO/SRA for sequencing-based data with the `spatial/` folder and images; large image
bundles to BioImage Archive or Zenodo; record panel, slide/area, preservation and section thickness.
