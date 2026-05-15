"""Indicator schemas."""
from datetime import datetime, date
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


# ============ Indicator Template Schemas ============

class IndicatorTemplateBase(BaseModel):
    """Base schema for indicator template."""
    id: str = Field(..., description="模板唯一标识，如 'MA200'")
    name: str = Field(..., description="显示名称")
    description: Optional[str] = Field(None, description="描述")
    indicator_type: str = Field(..., description="指标类型: metric/signal/composite")
    category: Optional[str] = Field(None, description="分类: trend/momentum/volatility/sentiment")
    processor_class: str = Field(..., description="处理器类名")
    default_params: Dict[str, Any] = Field(default_factory=dict, description="默认参数")
    output_fields: List[Dict[str, Any]] = Field(default_factory=list, description="输出字段定义")
    grading_config: Optional[Dict[str, Any]] = Field(None, description="分档配置")
    is_active: bool = Field(default=True, description="是否激活")


class IndicatorTemplateCreate(IndicatorTemplateBase):
    """Schema for creating indicator template."""
    pass


class IndicatorTemplateUpdate(BaseModel):
    """Schema for updating indicator template."""
    name: Optional[str] = None
    description: Optional[str] = None
    default_params: Optional[Dict[str, Any]] = None
    output_fields: Optional[List[Dict[str, Any]]] = None
    grading_config: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class IndicatorTemplateResponse(IndicatorTemplateBase):
    """Schema for indicator template response."""
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============ Indicator Instance Schemas ============

class IndicatorBase(BaseModel):
    """Base schema for indicator instance."""
    template_id: str = Field(..., description="模板ID")
    asset_id: str = Field(..., description="标的ID")
    name: str = Field(..., description="实例名称")
    params: Dict[str, Any] = Field(default_factory=dict, description="实例参数")
    is_active: bool = Field(default=True, description="是否激活")


class IndicatorCreate(IndicatorBase):
    """Schema for creating indicator instance."""
    pass


class IndicatorUpdate(BaseModel):
    """Schema for updating indicator instance."""
    name: Optional[str] = None
    params: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class IndicatorResponse(IndicatorBase):
    """Schema for indicator response."""
    id: int
    last_calculated_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    template: Optional[IndicatorTemplateResponse] = None
    config: Optional[Dict[str, Any]] = None  # Asset-specific config (e.g., MA200 multipliers)

    class Config:
        from_attributes = True


# ============ Indicator Value Schemas ============

class IndicatorValueBase(BaseModel):
    """Base schema for indicator value."""
    date: date
    value: float
    value_text: Optional[str] = None
    grade: Optional[str] = None
    grade_label: Optional[str] = None
    extra_data: Dict[str, Any] = Field(default_factory=dict)


class IndicatorValueCreate(IndicatorValueBase):
    """Schema for creating indicator value."""
    indicator_id: int
    timestamp: datetime


class IndicatorValueResponse(IndicatorValueBase):
    """Schema for indicator value response."""
    id: int
    indicator_id: int
    timestamp: datetime
    source: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ============ Request/Response Schemas ============

class CalculateIndicatorRequest(BaseModel):
    """Request schema for calculating indicator."""
    start: Optional[date] = Field(None, description="开始日期，默认30天前")
    end: Optional[date] = Field(None, description="结束日期，默认今天")


class CalculateIndicatorResponse(BaseModel):
    """Response schema for calculate indicator."""
    indicator_id: int
    calculated_count: int
    message: str


class IndicatorQueryParams(BaseModel):
    """Query parameters for indicator values."""
    start: Optional[date] = Field(None, description="开始日期")
    end: Optional[date] = Field(None, description="结束日期")
    limit: int = Field(default=100, ge=1, le=1000, description="返回数量限制")
