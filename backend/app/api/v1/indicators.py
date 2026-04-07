"""Indicator API routes."""
from datetime import date, datetime, timedelta
from typing import List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.core.database import get_db
from app.models.indicator import IndicatorTemplate, Indicator, IndicatorValue
from app.models.asset import Asset
from app.schemas.indicator import (
    IndicatorTemplateCreate, IndicatorTemplateUpdate, IndicatorTemplateResponse,
    IndicatorCreate, IndicatorUpdate, IndicatorResponse,
    IndicatorValueResponse, CalculateIndicatorRequest, CalculateIndicatorResponse,
    IndicatorQueryParams
)
from app.indicators.registry import create_processor

router = APIRouter(prefix="/indicators", tags=["indicators"])


# ============ Template Routes ============

@router.post("/templates", response_model=IndicatorTemplateResponse)
def create_template(template: IndicatorTemplateCreate, db: Session = Depends(get_db)):
    """Create a new indicator template."""
    db_template = db.query(IndicatorTemplate).filter(IndicatorTemplate.id == template.id).first()
    if db_template:
        raise HTTPException(status_code=400, detail="Template already exists")
    
    db_template = IndicatorTemplate(**template.model_dump())
    db.add(db_template)
    db.commit()
    db.refresh(db_template)
    return db_template


