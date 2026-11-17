#!/usr/bin/env Rscript
# DESeq2 differential expression. Model and contrast are governed by
# policy/authority.yaml (statistics.change_model_or_contrast = human_approval).
suppressPackageStartupMessages(library(DESeq2))
args <- commandArgs(trailingOnly = TRUE)
counts <- read.delim(args[1], row.names = 1, check.names = FALSE)
sheet  <- read.delim(args[2], stringsAsFactors = TRUE)
sheet  <- sheet[match(colnames(counts), sheet$sample_id), ]
stopifnot(identical(as.character(sheet$sample_id), colnames(counts)))
sheet$condition <- relevel(factor(sheet$condition), ref = "control")
dds <- DESeqDataSetFromMatrix(round(as.matrix(counts)), sheet, design = ~ condition)
dds <- DESeq(dds, parallel = FALSE)
res <- results(dds, contrast = c("condition", "treatment", "control"))
out <- data.frame(gene_id = rownames(res), log2fc = res$log2FoldChange,
                  pvalue = res$pvalue, padj = res$padj)
out <- out[!is.na(out$padj), ]
write.table(out, args[3], sep = "\t", quote = FALSE, row.names = FALSE)
