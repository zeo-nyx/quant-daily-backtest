import pandas as pd
from strategy.base_strategy import BaseStrategy

class SMAStrategy(BaseStrategy):

    def __init__(self, short_window=20, long_window=50):
        self.short_window = short_window
        self.long_window = long_window

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:

        df = data.copy()

        df["SMA_Short"] = df["Close"].rolling(self.short_window).mean()
        df["SMA_Long"] = df["Close"].rolling(self.long_window).mean()

        df["Signal"] = 0
        df.loc[df["SMA_Short"] > df["SMA_Long"], "Signal"] = 1
        df.loc[df["SMA_Short"] < df["SMA_Long"], "Signal"] = -1

        return df