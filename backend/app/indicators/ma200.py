"""MA200 Indicator - 200日均线偏离度."""
from datetime import date, datetime, timedelta
from typing import List, Optional
import pandas as pd
import numpy as np

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.price_data import PriceData
from app.indicators.base import BaseIndicatorProcessor, IndicatorResult
from app.indicators.registry import register_processor
from app.indicators.init_targets import ensure_binance_asset, ensure_yfinance_asset, ensure_indicator


@register_processor
class MA200Indicator(BaseIndicatorProcessor):
    """
    200日均线偏离度指标.
    
    计算当前价格相对于200日均线的偏离程度。
    用于判断中长期趋势和估值水平。
    
    参数:
        period: 均线周期，默认200日
        price_field: 使用的价格字段，默认"close"
    """
    
    name = "MA200"
    display_name = "200日均线偏离度"
    description = "计算价格相对于200日均线的偏离百分比"
    
    default_params = {
        "period": 200,
        "price_field": "close"
    }
    
    param_descriptions = {
        "period": "均线周期（天数）",
        "price_field": "使用的价格字段 (open/high/low/close)"
    }
    
    output_fields = [
        {"name": "value", "type": "float", "description": "偏离百分比 (%)"},
        {"name": "value_text", "type": "string", "description": "文本描述", "optional": True},
        {"name": "grade", "type": "string", "description": "档位: very_low/low/medium/high/very_high", "optional": True},
        {"name": "grade_label", "type": "string", "description": "档位标签", "optional": True},
        {"name": "ma_value", "type": "float", "description": "200日均线值", "optional": True},
        {"name": "current_price", "type": "float", "description": "当前价格", "optional": True},
    ]
    
    # 分档配置：根据偏离度分档
    grading_config = {
        "grades": [
            {"grade": "very_low", "min": float('-inf'), "max": -50, "label": "极度低估"},
            {"grade": "low", "min": -50, "max": -25, "label": "低估"},
            {"grade": "medium_low", "min": -25, "max": -10, "label": "偏低"},
            {"grade": "medium", "min": -10, "max": 10, "label": "合理"},
            {"grade": "medium_high", "min": 10, "max": 25, "label": "偏高"},
            {"grade": "high", "min": 25, "max": 50, "label": "高估"},
            {"grade": "very_high", "min": 50, "max": float('inf'), "label": "极度高估"},
        ]
    }
    
    async def calculate(
        self,
        asset_id: str,
        start: date,
        end: date
    ) -> List[IndicatorResult]:
        """Calculate MA200 deviation for given date range."""
        period = self.params.get("period", 200)
        price_field = self.params.get("price_field", "close")
        
        # Need extra data for MA calculation (200 days + buffer)
        buffer_days = period + 30
        data_start = start - timedelta(days=buffer_days)
        
        # Fetch price data from database
        db = SessionLocal()
        try:
            prices = db.query(PriceData).filter(
                PriceData.asset_id == asset_id,
                PriceData.date >= data_start,
                PriceData.date <= end,
                PriceData.interval == "1d"
            ).order_by(PriceData.date).all()
        finally:
            db.close()
        
        # Need at least period + 10 days of data
        if len(prices) < period + 10:
            print(f"  Insufficient data: {len(prices)} records, need {period + 10}")
            return []
        
        # Convert to DataFrame
        df = pd.DataFrame([
            {
                "date": p.date,
                "close": p.close,
                "open": p.open,
                "high": p.high,
                "low": p.low,
            }
            for p in prices
        ])
        df.set_index("date", inplace=True)
        
        # Calculate 200-day MA directly on daily data
        df["ma200"] = df[price_field].rolling(window=period, min_periods=period).mean()
        
        # Calculate deviation percentage
        df["deviation"] = ((df[price_field] - df["ma200"]) / df["ma200"] * 100)
        
        # Filter to requested date range
        df = df[df.index >= start]
        df = df[df.index <= end]
        
        # Convert to results
        results = []
        for idx, row in df.iterrows():
            if pd.isna(row["deviation"]):
                continue
            
            value = float(row["deviation"])
            grading = self.apply_grading(value)
            
            # Generate text description
            value_text = self._generate_description(value, grading.get("grade_label"))
            
            results.append(IndicatorResult(
                date=idx if isinstance(idx, date) else idx.date(),
                timestamp=datetime.combine(idx if isinstance(idx, date) else idx.date(), datetime.min.time()),
                value=value,
                value_text=value_text,
                grade=grading.get("grade"),
                grade_label=grading.get("grade_label"),
                extra_data={
                    "ma_value": float(row["ma200"]) if not pd.isna(row["ma200"]) else None,
                    "current_price": float(row[price_field]) if not pd.isna(row[price_field]) else None,
                }
            ))
        
        return results
    
    def _generate_description(self, deviation: float, grade_label: Optional[str]) -> str:
        """Generate text description for deviation."""
        if deviation < -50:
            return f"极度低估 ({deviation:.1f}%)"
        elif deviation < -25:
            return f"显著低估 ({deviation:.1f}%)"
        elif deviation < -10:
            return f"略微低估 ({deviation:.1f}%)"
        elif deviation < 10:
            return f"估值合理 ({deviation:+.1f}%)"
        elif deviation < 25:
            return f"略微高估 ({deviation:+.1f}%)"
        elif deviation < 50:
            return f"显著高估 ({deviation:+.1f}%)"
        else:
            return f"极度高估 ({deviation:+.1f}%)"


def init_ma200_targets(db: Session) -> int:
    """
    Initialize required assets + MA200 indicators.

    Rules:
    - Ensure ^GSPC exists through yfinance channel and is watched.
    - Ensure BTCUSDT exists through Binance channel and is watched.
    - Ensure MA200 indicator exists for both assets.
    """
    created = 0

    targets = [
        ("^GSPC", "yfinance"),
        ("BTCUSDT", "binance"),
    ]
    for asset_id, source in targets:
        if source == "yfinance":
            asset = ensure_yfinance_asset(db, asset_id=asset_id, watch=True)
        else:
            asset = ensure_binance_asset(db, asset_id=asset_id, watch=True)

        if not asset:
            continue

        if ensure_indicator(
            db=db,
            template_id="MA200",
            asset_id=asset_id,
            name=f"{asset.symbol} 200日均线偏离度",
            params={"period": 200, "price_field": "close"},
        ):
            created += 1

    return created
