"""Market sentiment indicators fetcher."""
from datetime import date, datetime
from typing import List, Optional
import requests
import pandas as pd
from io import StringIO
from sqlalchemy.orm import Session

from app.indicators.base import BaseIndicatorProcessor, IndicatorResult
from app.indicators.registry import register_processor
from app.indicators.init_targets import ensure_binance_asset, ensure_indicator


@register_processor
class BTCFearGreedIndicator(BaseIndicatorProcessor):
    """
    BTC 恐慌贪婪指数.
    
    数据来源: alternative.me
    https://api.alternative.me/fng/
    
    指数范围: 0-100
    - 0-24: 极度恐惧 (Extreme Fear)
    - 25-49: 恐惧 (Fear)
    - 50-74: 贪婪 (Greed)
    - 75-100: 极度贪婪 (Extreme Greed)
    """
    
    name = "BTC_FEAR_GREED"
    display_name = "BTC恐慌贪婪指数"
    description = "Alternative.me BTC Fear & Greed Index"
    
    default_params = {
        "api_url": "https://api.alternative.me/fng/",
    }
    
    output_fields = [
        {"name": "value", "type": "float", "description": "指数值 (0-100)"},
        {"name": "value_text", "type": "string", "description": "情绪描述"},
        {"name": "grade", "type": "string", "description": "档位: extreme_fear/fear/neutral/greed/extreme_greed"},
        {"name": "grade_label", "type": "string", "description": "档位标签"},
    ]
    
    grading_config = {
        "grades": [
            {"grade": "extreme_fear", "min": 0, "max": 25, "label": "极度恐惧"},
            {"grade": "fear", "min": 25, "max": 50, "label": "恐惧"},
            {"grade": "neutral", "min": 46, "max": 55, "label": "中性"},
            {"grade": "greed", "min": 50, "max": 75, "label": "贪婪"},
            {"grade": "extreme_greed", "min": 75, "max": 100, "label": "极度贪婪"},
        ]
    }
    
    async def calculate(
        self,
        asset_id: str,
        start: date,
        end: date
    ) -> List[IndicatorResult]:
        """Fetch BTC fear & greed data from API."""
        api_url = self.params.get("api_url", "https://api.alternative.me/fng/")
        
        # Calculate days needed
        days = (end - start).days + 30  # Add buffer
        
        try:
            response = requests.get(
                api_url,
                params={
                    "limit": min(days, 1000),  # API limit
                    "format": "json"
                },
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            print(f"Error fetching BTC fear & greed: {e}")
            return []
        
        if "data" not in data:
            return []
        
        results = []
        for item in data["data"]:
            try:
                # Parse timestamp (API returns timestamp in seconds)
                timestamp = datetime.fromtimestamp(int(item["timestamp"]))
                value = float(item["value"])
                value_classification = item.get("value_classification", "")
                
                # Filter by date range
                if timestamp.date() < start or timestamp.date() > end:
                    continue
                
                # Apply grading
                grading = self.apply_grading(value)
                
                results.append(IndicatorResult(
                    date=timestamp.date(),
                    timestamp=timestamp,
                    value=value,
                    value_text=self._get_chinese_label(value_classification),
                    grade=grading.get("grade"),
                    grade_label=grading.get("grade_label"),
                    extra_data={
                        "classification": value_classification,
                    }
                ))
            except (KeyError, ValueError) as e:
                print(f"Error parsing item: {e}")
                continue
        
        # Sort by date
        results.sort(key=lambda x: x.date)
        return results
    
    async def calculate_latest(self, asset_id: str) -> Optional[IndicatorResult]:
        """Fetch latest BTC fear & greed value."""
        api_url = self.params.get("api_url", "https://api.alternative.me/fng/")
        
        try:
            response = requests.get(
                api_url,
                params={"limit": 1, "format": "json"},
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            print(f"Error fetching latest BTC fear & greed: {e}")
            return None
        
        if not data.get("data"):
            return None
        
        item = data["data"][0]
        try:
            timestamp = datetime.fromtimestamp(int(item["timestamp"]))
            value = float(item["value"])
            value_classification = item.get("value_classification", "")
            
            grading = self.apply_grading(value)
            
            return IndicatorResult(
                date=timestamp.date(),
                timestamp=timestamp,
                value=value,
                value_text=self._get_chinese_label(value_classification),
                grade=grading.get("grade"),
                grade_label=grading.get("grade_label"),
                extra_data={
                    "classification": value_classification,
                }
            )
        except (KeyError, ValueError) as e:
            print(f"Error parsing latest item: {e}")
            return None
    
    def _get_chinese_label(self, classification: str) -> str:
        """Convert English classification to Chinese."""
        mapping = {
            "Extreme Fear": "极度恐惧",
            "Fear": "恐惧",
            "Neutral": "中性",
            "Greed": "贪婪",
            "Extreme Greed": "极度贪婪",
        }
        return mapping.get(classification, classification)


def init_btc_fear_greed_targets(db: Session) -> int:
    """
    Initialize required asset + indicator instances for BTC Fear & Greed.

    Rules:
    - Ensure BTCUSDT exists through Binance channel and is watched.
    - Ensure BTC_FEAR_GREED indicator exists for BTCUSDT.
    """
    created = 0
    btc_asset = ensure_binance_asset(db, asset_id="BTCUSDT", watch=True)
    if btc_asset:
        if ensure_indicator(
            db=db,
            template_id="BTC_FEAR_GREED",
            asset_id="BTCUSDT",
            name="BTC恐慌贪婪指数",
            params={"api_url": "https://api.alternative.me/fng/"},
        ):
            created += 1
    return created
