#!/usr/bin/env sh
# Rebuild every derived file under data/bom from the fetched sources (see data/bom/SOURCES.md).
set -e
E=data/bom/1830/edition_1830.jsonl
uv run python -m ingest.edition_1830 data/bom/1830/jenson-reproduction-1830.txt -o $E
mkdir -p data/bom/reports
for d in printers original; do
  uv run python -m ingest.align $E data/private/bom/jsp_$d.jsonl -o data/bom/align_$d.jsonl \
    --paragraphs data/bom/align_${d}_paragraphs.jsonl --report data/bom/reports/align_$d.md --label "$d manuscript"
  uv run python -m ingest.diff_report $E data/private/bom/jsp_$d.jsonl -o data/bom/diff_$d.jsonl \
    --report data/bom/reports/diff_$d.md --label "$d manuscript vs 1830"
done
uv run python -m ingest.extant data/private/bom/jsp_original.jsonl data/bom/align_original.jsonl -o data/bom/reports/original_extant.md
uv run python -m metadata.manifest build data/bom -o data/manifests/bom.jsonl
uv run python -m metadata.manifest build data/private/bom -o data/manifests/bom-private.jsonl