@router.get("/templates", response_model=List[IndicatorTemplateResponse])
def list_templates(
    indicator_type: str = None,
    category: str = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List indicator templates."""
    query = db.query(IndicatorTemplate)
    if indicator_type:
        query = query.filter(IndicatorTemplate.indicator_type == indicator_type)
    if category:
        query = query.filter(IndicatorTemplate.category == category)
    return query.offset(skip).limit(limit).all()


@router.get("/templates/{template_id}", response_model=IndicatorTemplateResponse)
def get_template(template_id: str, db: Session = Depends(get_db)):
    """Get indicator template by ID."""
    template = db.query(IndicatorTemplate).filter(IndicatorTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template


@router.put("/templates/{template_id}", response_model=IndicatorTemplateResponse)
def update_template(template_id: str, template_update: IndicatorTemplateUpdate, db: Session = Depends(get_db)):
    """Update indicator template."""
    template = db.query(IndicatorTemplate).filter(IndicatorTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    update_data = template_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(template, field, value)
    
    db.commit()
    db.refresh(template)
    return template


@router.delete("/templates/{template_id}")
def delete_template(template_id: str, db: Session = Depends(get_db)):
    """Delete indicator template."""
    template = db.query(IndicatorTemplate).filter(IndicatorTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    db.delete(template)
    db.commit()
    return {"message": "Template deleted successfully"}


# ============ Indicator Instance Routes ============

@router.post("", response_model=IndicatorResponse)
def create_indicator(indicator: IndicatorCreate, db: Session = Depends(get_db)):
    """Create a new indicator instance."""
    # Check template exists
    template = db.query(IndicatorTemplate).filter(IndicatorTemplate.id == indicator.template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    # Check asset exists
    asset = db.query(Asset).filter(Asset.id == indicator.asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    # Check duplicate
    existing = db.query(Indicator).filter(
        Indicator.template_id == indicator.template_id,
        Indicator.asset_id == indicator.asset_id,
        Indicator.name == indicator.name
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Indicator already exists")
    
    db_indicator = Indicator(**indicator.model_dump())
    db.add(db_indicator)
    db.commit()
    db.refresh(db_indicator)
    return db_indicator


@router.get("", response_model=List[IndicatorResponse])
def list_indicators(
    asset_id: str = None,
    template_id: str = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List indicator instances."""
    query = db.query(Indicator)
    if asset_id:
        query = query.filter(Indicator.asset_id == asset_id)
    if template_id:
        query = query.filter(Indicator.template_id == template_id)
    return query.offset(skip).limit(limit).all()


@router.get("/{indicator_id}", response_model=IndicatorResponse)
def get_indicator(indicator_id: int, db: Session = Depends(get_db)):
    """Get indicator instance by ID."""
    indicator = db.query(Indicator).filter(Indicator.id == indicator_id).first()
    if not indicator:
        raise HTTPException(status_code=404, detail="Indicator not found")
    return indicator


@router.put("/{indicator_id}", response_model=IndicatorResponse)
def update_indicator(indicator_id: int, indicator_update: IndicatorUpdate, db: Session = Depends(get_db)):
    """Update indicator instance."""
    indicator = db.query(Indicator).filter(Indicator.id == indicator_id).first()
    if not indicator:
        raise HTTPException(status_code=404, detail="Indicator not found")
    
    update_data = indicator_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(indicator, field, value)
    
    db.commit()
    db.refresh(indicator)
    return indicator


@router.delete("/{indicator_id}")
def delete_indicator(indicator_id: int, db: Session = Depends(get_db)):
    """Delete indicator instance."""
    indicator = db.query(Indicator).filter(Indicator.id == indicator_id).first()
    if not indicator:
        raise HTTPException(status_code=404, detail="Indicator not found")
    
    db.delete(indicator)
    db.commit()
    return {"message": "Indicator deleted successfully"}


# ============ Indicator Value Routes ============

@router.get("/{indicator_id}/values", response_model=List[IndicatorValueResponse])
def get_indicator_values(
    indicator_id: int,
    start: date = None,
    end: date = None,
    limit: int = 100,
    auto_fetch: bool = Query(True, description="数据为空时自动获取历史数据"),
    db: Session = Depends(get_db)
):
    """Get indicator values.
    
    - auto_fetch: 如果数据库中没有数据且此参数为 true，自动计算/获取历史数据（默认过去4年）
    """
    import asyncio
    from app.indicators.registry import create_processor
    
    indicator = db.query(Indicator).filter(Indicator.id == indicator_id).first()
    if not indicator:
        raise HTTPException(status_code=404, detail="Indicator not found")
    
    query = db.query(IndicatorValue).filter(IndicatorValue.indicator_id == indicator_id)
    
    if start:
        query = query.filter(IndicatorValue.date >= start)
    if end:
        query = query.filter(IndicatorValue.date <= end)
    
    values = query.order_by(desc(IndicatorValue.date)).limit(limit).all()
    
    # 自动获取数据模式：如果数据库为空且允许自动获取
    if not values and auto_fetch:
        print(f"[Indicator] No data found for indicator {indicator_id}, auto-fetching...")
        
        try:
            template = indicator.template
            if template:
                # 创建处理器
                processor = create_processor(template.processor_class, indicator.params)
                if processor:
                    # 计算过去4年的数据
                    end_date = date.today()
                    start_date = end_date - timedelta(days=4*365)  # 4年
                    
                    results = asyncio.run(processor.calculate(indicator.asset_id, start_date, end_date))
                    
                    if results:
                        # 保存到数据库
                        for result in results:
                            existing = db.query(IndicatorValue).filter(
                                IndicatorValue.indicator_id == indicator_id,
                                IndicatorValue.date == result.date
                            ).first()
                            
                            if existing:
                                existing.value = result.value
                                existing.value_text = result.value_text
                                existing.grade = result.grade
                                existing.grade_label = result.grade_label
                                existing.extra_data = result.extra_data or {}
                            else:
                                db_value = IndicatorValue(
                                    indicator_id=indicator_id,
                                    date=result.date,
                                    timestamp=result.timestamp,
                                    value=result.value,
                                    value_text=result.value_text,
                                    grade=result.grade,
                                    grade_label=result.grade_label,
                                    extra_data=result.extra_data or {},
                                    source="auto_fetch"
                                )
                                db.add(db_value)
                        
                        db.commit()
                        print(f"[Indicator] Auto-fetched {len(results)} values for indicator {indicator_id}")
                        
                        # 重新查询获取最新数据
                        values = query.order_by(desc(IndicatorValue.date)).limit(limit).all()
        except Exception as e:
            print(f"[Indicator] Auto-fetch failed for indicator {indicator_id}: {e}")
            # 不抛出异常，返回空列表
    
    return values[::-1]  # Return in ascending order


# ============ Calculation Routes ============

async def _calculate_indicator_task(indicator_id: int, start: date, end: date):
    """Background task to calculate indicator values."""
    from app.core.database import SessionLocal
    
    db = SessionLocal()
    try:
        indicator = db.query(Indicator).filter(Indicator.id == indicator_id).first()
        if not indicator:
            return
        
        template = indicator.template
        if not template:
            return
        
        # Create processor
        processor_class = template.processor_class
        # Extract class name from processor_class path
        if "." in processor_class:
            # e.g., "app.indicators.ma200.MA200Indicator" -> get from registry by name
            # The processor should be registered by its name attribute
            from app.indicators.registry import get_processor
            # Map class path to registered name
            processor_name = processor_class.split(".")[-1].replace("Indicator", "")
            processor = create_processor(processor_name, indicator.params)
        else:
            processor = create_processor(processor_class, indicator.params)
        
        if not processor:
            print(f"Processor not found: {processor_class}")
            return
        
        # Calculate values
        results = await processor.calculate(indicator.asset_id, start, end)
        
        # Save to database
        for result in results:
            # Check if value already exists for this date
            existing = db.query(IndicatorValue).filter(
                IndicatorValue.indicator_id == indicator_id,
                IndicatorValue.date == result.date
            ).first()
            
            if existing:
                # Update existing
                existing.value = result.value
                existing.value_text = result.value_text
                existing.grade = result.grade
                existing.grade_label = result.grade_label
                existing.extra_data = result.extra_data or {}
                existing.timestamp = result.timestamp
            else:
                # Create new
                db_value = IndicatorValue(
                    indicator_id=indicator_id,
                    date=result.date,
                    timestamp=result.timestamp,
                    value=result.value,
                    value_text=result.value_text,
                    grade=result.grade,
                    grade_label=result.grade_label,
                    extra_data=result.extra_data or {},
                    source="calculation"
                )
                db.add(db_value)
        
        # Update indicator last calculated
        indicator.last_calculated_at = datetime.utcnow()
        db.commit()
        print(f"Calculated {len(results)} values for indicator {indicator_id}")
        
    except Exception as e:
        print(f"Error calculating indicator {indicator_id}: {e}")
        db.rollback()
    finally:
        db.close()


@router.post("/{indicator_id}/calculate", response_model=CalculateIndicatorResponse)
def calculate_indicator(
    indicator_id: int,
    request: CalculateIndicatorRequest = None,
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db)
):
    """Trigger indicator calculation."""
    indicator = db.query(Indicator).filter(Indicator.id == indicator_id).first()
    if not indicator:
        raise HTTPException(status_code=404, detail="Indicator not found")
    
    # Determine date range
    end = request.end if request and request.end else datetime.now().date()
    start = request.start if request and request.start else end - timedelta(days=365)
    
    # Run calculation in background
    if background_tasks:
        background_tasks.add_task(_calculate_indicator_task, indicator_id, start, end)
        return CalculateIndicatorResponse(
            indicator_id=indicator_id,
            calculated_count=0,
            message="Calculation started in background"
        )
    else:
        # Synchronous calculation (for testing)
        import asyncio
        asyncio.create_task(_calculate_indicator_task(indicator_id, start, end))
        return CalculateIndicatorResponse(
            indicator_id=indicator_id,
            calculated_count=0,
            message="Calculation started"
        )


@router.get("/{indicator_id}/latest", response_model=IndicatorValueResponse)
def get_latest_value(indicator_id: int, db: Session = Depends(get_db)):
    """Get latest indicator value."""
    indicator = db.query(Indicator).filter(Indicator.id == indicator_id).first()
    if not indicator:
        raise HTTPException(status_code=404, detail="Indicator not found")
    
    value = db.query(IndicatorValue).filter(
        IndicatorValue.indicator_id == indicator_id
    ).order_by(desc(IndicatorValue.date)).first()
    
    if not value:
        raise HTTPException(status_code=404, detail="No value found")
    
    return value
