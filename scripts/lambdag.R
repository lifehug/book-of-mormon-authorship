#!/usr/bin/env Rscript
# BOM-96 (exploratory): LambdaG (Nini et al., arXiv 2403.08462) from the authors' package
# `idiolect`, on the texts and pairs written by `python -m eval.nobody prepare`.
# For each questioned book: its candidates' known texts as K, every other known text as the
# reference population. Content masking is the package's POSnoise (spaCy en_core_web_sm).
# Resumes: books already in the output are skipped.
# Usage: KMP_DUPLICATE_LIB_OK=TRUE RETICULATE_PYTHON=.venv/bin/python Rscript scripts/lambdag.R [N books]
suppressMessages({library(idiolect); library(quanteda); library(jsonlite)})
work <- "data/corpus/nobody"
out <- file.path(work, "lambdag.csv")
rows <- stream_in(file(file.path(work, "texts.jsonl")), verbose = FALSE)
pairs <- fromJSON(file.path(work, "pairs.json"))
masked_path <- file.path(work, "masked.rds")
if (file.exists(masked_path)) {
  sents <- readRDS(masked_path)
} else {
  # masked in batches: the whole set at once died without a message (2026-11-14)
  parts <- list()
  for (i in seq(1, nrow(rows), by = 20)) {
    j <- min(i + 19, nrow(rows))
    x <- corpus(rows$text[i:j], docnames = rows$id[i:j])
    docvars(x, "author") <- rows$author[i:j]
    docvars(x, "role") <- rows$role[i:j]
    parts[[length(parts) + 1]] <- tokenize_sents(contentmask(x))
    cat(sprintf("masked %d/%d\n", j, nrow(rows)))
  }
  sents <- do.call(c, parts)
  saveRDS(sents, masked_path)
}
done <- if (file.exists(out)) unique(read.csv(out)$Q) else character(0)
books <- setdiff(unique(pairs$book), sub("^q:", "", done))
args <- commandArgs(trailingOnly = TRUE)
if (length(args)) books <- head(books, as.integer(args[1]))
k_all <- tokens_subset(sents, role == "k")
for (b in books) {
  t0 <- Sys.time()
  cands <- pairs$candidate[pairs$book == b]
  q <- tokens_subset(sents, role == "q" & author == b)
  k <- tokens_subset(k_all, author %in% cands)
  ref <- tokens_subset(k_all, !(author %in% cands))
  res <- lambdaG(q, k, ref, N = 10, r = 30)
  res <- data.frame(Q = res$Q, K = res$K, target = res$target, score = res$score)
  write.table(res, out, sep = ",", row.names = FALSE, col.names = !file.exists(out), append = file.exists(out))
  cat(sprintf("%s: %d candidates, %.1f s\n", b, length(cands), as.numeric(difftime(Sys.time(), t0, units = "secs"))))
}
