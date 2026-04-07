"""Asset schemas."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class AssetBase(BaseModel):
    """Base asset schema."""
    symbol: str = Field(..., description="标的代码，如 BTC")
    name: str = Field(..., description="标的名称，如 Bitcoin USD")
    asset_type: str = Field(..., description="类型: crypto/stock/etf/commodity/fund/index")
    exchange: Optional[str] = Field(None, description="交易所")
    country: Optional[str] = Field(None, description="所属市场")
    currency: str = Field(default="USD", description="计价货币")
    data_source: str = Field(..., description="数据源标识")
    source_symbol: str = Field(..., description="数据源原始代码")
    is_active: bool = Field(default=True)
    is_watched: bool = Field(default=False, description="是否在关注列表中")
    config: Optional[dict] = Field(default_factory=dict, description="额外配置")


class AssetCreate(AssetBase):
    """Create asset schema."""
    id: str = Field(..., description="唯一标识，如 BTC-USD")


class AssetUpdate(BaseModel):
    """Update asset schema."""
    name: Optional[str] = None
    is_active: Optional[bool] = None
    is_watched: Optional[bool] = None
    config: Optional[dict] = None


class AssetResponse(AssetBase):
    """Asset response schema."""
    id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
