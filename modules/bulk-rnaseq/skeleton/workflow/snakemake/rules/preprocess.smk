rule trim:
    input:
        r1=lambda w: samples.loc[w.sample, "fastq_1"],
        r2=lambda w: samples.loc[w.sample, "fastq_2"],
    output:
        r1=f"{OUT}/trimmed/{{sample}}_R1.fastq.gz",
        r2=f"{OUT}/trimmed/{{sample}}_R2.fastq.gz",
        json=f"{OUT}/trimmed/{{sample}}.fastp.json",
    log:
        f"logs/trim/{{sample}}.log",
    threads: config["threads"].get("trim", 4)
    shell:
        "fastp -w {threads} -i {input.r1} -I {input.r2} -o {output.r1} -O {output.r2} "
        "-j {output.json} &> {log} && "
        "python3 scripts/write_lineage.py --out {output.r1} --stage trimmed "
        "--inputs {input.r1} {input.r2} --input-stage raw"


rule align:
    input:
        r1=rules.trim.output.r1,
        r2=rules.trim.output.r2,
    output:
        bam=f"{OUT}/aligned/{{sample}}.bam",
    log:
        f"logs/align/{{sample}}.log",
    threads: config["threads"]["align"]
    params:
        index=config["genome"].get("star_index", "data/external/star_index"),
    shell:
        "STAR --runThreadN {threads} --genomeDir {params.index} "
        "--readFilesIn {input.r1} {input.r2} --readFilesCommand zcat "
        "--outSAMtype BAM SortedByCoordinate --outStd BAM_SortedByCoordinate "
        "> {output.bam} 2> {log} && "
        "python3 scripts/write_lineage.py --out {output.bam} --stage aligned "
        "--inputs {input.r1} {input.r2} --input-stage trimmed"


rule filter_mapq:
    input:
        rules.align.output.bam,
    output:
        f"{OUT}/filtered/{{sample}}.bam",
    log:
        f"logs/filter_mapq/{{sample}}.log",
    threads: config["threads"].get("filter", 2)
    params:
        q=config["filters"]["min_mapq"],
    shell:
        "samtools view -@ {threads} -b -q {params.q} {input} > {output} && "
        "python3 scripts/write_lineage.py --out {output} --stage filtered "
        "--inputs {input} --input-stage aligned --param min_mapq={params.q}"


rule dedup:
    input:
        rules.filter_mapq.output,
    output:
        bam=f"{OUT}/dedup/{{sample}}.bam",
        bai=f"{OUT}/dedup/{{sample}}.bam.bai",
    log:
        f"logs/dedup/{{sample}}.log",
    threads: config["threads"].get("dedup", 2)
    shell:
        "samtools collate -@ {threads} -O -u {input} | samtools fixmate -@ {threads} -m -u - - "
        "| samtools sort -@ {threads} -u - | samtools markdup -@ {threads} -r - {output.bam} && "
        "samtools index -@ {threads} {output.bam} && "
        "python3 scripts/write_lineage.py --out {output.bam} --stage dedup "
        "--inputs {input} --input-stage filtered"
