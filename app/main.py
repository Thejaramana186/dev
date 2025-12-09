from fastapi import FastAPI, Depends, Request, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import csv
import os
from pathlib import Path
import time
import asyncio

from apscheduler.schedulers.background import BackgroundScheduler

from app.db import engine, get_db, Base
from app.models import Company, DailyOHLC
from app import crud, fetcher
from prometheus_fastapi_instrumentator import Instrumentator


# -------------------------------
# INITIAL SETUP
# -------------------------------

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Nifty 50 Stock Data Fetcher")
instrumentator = Instrumentator().instrument(app).expose(app)

BASE_DIR = Path(__file__).resolve().parent

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


# -------------------------------
# CSV LOADER
# -------------------------------

def load_companies_from_csv(db: Session):
    """Load company list from tickers.csv into DB."""
    csv_path = BASE_DIR.parent / "tickers.csv"
    if not csv_path.exists():
        return {"error": "tickers.csv not found"}

    loaded = 0
    with open(csv_path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            crud.get_or_create_company(
                db,
                symbol=row["symbol"],
                name=row["name"],
                yahoo_ticker=row["yahoo_ticker"],
            )
            loaded += 1

    return {"loaded": loaded}


# -------------------------------
# AUTO FETCH JOB
# -------------------------------

def scheduled_auto_fetch():
    """Fetch delta OHLC for all companies once per day."""
    db = next(get_db())

    companies = crud.get_all_companies(db)

    # Load from CSV if empty
    if not companies:
        load_companies_from_csv(db)
        companies = crud.get_all_companies(db)

    print("🔄 Running scheduled auto-fetch...")

    for company in companies:
        last_date = crud.get_latest_date(db, company.id)

        # Determine start date
        start_date = (
            (last_date + timedelta(days=1)).strftime("%Y-%m-%d")
            if last_date else "2000-01-01"
        )

        # Fetch new rows from Yahoo
        new_data = fetcher.fetch_historical_data(
            company.yahoo_ticker,
            start_date=start_date,
        )

        # Insert into DB
        if new_data:
            inserted = crud.bulk_insert_ohlc(db, company.id, new_data)
            print(f"✔ {company.symbol}: inserted {inserted} new rows")
        else:
            print(f"⏩ {company.symbol}: No new data")

    db.close()
    print("✅ Auto-fetch job completed.")


# -------------------------------
# SCHEDULER STARTUP
# -------------------------------

scheduler = BackgroundScheduler()

@app.on_event("startup")
async def start_scheduler():
    # Prevent scheduler in reload worker
    if os.getenv("RUN_MAIN") != "true":  
        print("⚠ Skipping scheduler (reload worker)")
        return

    await asyncio.sleep(1)
    scheduler.start()
    print("🟢 Scheduler started in main process.")
# -------------------------------
# ROUTES
# -------------------------------

@app.get("/", response_class=HTMLResponse)
async def home(request: Request, db: Session = Depends(get_db)):
    companies = crud.get_all_companies(db)

    company_stats = [
        {
            "company": c,
            "count": crud.get_data_count(db, c.id),
            "latest_date": crud.get_latest_date(db, c.id),
        }
        for c in companies
    ]

    return templates.TemplateResponse("index.html", {
        "request": request,
        "companies": company_stats,
    })


@app.get("/company/{symbol}", response_class=HTMLResponse)
async def company_detail(symbol: str, request: Request, db: Session = Depends(get_db)):
    company = crud.get_company_by_symbol(db, symbol)
    if not company:
        return HTMLResponse(content="Company not found", status_code=404)

    data = crud.get_company_data(db, company.id)[:100]

    return templates.TemplateResponse("company.html", {
        "request": request,
        "company": company,
        "data": data,
        "total_records": crud.get_data_count(db, company.id),
    })


@app.get("/custom-fetch", response_class=HTMLResponse)
async def custom_fetch_page(request: Request):
    return templates.TemplateResponse("custom_fetch.html", {"request": request})


@app.post("/api/load-companies")
async def api_load_companies(db: Session = Depends(get_db)):
    return load_companies_from_csv(db)


@app.get("/api/companies")
async def api_get_companies(db: Session = Depends(get_db)):
    companies = crud.get_all_companies(db)

    result = []
    for c in companies:
        latest = crud.get_latest_date(db, c.id)
        result.append({
            "id": c.id,
            "symbol": c.symbol,
            "name": c.name,
            "yahoo_ticker": c.yahoo_ticker,
            "data_count": crud.get_data_count(db, c.id),
            "latest_date": str(latest) if latest else None,
        })

    return result


@app.get("/api/company/{symbol}/data")
async def api_get_company_data(symbol: str, limit: int = 100, db: Session = Depends(get_db)):
    company = crud.get_company_by_symbol(db, symbol)
    if not company:
        return JSONResponse(status_code=404, content={"error": "Company not found"})

    data = crud.get_company_data(db, company.id)[:limit]

    return {
        "symbol": company.symbol,
        "name": company.name,
        "data": [
            {
                "date": str(d.date),
                "open": d.open,
                "high": d.high,
                "low": d.low,
                "close": d.close,
                "volume": d.volume,
            }
            for d in data
        ],
    }


@app.post("/api/fetch-all")
async def api_fetch_all(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    companies = crud.get_all_companies(db)

    if not companies:
        load_companies_from_csv(db)
        companies = crud.get_all_companies(db)

    def fetch_task():
        db_task = next(get_db())
        try:
            for i, company in enumerate(companies):

                # avoid Yahoo rate limit
                if i > 0:
                    time.sleep(0.5)

                last_date = crud.get_latest_date(db_task, company.id)

                if last_date:
                    start_date = (last_date + timedelta(days=1)).strftime("%Y-%m-%d")
                else:
                    start_date = "2000-01-01"

                new_data = fetcher.fetch_historical_data(
                    company.yahoo_ticker,
                    start_date=start_date,
                )

                if new_data:
                    inserted = crud.bulk_insert_ohlc(db_task, company.id, new_data)
                    print(f"Inserted {inserted} records for {company.symbol}")
        finally:
            db_task.close()

    background_tasks.add_task(fetch_task)

    return {"message": f"Started background fetch for {len(companies)} companies."}


@app.post("/api/fetch-company/{symbol}")
async def api_fetch_company(symbol: str, db: Session = Depends(get_db)):
    company = crud.get_company_by_symbol(db, symbol)
    if not company:
        return JSONResponse(status_code=404, content={"error": "Company not found"})

    last_date = crud.get_latest_date(db, company.id)

    start_date = (last_date + timedelta(days=1)).strftime("%Y-%m-%d") if last_date else "2000-01-01"

    new_data = fetcher.fetch_historical_data(company.yahoo_ticker, start_date=start_date)

    if not new_data:
        return {"message": "No new data found."}

    inserted = crud.bulk_insert_ohlc(db, company.id, new_data)
    return {"symbol": symbol, "fetched": len(new_data), "inserted": inserted}


@app.post("/api/fetch-custom")
async def api_fetch_custom(request: Request):
    form_data = await request.form()

    symbol = form_data.get("symbol", "").strip().upper()
    start_date = form_data.get("start_date", "2000-01-01")
    end_date = form_data.get("end_date", datetime.now().strftime("%Y-%m-%d"))

    if not symbol:
        return JSONResponse(status_code=400, content={"error": "Symbol is required"})

    yahoo_ticker = symbol if symbol.endswith(".NS") else f"{symbol}.NS"

    data = fetcher.fetch_historical_data(
        yahoo_ticker,
        start_date=start_date,
        end_date=end_date,
    )

    if not data:
        return {"success": False, "message": f"No data found for {symbol}"}

    return {
        "success": True,
        "symbol": symbol,
        "yahoo_ticker": yahoo_ticker,
        "start_date": start_date,
        "end_date": end_date,
        "records": len(data),
        "data": data,
    }


# -------------------------------
# RUN Uvicorn
# -------------------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
