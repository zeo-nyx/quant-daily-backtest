"""Tests for utils.data_loader module - deterministic with mocks."""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
from utils.data_loader import load_data, validate_dataframe, DataLoadError


def test_validate_dataframe_valid():
    """Test validation passes for valid dataframe."""
    df = pd.DataFrame({
        'Open': np.random.rand(200),
        'High': np.random.rand(200),
        'Low': np.random.rand(200),
        'Close': np.random.rand(200),
        'Volume': np.random.randint(1000, 10000, 200)
    })
    
    # Should not raise
    validate_dataframe(df)


def test_validate_dataframe_empty():
    """Test validation fails for empty dataframe."""
    df = pd.DataFrame()
    
    with pytest.raises(DataLoadError, match="empty"):
        validate_dataframe(df)


def test_validate_dataframe_missing_columns():
    """Test validation fails for missing required columns."""
    df = pd.DataFrame({
        'Close': [100, 101, 102],
        'Volume': [1000, 1100, 1200]
    })
    
    with pytest.raises(DataLoadError, match="Missing required columns"):
        validate_dataframe(df)


def test_validate_dataframe_insufficient_rows():
    """Test validation fails for insufficient rows."""
    df = pd.DataFrame({
        'Open': [100],
        'High': [101],
        'Low': [99],
        'Close': [100],
        'Volume': [1000]
    })
    
    with pytest.raises(DataLoadError, match="Insufficient data"):
        validate_dataframe(df)


@patch('utils.data_loader.yf.download')
def test_load_data_success(mock_download):
    """Test successful data loading."""
    # Mock successful download
    mock_df = pd.DataFrame({
        'Open': np.random.rand(200) * 100 + 100,
        'High': np.random.rand(200) * 100 + 100,
        'Low': np.random.rand(200) * 100 + 100,
        'Close': np.random.rand(200) * 100 + 100,
        'Volume': np.random.randint(1000000, 5000000, 200)
    })
    mock_download.return_value = mock_df
    
    result = load_data()
    
    assert not result.empty
    assert len(result) >= 100  # MIN_REQUIRED_ROWS
    assert 'Close' in result.columns
    mock_download.assert_called_once()


@patch('utils.data_loader.yf.download')
def test_load_data_retry_on_failure(mock_download):
    """Test data loading retries on failure."""
    # First attempt fails, second succeeds
    mock_df = pd.DataFrame({
        'Open': np.random.rand(200) * 100 + 100,
        'High': np.random.rand(200) * 100 + 100,
        'Low': np.random.rand(200) * 100 + 100,
        'Close': np.random.rand(200) * 100 + 100,
        'Volume': np.random.randint(1000000, 5000000, 200)
    })
    
    mock_download.side_effect = [
        Exception("Network error"),
        mock_df
    ]
    
    result = load_data()
    
    assert not result.empty
    assert mock_download.call_count == 2


@patch('utils.data_loader.yf.download')
@patch('utils.data_loader.time.sleep')  # Mock sleep to avoid delay in tests
def test_load_data_all_retries_fail(mock_sleep, mock_download):
    """Test data loading raises after all retries fail."""
    # All attempts fail
    mock_download.side_effect = Exception("Persistent network error")
    
    with pytest.raises(DataLoadError, match="Failed to load data"):
        load_data()
    
    # Should attempt MAX_RETRIES times
    assert mock_download.call_count == 3  # MAX_RETRIES = 3


@patch('utils.data_loader.yf.download')
def test_load_data_handles_nans(mock_download):
    """Test data loading handles and removes NaN values."""
    # Mock data with NaNs
    mock_df = pd.DataFrame({
        'Open': [100, 101, np.nan, 103] + list(np.random.rand(200) * 100 + 100),
        'High': [101, 102, 104, 105] + list(np.random.rand(200) * 100 + 100),
        'Low': [99, 100, 102, np.nan] + list(np.random.rand(200) * 100 + 100),
        'Close': [100, 101, 103, 104] + list(np.random.rand(200) * 100 + 100),
        'Volume': [1000, 1100, 1200, 1300] + list(np.random.randint(1000000, 5000000, 200))
    })
    mock_download.return_value = mock_df
    
    result = load_data()
    
    # NaN rows should be dropped
    assert not result.isnull().any().any()
    assert len(result) < len(mock_df)  # Some rows were dropped
