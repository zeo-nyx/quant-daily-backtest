"""Live API tests - marked for optional execution."""

import pytest
from utils.data_loader import load_data


@pytest.mark.live
def test_data_loads():
    """Test that live data can be loaded from Yahoo Finance."""
    df = load_data()
    assert not df.empty
    assert "Close" in df.columns
    assert len(df) >= 100  # Should have sufficient data