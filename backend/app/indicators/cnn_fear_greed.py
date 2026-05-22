"""CNN Fear & Greed Index - 美股恐慌贪婪指数."""
from datetime import date, datetime
from typing import List, Optional
import requests
import pandas as pd
from io import StringIO
from sqlalchemy.orm import Session

from app.indicators.base import BaseIndicatorProcessor, IndicatorResult
from app.indicators.registry import register_processor
from app.indicators.init_targets import ensure_yfinance_asset, ensure_indicator
from app.core.config import settings


@register_processor
class CNNFearGreedIndicator(BaseIndicatorProcessor):
    """
    CNN Fear & Greed Index - 美股市场恐慌贪婪指数.

    数据来源:
    - 历史数据: CSV (github.com/whit3rabbit/fear-greed-data)
      覆盖 2011-01-03 至今，约 3800+ 个交易日
    - 实时/增量: CNN API (production.dataviz.cnn.io)
      支持最近 ~3.7 年历史，需代理 + 浏览器 headers

    指数范围: 0-100
    - 0-24:   极度恐惧 (Extreme Fear)
    - 25-44:  恐惧 (Fear)
    - 45-55:  中性 (Neutral)
    - 56-75:  贪婪 (Greed)
    - 76-100: 极度贪婪 (Extreme Greed)
    """

    name = "CNN_FEAR_GREED"
    display_name = "美股恐慌贪婪指数"
    description = "CNN Fear & Greed Index，基于美股市场的综合情绪指标"

    default_params = {
        "csv_url": "https://raw.githubusercontent.com/whit3rabbit/fear-greed-data/main/fear-greed.csv",
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
            {"grade": "fear", "min": 25, "max": 45, "label": "恐惧"},
            {"grade": "neutral", "min": 45, "max": 56, "label": "中性"},
            {"grade": "greed", "min": 56, "max": 75, "label": "贪婪"},
            {"grade": "extreme_greed", "min": 75, "max": 100, "label": "极度贪婪"},
        ]
    }

    _cached_df: Optional[pd.DataFrame] = None
    _api_headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://edition.cnn.com/markets/fear-and-greed",
        "Origin": "https://edition.cnn.com",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "cross-site",
    }

    @property
    def _proxies(self) -> Optional[dict]:
        if settings.PROXY_URL:
            return {"http": settings.PROXY_URL, "https": settings.PROXY_URL}
        return None

    def _load_csv(self) -> Optional[pd.DataFrame]:
        """Load fear & greed data from CSV URL."""
        if self._cached_df is not None:
            return self._cached_df

        csv_url = self.params.get("csv_url", self.default_params["csv_url"])
        try:
            response = requests.get(csv_url, timeout=60)
            response.raise_for_status()
            df = pd.read_csv(StringIO(response.text))
            df["Date"] = pd.to_datetime(df["Date"]).dt.date
            df = df.sort_values("Date").reset_index(drop=True)
            self._cached_df = df
            return df
        except Exception as e:
            print(f"[CNN_FearGreed] Error loading CSV: {e}")
            return None

    def _fetch_api(self, start: date, end: date) -> Optional[pd.DataFrame]:
        """Fetch data from CNN API. Supports up to ~3.7 years of history."""
        url = f"https://production.dataviz.cnn.io/index/fearandgreed/graphdata/{start.isoformat()}"
        try:
            response = requests.get(
                url, headers=self._api_headers, proxies=self._proxies, timeout=30
            )
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            print(f"[CNN_FearGreed] API request failed: {e}")
            return None

        records = data.get("fear_and_greed_historical", {}).get("data", [])
        if not records:
            return None

        rows = []
        for item in records:
            ts_ms = item.get("x")
            value = item.get("y")
            rating = item.get("rating", "")
            if ts_ms is None or value is None:
                continue
            item_date = datetime.utcfromtimestamp(ts_ms / 1000).date()
            if item_date < start or item_date > end:
                continue
            rows.append({"Date": item_date, "Fear Greed": value, "Rating": rating})

        if not rows:
            return None

        df = pd.DataFrame(rows).sort_values("Date").reset_index(drop=True)
        return df

    async def calculate(
        self,
        asset_id: str,
        start: date,
        end: date
    ) -> List[IndicatorResult]:
        """Fetch CNN Fear & Greed data for given date range.

        Strategy:
        - If date range is within last ~3 years, try CNN API first (more real-time)
        - Fall back to CSV (full history, 2011-present)
        """
        days = (end - start).days
        df = None

        # Try API for recent data (< 3.5 years, API limit ~1300 records)
        if days < 3.5 * 365:
            df = self._fetch_api(start, end)
            if df is not None and not df.empty:
                print(f"[CNN_FearGreed] Using API data: {len(df)} records")

        # Fall back to CSV
        if df is None:
            df = self._load_csv()
            if df is not None and not df.empty:
                mask = (df["Date"] >= start) & (df["Date"] <= end)
                df = df[mask]
                print(f"[CNN_FearGreed] Using CSV data: {len(df)} records")

        if df is None or df.empty:
            return []

        results = []
        for _, row in df.iterrows():
            value = float(row["Fear Greed"])
            rating = row["Rating"]
            grading = self.apply_grading(value)

            results.append(IndicatorResult(
                date=row["Date"],
                timestamp=datetime.combine(row["Date"], datetime.min.time()),
                value=value,
                value_text=self._get_chinese_label(rating),
                grade=grading.get("grade"),
                grade_label=grading.get("grade_label"),
                extra_data={
                    "rating": rating,
                    "source": "cnn_fear_greed_api" if "api" in str(row.get("source", "")) else "cnn_fear_greed_csv",
                }
            ))

        return results

    async def calculate_latest(self, asset_id: str) -> Optional[IndicatorResult]:
        """Fetch latest CNN Fear & Greed value.

        Priority: CNN API (real-time) → CSV (daily snapshot)
        """
        # Try API first for real-time data
        url = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"
        try:
            response = requests.get(
                url, headers=self._api_headers, proxies=self._proxies, timeout=30
            )
            response.raise_for_status()
            data = response.json()
            fg = data.get("fear_and_greed", {})
            score = fg.get("score")
            rating = fg.get("rating", "")
            ts_str = fg.get("timestamp", "")

            if score is not None:
                latest_date = datetime.fromisoformat(ts_str.replace("Z", "+00:00")).date() if ts_str else date.today()
                grading = self.apply_grading(float(score))
                print(f"[CNN_FearGreed] Latest from API: {latest_date} = {score} ({rating})")
                return IndicatorResult(
                    date=latest_date,
                    timestamp=datetime.combine(latest_date, datetime.min.time()),
                    value=float(score),
                    value_text=self._get_chinese_label(rating),
                    grade=grading.get("grade"),
                    grade_label=grading.get("grade_label"),
                    extra_data={
                        "rating": rating,
                        "source": "cnn_fear_greed_api",
                    }
                )
        except Exception as e:
            print(f"[CNN_FearGreed] API latest failed: {e}, falling back to CSV")

        # Fall back to CSV
        df = self._load_csv()
        if df is None or df.empty:
            return None

        row = df.iloc[-1]
        value = float(row["Fear Greed"])
        rating = row["Rating"]
        grading = self.apply_grading(value)

        return IndicatorResult(
            date=row["Date"],
            timestamp=datetime.combine(row["Date"], datetime.min.time()),
            value=value,
            value_text=self._get_chinese_label(rating),
            grade=grading.get("grade"),
            grade_label=grading.get("grade_label"),
            extra_data={
                "rating": rating,
                "source": "cnn_fear_greed_csv",
            }
        )

    def _get_chinese_label(self, rating: str) -> str:
        """Convert English rating to Chinese."""
        mapping = {
            "extreme fear": "极度恐惧",
            "fear": "恐惧",
            "neutral": "中性",
            "greed": "贪婪",
            "extreme greed": "极度贪婪",
        }
        return mapping.get(rating.lower(), rating)


def init_cnn_fear_greed_targets(db: Session) -> int:
    """
    Initialize CNN Fear & Greed indicator for ^GSPC (S&P 500).

    The CNN Fear & Greed Index is a broad US market sentiment indicator,
    naturally associated with the S&P 500 benchmark.
    """
    created = 0
    asset = ensure_yfinance_asset(db, asset_id="^GSPC", watch=True)
    if asset:
        if ensure_indicator(
            db=db,
            template_id="CNN_FEAR_GREED",
            asset_id="^GSPC",
            name="美股恐慌贪婪指数CNN",
            params={"csv_url": "https://raw.githubusercontent.com/whit3rabbit/fear-greed-data/main/fear-greed.csv"},
        ):
            created += 1
    return created
