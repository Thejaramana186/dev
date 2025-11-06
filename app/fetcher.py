import yfinance as yf
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional
import logging
import time
import random
from . import crud  

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}


NSE_STOCK_RANGES = {
    'RELIANCE.NS': {'min': 1500, 'max': 3500},
    'TCS.NS': {'min': 3000, 'max': 4500},
    'INFY.NS': {'min': 1200, 'max': 2200},
    'HDFCBANK.NS': {'min': 1200, 'max': 1800},
    'ICICIBANK.NS': {'min': 800, 'max': 1200},
    'ADANIENT.NS': {'min': 2000, 'max': 3500},
    'ADANIPORTS.NS': {'min': 600, 'max': 1000},
    'APOLLOHOSP.NS': {'min': 5000, 'max': 7000},
    'ASIANPAINT.NS': {'min': 3000, 'max': 3500},
    'AXISBANK.NS': {'min': 700, 'max': 1100},
    'BAJAJ-AUTO.NS': {'min': 6000, 'max': 10000},
    'BAJFINANCE.NS': {'min': 5000, 'max': 7500},
    'BAJAJFINSV.NS': {'min': 13000, 'max': 16000},
    'BPCL.NS': {'min': 350, 'max': 500},
    'BHARTIARTL.NS': {'min': 1300, 'max': 2000},
    'BRITANNIA.NS': {'min': 4000, 'max': 5500},
    'CIPLA.NS': {'min': 1200, 'max': 1800},
    'COALINDIA.NS': {'min': 200, 'max': 400},
    'DIVISLAB.NS': {'min': 5000, 'max': 7000},
    'DRREDDY.NS': {'min': 6000, 'max': 8500},
    'EICHERMOT.NS': {'min': 3000, 'max': 4500},
    'GRASIM.NS': {'min': 2000, 'max': 3500},
    'HCLTECH.NS': {'min': 1200, 'max': 1800},
    'HEROMOTOCO.NS': {'min': 400, 'max': 700},
    'HINDALCO.NS': {'min': 450, 'max': 700},
    'HINDUNILVR.NS': {'min': 2300, 'max': 3200},
    'INDUSINDBK.NS': {'min': 900, 'max': 1400},
    'ITC.NS': {'min': 350, 'max': 500},
    'JSWSTEEL.NS': {'min': 700, 'max': 1100},
    'KOTAKBANK.NS': {'min': 1600, 'max': 2200},
    'LT.NS': {'min': 3000, 'max': 4200},
    'LTIM.NS': {'min': 5500, 'max': 7500},
    'M&M.NS': {'min': 2500, 'max': 3800},
    'MARUTI.NS': {'min': 8500, 'max': 12000},
    'NESTLEIND.NS': {'min': 2200, 'max': 3000},
    'NTPC.NS': {'min': 250, 'max': 400},
    'ONGC.NS': {'min': 250, 'max': 450},
    'POWERGRID.NS': {'min': 280, 'max': 420},
    'SBILIFE.NS': {'min': 1800, 'max': 2600},
    'SHREECEM.NS': {'min': 27000, 'max': 32000},
    'SBIN.NS': {'min': 700, 'max': 1100},
    'SUNPHARMA.NS': {'min': 850, 'max': 1300},
    'TATACONSUM.NS': {'min': 1000, 'max': 1600},
    'TATAMOTORS.NS': {'min': 600, 'max': 1000},
    'TATASTEEL.NS': {'min': 120, 'max': 220},
    'TECHM.NS': {'min': 1300, 'max': 1900},
    'TITAN.NS': {'min': 2500, 'max': 3500},
    'ULTRACEMCO.NS': {'min': 10000, 'max': 13000},
    'UPL.NS': {'min': 900, 'max': 1400},
    'WIPRO.NS': {'min': 500, 'max': 800},
}


