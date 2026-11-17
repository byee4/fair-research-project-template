rule count:
    input:
        bams=expand(f"{OUT}/dedup/{{sample}}.bam", sample=SAMPLES),
        gtf=config["genome"]["annotation"],
    output:
        f"{OUT}/counts/counts_matrix.tsv",
    log:
        f"logs/count/count.log",
    threads: config["threads"]["count"]
    shell:
        "featureCounts -T {threads} -p --countReadPairs -s 2 -a {input.gtf} -o {output}.raw {input.bams} && "
        "python3 scripts/tidy_featurecounts.py {output}.raw {output} && "
        "python3 scripts/write_lineage.py --out {output} --stage counts "
        "--inputs {input.bams} --input-stage dedup"


rule merge_group:
    input:
        lambda w: expand(
            f"{OUT}/dedup/{{sample}}.bam",
            sample=samples.index[samples["group"] == w.group],
        ),
    output:
        f"{OUT}/merged/{{group}}.bedgraph",
    log:
        f"logs/merge_group/{{group}}.log",
    threads: config["threads"].get("merge", 2)
    shell:
        "samtools merge -@ {threads} -o - {input} | bedtools genomecov -ibam - -bg > {output} && "
        "python3 scripts/write_lineage.py --out {output} --stage merged "
        "--inputs {input} --input-stage dedup"


rule diff:
    input:
        counts=rules.count.output,
        sheet=config["samplesheet"],
    output:
        f"{OUT}/diff/diff_results.tsv",
    log:
        f"logs/diff/diff.log",
    threads: 1
    shell:
        "Rscript scripts/diff.R {input.counts} {input.sheet} {output} {threads} && "
        "python3 scripts/write_lineage.py --out {output} --stage diff "
        "--inputs {input.counts} --input-stage counts"
