"""Sector and industry data synchronization service."""
import logging
from datetime import datetime
from typing import Dict, List

import yfinance as yf

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.sector import Sector, Industry, SectorTopCompany, IndustryTopCompany
from app.services.yfinance_search import yfinance_service

logger = logging.getLogger("sector_sync")

if settings.PROXY_URL:
    yf.config.network.proxy = {
        "http": settings.PROXY_URL,
        "https": settings.PROXY_URL,
    }


def _get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def sync_sectors() -> Dict[str, any]:
    """Sync all GICS sectors from yfinance to database."""
    db = next(_get_db())
    try:
        sectors_data = yfinance_service.get_sectors()
        count = 0
        for s in sectors_data:
            sector = db.query(Sector).filter(Sector.key == s["key"]).first()
            if not sector:
                sector = Sector(key=s["key"])
                db.add(sector)
            sector.name = s["name"]
            sector.name_zh = s.get("name_zh")
            sector.company_count = s.get("company_count", 0)
            sector.last_updated_at = datetime.utcnow()
            count += 1
        db.commit()
        logger.info("Synced %d sectors", count)
        return {"status": "success", "count": count}
    except Exception as e:
        db.rollback()
        logger.exception("Failed to sync sectors")
        return {"status": "error", "message": str(e)}
    finally:
        db.close()


def sync_industries() -> Dict[str, any]:
    """Sync all industries for each sector from yfinance to database."""
    db = next(_get_db())
    try:
        sectors = db.query(Sector).all()
        total = 0
        for sector in sectors:
            industries_data = yfinance_service.get_industries_by_sector(sector.key)
            for ind in industries_data:
                industry = db.query(Industry).filter(Industry.key == ind["key"]).first()
                if not industry:
                    industry = Industry(key=ind["key"])
                    db.add(industry)
                industry.name = ind["name"]
                industry.sector_key = sector.key
                industry.symbol = ind.get("symbol")
                industry.market_weight = ind.get("market_weight")
                industry.last_updated_at = datetime.utcnow()
                total += 1
            db.commit()
        logger.info("Synced %d industries", total)
        return {"status": "success", "count": total}
    except Exception as e:
        db.rollback()
        logger.exception("Failed to sync industries")
        return {"status": "error", "message": str(e)}
    finally:
        db.close()


def sync_all() -> Dict[str, any]:
    """Sync sectors and industries metadata to local database."""
    logger.info("Starting sector/industry sync...")
    result = {
        "sectors": sync_sectors(),
        "industries": sync_industries(),
    }
    logger.info("Sector/industry sync completed")
    return result
