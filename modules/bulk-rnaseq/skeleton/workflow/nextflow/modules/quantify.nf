process COUNT {
    label 'process_medium'
    publishDir "${params.outdir}/counts", mode: 'copy'
    input:
    path bams
    path gtf
    output:
    path "counts_matrix.tsv*", emit: counts
    script:
    """
    featureCounts -T ${task.cpus} -p --countReadPairs -s 2 -a ${gtf} -o counts.raw ${bams}
    tidy_featurecounts.py counts.raw counts_matrix.tsv
    write_lineage.py --out counts_matrix.tsv --stage counts --inputs ${bams} --input-stage dedup
    """
}

process MERGE_GROUP {
    tag "${group}"
    label 'process_low'
    publishDir "${params.outdir}/merged", mode: 'copy'
    input:
    tuple val(group), path(bams)
    output:
    path "${group}.bedgraph*", emit: signal
    script:
    """
    samtools merge -@ ${task.cpus} -o - ${bams} | bedtools genomecov -ibam - -bg > ${group}.bedgraph
    write_lineage.py --out ${group}.bedgraph --stage merged --inputs ${bams} --input-stage dedup
    """
}

process DIFF {
    label 'process_low'
    publishDir "${params.outdir}/diff", mode: 'copy'
    input:
    path counts
    path sheet
    output:
    path "diff_results.tsv*"
    script:
    """
    diff.R counts_matrix.tsv ${sheet} diff_results.tsv ${task.cpus}
    write_lineage.py --out diff_results.tsv --stage diff --inputs counts_matrix.tsv --input-stage counts
    """
}

process QC_SUMMARY {
    label 'process_single'
    publishDir "${params.outdir}/qc", mode: 'copy'
    input:
    path trimmed_json
    path aligned
    path filtered
    path dedup
    path merged
    path sheet
    output:
    path "qc_summary.tsv*"
    script:
    """
    # Arrange staged files into the named-stage layout qc_summary.py expects
    mkdir -p qc_in/trimmed qc_in/aligned qc_in/filtered qc_in/dedup
    for f in ${trimmed_json}; do ln -s ../../\$f qc_in/trimmed/\$f; done
    for f in ${aligned};  do ln -s ../../\$f qc_in/aligned/\$f; done
    for f in ${filtered}; do ln -s ../../\$f qc_in/filtered/\${f%.filtered.bam}.bam; done
    for f in ${dedup};    do ln -s ../../\$f qc_in/dedup/\${f%.dedup.bam}.bam; done
    qc_summary.py --sheet ${sheet} --outdir qc_in --out qc_summary.tsv --threads ${task.cpus}
    """
}
