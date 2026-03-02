import yfinance as yf
import pandas as pd
from config.settings import TICKER, LOOKBACK_PERIOD, INTERVAL

def load_data() -> pd.DataFrame:

    df = yf.download(
        TICKER,
        period=LOOKBACK_PERIOD,
        interval=INTERVAL,
        auto_adjust=True
    )

    df = df.dropna()
    return df