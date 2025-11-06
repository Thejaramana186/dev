from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models import Company, DailyOHLC
from datetime import date
from typing import List, Optional




def get_or_create_company(db: Session, symbol: str, name: str, yahoo_ticker: str) -> Company:
    """Get existing company or create a new one."""
    company = db.query(Company).filter(Company.symbol == symbol).first()
    if not company:
        company = Company(symbol=symbol, name=name, yahoo_ticker=yahoo_ticker)
        db.add(company)
        db.commit()
        db.refresh(company)
    return company


def get_all_companies(db: Session) -> List[Company]:
    """Return all companies ordered by name."""
    return db.query(Company).order_by(Company.name).all()


def get_company_by_symbol(db: Session, symbol: str) -> Optional[Company]:
    """Return company by its stock symbol."""
    return db.query(Company).filter(Company.symbol == symbol).first()




def get_latest_date(db: Session, company_id: int) -> Optional[date]:
    """Return the most recent date of stored OHLC data for a company."""
    result = (
        db.query(func.max(DailyOHLC.date))
        .filter(DailyOHLC.company_id == company_id)
        .scalar()
    )
    return result


def bulk_insert_ohlc(db: Session, company_id: int, ohlc_data: List[dict]) -> int:
    """
    Bulk insert OHLC data for a company.
    Skips existing dates to prevent duplicates.
    Returns count of new records inserted.
    """
    if not ohlc_data:
        return 0

    
    existing_dates = {
        row[0]
        for row in db.query(DailyOHLC.date)
        .filter(DailyOHLC.company_id == company_id)
        .all()
    }

    new_records = []
    for record in ohlc_data:
        record_date = record["date"]
        if record_date not in existing_dates:
            new_records.append(
                DailyOHLC(
                    company_id=company_id,
                    date=record_date,
                    open=record["open"],
                    high=record["high"],
                    low=record["low"],
                    close=record["close"],
                    volume=record["volume"],
                )
            )

    if new_records:
        db.bulk_save_objects(new_records)
        db.commit()

    return len(new_records)


def get_company_data(
    db: Session,
    company_id: int,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
) -> List[DailyOHLC]:
    """Get OHLC data for a company with optional date filters."""
    query = db.query(DailyOHLC).filter(DailyOHLC.company_id == company_id)

    if start_date:
        query = query.filter(DailyOHLC.date >= start_date)
    if end_date:
        query = query.filter(DailyOHLC.date <= end_date)

    return query.order_by(DailyOHLC.date.desc()).all()


def get_data_count(db: Session, company_id: int) -> int:
    """Return total number of OHLC data records for a company."""
    return db.query(DailyOHLC).filter(DailyOHLC.company_id == company_id).count()



def get_last_date_from_db(db: Session, company_id: int) -> Optional[date]:
    """Alias for delta fetch logic — returns the last available date."""
    return get_latest_date(db, company_id)


def save_stock_data(db: Session, company_id: int, ohlc_data: List[dict]) -> int:
    """Save newly fetched OHLC data, avoiding duplicates."""
    return bulk_insert_ohlc(db, company_id, ohlc_data)
