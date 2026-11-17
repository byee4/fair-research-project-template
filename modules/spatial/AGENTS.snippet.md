## Assay notes: spatial transcriptomics (modules/spatial)
- One row per tissue section. Biological replicates are distinct `donor`s, never sections of one donor.
- Never mix platforms, panels, or preservation methods in one comparison without a decision record.
- Keep images and coordinates together (SpatialData .zarr); never resize/re-register images by hand.
- Before any spatial statistics: confirm tissue detection/alignment in the QC report and say so.
- Segmentation parameters are scientific parameters (policy: change_filter_thresholds → human_approval).
- Use spatialdata-io readers for vendor bundles; record vendor software versions from the bundle.
