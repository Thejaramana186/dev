from flask_apscheduler import APScheduler
from app.fetcher import fetch_delta_data
from app import db

scheduler = APScheduler()

def scheduled_job():
    with app.app_context():
        tickers = ["AAPL", "MSFT", "RELIANCE.NS"] 
        for t in tickers:
            fetch_delta_data(t, db.session)

def create_app():
    app = Flask(__name__)
    
    

    scheduler.init_app(app)
    scheduler.start()

    
    scheduler.add_job(
        id="daily_fetch",
        func=scheduled_job,
        trigger="interval",
        hours=24
    )

    return app
