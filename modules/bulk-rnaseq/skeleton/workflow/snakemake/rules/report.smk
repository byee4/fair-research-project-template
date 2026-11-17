rule qc_summary:
    input:
        raw=[samples.loc[s, "fastq_1"] for s in SAMPLES],
        trimmed=expand(f"{OUT}/trimmed/{{sample}}.fastp.json", sample=SAMPLES),
        aligned=expand(f"{OUT}/aligned/{{sample}}.bam", sample=SAMPLES),
        filtered=expand(f"{OUT}/filtered/{{sample}}.bam", sample=SAMPLES),
        dedup=expand(f"{OUT}/dedup/{{sample}}.bam", sample=SAMPLES),
        merged=expand(f"{OUT}/merged/{{group}}.bedgraph", group=GROUPS),
        sheet=config["samplesheet"],
    output:
        f"{OUT}/qc/qc_summary.tsv",
    log:
        "logs/qc_summary.log",
    threads: 1
    params:
        outdir=lambda wildcards, output: os.path.dirname(os.path.dirname(output[0])),
    shell:
        # qc_summary.py must emit one row per (sample, stage) using ONLY the named
        # stage inputs, plus one row per merge group. Contract: contracts/data_products.yaml
        "python3 scripts/qc_summary.py --sheet {input.sheet} --outdir {params.outdir} --out {output} --threads {threads} &> {log}"
