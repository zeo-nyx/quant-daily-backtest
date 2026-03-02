import numpy as np
import pandas as pd

def compute_returns(df: pd.DataFrame):

    df["Returns"] = df["Close"].pct_change()
    df["Strategy_Returns"] = df["Signal"].shift(1) * df["Returns"]

    df["Cumulative_Market"] = (1 + df["Returns"]).cumprod()
    df["Cumulative_Strategy"] = (1 + df["Strategy_Returns"]).cumprod()

    return df


def sharpe_ratio(returns, risk_free_rate=0.02):

    excess_returns = returns - risk_free_rate / 252
    return np.sqrt(252) * excess_returns.mean() / excess_returns.std()


def max_drawdown(cumulative_returns):

    rolling_max = cumulative_returns.cummax()
    drawdown = cumulative_returns / rolling_max - 1
    return drawdown.min()


def compute_metrics(df):

    strategy_returns = df["Strategy_Returns"].dropna()
    cumulative = df["Cumulative_Strategy"]

    metrics = {
        "Total Return": float(cumulative.iloc[-1] - 1),
        "Sharpe Ratio": float(sharpe_ratio(strategy_returns)),
        "Max Drawdown": float(max_drawdown(cumulative))
    }

    return metrics