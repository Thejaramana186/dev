from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models import Company, DailyOHLC
from datetime import date
from typing import List, Optional


def get_or_create_company(db: Session, symbol: str, name: str, yahoo_ticker: str) -> Company:
    """Get existing company or create new one"""
    company = db.query(Company).filter(Company.symbol == symbol).first()
    if not company:
        company = Company(symbol=symbol, name=name, yahoo_ticker=yahoo_ticker)
        db.add(company)
        db.commit()
        db.refresh(company)
    return company


def get_all_companies(db: Session) -> List[Company]:
    """Get all companies"""
    return db.query(Company).order_by(Company.name).all()


def get_company_by_symbol(db: Session, symbol: str) -> Optional[Company]:
    """Get company by symbol"""
    return db.query(Company).filter(Company.symbol == symbol).first()


def bulk_insert_ohlc(db: Session, company_id: int, ohlc_data: List[dict]):
    """Bulk insert OHLC data, skip duplicates"""
    existing_dates = {
        row[0] for row in db.query(DailyOHLC.date)
        .filter(DailyOHLC.company_id == company_id)
        .all()
    }

    new_records = []
    for record in ohlc_data:
        if record['date'] not in existing_dates:
            new_records.append(DailyOHLC(
                company_id=company_id,
                date=record['date'],
                open=record['open'],
                high=record['high'],
                low=record['low'],
                close=record['close'],
                volume=record['volume']
            ))

    if new_records:
        db.bulk_save_objects(new_records)
        db.commit()

    return len(new_records)


def get_company_data(db: Session, company_id: int, start_date: Optional[date] = None,
                     end_date: Optional[date] = None) -> List[DailyOHLC]:
    """Get OHLC data for a company with optional date filtering"""
    query = db.query(DailyOHLC).filter(DailyOHLC.company_id == company_id)

    if start_date:
        query = query.filter(DailyOHLC.date >= start_date)
    if end_date:
        query = query.filter(DailyOHLC.date <= end_date)

    return query.order_by(DailyOHLC.date.desc()).all()


def get_data_count(db: Session, company_id: int) -> int:
    """Get count of data points for a company"""
    return db.query(DailyOHLC).filter(DailyOHLC.company_id == company_id).count()


def get_latest_date(db: Session, company_id: int) -> Optional[date]:
    """Get the latest date for which data exists"""
    result = db.query(DailyOHLC.date)\
        .filter(DailyOHLC.company_id == company_id)\
        .order_by(DailyOHLC.date.desc())\
        .first()
    return result[0] if result else None
