"""Price API routes."""
from typing import List, Optional, Dict
from datetime import date, datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from app.core.database import get_db
from app.models.price_data import PriceData
from app.models.asset import Asset
from app.schemas.price import PriceResponse, LatestPriceResponse, SparklineResponse, SparklineData

router = APIRouter(prefix="/prices", tags=["prices"])


@router.get("", response_model=List[PriceResponse])
def get_prices(
    asset_id: str,
    start: Optional[date] = Query(None, description="开始日期"),
    end: Optional[date] = Query(None, description="结束日期"),
    interval: str = Query("1d", description="周期: 1d/1w/1m"),
    limit: int = Query(100, description="返回数量限制"),
    db: Session = Depends(get_db)
):
    """Get price data for an asset."""
    # Check asset exists
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    # Build query
    query = db.query(PriceData).filter(
        PriceData.asset_id == asset_id,
        PriceData.interval == interval
    )
    
    if start:
        query = query.filter(PriceData.date >= start)
    if end:
        query = query.filter(PriceData.date <= end)
    
    # Order by date descending, limit results
    prices = query.order_by(desc(PriceData.date)).limit(limit).all()
    
    return prices[::-1]  # Reverse to ascending order


@router.get("/latest", response_model=Optional[PriceResponse])
def get_latest_price(asset_id: str, db: Session = Depends(get_db)):
    """Get latest price for an asset."""
    price = db.query(PriceData).filter(
        PriceData.asset_id == asset_id
    ).order_by(desc(PriceData.date)).first()
    
    if not price:
        raise HTTPException(status_code=404, detail="No price data found")
    
    return price


@router.get("/latest/batch", response_model=List[LatestPriceResponse])
def get_latest_prices_batch(
    asset_ids: str = Query(..., description="Comma-separated asset IDs (e.g., BTC-USD,SPY,AAPL)"),
    db: Session = Depends(get_db)
):
    """
    Get latest prices for multiple assets (batch endpoint for watchlist).
    
    Returns latest price, change, and data freshness for each asset.
    """
    if not asset_ids:
        return []
    
    # Parse asset_ids
    id_list = [id.strip() for id in asset_ids.split(",") if id.strip()]
    
    if not id_list:
        return []
    
    # Get all assets info
    assets = db.query(Asset).filter(Asset.id.in_(id_list)).all()
    asset_map = {a.id: a for a in assets}
    
    # Get latest price for each asset using subquery
    results = []
    today = date.today()
    yesterday = today - timedelta(days=1)
    
    for asset_id in id_list:
        asset = asset_map.get(asset_id)
        if not asset:
            continue
        
        # Get latest price
        latest = db.query(PriceData).filter(
            PriceData.asset_id == asset_id
        ).order_by(desc(PriceData.date)).first()
        
        if not latest:
            continue
        
        # Get previous day price for change calculation
        previous = db.query(PriceData).filter(
            PriceData.asset_id == asset_id,
            PriceData.date < latest.date
        ).order_by(desc(PriceData.date)).first()
        
        # Calculate change
        change = None
        change_percent = None
        if previous and previous.close:
            change = latest.close - previous.close
            change_percent = (change / previous.close) * 100
        
        # Determine data freshness
        # fresh: 0-2 days, stale: 2-5 days, outdated: >5 days
        days_since_update = (today - latest.date).days
        if days_since_update <= 2:
            freshness = "fresh"
        elif days_since_update <= 5:
            freshness = "stale"
        else:
            freshness = "outdated"
        
        results.append(LatestPriceResponse(
            asset_id=asset_id,
            symbol=asset.symbol,
            close=latest.close,
            open=latest.open,
            high=latest.high,
            low=latest.low,
            volume=latest.volume,
            change=round(change, 2) if change is not None else None,
            change_percent=round(change_percent, 2) if change_percent is not None else None,
            date=latest.date,
            last_updated=latest.created_at or datetime.utcnow(),
            data_freshness=freshness
        ))
    
    return results


