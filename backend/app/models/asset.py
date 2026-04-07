"""Asset model."""
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, DateTime, Boolean, JSON
from sqlalchemy.orm import relationship

from app.core.database import Base


class Asset(Base):
    """Asset (标的) model."""
    
    __tablename__ = "assets"
    
    # Primary key - 唯一标识，如 "BTC-USD"
    id = Column(String, primary_key=True, index=True)
    
    # Basic info
    symbol = Column(String, nullable=False, index=True)  # 代码，如 "BTC"
    name = Column(String, nullable=False)  # 名称，如 "Bitcoin USD"
    
    # Classification
    asset_type = Column(String, nullable=False, index=True)  # crypto/stock/etf/commodity/fund/index
    exchange = Column(String, nullable=True)  # 交易所，如 "NASDAQ"
    country = Column(String, nullable=True)  # 所属市场，如 "US"
    currency = Column(String, default="USD")  # 计价货币
    
    # Data source config
    data_source = Column(String, nullable=False)  # 数据源，如 "yfinance"
    source_symbol = Column(String, nullable=False)  # 数据源原始代码
    
    # Status
    is_active = Column(Boolean, default=True)
    is_watched = Column(Boolean, default=False, index=True)  # 是否在关注列表中
    
    # Extra config (JSON)
    config = Column(JSON, default=dict)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    price_data = relationship("PriceData", back_populates="asset", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Asset(id='{self.id}', symbol='{self.symbol}', type='{self.asset_type}')>"
