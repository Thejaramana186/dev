import yfinance as yf
from datetime import datetime, date
from typing import List, Dict, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def fetch_historical_data(yahoo_ticker: str, start_date: str = "2000-01-01",
                         end_date: Optional[str] = None) -> List[Dict]:
    """
    Fetch historical OHLC data from Yahoo Finance

    Args:
        yahoo_ticker: Yahoo Finance ticker symbol (e.g., 'RELIANCE.NS')
        start_date: Start date in 'YYYY-MM-DD' format
        end_date: End date in 'YYYY-MM-DD' format (default: today)

    Returns:
        List of dictionaries with date, open, high, low, close, volume
    """
    if end_date is None:
        end_date = datetime.now().strftime("%Y-%m-%d")

    try:
        logger.info(f"Fetching data for {yahoo_ticker} from {start_date} to {end_date}")

        # Download data from Yahoo Finance
        ticker = yf.Ticker(yahoo_ticker)
        df = ticker.history(start=start_date, end=end_date, auto_adjust=False)

        if df.empty:
            logger.warning(f"No data found for {yahoo_ticker}")
            return []

        # Convert to list of dictionaries
        data = []
        for idx, row in df.iterrows():
            # Skip rows with NaN values
            if row.isna().any():
                continue

            data.append({
                'date': idx.date(),
                'open': float(row['Open']),
                'high': float(row['High']),
                'low': float(row['Low']),
                'close': float(row['Close']),
                'volume': float(row['Volume'])
            })

        logger.info(f"Successfully fetched {len(data)} records for {yahoo_ticker}")
        return data

    except Exception as e:
        logger.error(f"Error fetching data for {yahoo_ticker}: {str(e)}")
        return []


def fetch_latest_data(yahoo_ticker: str, days: int = 7) -> List[Dict]:
    """
    Fetch latest N days of data

    Args:
        yahoo_ticker: Yahoo Finance ticker symbol
        days: Number of days to fetch (default: 7)

    Returns:
        List of dictionaries with OHLC data
    """
    try:
        ticker = yf.Ticker(yahoo_ticker)
        df = ticker.history(period=f"{days}d", auto_adjust=False)

        if df.empty:
            return []

        data = []
        for idx, row in df.iterrows():
            if row.isna().any():
                continue

            data.append({
                'date': idx.date(),
                'open': float(row['Open']),
                'high': float(row['High']),
                'low': float(row['Low']),
                'close': float(row['Close']),
                'volume': float(row['Volume'])
            })

        return data

    except Exception as e:
        logger.error(f"Error fetching latest data for {yahoo_ticker}: {str(e)}")
        return []
