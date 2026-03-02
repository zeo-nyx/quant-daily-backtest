# Quant Daily Backtest Engine

A production-ready, stateful quantitative research pipeline that fetches daily market data, runs adaptive strategy backtests with parameter optimization, tracks performance history, and automates execution via GitHub Actions with comprehensive CI validation.

This project demonstrates institutional-grade quant research engineering with robust error handling, deterministic testing, and full CI/CD integration.

---

## 🎯 Current Features

### Production-Ready Infrastructure

- **Robust data ingestion** with retry logic, timeout handling, and validation
- **Comprehensive logging** with structured output and error tracking
- **Atomic persistence** preventing partial writes during failures
- **Failure-safe orchestration** with explicit exit codes
- **Deterministic test suite** with 35 test cases (plus 1 optional live test)
- **Schema-versioned state** with automatic migration and validation

### Adaptive Strategy Optimization

- **Hybrid retuning triggers**:
  - Scheduled: automatically every 7 days
  - Performance-based: when Sharpe ratio falls below threshold
- **Bounded grid search** optimization over SMA parameter space
- **Risk-adjusted objective**: maximizes Sharpe ratio minus drawdown penalty
- **Constrained search space**: prevents overfitting with sensible bounds
- **Minimum data requirement**: 200 bars (supports 1-year daily data)

### Performance Analytics

- **Numerically safe metrics** with zero-variance guards
- **Risk-adjusted returns**: Sharpe ratio, max drawdown, total return
- **Composite objective** function for optimization
- **Historical tracking** with append-only CSV

### Automation & CI/CD

- **Daily automated runs** via GitHub Actions (weekdays 22:00 UTC)
- **Deterministic tests** running on every PR/push
- **Optional live API tests** for scheduled smoke testing
- **Artifact validation** before committing results
- **Pip caching** for faster CI/CD execution

---

## Project Structure

```
quant-daily-backtest/
├── config/
│   └── settings.py          # Centralized configuration (bounds, triggers, etc.)
├── strategy/
│   ├── base_strategy.py     # Strategy interface
│   ├── sma_strategy.py      # Basic SMA crossover
│   └── adaptive_sma.py      # Optimization-based adaptive strategy
├── analytics/
│   └── metrics.py           # Numerically safe performance metrics
├── utils/
│   └── data_loader.py       # Data ingestion with retries & validation
├── state/
│   ├── model_state.json     # Versioned parameter state
│   └── performance_history.csv  # Append-only performance log
├── results/
│   ├── latest_metrics.json  # Most recent backtest metrics
│   └── equity_curve.png     # Strategy vs market visualization
├── tests/
│   ├── test_metrics.py      # Deterministic metrics tests
│   ├── test_strategy.py     # Strategy & optimization tests
│   ├── test_data_loader.py  # Data loading tests (mocked)
│   └── test_pipeline.py     # Live API smoke test (optional)
├── run_pipeline.py          # Main orchestration script
├── pytest.ini               # Test configuration
└── .github/workflows/       # CI/CD automation
```

---

## System Workflow

### 1. Data Ingestion

- Downloads market data using `yfinance` with configurable ticker and period
- Implements bounded retries with exponential backoff
- Validates required columns and minimum row count
- Handles network failures gracefully

### 2. Strategy Execution

- Loads versioned state from previous runs (or initializes with defaults)
- Generates trading signals using current SMA parameters
- Applies 1-bar lag to prevent lookahead bias

### 3. Performance Metrics

Computes risk-adjusted metrics with numerical safety:

- **Sharpe Ratio** (annualized, with zero-variance guards)
- **Total Return** (cumulative strategy performance)
- **Maximum Drawdown** (worst peak-to-trough decline)
- **Objective Score** (Sharpe - λ × |MaxDrawdown|)

### 4. Adaptive Optimization

Checks hybrid retune triggers:

- **Scheduled**: Every 7 days since last optimization
- **Performance**: When Sharpe ratio < -0.5

If triggered, performs bounded grid search:

- Short window: 5-50 (step 2)
- Long window: 20-200 (step 5)
- Constraint: short < long
- Objective: Maximize Sharpe - 0.5 × |MaxDrawdown|
- Minimum data: 200 bars required

### 5. Stateful Persistence

- Atomically writes state to temp files, then renames
- Updates performance history (append-only CSV)
- Saves visualization (strategy vs market equity curves)
- Only commits on full success (no partial writes)

---

## Automation Setup

### Daily Pipeline (`daily.yml`)

Runs automatically weekdays at 22:00 UTC:

1. Fetches latest market data
2. Executes strategy with current parameters
3. Checks retune triggers and optimizes if due
4. Validates output artifacts (JSON schema, file existence)
5. Commits results **only on successful validation**
6. Uploads artifacts for audit trail (30-day retention)

### Continuous Integration (`ci.yml`)

On every push/PR:

- **Deterministic tests**: 35 unit/integration tests (mocked data)
- **Code quality**: Flake8 lint checks for syntax errors
- **Test coverage**: Reports line coverage metrics
- **Optional live tests**: Scheduled smoke test against real API

---

## Local Setup & Execution

### Installation

```bash
pip install -r requirements.txt
```

### Run Pipeline

```bash
python run_pipeline.py
```

**Exit codes:**

- `0`: Success
- `1`: Data loading failure
- `2`: Strategy execution failure
- `3`: Persistence failure

### Run Tests

```bash
# All deterministic tests (recommended)
pytest -m "not live"

# Include live API test
pytest

# With coverage
pytest -m "not live" --cov=. --cov-report=term-missing
```

---

## Configuration

All settings in [`config/settings.py`](config/settings.py):

**Data Settings:**

- Ticker, lookback period, interval
- Retry limits, timeout, minimum rows

**Optimization Settings:**

- Parameter bounds and step sizes
- Retune interval (days)
- Performance trigger threshold
- Drawdown penalty weight
- Minimum bars for optimization: 200

**Schema:**

- State version for migration compatibility

---

## Generated Outputs

### Results (regenerated each run)

- `results/latest_metrics.json` - Current performance metrics
- `results/equity_curve.png` - Strategy vs market visualization

### State (persistent, atomically updated)

- `state/model_state.json` - Current parameters, last retune, objective
- `state/performance_history.csv` - Append-only historical log

---

## Core Value Proposition

**Demonstrates production quant engineering:**

- ✅ Robust error handling and failure recovery
- ✅ Comprehensive test coverage (deterministic + optional live)
- ✅ Atomic operations preventing data corruption
- ✅ Versioned state schema with validation
- ✅ Optimization-based adaptation (not heuristic)
- ✅ Risk-adjusted objective functions
- ✅ Full CI/CD pipeline with artifact validation
- ✅ Structured logging and observability
- ✅ Reproducible workflows

---

## 🚀 Roadmap

**Planned Enhancements:**

- Walk-forward optimization with out-of-sample validation
- Transaction costs, slippage, and realistic execution assumptions
- Multi-asset portfolio strategies
- Advanced feature engineering (technical indicators, regime detection)
- ML model integration with periodic retraining
- Interactive dashboard for performance monitoring
- Rolling performance charts and parameter evolution visualization
- Experiment tracking (MLflow/Weights & Biases integration)
- Bayesian optimization for faster parameter search
- Ensemble strategies with allocation optimization

---

## Disclaimer

**For research and educational purposes only.**  
Not financial or investment advice.

---

**Author:** Production-grade quantitative research demonstration
