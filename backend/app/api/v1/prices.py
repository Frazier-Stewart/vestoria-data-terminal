"""Price API routes."""
from typing import List, Optional, Dict, Any
from datetime import date, datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from app.core.database import get_db
from app.models.price_data import PriceData
from app.models.asset import Asset
from app.schemas.price import PriceResponse, LatestPriceResponse, SparklineResponse, SparklineData, BackfillRangeRequest

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


@router.get("/gap-check", response_model=Dict[str, Any])
def check_price_gaps(
    asset_id: str,
    threshold_days: int = Query(10, ge=1, le=30, description="缺失天数阈值"),
    db: Session = Depends(get_db)
):
    """
    Check for price data gaps for an asset.
    
    Returns information about missing data gaps, including:
    - has_gap: Whether there are gaps larger than threshold_days
    - total_missing: Total number of missing days
    - gaps: List of gap periods (start_date, end_date, days)
    - latest_date: Latest available data date
    """
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    # Get all price dates
    prices = db.query(PriceData).filter(
        PriceData.asset_id == asset_id,
        PriceData.interval == "1d"
    ).order_by(PriceData.date).all()
    
    if not prices:
        return {
            "asset_id": asset_id,
            "has_data": False,
            "has_gap": True,
            "total_missing": 0,
            "gaps": [],
            "message": "No price data available"
        }
    
    # Find gaps
    dates = [p.date for p in prices]
    today = date.today()
    earliest = dates[0]
    latest = dates[-1]
    
    gaps = []
    total_missing = 0
    
    # Check for gaps between available dates
    for i in range(1, len(dates)):
        prev_date = dates[i-1]
        curr_date = dates[i]
        gap_days = (curr_date - prev_date).days - 1
        
        if gap_days >= threshold_days:
            gaps.append({
                "start_date": prev_date.isoformat(),
                "end_date": curr_date.isoformat(),
                "days": gap_days
            })
            total_missing += gap_days
    
    # Check gap from latest to today
    days_since_latest = (today - latest).days
    if days_since_latest >= threshold_days:
        gaps.append({
            "start_date": latest.isoformat(),
            "end_date": today.isoformat(),
            "days": days_since_latest
        })
        total_missing += days_since_latest
    
    return {
        "asset_id": asset_id,
        "has_data": True,
        "has_gap": len(gaps) > 0,
        "total_missing": total_missing,
        "gaps": gaps,
        "earliest_date": earliest.isoformat(),
        "latest_date": latest.isoformat(),
        "threshold_days": threshold_days
    }


@router.post("/gap-fill", response_model=Dict[str, Any])
def fill_price_gaps(
    asset_id: str,
    background: bool = Query(False, description="是否在后台异步执行"),
    db: Session = Depends(get_db)
):
    """
    Fill missing price data gaps for an asset.
    
    This endpoint fetches data for all detected gaps and saves to database.
    """
    from app.services.backfill import update_asset_with_fetcher
    
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    # Get gap check info
    prices = db.query(PriceData).filter(
        PriceData.asset_id == asset_id,
        PriceData.interval == "1d"
    ).order_by(PriceData.date).all()
    
    if not prices:
        # No data at all, fetch full history (1 year)
        try:
            result = update_asset_with_fetcher(
                asset=asset,
                start=date.today() - timedelta(days=365),
                end=date.today(),
                interval="1d",
                db=db,
                close_db=False
            )
            return {
                "asset_id": asset_id,
                "status": "success",
                "message": "Fetched full year of data",
                "filled_days": result.get("records", 0),
                "details": result
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to fetch data: {str(e)}")
    
    # Find and fill gaps
    dates = [p.date for p in prices]
    today = date.today()
    latest = dates[-1]
    
    filled_gaps = []
    total_filled = 0
    
    # Fill gaps between dates
    for i in range(1, len(dates)):
        prev_date = dates[i-1]
        curr_date = dates[i]
        gap_days = (curr_date - prev_date).days - 1
        
        if gap_days >= 1:  # Fill all gaps, not just large ones
            try:
                result = update_asset_with_fetcher(
                    asset=asset,
                    start=prev_date + timedelta(days=1),
                    end=curr_date - timedelta(days=1),
                    interval="1d",
                    db=db,
                    close_db=False
                )
                filled_days = result.get("records", 0)
                filled_gaps.append({
                    "start_date": prev_date.isoformat(),
                    "end_date": curr_date.isoformat(),
                    "filled_days": filled_days
                })
                total_filled += filled_days
            except Exception as e:
                filled_gaps.append({
                    "start_date": prev_date.isoformat(),
                    "end_date": curr_date.isoformat(),
                    "error": str(e)
                })
    
    # Fill gap from latest to today
    days_since_latest = (today - latest).days
    if days_since_latest >= 1:
        try:
            result = update_asset_with_fetcher(
                asset=asset,
                start=latest + timedelta(days=1),
                end=today,
                interval="1d",
                db=db,
                close_db=False
            )
            filled_days = result.get("records", 0)
            filled_gaps.append({
                "start_date": latest.isoformat(),
                "end_date": today.isoformat(),
                "filled_days": filled_days
            })
            total_filled += filled_days
        except Exception as e:
            filled_gaps.append({
                "start_date": latest.isoformat(),
                "end_date": today.isoformat(),
                "error": str(e)
            })
    
    return {
        "asset_id": asset_id,
        "status": "success",
        "message": f"Filled {total_filled} days across {len(filled_gaps)} gaps",
        "total_filled": total_filled,
        "filled_gaps": filled_gaps
    }


@router.post("/backfill-range", response_model=Dict[str, Any])
def backfill_price_range(
    asset_id: str,
    request: BackfillRangeRequest,
    db: Session = Depends(get_db)
):
    """
    Backfill price data for a specific date range.
    
    This allows users to fetch historical data for a custom time period.
    """
    from app.services.backfill import update_asset_with_fetcher
    
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    # Validate date range
    if request.start_date > request.end_date:
        raise HTTPException(status_code=400, detail="Start date must be before end date")
    
    if request.end_date > date.today():
        raise HTTPException(status_code=400, detail="End date cannot be in the future")
    
    days = (request.end_date - request.start_date).days + 1
    if days > 365 * 5:  # Max 5 years
        raise HTTPException(status_code=400, detail="Date range cannot exceed 5 years")
    
    try:
        result = update_asset_with_fetcher(
            asset=asset,
            start=request.start_date,
            end=request.end_date,
            interval="1d",
            db=db,
            close_db=False
        )
        
        return {
            "asset_id": asset_id,
            "status": "success",
            "message": f"Fetched {result.get('records', 0)} days of data",
            "start_date": request.start_date.isoformat(),
            "end_date": request.end_date.isoformat(),
            "days_requested": days,
            "days_filled": result.get("records", 0),
            "details": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch data: {str(e)}")
