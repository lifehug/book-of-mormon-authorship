#!/usr/bin/env sh
# Clone or update the private data repo into data/private/.
# Licensed source texts live there (see data/bom/SOURCES.md, section 7). If you do not have
# access, rebuild the directory from the sources instead; the manifests let you verify it.
# Large scans are stored with Git LFS (see data/private/.gitattributes), so git-lfs must be
# installed; without it those files arrive as ~130-byte pointer files and fail the manifests.
set -e
REPO="${BOM_DATA_REPO:-git@github.com:lifehug/bom-authorship-data.git}"
if [ -d data/private/.git ]; then
  git -C data/private pull --ff-only
else
  git clone "$REPO" data/private
fi
git -C data/private lfs install --local
git -C data/private lfs pull
