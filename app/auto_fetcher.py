import time
from app import create_app, db
from app.fetcher import fetch_delta_data

app = create_app()
app.app_context().push()

tickers = ["AAPL", "MSFT", "RELIANCE.NS"]

while True:
    for t in tickers:
        fetch_delta_data(t, db.session)

    print("Waiting 6 hours...")
    time.sleep(21600) 
