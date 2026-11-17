process TRIM {
    tag "${meta.id}"
    label 'process_medium'
    input:
    tuple val(meta), path(r1), path(r2)
    output:
    tuple val(meta), path("${meta.id}_R{1,2}.trim.fastq.gz"), emit: reads
    tuple val(meta), path("${meta.id}.fastp.json"), emit: json
    script:
    """
    fastp -w ${task.cpus} -i ${r1} -I ${r2} -o ${meta.id}_R1.trim.fastq.gz -O ${meta.id}_R2.trim.fastq.gz -j ${meta.id}.fastp.json
    write_lineage.py --out ${meta.id}_R1.trim.fastq.gz --stage trimmed --inputs ${r1} ${r2} --input-stage raw
    """
}

process ALIGN {
    tag "${meta.id}"
    label 'process_high'
    input:
    tuple val(meta), path(reads)
    path index
    output:
    tuple val(meta), path("${meta.id}.bam"), emit: bam
    script:
    """
    STAR --runThreadN ${task.cpus} --genomeDir ${index} --readFilesIn ${reads} --readFilesCommand zcat \\
         --outSAMtype BAM SortedByCoordinate --outStd BAM_SortedByCoordinate > ${meta.id}.bam
    write_lineage.py --out ${meta.id}.bam --stage aligned --inputs ${reads} --input-stage trimmed
    """
}

process FILTER_MAPQ {
    tag "${meta.id}"
    label 'process_low'
    input:
    tuple val(meta), path(bam)
    val min_mapq
    output:
    tuple val(meta), path("${meta.id}.filtered.bam"), emit: bam
    script:
    """
    samtools view -@ ${task.cpus} -b -q ${min_mapq} ${bam} > ${meta.id}.filtered.bam
    write_lineage.py --out ${meta.id}.filtered.bam --stage filtered --inputs ${bam} --input-stage aligned --param min_mapq=${min_mapq}
    """
}

process DEDUP {
    tag "${meta.id}"
    label 'process_low'
    input:
    tuple val(meta), path(bam)
    output:
    tuple val(meta), path("${meta.id}.dedup.bam"), path("${meta.id}.dedup.bam.bai"), emit: bam
    script:
    """
    samtools collate -@ ${task.cpus} -O -u ${bam} | samtools fixmate -@ ${task.cpus} -m -u - - \\
      | samtools sort -@ ${task.cpus} -u - | samtools markdup -@ ${task.cpus} -r - ${meta.id}.dedup.bam
    samtools index -@ ${task.cpus} ${meta.id}.dedup.bam
    write_lineage.py --out ${meta.id}.dedup.bam --stage dedup --inputs ${bam} --input-stage filtered
    """
}
