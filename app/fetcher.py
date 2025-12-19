import yfinance as yf
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging
import pandas as pd
from . import crud

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



def _last_trading_day() -> datetime:
    """
    Returns the most recent trading day (handles weekends).
    """
    today = datetime.now().date()

    
    if today.weekday() == 5:
        today -= timedelta(days=1)

    
    elif today.weekday() == 6:
        today -= timedelta(days=2)

    return datetime.combine(today, datetime.min.time())



def _clean_row(idx, row) -> Optional[Dict]:
    try:
        open_val = row["Open"]
        high_val = row["High"]
        low_val = row["Low"]
        close_val = row["Close"]
        volume_val = row["Volume"] if "Volume" in row else 0


        if (
            pd.isna(open_val)
            or pd.isna(high_val)
            or pd.isna(low_val)
            or pd.isna(close_val)
        ):
            return None

        return {
            "date": idx.date(),
            "open": float(open_val),
            "high": float(high_val),
            "low": float(low_val),
            "close": float(close_val),
            "volume": int(volume_val) if not pd.isna(volume_val) else 0,
        }

    except Exception as e:
        logger.error(f"❌ Row cleanup error: {e}")
        return None



def _normalize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Yahoo Finance sometimes returns MultiIndex columns.
    This flattens them safely.
    """
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df



def fetch_historical_data(
    yahoo_ticker: str,
    start_date: str = "2000-01-01",
    end_date: Optional[str] = None,
) -> List[Dict]:

    if end_date is None:
        end_date = _last_trading_day().strftime("%Y-%m-%d")


    try:
        df = yf.download(
            yahoo_ticker,
            start=start_date,
            end=end_date,
            auto_adjust=False,
            progress=False,
            threads=False,
        )

        if df.empty:
            logger.warning(f"⚠ EMPTY Yahoo Finance data for {yahoo_ticker}")
            return []

        df = _normalize_dataframe(df)

        data: List[Dict] = []
        for idx, row in df.iterrows():
            cleaned = _clean_row(idx, row)
            if cleaned:
                data.append(cleaned)

        logger.info(f"📈 {yahoo_ticker}: {len(data)} rows fetched")
        return data

    except Exception as e:
        logger.error(f"❌ Error fetching data for {yahoo_ticker}: {e}")
        return []



def fetch_latest_data(yahoo_ticker: str, days: int = 7) -> List[Dict]:

    try:
        df = yf.download(
            yahoo_ticker,
            period=f"{days}d",
            auto_adjust=False,
            progress=False,
            threads=False,
        )

        if df.empty:
            logger.warning(f"⚠ EMPTY latest Yahoo data for {yahoo_ticker}")
            return []

        df = _normalize_dataframe(df)

        data: List[Dict] = []
        for idx, row in df.iterrows():
            cleaned = _clean_row(idx, row)
            if cleaned:
                data.append(cleaned)

        logger.info(f"📈 {yahoo_ticker}: {len(data)} latest rows fetched")
        return data

    except Exception as e:
        logger.error(f"❌ Error fetching latest data for {yahoo_ticker}: {e}")
        return []



def fetch_delta_data(yahoo_ticker: str, db_session) -> List[Dict]:
    """
    Fetch only rows newer than the latest stored date.
    """

    last_date = crud.get_last_date_from_db(yahoo_ticker, db_session)

    if last_date:
        start_date = (last_date + timedelta(days=1)).strftime("%Y-%m-%d")
    else:
        start_date = "2000-01-01"

    end_dt = _last_trading_day()
    end_date = (end_dt + timedelta(days=1)).strftime("%Y-%m-%d")

    if datetime.strptime(start_date, "%Y-%m-%d").date() > end_dt.date():
        logger.info(f"⏩ No new data for {yahoo_ticker}")
        return []

    logger.info(f"🔍 Delta fetch: {yahoo_ticker} | {start_date} → {end_date}")

    new_rows = fetch_historical_data(yahoo_ticker, start_date, end_date)

    if not new_rows:
        logger.info(f"⚠ No new rows found for {yahoo_ticker}")
        return []

    crud.save_stock_data(yahoo_ticker, new_rows, db_session)

    logger.info(f"✅ Saved {len(new_rows)} new rows for {yahoo_ticker}")
    return new_rows
