import json
import os
import logging
from datetime import datetime
from typing import Tuple, Optional
import pandas as pd
import numpy as np
from strategy.base_strategy import BaseStrategy
from analytics.metrics import compute_returns, compute_metrics
from config.settings import (
    SHORT_WINDOW_MIN, SHORT_WINDOW_MAX, SHORT_WINDOW_STEP,
    LONG_WINDOW_MIN, LONG_WINDOW_MAX, LONG_WINDOW_STEP,
    RETUNE_INTERVAL_DAYS, PERFORMANCE_TRIGGER_SHARPE_THRESHOLD,
    MIN_BARS_FOR_OPTIMIZATION, STATE_SCHEMA_VERSION
)

STATE_FILE = "state/model_state.json"
logger = logging.getLogger(__name__)


class AdaptiveSMAStrategy(BaseStrategy):
    """
    SMA crossover strategy with hybrid optimization-based adaptation.
    
    Retuning triggers:
    - Scheduled: every RETUNE_INTERVAL_DAYS
    - Performance: when rolling Sharpe falls below threshold
    """

    def __init__(self):
        # Default parameters
        self.short_window = 20
        self.long_window = 50
        self.last_retune_date = None
        self.last_objective = None
        self.schema_version = STATE_SCHEMA_VERSION
        
        self.load_state()

    def load_state(self):
        """Load state from disk with validation and fallback."""
        if not os.path.exists(STATE_FILE):
            logger.info("No existing state file found. Using defaults.")
            return
        
        try:
            with open(STATE_FILE, "r") as f:
                state = json.load(f)
            
            # Validate schema version
            if state.get("schema_version") != STATE_SCHEMA_VERSION:
                logger.warning(
                    f"State schema version mismatch: {state.get('schema_version')} != {STATE_SCHEMA_VERSION}. "
                    f"Using defaults and will overwrite on next save."
                )
                return
            
            # Validate required fields
            if "short_window" not in state or "long_window" not in state:
                logger.warning("State missing required fields. Using defaults.")
                return
            
            # Load validated state
            self.short_window = int(state["short_window"])
            self.long_window = int(state["long_window"])
            self.last_retune_date = state.get("last_retune_date")
            self.last_objective = state.get("last_objective")
            
            logger.info(
                f"Loaded state: short={self.short_window}, long={self.long_window}, "
                f"last_retune={self.last_retune_date}, objective={self.last_objective}"
            )
            
        except (json.JSONDecodeError, ValueError, TypeError) as e:
            logger.error(f"Failed to load state: {e}. Using defaults.")
            # Keep defaults set in __init__

    def save_state(self):
        """Save state to disk with schema version."""
        os.makedirs("state", exist_ok=True)
        
        state = {
            "schema_version": STATE_SCHEMA_VERSION,
            "short_window": self.short_window,
            "long_window": self.long_window,
            "last_retune_date": self.last_retune_date,
            "last_objective": self.last_objective
        }
        
        with open(STATE_FILE, "w") as f:
            json.dump(state, f, indent=4)
        
        logger.info(f"Saved state: short={self.short_window}, long={self.long_window}")

    def should_retune(self, current_sharpe: float) -> Tuple[bool, str]:
        """
        Determine if retuning should occur based on hybrid triggers.
        
        Args:
            current_sharpe: Current rolling Sharpe ratio
            
        Returns:
            (should_retune, reason): Boolean and reason string
        """
        # Performance trigger
        if current_sharpe < PERFORMANCE_TRIGGER_SHARPE_THRESHOLD:
            return True, f"performance_trigger (Sharpe={current_sharpe:.3f} < {PERFORMANCE_TRIGGER_SHARPE_THRESHOLD})"
        
        # Scheduled trigger
        if self.last_retune_date is None:
            return True, "first_run"
        
        try:
            last_retune = datetime.fromisoformat(self.last_retune_date)
            days_since_retune = (datetime.now() - last_retune).days
            
            if days_since_retune >= RETUNE_INTERVAL_DAYS:
                return True, f"scheduled (days_since_retune={days_since_retune} >= {RETUNE_INTERVAL_DAYS})"
        except (ValueError, TypeError) as e:
            logger.warning(f"Invalid last_retune_date: {e}. Triggering retune.")
            return True, "invalid_date"
        
        return False, "no_trigger"

    def optimize_parameters(self, data: pd.DataFrame) -> Tuple[int, int, Optional[float]]:
        """
        Grid search over parameter space to find optimal SMA windows.
        
        Args:
            data: Historical price data
            
        Returns:
            (best_short, best_long, best_objective): Optimal parameters and objective.
            If optimization is skipped, objective is None.
        """
        if len(data) < MIN_BARS_FOR_OPTIMIZATION:
            logger.warning(
                f"Insufficient data for optimization: {len(data)} < {MIN_BARS_FOR_OPTIMIZATION}. "
                f"Keeping current parameters."
            )
            return self.short_window, self.long_window, None
        
        logger.info("Starting parameter optimization...")
        
        best_short = self.short_window
        best_long = self.long_window
        best_objective = -np.inf
        
        candidates_tested = 0
        
        # Grid search
        for short in range(SHORT_WINDOW_MIN, SHORT_WINDOW_MAX + 1, SHORT_WINDOW_STEP):
            for long in range(LONG_WINDOW_MIN, LONG_WINDOW_MAX + 1, LONG_WINDOW_STEP):
                # Enforce short < long constraint
                if short >= long:
                    continue
                
                # Skip if windows exceed data length
                if long > len(data):
                    continue
                
                try:
                    # Evaluate this parameter combination
                    test_signals = self._generate_signals_with_params(data, short, long)
                    test_results = compute_returns(test_signals)
                    metrics = compute_metrics(test_results)
                    
                    objective = metrics["Objective"]
                    
                    if objective > best_objective:
                        best_objective = objective
                        best_short = short
                        best_long = long
                    
                    candidates_tested += 1
                    
                except Exception as e:
                    logger.debug(f"Failed to evaluate short={short}, long={long}: {e}")
                    continue
        
        logger.info(
            f"Optimization complete. Tested {candidates_tested} candidates. "
            f"Best: short={best_short}, long={best_long}, objective={best_objective:.4f}"
        )
        
        return best_short, best_long, best_objective

    def _generate_signals_with_params(
        self, data: pd.DataFrame, short_window: int, long_window: int
    ) -> pd.DataFrame:
        """Generate signals with specific parameter values (helper for optimization)."""
        df = data.copy()
        
        df["SMA_Short"] = df["Close"].rolling(short_window).mean()
        df["SMA_Long"] = df["Close"].rolling(long_window).mean()
        
        df["Signal"] = 0
        df.loc[df["SMA_Short"] > df["SMA_Long"], "Signal"] = 1
        df.loc[df["SMA_Short"] < df["SMA_Long"], "Signal"] = -1
        
        return df

    def retune_if_due(self, data: pd.DataFrame, current_sharpe: float) -> bool:
        """
        Check if retuning is due and perform optimization if needed.
        
        Args:
            data: Historical price data
            current_sharpe: Current Sharpe ratio
            
        Returns:
            bool: True if retuning was performed
        """
        should_retune, reason = self.should_retune(current_sharpe)
        
        if not should_retune:
            logger.info(f"Retuning not due: {reason}")
            return False
        
        logger.info(f"Retuning triggered: {reason}")
        
        # Perform optimization
        new_short, new_long, new_objective = self.optimize_parameters(data)

        if new_objective is None:
            logger.info("Retune skipped: insufficient data for optimization window.")
            return False
        
        # Update parameters
        self.short_window = new_short
        self.long_window = new_long
        self.last_objective = new_objective
        self.last_retune_date = datetime.now().isoformat()
        
        logger.info(
            f"Parameters updated: short={self.short_window}, long={self.long_window}, "
            f"objective={self.last_objective:.4f}"
        )
        
        return True

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """Generate trading signals using current SMA parameters."""
        return self._generate_signals_with_params(data, self.short_window, self.long_window)