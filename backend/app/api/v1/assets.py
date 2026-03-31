"""Asset API routes."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.asset import Asset
from app.schemas.asset import AssetCreate, AssetUpdate, AssetResponse
from app.services.yfinance_search import yfinance_service

router = APIRouter(prefix="/assets", tags=["assets"])


# ============ Pydantic Models for Search ============

class StockInfoResponse(BaseModel):
    """股票信息响应"""
    symbol: str
    name: str
    sector: Optional[str] = None
    industry: Optional[str] = None
    market_cap: Optional[float] = None
    trailing_pe: Optional[float] = None
    price: Optional[float] = None
    currency: str = "USD"
    exchange: Optional[str] = None


class SectorResponse(BaseModel):
    """板块响应"""
    key: str
    name: str
    name_zh: str
    company_count: int


class IndustryResponse(BaseModel):
    """子行业响应"""
    key: str
    name: str
    symbol: str
    market_weight: Optional[float] = None


class SearchResponse(BaseModel):
    """搜索响应"""
    query: str
    results: List[StockInfoResponse]
    count: int


# ============ NEW: Search Endpoints (must be before /{asset_id}) ============

@router.get("/search/yfinance", response_model=SearchResponse)
async def search_stocks(
    q: str = Query(..., description="搜索关键词 (代码或名称)"),
    limit: int = Query(20, ge=1, le=100, description="返回数量限制")
):
    """
    搜索股票
    
    支持:
    - 按代码搜索 (如: AAPL, MSFT)
    - 按名称搜索 (如: Apple)
    - 预定义股票池优先 (GLD, SPY 等)
    """
    results = yfinance_service.search_by_symbol(q)
    
    return SearchResponse(
        query=q,
        results=[StockInfoResponse(**vars(r)) for r in results[:limit]],
        count=len(results[:limit])
    )


@router.get("/sectors", response_model=List[SectorResponse])
async def get_sectors():
    """
    获取所有 GICS 板块
    
    返回 11 个标准 GICS 板块及其基本信息
    """
    sectors = yfinance_service.get_sectors()
    return [SectorResponse(**s) for s in sectors]


@router.get("/sectors/{sector_key}/industries", response_model=List[IndustryResponse])
async def get_industries_by_sector(sector_key: str):
    """
    获取指定板块下的所有子行业
    
    - sector_key: 板块代码 (如: technology, financial-services)
    """
    industries = yfinance_service.get_industries_by_sector(sector_key)
    return [IndustryResponse(**i) for i in industries]


@router.get("/sectors/{sector_key}/top-companies", response_model=List[StockInfoResponse])
async def get_top_companies_by_sector(
    sector_key: str,
    count: int = Query(20, ge=1, le=100, description="返回数量"),
    sort_by: str = Query("market_cap", enum=["market_cap", "trailing_pe", "name"], description="排序字段")
):
    """
    获取板块内市值最高的公司
    
    使用 Yahoo Finance 的板块筛选器，按市值排序
    
    - sector_key: 板块代码
    - count: 返回数量 (默认20)
    - sort_by: 排序方式 (market_cap/trailing_pe/name)
    """
    results = yfinance_service.get_top_companies_by_sector(sector_key, count, sort_by)
    return [StockInfoResponse(**vars(r)) for r in results]


@router.get("/industries/{industry_key}/top-companies", response_model=List[StockInfoResponse])
async def get_top_companies_by_industry(
    industry_key: str,
    count: int = Query(10, ge=1, le=50, description="返回数量")
):
    """
    获取子行业内的龙头公司
    
    - industry_key: 子行业代码 (如: software-infrastructure, banks-diversified)
    - count: 返回数量 (默认10)
    """
    results = yfinance_service.get_top_companies_by_industry(industry_key, count)
    return [StockInfoResponse(**vars(r)) for r in results]


@router.get("/predefined", response_model=List[StockInfoResponse])
async def get_predefined_tickers():
    """
    获取预定义的核心股票池
    
    包括: GLD, SPY, QQQ, Sector SPDRs 等常用标的
    """
    results = yfinance_service.get_predefined_tickers()
    return [StockInfoResponse(**vars(r)) for r in results]


# ============ Original CRUD Endpoints ============

@router.post("", response_model=AssetResponse)
def create_asset(asset: AssetCreate, db: Session = Depends(get_db)):
    """Create a new asset."""
    # Check if asset already exists
    db_asset = db.query(Asset).filter(Asset.id == asset.id).first()
    if db_asset:
        raise HTTPException(status_code=400, detail="Asset already exists")
    
    db_asset = Asset(**asset.model_dump())
    db.add(db_asset)
    db.commit()
    db.refresh(db_asset)
    return db_asset


@router.get("", response_model=List[AssetResponse])
def list_assets(
    asset_type: str = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all assets."""
    query = db.query(Asset)
    if asset_type:
        query = query.filter(Asset.asset_type == asset_type)
    return query.offset(skip).limit(limit).all()


@router.get("/{asset_id}", response_model=AssetResponse)
def get_asset(asset_id: str, db: Session = Depends(get_db)):
    """Get asset by ID."""
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset


@router.put("/{asset_id}", response_model=AssetResponse)
def update_asset(asset_id: str, asset_update: AssetUpdate, db: Session = Depends(get_db)):
    """Update an asset."""
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    update_data = asset_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(asset, field, value)
    
    db.commit()
    db.refresh(asset)
    return asset


@router.delete("/{asset_id}")
def delete_asset(asset_id: str, db: Session = Depends(get_db)):
    """Delete an asset."""
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    db.delete(asset)
    db.commit()
    return {"message": "Asset deleted successfully"}
