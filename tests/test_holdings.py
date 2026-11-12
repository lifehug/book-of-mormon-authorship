"""Every data folder is described in the holdings index (metadata.holdings)."""

import pytest

from metadata.holdings import DESCRIPTIONS, folders


def test_every_data_folder_is_described():
    found = folders()
    if not found:
        pytest.skip("no data/private or data/corpus on this machine")
    missing = [f for f in found if f not in DESCRIPTIONS]
    assert not missing, f"add these to metadata.holdings.DESCRIPTIONS: {missing}"
