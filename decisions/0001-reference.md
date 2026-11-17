# 0001 — Reference genome and annotation

- Date: YYYY-MM-DD
- Domain: parameters
- Authority level: human_approval
- Proposed by: <name / agent during project interview>
- Approved by: PENDING

## Context
Alignment, quantification, and annotation of results depend on one reference build and
annotation version (all sequencing-based assays; imaging assays use the panel's annotation).

## Options considered
1. <build + annotation the lab uses for this organism, e.g. GRCh38 + GENCODE vNN>
2. <alternative>

## Decision and rule/evidence applied
<choice>, matching lab standard / comparison datasets. Checksums in data/external/MANIFEST.tsv.

## Uncertainty
Chromosome naming (chr1 vs 1) must match across FASTA, GTF, and any external data.

## Consequences / re-validation triggered
Any change re-opens all gates for every claim.
