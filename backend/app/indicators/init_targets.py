"""Initialization helpers for indicator-required assets and instances."""
import logging
from typing import Optional

import requests
from sqlalchemy.orm import Session

from app.models.asset import Asset
from app.models.indicator import Indicator, IndicatorTemplate
from app.services.yfinance_search import yfinance_service

logger = logging.getLogger("indicators.init")


def ensure_binance_asset(db: Session, asset_id: str = "BTCUSDT", watch: bool = True) -> Optional[Asset]:
    """Ensure a Binance asset exists; create from exchange metadata if possible."""
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if asset:
        if watch and not asset.is_watched:
            asset.is_watched = True
        if not asset.is_active:
            asset.is_active = True
        return asset

    try:
        response = requests.get("https://api.binance.com/api/v3/exchangeInfo", timeout=20)
        response.raise_for_status()
        symbols = response.json().get("symbols", [])
        matched = next((s for s in symbols if s.get("symbol") == asset_id and s.get("status") == "TRADING"), None)
        if matched:
            base_asset = matched.get("baseAsset", asset_id.replace("USDT", "").replace("USD", ""))
            quote_asset = matched.get("quoteAsset", "USDT")
            asset = Asset(
                id=asset_id,
                symbol=base_asset,
                name=f"{base_asset} / {quote_asset}",
                asset_type="crypto",
                exchange="BINANCE",
                currency=quote_asset,
                data_source="binance",
                source_symbol=asset_id,
                is_active=True,
                is_watched=watch,
            )
            db.add(asset)
            db.flush()
            logger.info("Created Binance asset %s from exchange metadata", asset_id)
            return asset
    except Exception as exc:
        logger.warning("Binance asset bootstrap failed for %s: %s", asset_id, exc)

    # Fallback: create with sensible defaults.
    base_symbol = asset_id.replace("USDT", "").replace("USD", "")
    asset = Asset(
        id=asset_id,
        symbol=base_symbol,
        name=f"{base_symbol} / USDT",
        asset_type="crypto",
        exchange="BINANCE",
        currency="USDT",
        data_source="binance",
        source_symbol=asset_id,
        is_active=True,
        is_watched=watch,
    )
    db.add(asset)
    db.flush()
    logger.info("Created Binance asset %s with fallback metadata", asset_id)
    return asset


def ensure_yfinance_asset(db: Session, asset_id: str, watch: bool = True) -> Optional[Asset]:
    """Ensure a yfinance asset exists; create from yfinance search if possible."""
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if asset:
        if watch and not asset.is_watched:
            asset.is_watched = True
        if not asset.is_active:
            asset.is_active = True
        return asset

    search_results = yfinance_service.search_by_symbol(asset_id, limit=10)
    matched = next((r for r in search_results if r.symbol == asset_id), None)

    if matched:
        asset = Asset(
            id=matched.symbol,
            symbol=matched.symbol,
            name=matched.name,
            asset_type="equity",
            exchange=matched.exchange or "US",
            currency=matched.currency or "USD",
            data_source="yfinance",
            source_symbol=matched.symbol,
            is_active=True,
            is_watched=watch,
        )
        db.add(asset)
        db.flush()
        logger.info("Created yfinance asset %s from search metadata", asset_id)
        return asset

    # Fallback: create with conservative defaults.
    asset = Asset(
        id=asset_id,
        symbol=asset_id,
        name=asset_id,
        asset_type="equity",
        exchange="US",
        currency="USD",
        data_source="yfinance",
        source_symbol=asset_id,
        is_active=True,
        is_watched=watch,
    )
    db.add(asset)
    db.flush()
    logger.info("Created yfinance asset %s with fallback metadata", asset_id)
    return asset


def ensure_indicator(
    db: Session,
    template_id: str,
    asset_id: str,
    name: str,
    params: Optional[dict] = None,
) -> bool:
    """Ensure indicator instance exists for template+asset."""
    template = db.query(IndicatorTemplate).filter(IndicatorTemplate.id == template_id).first()
    if not template:
        return False

    exists = db.query(Indicator).filter(
        Indicator.template_id == template_id,
        Indicator.asset_id == asset_id,
    ).first()
    if exists:
        return False

    indicator = Indicator(
        template_id=template_id,
        asset_id=asset_id,
        name=name,
        params=params or {},
        is_active=True,
    )
    db.add(indicator)
    return True
