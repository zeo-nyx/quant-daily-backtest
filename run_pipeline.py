import os
import json
import pandas as pd
import matplotlib.pyplot as plt

from utils.data_loader import load_data
from strategy.adaptive_sma import AdaptiveSMAStrategy
from analytics.metrics import compute_returns, compute_metrics


PERF_HISTORY = "state/performance_history.csv"


def update_performance_history(metrics):
    os.makedirs("state", exist_ok=True)

    new_row = pd.DataFrame([metrics])

    if os.path.exists(PERF_HISTORY):
        history = pd.read_csv(PERF_HISTORY)
        history = pd.concat([history, new_row], ignore_index=True)
    else:
        history = new_row

    history.to_csv(PERF_HISTORY, index=False)


def save_plot(df):
    os.makedirs("results", exist_ok=True)
    plt.figure()
    plt.plot(df["Cumulative_Strategy"])
    plt.title("Equity Curve")
    plt.savefig("results/equity_curve.png")
    plt.close()


def main():

    data = load_data()

    strategy = AdaptiveSMAStrategy()
    signals = strategy.generate_signals(data)

    results = compute_returns(signals)
    metrics = compute_metrics(results)

    # Adapt based on today's Sharpe
    strategy.adapt_parameters(metrics["Sharpe Ratio"])
    strategy.save_state()

    update_performance_history(metrics)
    save_plot(results)

    with open("results/latest_metrics.json", "w") as f:
        json.dump(metrics, f, indent=4)

    print("Stateful pipeline completed.")


if __name__ == "__main__":
    main()