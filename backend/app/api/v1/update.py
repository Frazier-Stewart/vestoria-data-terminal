"""Update API routes."""
from datetime import date, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.asset import Asset
from app.models.price_data import PriceData
from app.fetchers.registry import get_fetcher
from app.services.backfill import backfill_asset, get_yfinance_symbol

router = APIRouter(prefix="/update", tags=["update"])


async def update_asset_prices_task(asset_id: str):
    """Background task to update asset prices."""
    from app.core.database import SessionLocal
    db = SessionLocal()
    try:
        asset = db.query(Asset).filter(Asset.id == asset_id).first()
        if not asset:
            print(f"Asset {asset_id} not found")
            return
        
        # Get fetcher for the asset's data source
        fetcher_class = get_fetcher(asset.data_source)
        if not fetcher_class:
            print(f"No fetcher found for {asset.data_source}")
            return
        
        fetcher = fetcher_class()
        
        # Fetch last 30 days of data
        end = date.today()
        start = end - timedelta(days=30)
        
        print(f"Fetching prices for {asset_id} from {start} to {end}")
        prices = await fetcher.fetch_prices(asset.source_symbol, start, end)
        
        if not prices:
            print(f"No prices fetched for {asset_id}")
            return
        
        # Save to database
        saved_count = 0
        for price_data in prices:
            # Check if price already exists
            existing = db.query(PriceData).filter(
                PriceData.asset_id == asset_id,
                PriceData.date == price_data["date"],
                PriceData.interval == "1d"
            ).first()
            
            if existing:
                # Update existing
                existing.open = price_data.get("open")
                existing.high = price_data.get("high")
                existing.low = price_data.get("low")
                existing.close = price_data["close"]
                existing.volume = price_data.get("volume")
                existing.source = asset.data_source
            else:
                # Create new
                db_price = PriceData(
                    asset_id=asset_id,
                    timestamp=price_data["timestamp"],
                    date=price_data["date"],
                    interval="1d",
                    open=price_data.get("open"),
                    high=price_data.get("high"),
                    low=price_data.get("low"),
                    close=price_data["close"],
                    volume=price_data.get("volume"),
                    source=asset.data_source
                )
                db.add(db_price)
            
            saved_count += 1
        
        db.commit()
        print(f"Saved {saved_count} prices for {asset_id}")
        
    except Exception as e:
        print(f"Error updating {asset_id}: {e}")
        db.rollback()
    finally:
        db.close()


@router.post("")
def trigger_update(
    asset_id: str = None,
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db)
):
    """Trigger price update for asset(s)."""
    if asset_id:
        # Update single asset
        asset = db.query(Asset).filter(Asset.id == asset_id).first()
        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found")
        
        if background_tasks:
            background_tasks.add_task(update_asset_prices_task, asset_id)
            return {"message": f"Update triggered for {asset_id}"}
        else:
            # Synchronous update
            import asyncio
            asyncio.run(update_asset_prices_task(asset_id))
            return {"message": f"Updated {asset_id}"}
    else:
        # Update all active assets
        assets = db.query(Asset).filter(Asset.is_active == True).all()
        
        if background_tasks:
            for asset in assets:
                background_tasks.add_task(update_asset_prices_task, asset.id)
        
        return {"message": f"Update triggered for {len(assets)} assets"}


@router.post("/backfill/{asset_id}")
def backfill_asset_prices(
    asset_id: str,
    days: int = Query(365, ge=1, le=3650, description="Number of days to backfill"),
    db: Session = Depends(get_db)
):
    """
    Backfill historical price data for a specific asset.
    
    This is a synchronous endpoint that fetches historical data immediately.
    Use this when adding a new asset to populate its price history.
    
    Args:
        asset_id: The asset ID to backfill
        days: Number of days of history to fetch (default: 365)
    
    Returns:
        Result with status and record counts
    """
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    # Get the yfinance symbol
    yf_symbol = get_yfinance_symbol(asset)
    
    # Calculate date range
    end = date.today()
    start = end - timedelta(days=days)
    
    # Run backfill
    result = backfill_asset(
        asset_id=asset.id,
        symbol=yf_symbol,
        start=start,
        end=end,
        db=db
    )
    
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result.get("message", "Backfill failed"))
    
    return {
        "asset_id": asset_id,
        "symbol": yf_symbol,
        "status": result["status"],
        "records": result.get("records", 0),
        "inserted": result.get("inserted", 0),
        "updated": result.get("updated", 0),
        "start_date": result.get("start_date"),
        "end_date": result.get("end_date"),
        "message": f"Successfully backfilled {result.get('records', 0)} price records"
    }


@router.post("/backfill", tags=["update"])
def backfill_multiple_assets(
    asset_ids: list[str] = Query(..., description="List of asset IDs to backfill"),
    days: int = Query(365, ge=1, le=3650, description="Number of days to backfill"),
    db: Session = Depends(get_db)
):
    """
    Backfill historical price data for multiple assets.
    
    Args:
        asset_ids: List of asset IDs to backfill
        days: Number of days of history to fetch (default: 365)
    
    Returns:
        Results for each asset
    """
    from app.services.backfill import backfill_all_assets
    
    end = date.today()
    start = end - timedelta(days=days)
    
    results = backfill_all_assets(
        start=start,
        end=end,
        asset_ids=asset_ids
    )
    
    success_count = sum(1 for r in results if r["status"] == "success")
    
    return {
        "total": len(results),
        "success": success_count,
        "failed": len(results) - success_count,
        "results": results
    }