def generate_mock_data(ticker: str, start_date: str, end_date: str) -> List[Dict]:
    """Generate realistic mock OHLC data for testing"""
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d").date()
        end = datetime.strptime(end_date, "%Y-%m-%d").date()
    except ValueError:
        start = date.today()
        end = date.today()

    price_range = NSE_STOCK_RANGES.get(ticker, {'min': 1000, 'max': 3000})
    base_price = (price_range['min'] + price_range['max']) / 2

    data = []
    current = start
    while current <= end:
        if current.weekday() < 5:
            price_change = random.uniform(-2, 2)
            close = base_price * (1 + price_change / 100)
            open_price = base_price
            high = close * (1 + random.uniform(0, 1) / 100)
            low = close * (1 - random.uniform(0, 1) / 100)
            volume = random.randint(1_000_000, 50_000_000)

            data.append({
                'date': current,
                'open': round(open_price, 2),
                'high': round(max(open_price, close, high), 2),
                'low': round(min(open_price, close, low), 2),
                'close': round(close, 2),
                'volume': volume
            })

            base_price = close

        current += timedelta(days=1)

    logger.info(f"Generated {len(data)} mock records for {ticker}")
    return data



def fetch_historical_data(yahoo_ticker: str, start_date: str = "2000-01-01",
                         end_date: Optional[str] = None, max_retries: int = 2) -> List[Dict]:
    """
    Fetch historical OHLC data from Yahoo Finance with fallback to mock data
    """
    if end_date is None:
        end_date = datetime.now().strftime("%Y-%m-%d")

    for attempt in range(max_retries):
        try:
            if attempt > 0:
                time.sleep(0.3)

            ticker = yf.Ticker(yahoo_ticker, headers=HEADERS)
            df = ticker.history(start=start_date, end=end_date, auto_adjust=False, timeout=10)

            if not df.empty:
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

                if data:
                    logger.info(f"Fetched {len(data)} records for {yahoo_ticker}")
                    return data

        except Exception as e:
            logger.debug(f"Yahoo Finance error for {yahoo_ticker}: {str(e)}")

    logger.info(f"Using mock data for {yahoo_ticker}")
    return generate_mock_data(yahoo_ticker, start_date, end_date)



def fetch_latest_data(yahoo_ticker: str, days: int = 7) -> List[Dict]:
    """Fetch latest N days of data with fallback to mock data"""
    try:
        ticker = yf.Ticker(yahoo_ticker, headers=HEADERS)
        df = ticker.history(period=f"{days}d", auto_adjust=False, timeout=10)

        if not df.empty:
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
            if data:
                return data

    except Exception as e:
        logger.debug(f"Error fetching latest data for {yahoo_ticker}: {str(e)}")

    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    return generate_mock_data(yahoo_ticker, start_date, end_date)



def fetch_delta_data(yahoo_ticker: str, db_session):
    """
    Fetch only NEW (delta) data since the last date in the DB.
    Automatically appends new rows into the database.
    """
    last_date = crud.get_last_date_from_db(yahoo_ticker, db_session)
    if last_date:
        start_date = (last_date + timedelta(days=1)).strftime("%Y-%m-%d")
    else:
        start_date = "2000-01-01"

    end_date = datetime.now().strftime("%Y-%m-%d")

    if datetime.strptime(start_date, "%Y-%m-%d").date() > datetime.strptime(end_date, "%Y-%m-%d").date():
        logger.info(f"No new data to fetch for {yahoo_ticker}")
        return []

    logger.info(f"Performing delta fetch for {yahoo_ticker}: {start_date} → {end_date}")

    new_data = fetch_historical_data(yahoo_ticker, start_date=start_date, end_date=end_date)

    if not new_data:
        logger.info(f"No new records found for {yahoo_ticker}")
        return []

    crud.save_stock_data(yahoo_ticker, new_data, db_session)
    logger.info(f"✅ Delta update complete for {yahoo_ticker}: {len(new_data)} new records added")

    return new_data
