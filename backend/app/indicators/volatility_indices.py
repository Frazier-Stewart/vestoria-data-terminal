"""Volatility indices processors: VXN, VXD, VVIX, OVX, GVZ."""
from datetime import date, datetime, timedelta
from typing import List, Optional
import yfinance as yf
import pandas as pd

from sqlalchemy.orm import Session

from app.indicators.base import BaseIndicatorProcessor, IndicatorResult
from app.indicators.registry import register_processor
from app.indicators.init_targets import ensure_yfinance_asset, ensure_indicator
from app.core.config import settings

# Configure yfinance proxy if set
if settings.PROXY_URL:
    yf.config.network.proxy = {
        "http": settings.PROXY_URL,
        "https": settings.PROXY_URL,
    }


class VolatilityIndexProcessor(BaseIndicatorProcessor):
    """Generic volatility index processor (yfinance-based)."""

    default_params = {
        "symbol": "",
        "threshold_low": 20,
        "threshold_high": 30,
    }

    param_descriptions = {
        "symbol": "Yahoo Finance 代码",
        "threshold_low": "低波动阈值",
        "threshold_high": "高波动阈值",
    }

    output_fields = [
        {"name": "value", "type": "float", "description": "波动率指数值"},
        {"name": "value_text", "type": "string", "description": "市场状态描述"},
        {"name": "grade", "type": "string", "description": "档位"},
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
        """Fetch volatility index data from Yahoo Finance."""
        symbol = self.params.get("symbol", "")
        if not symbol:
            return []

        try:
            ticker = yf.Ticker(symbol)
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
            print(f"Error fetching {symbol} data: {e}")
            return []

    async def calculate_latest(self, asset_id: str) -> Optional[IndicatorResult]:
        """Fetch latest volatility index value."""
        symbol = self.params.get("symbol", "")
        if not symbol:
            return None

        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="5d")

            if hist.empty:
                return None

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
            print(f"Error fetching latest {symbol}: {e}")
            return None

    def _generate_description(self, value: float, grade_label: Optional[str]) -> str:
        """Generate text description for volatility value."""
        label = grade_label or ""
        return f"{label} ({value:.2f})"


# ──────────────────────────────────────────────────────────────
# 1. VIX — CBOE Volatility Index
# ──────────────────────────────────────────────────────────────
@register_processor
class VIXIndicator(VolatilityIndexProcessor):
    """
    VIX — CBOE Volatility Index.

    标普500的30天隐含波动率，最广泛使用的市场恐慌指数。
    典型区间 12~25，>30 视为恐慌，>40 极度恐慌。
    """
    name = "VIX"
    display_name = "标普500波动率指数VIX"
    description = "CBOE Volatility Index (市场恐慌指数)"
    default_params = {"symbol": "^VIX", "threshold_low": 20, "threshold_high": 30}

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


# ──────────────────────────────────────────────────────────────
# 2. VXN — Nasdaq 100 Volatility Index
# ──────────────────────────────────────────────────────────────
@register_processor
class VXNIndicator(VolatilityIndexProcessor):
    """
    VXN — CBOE Nasdaq-100 Volatility Index.

    Nasdaq-100 的 30 天隐含波动率，对标 VIX，反映科技股恐慌程度。
    典型区间 15~35，历史极端值可达 90+。
    """
    name = "VXN"
    display_name = "纳斯达克波动率指数VXN"
    description = "CBOE Nasdaq-100 Volatility Index (科技股恐慌指数)"
    default_params = {"symbol": "^VXN", "threshold_low": 20, "threshold_high": 30}


# ──────────────────────────────────────────────────────────────
# 2. VXD — DJIA Volatility Index
# ──────────────────────────────────────────────────────────────
@register_processor
class VXDIndicator(VolatilityIndexProcessor):
    """
    VXD — CBOE DJIA Volatility Index.

    道琼斯工业平均指数的 30 天隐含波动率。
    由于道指成分股较稳健，VXD 通常略低于 VIX。
    """
    name = "VXD"
    display_name = "道琼斯波动率指数VXD"
    description = "CBOE DJIA Volatility Index (道指恐慌指数)"
    default_params = {"symbol": "^VXD", "threshold_low": 18, "threshold_high": 28}


