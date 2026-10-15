#!/usr/bin/env sh
# Re-download the public-domain KJV sources listed in data/kjv/SOURCES.md.
set -e
mkdir -p data/kjv/raw
T=$(mktemp -d)
curl -L "https://eBible.org/Scriptures/eng-kjv_vpl.zip" -o "$T/vpl.zip"
unzip -oq "$T/vpl.zip" -d "$T"
cp "$T/eng-kjv_vpl.txt" data/kjv/raw/ebible-eng-kjv_vpl.txt
cp "$T/eng-kjv_about.htm" data/kjv/raw/ebible-eng-kjv_about.htm
curl -L "https://archive.org/download/holybiblecontain00cann/holybiblecontain00cann_djvu.txt" \
  -o data/kjv/raw/phinney-1828-cooperstown-ocr.txt
rm -rf "$T"
