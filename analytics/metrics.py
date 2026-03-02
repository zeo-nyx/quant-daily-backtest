import numpy as np
import pandas as pd
import logging
from config.settings import RISK_FREE_RATE, DRAWDOWN_PENALTY_LAMBDA

logger = logging.getLogger(__name__)


def compute_returns(df: pd.DataFrame):
    """Compute returns and cumulative performance."""
    df["Returns"] = df["Close"].pct_change()
    df["Strategy_Returns"] = df["Signal"].shift(1) * df["Returns"]

    df["Cumulative_Market"] = (1 + df["Returns"]).cumprod()
    df["Cumulative_Strategy"] = (1 + df["Strategy_Returns"]).cumprod()

    return df


def sharpe_ratio(returns, risk_free_rate=None):
    """
    Calculate annualized Sharpe ratio with numerical safety.
    
    Args:
        returns: pd.Series of daily returns
        risk_free_rate: Annual risk-free rate (default from config)
        
    Returns:
        float: Sharpe ratio, or 0.0 if calculation is invalid
    """
    if risk_free_rate is None:
        risk_free_rate = RISK_FREE_RATE
    
    if len(returns) == 0:
        logger.warning("Cannot compute Sharpe ratio: empty returns series.")
        return 0.0
    
    excess_returns = returns - risk_free_rate / 252
    mean_excess = excess_returns.mean()
    std_excess = excess_returns.std()
    
    # Guard against zero or near-zero standard deviation
    if std_excess < 1e-10 or np.isnan(std_excess):
        logger.warning(f"Cannot compute Sharpe ratio: std={std_excess}")
        return 0.0
    
    sharpe = np.sqrt(252) * mean_excess / std_excess
    
    # Guard against NaN/inf
    if not np.isfinite(sharpe):
        logger.warning(f"Sharpe ratio is not finite: {sharpe}")
        return 0.0
    
    return float(sharpe)


def max_drawdown(cumulative_returns):
    """
    Calculate maximum drawdown with numerical safety.
    
    Args:
        cumulative_returns: pd.Series of cumulative returns
        
    Returns:
        float: Maximum drawdown (negative value), or 0.0 if invalid
    """
    if len(cumulative_returns) == 0:
        logger.warning("Cannot compute max drawdown: empty series.")
        return 0.0
    
    rolling_max = cumulative_returns.cummax()
    drawdown = cumulative_returns / rolling_max - 1
    max_dd = drawdown.min()
    
    # Guard against NaN/inf
    if not np.isfinite(max_dd):
        logger.warning(f"Max drawdown is not finite: {max_dd}")
        return 0.0
    
    return float(max_dd)


def compute_objective(sharpe: float, max_dd: float, lambda_penalty: float = None) -> float:
    """
    Compute optimization objective: Sharpe - lambda * |MaxDrawdown|
    
    Args:
        sharpe: Sharpe ratio
        max_dd: Maximum drawdown (negative value)
        lambda_penalty: Penalty weight (default from config)
        
    Returns:
        float: Objective value (higher is better)
    """
    if lambda_penalty is None:
        lambda_penalty = DRAWDOWN_PENALTY_LAMBDA
    
    # max_dd is negative, so we take absolute value for penalty
    objective = sharpe - lambda_penalty * abs(max_dd)
    
    return float(objective)


def compute_metrics(df):
    """
    Compute performance metrics with numerical safety.
    
    Args:
        df: DataFrame with strategy returns and cumulative performance
        
    Returns:
        dict: Metrics dictionary with required fields
        
    Raises:
        ValueError: If dataframe is empty or missing required columns
    """
    if df.empty:
        raise ValueError("Cannot compute metrics: dataframe is empty.")
    
    required_cols = ["Strategy_Returns", "Cumulative_Strategy"]
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Cannot compute metrics: missing columns {missing}")
    
    strategy_returns = df["Strategy_Returns"].dropna()
    cumulative = df["Cumulative_Strategy"]
    
    if len(strategy_returns) == 0:
        raise ValueError("Cannot compute metrics: no valid strategy returns.")
    
    if len(cumulative) == 0:
        raise ValueError("Cannot compute metrics: no cumulative returns.")
    
    sharpe = sharpe_ratio(strategy_returns)
    max_dd = max_drawdown(cumulative)
    total_return = float(cumulative.iloc[-1] - 1)
    
    metrics = {
        "Total Return": total_return,
        "Sharpe Ratio": sharpe,
        "Max Drawdown": max_dd,
        "Objective": compute_objective(sharpe, max_dd)
    }

    return metrics