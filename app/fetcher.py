import yfinance as yf
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging
from . import crud

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------
# CLEAN ROW EXTRACTOR
# ---------------------------------------------------------
def _clean_row(idx, row):
    """Convert a Yahoo Finance row into a safe Python dict."""

    try:
        open_val = float(row["Open"]) if row["Open"] is not None else 0
        high_val = float(row["High"]) if row["High"] is not None else 0
        low_val = float(row["Low"]) if row["Low"] is not None else 0
        close_val = float(row["Close"]) if row["Close"] is not None else 0
        volume_val = float(row.get("Volume", 0) or 0)

        return {
            "date": idx.to_pydatetime().date(),
            "open": open_val,
            "high": high_val,
            "low": low_val,
            "close": close_val,
            "volume": volume_val,
        }

    except Exception as e:
        logger.error(f"❌ Row cleanup error: {e}")
        return None


# ---------------------------------------------------------
# FETCH HISTORICAL DATA
# ---------------------------------------------------------
def fetch_historical_data(
    yahoo_ticker: str,
    start_date: str = "2000-01-01",
    end_date: Optional[str] = None
) -> List[Dict]:

    if end_date is None:
        end_date = datetime.now().strftime("%Y-%m-%d")

    try:
        df = yf.download(
            yahoo_ticker,
            start=start_date,
            end=end_date,
            auto_adjust=False,
            progress=False,
            threads=False  # prevents rare yfinance thread crashes
        )

        if df.empty:
            logger.warning(f"⚠ EMPTY Yahoo Finance data for {yahoo_ticker}")
            return []

        data = []
        for idx, row in df.iterrows():
            cleaned = _clean_row(idx, row)
            if cleaned:
                data.append(cleaned)

        logger.info(f"📈 {yahoo_ticker}: {len(data)} rows fetched")
        return data

    except Exception as e:
        logger.error(f"❌ Error fetching data for {yahoo_ticker}: {e}")
        return []


# ---------------------------------------------------------
# FETCH LATEST N DAYS
# ---------------------------------------------------------
def fetch_latest_data(yahoo_ticker: str, days: int = 7) -> List[Dict]:

    try:
        df = yf.download(
            yahoo_ticker,
            period=f"{days}d",
            auto_adjust=False,
            progress=False,
            threads=False
        )

        if df.empty:
            logger.warning(f"⚠ EMPTY latest Yahoo data for {yahoo_ticker}")
            return []

        data = []
        for idx, row in df.iterrows():
            cleaned = _clean_row(idx, row)
            if cleaned:
                data.append(cleaned)

        return data

    except Exception as e:
        logger.error(f"❌ Error fetching latest data for {yahoo_ticker}: {e}")
        return []


# ---------------------------------------------------------
# DELTA FETCH (ONLY NEW ROWS)
# ---------------------------------------------------------
def fetch_delta_data(yahoo_ticker: str, db_session):
    """
    Fetch only new rows since the last saved date in DB.
    """

    last_date = crud.get_last_date_from_db(yahoo_ticker, db_session)

    if last_date:
        start_date = (last_date + timedelta(days=1)).strftime("%Y-%m-%d")
    else:
        start_date = "2000-01-01"

    end_date = datetime.now().strftime("%Y-%m-%d")

    # No need to fetch if DB is already up-to-date
    if datetime.strptime(start_date, "%Y-%m-%d").date() > datetime.strptime(end_date, "%Y-%m-%d").date():
        logger.info(f"⏩ No new data for {yahoo_ticker}")
        return []

    logger.info(f"🔍 Delta fetch: {yahoo_ticker} | {start_date} → {end_date}")

    new_rows = fetch_historical_data(yahoo_ticker, start_date, end_date)

    if not new_rows:
        logger.info(f"⚠ No new rows found for {yahoo_ticker}")
        return []

    # Save into database
    crud.save_stock_data(yahoo_ticker, new_rows, db_session)

    logger.info(f"✅ Saved {len(new_rows)} new rows for {yahoo_ticker}")
    return new_rows
