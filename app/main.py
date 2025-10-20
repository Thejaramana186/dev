from fastapi import FastAPI, Depends, Request, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import csv
import os
from pathlib import Path

from app.db import engine, get_db, Base
from app.models import Company, DailyOHLC
from app import crud, fetcher

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Nifty 50 Stock Data Fetcher")

# Setup static files and templates
BASE_DIR = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


def load_companies_from_csv(db: Session):
    """Load companies from tickers.csv into database"""
    csv_path = BASE_DIR.parent / "tickers.csv"

    if not csv_path.exists():
        return {"error": "tickers.csv not found"}

    loaded = 0
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            crud.get_or_create_company(
                db,
                symbol=row['symbol'],
                name=row['name'],
                yahoo_ticker=row['yahoo_ticker']
            )
            loaded += 1

    return {"loaded": loaded}


@app.get("/", response_class=HTMLResponse)
async def home(request: Request, db: Session = Depends(get_db)):
    """Home page showing all companies"""
    companies = crud.get_all_companies(db)

    # Get data counts for each company
    company_stats = []
    for company in companies:
        count = crud.get_data_count(db, company.id)
        latest = crud.get_latest_date(db, company.id)
        company_stats.append({
            "company": company,
            "count": count,
            "latest_date": latest
        })

    return templates.TemplateResponse(
        "index.html",
        {"request": request, "companies": company_stats}
    )


@app.get("/company/{symbol}", response_class=HTMLResponse)
async def company_detail(symbol: str, request: Request, db: Session = Depends(get_db)):
    """Company detail page showing historical data"""
    company = crud.get_company_by_symbol(db, symbol)

    if not company:
        return HTMLResponse(content="Company not found", status_code=404)

    # Get recent data (last 100 records)
    data = crud.get_company_data(db, company.id)[:100]

    return templates.TemplateResponse(
        "company.html",
        {
            "request": request,
            "company": company,
            "data": data,
            "total_records": crud.get_data_count(db, company.id)
        }
    )


@app.post("/api/load-companies")
async def api_load_companies(db: Session = Depends(get_db)):
    """Load companies from tickers.csv"""
    result = load_companies_from_csv(db)
    return result


@app.post("/api/fetch-all")
async def api_fetch_all(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Fetch historical data for all companies"""
    companies = crud.get_all_companies(db)

    if not companies:
        # Load companies first
        load_companies_from_csv(db)
        companies = crud.get_all_companies(db)

    def fetch_task():
        db_task = next(get_db())
        try:
            for company in companies:
                data = fetcher.fetch_historical_data(
                    company.yahoo_ticker,
                    start_date="2000-01-01"
                )
                if data:
                    inserted = crud.bulk_insert_ohlc(db_task, company.id, data)
                    print(f"Inserted {inserted} records for {company.symbol}")
        finally:
            db_task.close()

    background_tasks.add_task(fetch_task)

    return {
        "message": f"Started fetching data for {len(companies)} companies",
        "companies": len(companies)
    }


@app.post("/api/fetch-company/{symbol}")
async def api_fetch_company(symbol: str, db: Session = Depends(get_db)):
    """Fetch historical data for a specific company"""
    company = crud.get_company_by_symbol(db, symbol)

    if not company:
        return JSONResponse(
            status_code=404,
            content={"error": "Company not found"}
        )

    data = fetcher.fetch_historical_data(
        company.yahoo_ticker,
        start_date="2000-01-01"
    )

    if data:
        inserted = crud.bulk_insert_ohlc(db, company.id, data)
        return {
            "symbol": symbol,
            "fetched": len(data),
            "inserted": inserted
        }
    else:
        return JSONResponse(
            status_code=500,
            content={"error": "Failed to fetch data"}
        )


@app.post("/api/update-company/{symbol}")
async def api_update_company(symbol: str, db: Session = Depends(get_db)):
    """Update company with latest data"""
    company = crud.get_company_by_symbol(db, symbol)

    if not company:
        return JSONResponse(
            status_code=404,
            content={"error": "Company not found"}
        )

    data = fetcher.fetch_latest_data(company.yahoo_ticker, days=7)

    if data:
        inserted = crud.bulk_insert_ohlc(db, company.id, data)
        return {
            "symbol": symbol,
            "fetched": len(data),
            "inserted": inserted
        }
    else:
        return JSONResponse(
            status_code=500,
            content={"error": "Failed to fetch data"}
        )


@app.get("/api/companies")
async def api_get_companies(db: Session = Depends(get_db)):
    """Get all companies with stats"""
    companies = crud.get_all_companies(db)

    result = []
    for company in companies:
        count = crud.get_data_count(db, company.id)
        latest = crud.get_latest_date(db, company.id)
        result.append({
            "id": company.id,
            "symbol": company.symbol,
            "name": company.name,
            "yahoo_ticker": company.yahoo_ticker,
            "data_count": count,
            "latest_date": str(latest) if latest else None
        })

    return result


@app.get("/api/company/{symbol}/data")
async def api_get_company_data(symbol: str, limit: int = 100, db: Session = Depends(get_db)):
    """Get OHLC data for a company"""
    company = crud.get_company_by_symbol(db, symbol)

    if not company:
        return JSONResponse(
            status_code=404,
            content={"error": "Company not found"}
        )

    data = crud.get_company_data(db, company.id)[:limit]

    return {
        "symbol": symbol,
        "name": company.name,
        "data": [
            {
                "date": str(d.date),
                "open": d.open,
                "high": d.high,
                "low": d.low,
                "close": d.close,
                "volume": d.volume
            }
            for d in data
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
