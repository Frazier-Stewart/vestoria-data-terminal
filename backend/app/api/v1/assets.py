"""Asset API routes."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.asset import Asset
from app.models.sector import Sector, Industry, SectorTopCompany, IndustryTopCompany
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
    q: Optional[str] = Query(None, description="搜索关键词 (代码或名称)"),
    sector: Optional[str] = Query(None, description="板块筛选 (如: technology)"),
    industry: Optional[str] = Query(None, description="行业筛选 (如: software)"),
    sort_by: Optional[str] = Query("market_cap", description="排序字段"),
    sort_order: Optional[str] = Query("desc", description="排序方向 (asc/desc)"),
    limit: int = Query(20, ge=1, le=100, description="返回数量限制")
):
    """
    搜索股票
    
    支持:
    - 按代码搜索 (如: AAPL, MSFT)
    - 按名称搜索 (如: Apple)
    - 按板块/行业筛选
    - 预定义股票池优先 (GLD, SPY 等)
    """
    results = []
    
    # 如果有搜索词，先搜索
    if q:
        results = yfinance_service.search_by_symbol(q, limit=limit)
    
    # 如果指定了板块，获取板块龙头
    if sector:
        sector_results = yfinance_service.get_top_companies_by_sector(sector, limit=limit)
        if q:
            # 合并结果（取交集）
            search_symbols = {r.symbol for r in results}
            results = [r for r in sector_results if r.symbol in search_symbols]
        else:
            results = sector_results
    
    # 客户端排序
    def sort_key(stock):
        if sort_by == "market_cap":
            return stock.market_cap or 0
        elif sort_by == "trailing_pe":
            return stock.trailing_pe or float('inf')
        elif sort_by == "name":
            return stock.name
        elif sort_by == "ticker":
            return stock.symbol
        return stock.market_cap or 0
    
    results = sorted(results, key=sort_key, reverse=(sort_order == "desc"))
    
    return SearchResponse(
        query=q or "",
        results=[StockInfoResponse(**vars(r)) for r in results[:limit]],
        count=len(results[:limit])
    )


@router.get("/sectors", response_model=List[SectorResponse])
async def get_sectors(db: Session = Depends(get_db)):
    """
    获取所有 GICS 板块
    
    返回 11 个标准 GICS 板块及其基本信息（从本地数据库读取）
    """
    sectors = db.query(Sector).order_by(Sector.name).all()
    return [
        SectorResponse(
            key=s.key,
            name=s.name,
            name_zh=s.name_zh or s.name,
            company_count=s.company_count or 0,
        )
        for s in sectors
    ]


@router.get("/sectors/{sector_key}/industries", response_model=List[IndustryResponse])
async def get_industries_by_sector(sector_key: str, db: Session = Depends(get_db)):
    """
    获取指定板块下的所有子行业
    
    - sector_key: 板块代码 (如: technology, financial-services)
    """
    industries = db.query(Industry).filter(Industry.sector_key == sector_key).order_by(Industry.name).all()
    return [
        IndustryResponse(
            key=i.key,
            name=i.name,
            symbol=i.symbol or "",
            market_weight=i.market_weight,
        )
        for i in industries
    ]


@router.get("/sectors/{sector_key}/top-companies", response_model=List[StockInfoResponse])
async def get_top_companies_by_sector(
    sector_key: str,
    count: int = Query(20, ge=1, le=100, description="返回数量")
):
    """
    获取指定板块下的龙头公司（按市值排序）
    
    - sector_key: 板块代码 (如: technology)
    - count: 返回公司数量
    """
    results = yfinance_service.get_top_companies_by_sector(sector_key, count=count)
    return [StockInfoResponse(**vars(r)) for r in results]


@router.get("/industries/{industry_key}/top-companies", response_model=List[StockInfoResponse])
async def get_top_companies_by_industry(
    industry_key: str,
    count: int = Query(20, ge=1, le=100, description="返回数量")
):
    """
    获取指定行业下的龙头公司（按市值排序）
    
    - industry_key: 行业代码
    - count: 返回公司数量
    """
    results = yfinance_service.get_top_companies_by_industry(industry_key, count=count)
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
        raise HTTPException(status_code=409, detail="Asset already exists")
    
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
