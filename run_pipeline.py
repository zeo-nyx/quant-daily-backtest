import os
import sys
import json
import logging
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

from utils.data_loader import load_data, DataLoadError
from strategy.adaptive_sma import AdaptiveSMAStrategy
from analytics.metrics import compute_returns, compute_metrics

PERF_HISTORY = "state/performance_history.csv"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def atomic_write(target_path: str, content: str):
    """
    Write content atomically by writing to temp file then renaming.
    
    Args:
        target_path: Final destination path
        content: Content to write
    """
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    temp_path = target_path + ".tmp"
    
    with open(temp_path, "w") as f:
        f.write(content)
    
    # Atomic rename (on Windows, need to remove target first)
    if os.path.exists(target_path):
        os.remove(target_path)
    os.rename(temp_path, target_path)


def update_performance_history(metrics):
    """Update performance history CSV with append-only behavior."""
    os.makedirs("state", exist_ok=True)

    # Add timestamp to metrics
    metrics_with_time = metrics.copy()
    metrics_with_time["timestamp"] = datetime.now().isoformat()
    
    new_row = pd.DataFrame([metrics_with_time])

    if os.path.exists(PERF_HISTORY):
        history = pd.read_csv(PERF_HISTORY)
        history = pd.concat([history, new_row], ignore_index=True)
    else:
        history = new_row

    # Atomic write
    temp_path = PERF_HISTORY + ".tmp"
    history.to_csv(temp_path, index=False)
    
    if os.path.exists(PERF_HISTORY):
        os.remove(PERF_HISTORY)
    os.rename(temp_path, PERF_HISTORY)
    
    logger.info(f"Updated performance history ({len(history)} records)")


def save_plot(df):
    """Generate and save equity curve plot."""
    os.makedirs("results", exist_ok=True)
    
    plt.figure(figsize=(10, 6))
    plt.plot(df.index, df["Cumulative_Strategy"], label="Strategy", linewidth=2)
    plt.plot(df.index, df["Cumulative_Market"], label="Market (Buy & Hold)", linewidth=1, alpha=0.7)
    plt.title("Equity Curve: Strategy vs Market")
    plt.xlabel("Date")
    plt.ylabel("Cumulative Return")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    plot_path = "results/equity_curve.png"
    plt.savefig(plot_path, dpi=100)
    plt.close()
    
    logger.info(f"Saved equity curve plot to {plot_path}")


def main():
    """
    Execute stateful pipeline with failure-safe orchestration.
    
    Exit codes:
        0: Success
        1: Data loading failure
        2: Strategy execution failure
        3: Persistence failure
    """
    logger.info("=" * 60)
    logger.info("Starting stateful backtest pipeline")
    logger.info("=" * 60)
    
    try:
        # Stage 1: Load data
        logger.info("Stage 1: Loading market data...")
        data = load_data()
        logger.info(f"Loaded {len(data)} bars of data")
        
    except DataLoadError as e:
        logger.error(f"Data loading failed: {e}")
        logger.error("Pipeline aborted. No state changes made.")
        sys.exit(1)
    
    try:
        # Stage 2: Generate signals
        logger.info("Stage 2: Initializing strategy and generating signals...")
        strategy = AdaptiveSMAStrategy()
        signals = strategy.generate_signals(data)
        
        # Stage 3: Compute returns and metrics
        logger.info("Stage 3: Computing returns and metrics...")
        results = compute_returns(signals)
        metrics = compute_metrics(results)
        
        logger.info(f"Performance metrics:")
        logger.info(f"  Total Return: {metrics['Total Return']:.4f}")
        logger.info(f"  Sharpe Ratio: {metrics['Sharpe Ratio']:.4f}")
        logger.info(f"  Max Drawdown: {metrics['Max Drawdown']:.4f}")
        logger.info(f"  Objective: {metrics['Objective']:.4f}")
        
        # Stage 4: Adaptive retuning
        logger.info("Stage 4: Checking if parameter retuning is due...")
        retuned = strategy.retune_if_due(data, metrics["Sharpe Ratio"])
        
        if retuned:
            logger.info("Parameters were retuned. Regenerating signals with new parameters...")
            # Regenerate with new parameters
            signals = strategy.generate_signals(data)
            results = compute_returns(signals)
            metrics = compute_metrics(results)
            
            logger.info(f"Updated performance metrics:")
            logger.info(f"  Total Return: {metrics['Total Return']:.4f}")
            logger.info(f"  Sharpe Ratio: {metrics['Sharpe Ratio']:.4f}")
            logger.info(f"  Max Drawdown: {metrics['Max Drawdown']:.4f}")
            logger.info(f"  Objective: {metrics['Objective']:.4f}")
        
    except Exception as e:
        logger.error(f"Strategy execution failed: {e}", exc_info=True)
        logger.error("Pipeline aborted. No state changes made.")
        sys.exit(2)
    
    try:
        # Stage 5: Persist results atomically
        logger.info("Stage 5: Persisting results...")
        
        # Save state
        strategy.save_state()
        
        # Save metrics
        metrics_json = json.dumps(metrics, indent=4)
        atomic_write("results/latest_metrics.json", metrics_json)
        logger.info("Saved latest metrics")
        
        # Update history
        update_performance_history(metrics)
        
        # Save plot
        save_plot(results)
        
    except Exception as e:
        logger.error(f"Persistence failed: {e}", exc_info=True)
        logger.error("Some outputs may not have been saved.")
        sys.exit(3)
    
    logger.info("=" * 60)
    logger.info("Pipeline completed successfully")
    logger.info("=" * 60)
    sys.exit(0)


if __name__ == "__main__":
    main()