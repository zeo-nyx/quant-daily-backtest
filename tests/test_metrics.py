"""Tests for analytics.metrics module - all deterministic."""

import pytest
import pandas as pd
import numpy as np
from analytics.metrics import (
    compute_returns, sharpe_ratio, max_drawdown,
    compute_objective, compute_metrics
)


def test_compute_returns():
    """Test return computation logic."""
    data = {
        'Close': [100, 102, 101, 103, 105],
        'Signal': [0, 1, 1, -1, -1]
    }
    df = pd.DataFrame(data)
    
    result = compute_returns(df)
    
    assert 'Returns' in result.columns
    assert 'Strategy_Returns' in result.columns
    assert 'Cumulative_Market' in result.columns
    assert 'Cumulative_Strategy' in result.columns
    
    # First return should be NaN
    assert pd.isna(result['Returns'].iloc[0])
    
    # At index 1, market cumulative should reflect first realized return (102/100 = 1.02)
    assert result['Cumulative_Market'].iloc[1] == pytest.approx(1.02, abs=0.001)


def test_sharpe_ratio_normal():
    """Test Sharpe ratio with normal returns."""
    returns = pd.Series([0.01, 0.02, -0.01, 0.015, 0.005] * 50)
    
    sharpe = sharpe_ratio(returns, risk_free_rate=0.02)
    
    assert isinstance(sharpe, float)
    assert np.isfinite(sharpe)


def test_sharpe_ratio_zero_variance():
    """Test Sharpe ratio with zero variance (constant returns)."""
    returns = pd.Series([0.01] * 100)
    
    sharpe = sharpe_ratio(returns, risk_free_rate=0.02)
    
    # Should return 0.0 for zero variance
    assert sharpe == 0.0


def test_sharpe_ratio_empty():
    """Test Sharpe ratio with empty series."""
    returns = pd.Series([])
    
    sharpe = sharpe_ratio(returns)
    
    assert sharpe == 0.0


def test_sharpe_ratio_with_nans():
    """Test Sharpe ratio with NaN values."""
    returns = pd.Series([0.01, np.nan, 0.02, np.nan, -0.01])
    
    # dropna before computing
    returns_clean = returns.dropna()
    sharpe = sharpe_ratio(returns_clean)
    
    assert isinstance(sharpe, float)
    assert np.isfinite(sharpe)


def test_max_drawdown_normal():
    """Test max drawdown with normal cumulative returns."""
    cumulative = pd.Series([1.0, 1.1, 1.05, 1.15, 1.12, 1.20])
    
    mdd = max_drawdown(cumulative)
    
    assert isinstance(mdd, float)
    assert mdd <= 0.0  # Drawdown is negative or zero
    assert np.isfinite(mdd)


def test_max_drawdown_no_drawdown():
    """Test max drawdown with monotonically increasing curve."""
    cumulative = pd.Series([1.0, 1.1, 1.2, 1.3, 1.4])
    
    mdd = max_drawdown(cumulative)
    
    assert mdd == 0.0


def test_max_drawdown_empty():
    """Test max drawdown with empty series."""
    cumulative = pd.Series([])
    
    mdd = max_drawdown(cumulative)
    
    assert mdd == 0.0


def test_compute_objective():
    """Test objective function computation."""
    sharpe = 1.5
    max_dd = -0.2
    lambda_penalty = 0.5
    
    objective = compute_objective(sharpe, max_dd, lambda_penalty)
    
    # J = 1.5 - 0.5 * 0.2 = 1.4
    assert objective == pytest.approx(1.4, abs=0.001)


def test_compute_objective_default_lambda():
    """Test objective with default lambda from config."""
    sharpe = 2.0
    max_dd = -0.15
    
    objective = compute_objective(sharpe, max_dd)
    
    assert isinstance(objective, float)
    assert np.isfinite(objective)


def test_compute_metrics_normal():
    """Test full metrics computation with valid data."""
    data = {
        'Close': [100, 102, 101, 103, 105, 107],
        'Signal': [0, 1, 1, 1, -1, -1]
    }
    df = pd.DataFrame(data)
    df = compute_returns(df)
    
    metrics = compute_metrics(df)
    
    assert 'Total Return' in metrics
    assert 'Sharpe Ratio' in metrics
    assert 'Max Drawdown' in metrics
    assert 'Objective' in metrics
    
    assert np.isfinite(metrics['Total Return'])
    assert np.isfinite(metrics['Sharpe Ratio'])
    assert np.isfinite(metrics['Max Drawdown'])
    assert np.isfinite(metrics['Objective'])


def test_compute_metrics_empty_dataframe():
    """Test metrics computation with empty dataframe."""
    df = pd.DataFrame()
    
    with pytest.raises(ValueError, match="empty"):
        compute_metrics(df)


def test_compute_metrics_missing_columns():
    """Test metrics computation with missing required columns."""
    df = pd.DataFrame({'Close': [100, 101, 102]})
    
    with pytest.raises(ValueError, match="missing columns"):
        compute_metrics(df)
