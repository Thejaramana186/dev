from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.db import Base


class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    yahoo_ticker = Column(String, unique=True, nullable=False)

    
    daily_data = relationship("DailyOHLC", back_populates="company", cascade="all, delete-orphan")


class DailyOHLC(Base):
    __tablename__ = "daily_ohlc"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    date = Column(Date, nullable=False, index=True)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)

    
    company = relationship("Company", back_populates="daily_data")

    
    __table_args__ = (UniqueConstraint('company_id', 'date', name='_company_date_uc'),)