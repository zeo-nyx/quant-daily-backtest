import json
import os
import pandas as pd
from strategy.base_strategy import BaseStrategy

STATE_FILE = "state/model_state.json"


class AdaptiveSMAStrategy(BaseStrategy):

    def __init__(self):
        self.short_window = 20
        self.long_window = 50
        self.load_state()

    def load_state(self):
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, "r") as f:
                state = json.load(f)
                self.short_window = state["short_window"]
                self.long_window = state["long_window"]

    def save_state(self):
        os.makedirs("state", exist_ok=True)
        with open(STATE_FILE, "w") as f:
            json.dump({
                "short_window": self.short_window,
                "long_window": self.long_window
            }, f, indent=4)

    def adapt_parameters(self, sharpe_ratio):
        # Simple adaptation rule
        if sharpe_ratio < 0:
            self.short_window += 5
            self.long_window += 5

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:

        df = data.copy()

        df["SMA_Short"] = df["Close"].rolling(self.short_window).mean()
        df["SMA_Long"] = df["Close"].rolling(self.long_window).mean()

        df["Signal"] = 0
        df.loc[df["SMA_Short"] > df["SMA_Long"], "Signal"] = 1
        df.loc[df["SMA_Short"] < df["SMA_Long"], "Signal"] = -1

        return df