# Experimental design (pre-registered before data arrive)

Write this BEFORE looking at any data. Validation criteria in `claims/claims.yaml`
must reference the questions and thresholds here.

## Questions
- Q1: ...

## Design
- Conditions, replicates, batches, randomization, blinding
- Expected data sources and delivery dates (core facility, collaborators, public accessions)

## Primary analysis (estimand, model, contrast)
- e.g. DESeq2 `~ batch + condition`, contrast treatment vs control, padj < 0.05

## Pre-specified validation criteria per gate
| Gate | Criterion |
|---|---|
| execution | mini fixture passes; all contracts pass on full data |
| design | replicate correlation > ...; no batch-condition confounding |
| inference | ... |
| biological | positive-control genes move in the expected direction; ... |
| external | replication in <public dataset> / orthogonal assay |

## Deviations
Record any deviation as a `decisions/` file; it re-opens affected gates.
