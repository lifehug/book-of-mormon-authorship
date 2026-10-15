#!/usr/bin/env sh
# Clone or update the private data repo into data/private/.
# Licensed source texts live there (see data/bom/SOURCES.md, section 7). If you do not have
# access, rebuild the directory from the sources instead; the manifests let you verify it.
set -e
REPO="${BOM_DATA_REPO:-git@github.com:lifehug/bom-authorship-data.git}"
if [ -d data/private/.git ]; then
  git -C data/private pull --ff-only
else
  git clone "$REPO" data/private
fi
