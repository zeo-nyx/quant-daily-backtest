import yfinance as yf
import pandas as pd
import time
import logging
from config.settings import (
    TICKER, LOOKBACK_PERIOD, INTERVAL,
    MAX_RETRIES, RETRY_DELAY_SECONDS, REQUEST_TIMEOUT_SECONDS,
    MIN_REQUIRED_ROWS
)

logger = logging.getLogger(__name__)


class DataLoadError(Exception):
    """Raised when data loading fails after all retries."""
    pass


def validate_dataframe(df: pd.DataFrame) -> None:
    """Validate that dataframe has required columns and sufficient rows."""
    required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
    
    if df.empty:
        raise DataLoadError("Downloaded dataframe is empty.")
    
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        raise DataLoadError(f"Missing required columns: {missing_cols}")
    
    if len(df) < MIN_REQUIRED_ROWS:
        raise DataLoadError(
            f"Insufficient data: {len(df)} rows, minimum {MIN_REQUIRED_ROWS} required."
        )


def load_data() -> pd.DataFrame:
    """
    Load data with retries, timeout, and validation.
    
    Returns:
        pd.DataFrame: Validated market data with OHLCV columns.
        
    Raises:
        DataLoadError: If data cannot be loaded after all retries or fails validation.
    """
    last_error = None
    
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.info(f"Attempting to download {TICKER} data (attempt {attempt}/{MAX_RETRIES})...")
            
            df = yf.download(
                TICKER,
                period=LOOKBACK_PERIOD,
                interval=INTERVAL,
                auto_adjust=True,
                progress=False,
                timeout=REQUEST_TIMEOUT_SECONDS
            )
            
            # Remove rows with any NaN values
            df = df.dropna()
            
            # Validate the result
            validate_dataframe(df)
            
            logger.info(f"Successfully loaded {len(df)} rows of data for {TICKER}.")
            return df
            
        except Exception as e:
            last_error = e
            logger.warning(
                f"Download attempt {attempt}/{MAX_RETRIES} failed: {type(e).__name__}: {e}"
            )
            
            if attempt < MAX_RETRIES:
                logger.info(f"Retrying in {RETRY_DELAY_SECONDS} seconds...")
                time.sleep(RETRY_DELAY_SECONDS)
            else:
                logger.error("All retry attempts exhausted.")
    
    # If we get here, all retries failed
    raise DataLoadError(
        f"Failed to load data after {MAX_RETRIES} attempts. Last error: {last_error}"
    )