#!/usr/bin/env nextflow
// Nextflow (DSL2, strict-syntax friendly) skeleton. Mirrors workflow/snakemake.
include { validateParameters } from 'plugin/nf-schema'
include { TRIM; ALIGN; FILTER_MAPQ; DEDUP } from './modules/preprocess'
include { COUNT; MERGE_GROUP; DIFF; QC_SUMMARY } from './modules/quantify'

// Sample-sheet paths are relative to the repo root (params.data_root) so runs are
// identical regardless of launch directory (incl. nf-test's temp dirs).
def resolveData(String p) {
    def f = p.startsWith('/') || p.contains('://') ? file(p) : file("${params.data_root}/${p}")
    if( !f.exists() ) error "Input not found: ${f} (from sample sheet value '${p}')"
    return f
}

workflow {
    validateParameters()

    // The sample sheet is validated by scripts/validate_samplesheet.py (core + assay schema + rules)
    // before every run (infra/tscc/run_pipeline.sbatch), so here we only read it.
    ch_samples = channel
        .fromPath(params.input)
        .splitCsv(header: true, sep: '\t')
        .map { row ->
            def meta = [id: row.sample_id, condition: row.condition, replicate: row.replicate as int,
                        group: row.group ?: null, strandedness: row.strandedness]
            tuple(meta, resolveData(row.fastq_1), resolveData(row.fastq_2))
        }

    TRIM(ch_samples)
    ALIGN(TRIM.out.reads, file(params.star_index))
    FILTER_MAPQ(ALIGN.out.bam, params.min_mapq)
    DEDUP(FILTER_MAPQ.out.bam)

    COUNT(DEDUP.out.bam.map { meta, bam, bai -> bam }.collect(), file(params.gtf))

    // Merge groups: keep merged outputs flowing into QC/reporting (a known agent failure mode).
    ch_groups = DEDUP.out.bam
        .filter { meta, bam, bai -> meta.group }
        .map { meta, bam, bai -> tuple(meta.group, bam) }
        .groupTuple()
    MERGE_GROUP(ch_groups)

    DIFF(COUNT.out.counts, file(params.input))
    QC_SUMMARY(
        TRIM.out.json.map { it[1] }.collect(),
        ALIGN.out.bam.map { it[1] }.collect(),
        FILTER_MAPQ.out.bam.map { it[1] }.collect(),
        DEDUP.out.bam.map { it[1] }.collect(),
        MERGE_GROUP.out.signal.collect(),
        file(params.input)
    )
}