@router.get("/sparkline/batch", response_model=List[SparklineResponse])
def get_sparkline_batch(
    asset_ids: str = Query(..., description="Comma-separated asset IDs (e.g., BTC-USD,SPY,AAPL)"),
    days: int = Query(7, ge=2, le=30, description="Number of days for sparkline (default: 7, max: 30)"),
    db: Session = Depends(get_db)
):
    """
    Get sparkline (mini chart) data for multiple assets.
    
    Returns the last N days of closing prices for each asset, suitable for
    rendering mini line charts in the watchlist.
    
    Args:
        asset_ids: Comma-separated list of asset IDs
        days: Number of days to include (2-30, default 7)
    
    Returns:
        List of sparkline data for each asset with price history
    """
    if not asset_ids:
        return []
    
    # Parse asset_ids
    id_list = [id.strip() for id in asset_ids.split(",") if id.strip()]
    
    if not id_list:
        return []
    
    # Get all assets info
    assets = db.query(Asset).filter(Asset.id.in_(id_list)).all()
    asset_map = {a.id: a for a in assets}
    
    # Calculate date range
    end_date = date.today()
    start_date = end_date - timedelta(days=days + 5)  # Get a few extra days to ensure we have enough data
    
    results = []
    
    for asset_id in id_list:
        asset = asset_map.get(asset_id)
        if not asset:
            continue
        
        # Get price history for the date range
        prices = db.query(PriceData).filter(
            PriceData.asset_id == asset_id,
            PriceData.interval == "1d",
            PriceData.date >= start_date,
            PriceData.date <= end_date
        ).order_by(PriceData.date.asc()).all()
        
        if not prices:
            continue
        
        # Take the last 'days' entries
        recent_prices = prices[-days:] if len(prices) > days else prices
        
        # Calculate overall change percent
        change_percent = None
        if len(recent_prices) >= 2:
            first_price = recent_prices[0].close
            last_price = recent_prices[-1].close
            if first_price > 0:
                change_percent = round(((last_price - first_price) / first_price) * 100, 2)
        
        # Build sparkline data
        sparkline_data = [
            SparklineData(date=p.date, close=p.close)
            for p in recent_prices
        ]
        
        results.append(SparklineResponse(
            asset_id=asset_id,
            symbol=asset.symbol,
            data=sparkline_data,
            days=len(sparkline_data),
            change_percent=change_percent
        ))
    
    return results


@router.post("/refresh", response_model=Dict[str, str])
def refresh_prices(
    asset_ids: Optional[List[str]] = Query(None, description="Asset IDs to refresh (None = all active)"),
    db: Session = Depends(get_db)
):
    """
    Trigger price refresh for specified assets or all active assets.
    
    This is a synchronous endpoint for manual refresh from watchlist.
    For large batches, use the scheduler endpoint.
    """
    from app.services.price_scheduler import run_price_update
    
    try:
        results = run_price_update(asset_ids=asset_ids, lookback_days=5)
        success_count = sum(1 for r in results if r.get("status") == "success")
        total = len(results)
        
        return {
            "status": "success",
            "message": f"Updated {success_count}/{total} assets",
            "details": f"New: {sum(r.get('inserted', 0) for r in results)}, "
                      f"Updated: {sum(r.get('updated', 0) for r in results)}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Refresh failed: {str(e)}")


@router.get("/live", response_model=List[PriceResponse])
def get_live_prices(
    asset_id: str,
    days: int = Query(365, ge=1, le=730, description="获取最近多少天的数据"),
    db: Session = Depends(get_db)
):
    """
    Get live price data directly from data source (not from database).
    
    This endpoint fetches real-time price data from the configured data source
    without saving to database. Useful for displaying prices for assets that
    are not in the watchlist.
    
    - asset_id: Asset ID (must exist in database)
    - days: Number of days to fetch (1-730, default 365)
    
    Returns price data in the same format as the regular prices endpoint.
    """
    import asyncio
    from app.fetchers.registry import get_fetcher
    
    # Get asset info
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    try:
        # Get appropriate fetcher
        fetcher_class = get_fetcher(asset.data_source)
        fetcher = fetcher_class()
        
        # Calculate date range
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        # Fetch live prices
        prices = asyncio.run(fetcher.fetch_prices(
            source_symbol=asset.source_symbol,
            start=start_date,
            end=end_date,
            interval="1d"
        ))
        
        if not prices:
            return []
        
        # Convert to PriceResponse format
        result = []
        now = datetime.utcnow()
        for p in prices:
            result.append(PriceResponse(
                id=0,  # Placeholder, not saved to DB
                asset_id=asset_id,
                timestamp=p.get("timestamp") or datetime.combine(p["date"], datetime.min.time()),
                date=p["date"],
                interval="1d",
                open=p.get("open"),
                high=p.get("high"),
                low=p.get("low"),
                close=p["close"],
                volume=p.get("volume"),
                created_at=now
            ))
        
        return result
        
    except Exception as e:
        print(f"Live price fetch error for {asset_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch live prices: {str(e)}")
