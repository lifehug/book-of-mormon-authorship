# Jockers et al. (2008) NSC with the authors' own tool, R's pamr, on their deposited counts
# (BOM-22). Called by `python -m eval.replicate jockers-pamr`, which passes:
#   args[1] = their counts (gzipped), args[2] = file of the 110 words, args[3] = output CSV,
#   args[4] = seed. Writes one row per chapter: threshold, first and second choice.
args <- commandArgs(trailingOnly = TRUE)
.libPaths(c(file.path(Sys.getenv("HOME"), ".R/library"), .libPaths()))
suppressMessages(library(pamr))
m <- read.table(gzfile(args[1]), header = TRUE, sep = "\t", quote = "\"", check.names = FALSE)
words <- readLines(args[2])
rel <- as.matrix(m) / rowSums(as.matrix(m))
rel <- rel[, words]
prefix <- sub("[0-9.]+$", "", rownames(rel))
map <- c(Barlow = "barlow", Cowdrey = "cowdery", Isaiah = "isaiah_malachi",
         Malachi = "isaiah_malachi", Longfellow = "longfellow", Pratt = "pratt",
         Rigdon = "rigdon", Spaulding = "spalding")
known <- prefix != "Unknown"
x <- t(rel[known, ]); y <- map[prefix[known]]; chap <- t(rel[!known, ])
set.seed(as.integer(args[4]))
fit <- pamr.train(list(x = x, y = factor(y)))
cv <- pamr.cv(fit, list(x = x, y = factor(y)))
best <- cv$threshold[which.min(cv$error)]
cat("cv threshold", best, "error", min(cv$error), "\n")
out <- NULL
for (th in c(best, 0.44)) {
  post <- pamr.predict(fit, chap, threshold = th, type = "posterior")
  ord <- t(apply(post, 1, function(p) names(sort(p, decreasing = TRUE))[1:2]))
  out <- rbind(out, data.frame(threshold = th, first = ord[, 1], second = ord[, 2]))
}
write.csv(out, args[3], row.names = FALSE)
