"""Sector and industry models."""
from datetime import datetime

from sqlalchemy import Column, String, Integer, Float, DateTime, Index

from app.core.database import Base


class Sector(Base):
    """GICS Sector model."""

    __tablename__ = "sectors"

    key = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    name_zh = Column(String, nullable=True)
    company_count = Column(Integer, default=0)
    last_updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Sector(key='{self.key}', name='{self.name}')>"


class Industry(Base):
    """Industry model under a sector."""

    __tablename__ = "industries"

    key = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    sector_key = Column(String, nullable=False, index=True)
    symbol = Column(String, nullable=True)
    market_weight = Column(Float, nullable=True)
    last_updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("ix_industries_sector_key", "sector_key"),
    )

    def __repr__(self):
        return f"<Industry(key='{self.key}', name='{self.name}')>"


class SectorTopCompany(Base):
    """Top companies within a sector."""

    __tablename__ = "sector_top_companies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sector_key = Column(String, nullable=False, index=True)
    symbol = Column(String, nullable=False, index=True)
    name = Column(String, nullable=False)
    market_cap = Column(Float, nullable=True)
    trailing_pe = Column(Float, nullable=True)
    price = Column(Float, nullable=True)
    currency = Column(String, default="USD")
    exchange = Column(String, nullable=True)
    last_updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("ix_sector_top_companies_sector_symbol", "sector_key", "symbol", unique=True),
    )

    def __repr__(self):
        return f"<SectorTopCompany(sector='{self.sector_key}', symbol='{self.symbol}')>"


class IndustryTopCompany(Base):
    """Top companies within an industry."""

    __tablename__ = "industry_top_companies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    industry_key = Column(String, nullable=False, index=True)
    symbol = Column(String, nullable=False, index=True)
    name = Column(String, nullable=False)
    market_cap = Column(Float, nullable=True)
    trailing_pe = Column(Float, nullable=True)
    price = Column(Float, nullable=True)
    currency = Column(String, default="USD")
    exchange = Column(String, nullable=True)
    last_updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("ix_industry_top_companies_industry_symbol", "industry_key", "symbol", unique=True),
    )

    def __repr__(self):
        return f"<IndustryTopCompany(industry='{self.industry_key}', symbol='{self.symbol}')>"
