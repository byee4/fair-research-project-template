#!/usr/bin/env python3
"""Convert featureCounts output to gene_id x sample_id matrix (columns renamed from BAM paths)."""

import re
import sys

import pandas as pd

raw, out = sys.argv[1], sys.argv[2]
df = pd.read_csv(raw, sep="\t", comment="#")
df = df.drop(columns=["Chr", "Start", "End", "Strand", "Length"]).rename(columns={"Geneid": "gene_id"})
df.columns = ["gene_id"] + [re.sub(r"(\.dedup)?\.bam$", "", c.split("/")[-1]) for c in df.columns[1:]]
df.to_csv(out, sep="\t", index=False)
