#!/usr/bin/env sh
# Re-download the public-domain 1830 edition texts listed in data/bom/SOURCES.md.
set -e
mkdir -p data/bom/1830
curl -L "https://archive.org/download/book-of-mormon-1830-digital-replica/1830%20BoM%200.7%20-%20%5Bno%20annotations%5D_djvu.txt" \
  -o data/bom/1830/jenson-reproduction-1830.txt
curl -L "https://archive.org/download/bookofmormonacco1830smit/bookofmormonacco1830smit_djvu.txt" \
  -o data/bom/1830/pittsburgh-scan-ocr-1830.txt
