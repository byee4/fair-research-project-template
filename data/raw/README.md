# data/raw — IMMUTABLE

Raw data lands here exactly as received and is never modified. Agents and humans may read only.

On TSCC the real files live on project storage and are symlinked here:
`/tscc/projects/<lab>/<project>/raw/` (backed up) → `data/raw/`.
On AWS, mirror to `s3://<lab-bucket>/<project>/raw/` with Object Lock or a deny-delete bucket policy.

After each delivery:
1. `chmod -R a-w <delivery_dir>`
2. `python3 scripts/make_manifest.py create data/raw/<delivery> --source "<core order / accession>" --glob "<pattern>" --append data/raw/MANIFEST.tsv`
   (use the `raw_globs` in `modules/<assay>/module.yaml`; vendor output bundles: `--glob "**/*"`)
3. `python3 scripts/make_manifest.py verify data/raw/MANIFEST.tsv`
4. Add rows to `config/samples.tsv` (with md5_1/md5_2) and run `python3 scripts/validate_samplesheet.py`
5. Commit MANIFEST.tsv and samples.tsv (never the data).

See `docs/data_intake_checklist.md`.