# ──────────────────────────────────────────────────────────────
# 3. OVX — Crude Oil Volatility Index
# ──────────────────────────────────────────────────────────────
@register_processor
class OVXIndicator(VolatilityIndexProcessor):
    """
    OVX — CBOE Crude Oil Volatility Index.

    原油 ETF (USO) 的 30 天隐含波动率。
    反映原油市场的恐慌与不确定性。
    典型区间 30~50，地缘政治/疫情时可能飙升至 200+。
    """
    name = "OVX"
    display_name = "原油波动率指数OVX"
    description = "CBOE Crude Oil Volatility Index (原油恐慌指数)"
    default_params = {"symbol": "^OVX", "threshold_low": 35, "threshold_high": 50}

    grading_config = {
        "grades": [
            {"grade": "calm", "min": 0, "max": 25, "label": "极度平静"},
            {"grade": "low", "min": 25, "max": 35, "label": "低波动"},
            {"grade": "normal", "min": 35, "max": 45, "label": "正常波动"},
            {"grade": "elevated", "min": 45, "max": 55, "label": "波动加剧"},
            {"grade": "fear", "min": 55, "max": 75, "label": "市场恐慌"},
            {"grade": "panic", "min": 75, "max": float('inf'), "label": "极度恐慌"},
        ]
    }


# ──────────────────────────────────────────────────────────────
# 5. GVZ — Gold Volatility Index
# ──────────────────────────────────────────────────────────────
@register_processor
class GVZIndicator(VolatilityIndexProcessor):
    """
    GVZ — CBOE Gold Volatility Index.

    黄金 ETF (GLD) 的 30 天隐含波动率。
    反映黄金市场的恐慌与不确定性。
    典型区间 10~20，避险需求高涨时可能飙升。
    """
    name = "GVZ"
    display_name = "黄金波动率指数GVZ"
    description = "CBOE Gold Volatility Index (黄金恐慌指数)"
    default_params = {"symbol": "^GVZ", "threshold_low": 15, "threshold_high": 20}

    grading_config = {
        "grades": [
            {"grade": "calm", "min": 0, "max": 12, "label": "极度平静"},
            {"grade": "low", "min": 12, "max": 15, "label": "低波动"},
            {"grade": "normal", "min": 15, "max": 18, "label": "正常波动"},
            {"grade": "elevated", "min": 18, "max": 22, "label": "波动加剧"},
            {"grade": "fear", "min": 22, "max": 28, "label": "市场恐慌"},
            {"grade": "panic", "min": 28, "max": float('inf'), "label": "极度恐慌"},
        ]
    }


# ──────────────────────────────────────────────────────────────
# Bootstrap: initialize assets + indicator instances
# ──────────────────────────────────────────────────────────────
_VOLATILITY_TARGETS = [
    ("VIX", "^VIX", "标普500波动率指数VIX", "CBOE Volatility Index"),
    ("VXN", "^VXN", "纳斯达克波动率指数VXN", "CBOE Nasdaq-100 Volatility Index"),
    ("VXD", "^VXD", "道琼斯波动率指数VXD", "CBOE DJIA Volatility Index"),

    ("OVX", "^OVX", "原油波动率指数OVX", "CBOE Crude Oil Volatility Index"),
    ("GVZ", "^GVZ", "黄金波动率指数GVZ", "CBOE Gold Volatility Index"),
]


def init_volatility_targets(db: Session) -> int:
    """Initialize required assets + indicator instances for volatility indices."""
    created = 0
    for template_id, asset_id, name, _ in _VOLATILITY_TARGETS:
        asset = ensure_yfinance_asset(db, asset_id=asset_id, watch=False)
        if not asset:
            continue
        if ensure_indicator(
            db=db,
            template_id=template_id,
            asset_id=asset_id,
            name=name,
            params={"symbol": asset_id},
        ):
            created += 1
    return created
