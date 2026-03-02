"""Tests for strategy.adaptive_sma module - all deterministic."""

import pytest
import pandas as pd
import numpy as np
import json
import os
import tempfile
from unittest.mock import patch
from datetime import datetime, timedelta
from strategy.adaptive_sma import AdaptiveSMAStrategy


@pytest.fixture
def mock_data():
    """Generate mock price data for testing."""
    np.random.seed(42)
    dates = pd.date_range('2024-01-01', periods=300, freq='D')
    prices = 100 + np.cumsum(np.random.randn(300) * 0.5)
    
    return pd.DataFrame({
        'Close': prices,
        'Open': prices * 0.99,
        'High': prices * 1.01,
        'Low': prices * 0.98,
        'Volume': np.random.randint(1000000, 5000000, 300)
    }, index=dates)


@pytest.fixture
def temp_state_dir(tmp_path):
    """Create temporary state directory and mock STATE_FILE."""
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    state_file = state_dir / "model_state.json"
    
    with patch('strategy.adaptive_sma.STATE_FILE', str(state_file)):
        yield state_file


def test_strategy_initialization():
    """Test strategy initializes with default parameters."""
    with patch('strategy.adaptive_sma.STATE_FILE', '/nonexistent/path.json'):
        strategy = AdaptiveSMAStrategy()
        
        assert strategy.short_window > 0
        assert strategy.long_window > 0
        assert strategy.short_window < strategy.long_window


def test_generate_signals(mock_data):
    """Test signal generation produces valid output."""
    with patch('strategy.adaptive_sma.STATE_FILE', '/nonexistent/path.json'):
        strategy = AdaptiveSMAStrategy()
        signals = strategy.generate_signals(mock_data)
        
        assert 'Signal' in signals.columns
        assert 'SMA_Short' in signals.columns
        assert 'SMA_Long' in signals.columns
        
        # Signals should be -1, 0, or 1
        assert signals['Signal'].isin([-1, 0, 1]).all()


def test_save_and_load_state(temp_state_dir):
    """Test state persistence round-trip."""
    strategy = AdaptiveSMAStrategy()
    strategy.short_window = 15
    strategy.long_window = 60
    strategy.last_objective = 1.23
    strategy.last_retune_date = "2024-01-15T10:00:00"
    
    strategy.save_state()
    
    assert temp_state_dir.exists()
    
    # Load state in new instance
    strategy2 = AdaptiveSMAStrategy()
    
    assert strategy2.short_window == 15
    assert strategy2.long_window == 60
    assert strategy2.last_objective == 1.23
    assert strategy2.last_retune_date == "2024-01-15T10:00:00"


def test_load_state_corrupted_json(temp_state_dir):
    """Test state loading handles corrupted JSON gracefully."""
    # Write invalid JSON
    with open(temp_state_dir, 'w') as f:
        f.write("{ invalid json")
    
    strategy = AdaptiveSMAStrategy()
    
    # Should fall back to defaults
    assert strategy.short_window > 0
    assert strategy.long_window > 0


def test_load_state_missing_fields(temp_state_dir):
    """Test state loading handles missing fields."""
    # Write state with missing fields
    with open(temp_state_dir, 'w') as f:
        json.dump({"schema_version": 2}, f)
    
    strategy = AdaptiveSMAStrategy()
    
    # Should fall back to defaults
    assert strategy.short_window > 0
    assert strategy.long_window > 0


def test_load_state_version_mismatch(temp_state_dir):
    """Test state loading handles schema version mismatch."""
    # Write state with old schema version
    with open(temp_state_dir, 'w') as f:
        json.dump({
            "schema_version": 1,
            "short_window": 10,
            "long_window": 30
        }, f)
    
    strategy = AdaptiveSMAStrategy()
    
    # Should fall back to defaults due to version mismatch
    assert strategy.short_window == 20  # default
    assert strategy.long_window == 50  # default


def test_should_retune_first_run(temp_state_dir):
    """Test retuning is triggered on first run."""
    strategy = AdaptiveSMAStrategy()
    strategy.last_retune_date = None
    
    should_retune, reason = strategy.should_retune(current_sharpe=1.0)
    
    assert should_retune is True
    assert "first_run" in reason


def test_should_retune_performance_trigger(temp_state_dir):
    """Test retuning is triggered by poor performance."""
    strategy = AdaptiveSMAStrategy()
    strategy.last_retune_date = datetime.now().isoformat()
    
    # Sharpe below threshold should trigger
    should_retune, reason = strategy.should_retune(current_sharpe=-1.0)
    
    assert should_retune is True
    assert "performance_trigger" in reason


def test_should_retune_scheduled_trigger(temp_state_dir):
    """Test retuning is triggered by schedule."""
    strategy = AdaptiveSMAStrategy()
    # Set last retune to 10 days ago
    strategy.last_retune_date = (datetime.now() - timedelta(days=10)).isoformat()
    
    should_retune, reason = strategy.should_retune(current_sharpe=1.5)
    
    assert should_retune is True
    assert "scheduled" in reason


def test_should_not_retune(temp_state_dir):
    """Test retuning is not triggered when not due."""
    strategy = AdaptiveSMAStrategy()
    # Set last retune to 2 days ago
    strategy.last_retune_date = (datetime.now() - timedelta(days=2)).isoformat()
    
    should_retune, reason = strategy.should_retune(current_sharpe=1.5)
    
    assert should_retune is False
    assert "no_trigger" in reason


def test_optimize_parameters(mock_data, temp_state_dir):
    """Test parameter optimization finds valid parameters."""
    strategy = AdaptiveSMAStrategy()
    
    best_short, best_long, best_obj = strategy.optimize_parameters(mock_data)
    
    assert best_short > 0
    assert best_long > 0
    assert best_short < best_long
    assert isinstance(best_obj, float)


def test_optimize_parameters_insufficient_data(temp_state_dir):
    """Test optimization handles insufficient data gracefully."""
    strategy = AdaptiveSMAStrategy()
    
    # Very small dataset
    small_data = pd.DataFrame({
        'Close': [100, 101, 102, 103, 104]
    })
    
    best_short, best_long, best_obj = strategy.optimize_parameters(small_data)
    
    # Should keep current parameters
    assert best_short == strategy.short_window
    assert best_long == strategy.long_window


def test_retune_if_due_performs_optimization(mock_data, temp_state_dir):
    """Test retune_if_due actually performs optimization when due."""
    strategy = AdaptiveSMAStrategy()
    strategy.last_retune_date = None  # Force retune
    
    initial_short = strategy.short_window
    initial_long = strategy.long_window
    
    retuned = strategy.retune_if_due(mock_data, current_sharpe=1.0)
    
    assert retuned is True
    assert strategy.last_retune_date is not None
    # Parameters may or may not change depending on optimization result
    assert strategy.short_window > 0
    assert strategy.long_window > 0


def test_retune_if_due_skips_when_not_due(mock_data, temp_state_dir):
    """Test retune_if_due skips optimization when not due."""
    strategy = AdaptiveSMAStrategy()
    strategy.last_retune_date = datetime.now().isoformat()
    
    initial_short = strategy.short_window
    initial_long = strategy.long_window
    
    retuned = strategy.retune_if_due(mock_data, current_sharpe=1.5)
    
    assert retuned is False
    assert strategy.short_window == initial_short
    assert strategy.long_window == initial_long
