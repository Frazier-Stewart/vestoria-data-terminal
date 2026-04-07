"""VIX Indicator - 波动率指数."""
from datetime import date, datetime, timedelta
from typing import List, Optional
import yfinance as yf
import pandas as pd

from app.indicators.base import BaseIndicatorProcessor, IndicatorResult
from app.indicators.registry import register_processor
from app.core.config import settings

# Configure yfinance proxy if set
if settings.PROXY_URL:
    yf.config.network.proxy = {
        "http": settings.PROXY_URL,
        "https": settings.PROXY_URL,
    }


@register_processor
class VIXIndicator(BaseIndicatorProcessor):
    """
    VIX 波动率指数.
    
    VIX (Volatility Index) 是衡量市场恐慌程度的指标。
    - VIX < 20: 市场平静
    - 20 ≤ VIX < 30: 市场紧张
    - VIX ≥ 30: 市场恐慌
    
    数据来源: Yahoo Finance (^VIX)
    """
    
    name = "VIX"
    display_name = "VIX波动率指数"
    description = "CBOE Volatility Index (市场恐慌指数)"
    
    default_params = {
        "symbol": "^VIX",
        "threshold_low": 20,      # 平静/紧张分界线
        "threshold_high": 30,     # 紧张/恐慌分界线
    }
    
    param_descriptions = {
        "symbol": "Yahoo Finance 代码",
        "threshold_low": "低波动阈值",
        "threshold_high": "高波动阈值",
    }
    
    output_fields = [
        {"name": "value", "type": "float", "description": "VIX值"},
        {"name": "value_text", "type": "string", "description": "市场状态描述"},
        {"name": "grade", "type": "string", "description": "档位: calm/normal/fear/panic"},
        {"name": "grade_label", "type": "string", "description": "档位标签"},
    ]
    
    grading_config = {
        "grades": [
            {"grade": "calm", "min": 0, "max": 15, "label": "极度平静"},
            {"grade": "low", "min": 15, "max": 20, "label": "低波动"},
            {"grade": "normal", "min": 20, "max": 25, "label": "正常波动"},
            {"grade": "elevated", "min": 25, "max": 30, "label": "波动加剧"},
            {"grade": "fear", "min": 30, "max": 40, "label": "市场恐慌"},
            {"grade": "panic", "min": 40, "max": float('inf'), "label": "极度恐慌"},
        ]
    }
    
    async def calculate(
        self,
        asset_id: str,
        start: date,
        end: date
    ) -> List[IndicatorResult]:
        """Fetch VIX data from Yahoo Finance."""
        symbol = self.params.get("symbol", "^VIX")
        
        try:
            ticker = yf.Ticker(symbol)
            
            # Download data
            df = ticker.history(start=start, end=end + timedelta(days=1))
            
            if df.empty:
                return []
            
            results = []
            for idx, row in df.iterrows():
                value = float(row["Close"])
                grading = self.apply_grading(value)
                
                results.append(IndicatorResult(
                    date=idx.date(),
                    timestamp=datetime.combine(idx.date(), datetime.min.time()),
                    value=value,
                    value_text=self._generate_description(value, grading.get("grade_label")),
                    grade=grading.get("grade"),
                    grade_label=grading.get("grade_label"),
                    extra_data={
                        "open": float(row["Open"]) if "Open" in row else None,
                        "high": float(row["High"]) if "High" in row else None,
                        "low": float(row["Low"]) if "Low" in row else None,
                        "volume": int(row["Volume"]) if "Volume" in row else None,
                    }
                ))
            
            return results
        except Exception as e:
            print(f"Error fetching VIX data: {e}")
            return []
    
    async def calculate_latest(self, asset_id: str) -> Optional[IndicatorResult]:
        """Fetch latest VIX value."""
        symbol = self.params.get("symbol", "^VIX")
        
        try:
            ticker = yf.Ticker(symbol)
            
            # Get today's data
            today = datetime.now().date()
            hist = ticker.history(period="5d")
            
            if hist.empty:
                return None
            
            # Get latest value
            latest = hist.iloc[-1]
            idx = hist.index[-1]
            value = float(latest["Close"])
            grading = self.apply_grading(value)
            
            return IndicatorResult(
                date=idx.date(),
                timestamp=datetime.combine(idx.date(), datetime.min.time()),
                value=value,
                value_text=self._generate_description(value, grading.get("grade_label")),
                grade=grading.get("grade"),
                grade_label=grading.get("grade_label"),
                extra_data={
                    "open": float(latest["Open"]) if "Open" in latest else None,
                    "high": float(latest["High"]) if "High" in latest else None,
                    "low": float(latest["Low"]) if "Low" in latest else None,
                    "volume": int(latest["Volume"]) if "Volume" in latest else None,
                }
            )
        except Exception as e:
            print(f"Error fetching latest VIX: {e}")
            return None
    
    def _generate_description(self, value: float, grade_label: Optional[str]) -> str:
        """Generate text description for VIX value."""
        if value < 15:
            return f"极度平静 ({value:.2f})"
        elif value < 20:
            return f"低波动 ({value:.2f})"
        elif value < 25:
            return f"正常波动 ({value:.2f})"
        elif value < 30:
            return f"波动加剧 ({value:.2f})"
        elif value < 40:
            return f"市场恐慌 ({value:.2f})"
        else:
            return f"极度恐慌 ({value:.2f})"
