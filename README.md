# Quant Daily Research Engine

A stateful, self-updating quantitative research pipeline that fetches daily market data, runs adaptive strategy backtests, tracks performance history, updates model parameters based on results, and automates via GitHub Actions with CI validation on every push.

This project showcases production-style quant research engineering with full CI/CD integration.

---

## Project Overview

This repository builds a modular quantitative research system that simulates real systematic strategy evolution over time.

**Key advantages over static backtests:**
- Persistent model state across runs
- Historical performance tracking
- Automatic parameter adaptation on performance degradation
- Daily automated execution
- Comprehensive automated testing

It mirrors institutional quant research workflows, moving beyond notebook experimentation.

---

## Project Structure

quant-daily-research/
├── config/ # Global configuration
├── strategy/ # Adaptive SMA strategy logic
├── analytics/ # Performance metrics
├── utils/ # Data loading utilities
├── state/ # Model state + performance history
├── results/ # Metrics and visualizations
├── tests/ # CI test suite
├── run_pipeline.py # Main pipeline entrypoint
└── .github/workflows/ # CI/CD automation


---

## System Workflow

### 1. Data Ingestion
Downloads and cleans latest market data using `yfinance`.

### 2. Strategy Execution
Runs adaptive SMA crossover strategy to generate long/short signals.

### 3. Backtesting
Calculates strategy returns, benchmark returns, and cumulative performance.

### 4. Performance Metrics
Computes key risk-adjusted metrics:
- Sharpe Ratio
- Total Return
- Maximum Drawdown

### 5. Stateful Adaptation
- Persists SMA parameters in `state/model_state.json`
- Logs performance in `state/performance_history.csv`
- Auto-adjusts parameters if Sharpe < 0
- Saves state for next execution

This creates primitive online learning behavior.

---

## Automation Setup

### Daily Pipeline
Runs automatically every weekday via GitHub Actions:
1. Fetches new data
2. Executes strategy
3. Updates model state
4. Commits results

### Continuous Integration
Every push triggers:
- Dependency installation
- Pytest execution
- Data validation
- Build verification

Ensures deployment-ready reliability.

---

## Local Setup & Execution

```bash
pip install -r requirements.txt
python run_pipeline.py

## Generated Outputs

results/latest_metrics.json
results/equity_curve.png
state/performance_history.csv
state/model_state.json


**Visual outputs include:**
- Equity curve plots
- Rolling performance charts
- Parameter evolution tracking
- Risk metrics dashboard

---

## Core Value Proposition

**Demonstrates production quant engineering:**
- Modular architecture
- OOP strategy design
- Stateful persistence
- Longitudinal performance tracking
- Full CI/CD pipeline
- Reproducible workflows

---

## Planned Enhancements
- Walk-forward optimization
- Transaction costs & slippage
- Multi-asset portfolios
- Advanced feature engineering
- ML model retraining
- Experiment tracking

---

## Disclaimer

For research/educational purposes only.  
**Not investment advice.**

---

**Author:** Systematic quantitative development roadmap
