"""
Yahoo Finance 搜索服务

结合两种模式：
1. 预定义股票池 (GLD, SPY 等核心标的)
2. yfinance Sector/Industry 实时获取板块龙头
"""

import yfinance as yf
from yfinance import EquityQuery
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
import functools
import time

from app.core.config import settings

# Configure yfinance proxy if set
if settings.PROXY_URL:
    yf.config.network.proxy = {
        "http": settings.PROXY_URL,
        "https": settings.PROXY_URL,
    }
    print(f"[yfinance] Proxy configured: {settings.PROXY_URL}")


@dataclass
class StockInfo:
    """股票信息"""
    symbol: str
    name: str
    sector: Optional[str] = None
    industry: Optional[str] = None
    market_cap: Optional[float] = None
    trailing_pe: Optional[float] = None
    price: Optional[float] = None
    currency: str = "USD"
    exchange: Optional[str] = None


# 预定义核心股票池 - 用户指定的 + 常见大盘标的
PREDEFINED_TICKERS = {
    # 用户指定
    "GLD": {"name": "SPDR Gold Shares", "category": "commodities"},
    "SPY": {"name": "SPDR S&P 500 ETF Trust", "category": "equities"},
    
    # 大盘指数 ETF
    "QQQ": {"name": "Invesco QQQ Trust", "category": "equities"},
    "IWM": {"name": "iShares Russell 2000 ETF", "category": "equities"},
    "VTI": {"name": "Vanguard Total Stock Market ETF", "category": "equities"},
    "VEA": {"name": "Vanguard FTSE Developed Markets ETF", "category": "equities"},
    "VWO": {"name": "Vanguard FTSE Emerging Markets ETF", "category": "equities"},
    "BND": {"name": "Vanguard Total Bond Market ETF", "category": "fixed_income"},
    
    # Sector SPDRs
    "XLK": {"name": "Technology Select Sector SPDR Fund", "category": "equities", "sector": "Technology"},
    "XLF": {"name": "Financial Select Sector SPDR Fund", "category": "equities", "sector": "Financials"},
    "XLE": {"name": "Energy Select Sector SPDR Fund", "category": "equities", "sector": "Energy"},
    "XLV": {"name": "Health Care Select Sector SPDR Fund", "category": "equities", "sector": "Health Care"},
    "XLI": {"name": "Industrial Select Sector SPDR Fund", "category": "equities", "sector": "Industrials"},
    "XLP": {"name": "Consumer Staples Select Sector SPDR Fund", "category": "equities", "sector": "Consumer Staples"},
    "XLY": {"name": "Consumer Discretionary Select Sector SPDR Fund", "category": "equities", "sector": "Consumer Discretionary"},
    "XLB": {"name": "Materials Select Sector SPDR Fund", "category": "equities", "sector": "Materials"},
    "XLU": {"name": "Utilities Select Sector SPDR Fund", "category": "equities", "sector": "Utilities"},
    "XLC": {"name": "Communication Services Select Sector SPDR Fund", "category": "equities", "sector": "Communication Services"},
    "XLRE": {"name": "Real Estate Select Sector SPDR Fund", "category": "equities", "sector": "Real Estate"},
    
    # 商品
    "SLV": {"name": "iShares Silver Trust", "category": "commodities"},
    "USO": {"name": "United States Oil Fund", "category": "commodities"},
    "UNG": {"name": "United States Natural Gas Fund", "category": "commodities"},
}


# 缓存
_cache = {}
_cache_time = {}
CACHE_TTL = 300  # 5分钟缓存


def _get_cache_key(*args, **kwargs) -> str:
    """生成缓存key"""
    return str(args) + str(sorted(kwargs.items()))


def _get_from_cache(key: str) -> Optional[Any]:
    """从缓存获取"""
    if key in _cache:
        if time.time() - _cache_time.get(key, 0) < CACHE_TTL:
            return _cache[key]
    return None


def _set_cache(key: str, value: Any):
    """设置缓存"""
    _cache[key] = value
    _cache_time[key] = time.time()


class YFinanceSearchService:
    """Yahoo Finance 搜索服务"""
    
    # GICS Sector key 映射 (yfinance 格式 -> GICS 标准名)
    SECTOR_KEY_MAP = {
        'technology': 'Technology',
        'healthcare': 'Health Care',
        'financial-services': 'Financials',
        'consumer-cyclical': 'Consumer Discretionary',
        'industrials': 'Industrials',
        'communication-services': 'Communication Services',
        'consumer-defensive': 'Consumer Staples',
        'energy': 'Energy',
        'basic-materials': 'Materials',
        'real-estate': 'Real Estate',
        'utilities': 'Utilities',
    }
    
    # 反向映射
    SECTOR_KEY_REVERSE = {v: k for k, v in SECTOR_KEY_MAP.items()}
    
    @staticmethod
    def search_by_symbol(query: str, limit: int = 20) -> List[StockInfo]:
        """
        按代码或名称搜索股票
        
        搜索结果只通过 yfinance 接口获取：
        1. 若输入像是股票代码，先用 yfinance.Ticker 获取详情
        2. 再用 yfinance.Search 做模糊搜索
        """
        results = []
        seen_symbols = set()
        query_upper = query.upper()
        
        # 1. 直接尝试获取 ticker 信息 (仅当输入明显是代码: 全大写、<=5字母)
        looks_like_ticker = len(query) <= 5 and query.isalpha() and query == query.upper()
        if looks_like_ticker:
            direct_match = YFinanceSearchService._get_stock_info(query_upper)
            if direct_match:
                results.append(direct_match)
                seen_symbols.add(direct_match.symbol)
        
        # 2. 模糊搜索 (当没有直接匹配，或输入不像标准代码时)
        if not looks_like_ticker or not results:
            try:
                search = yf.Search(query, max_results=limit, raise_errors=True)
                for quote in search.quotes:
                    symbol = quote.get("symbol")
                    if not symbol or symbol in seen_symbols:
                        continue
                    # 过滤：优先股票/ETF，排除货币等
                    quote_type = quote.get("quoteType", "").lower()
                    if quote_type not in ("equity", "etf", "mutualfund", "index", ""):
                        continue
                    stock = StockInfo(
                        symbol=symbol,
                        name=quote.get("longname") or quote.get("shortname", symbol),
                        sector=None,
                        industry=None,
                        market_cap=quote.get("marketCap"),
                        trailing_pe=None,
                        price=quote.get("regularMarketPrice"),
                        currency=quote.get("currency", "USD"),
                        exchange=quote.get("exchange"),
                    )
                    results.append(stock)
                    seen_symbols.add(symbol)
            except Exception as e:
                print(f"Search failed for '{query}': {e}")
        
        return results
    
    @staticmethod
    def _get_stock_info(symbol: str) -> Optional[StockInfo]:
        """获取单个股票详情"""
        cache_key = f"stock_info:{symbol}"
        cached = _get_from_cache(cache_key)
        if cached:
            return cached
        
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            stock = StockInfo(
                symbol=symbol,
                name=info.get('longName') or info.get('shortName', symbol),
                sector=info.get('sector'),
                industry=info.get('industry'),
                market_cap=info.get('marketCap'),
                trailing_pe=info.get('trailingPE'),
                price=info.get('currentPrice') or info.get('previousClose'),
                currency=info.get('currency', 'USD'),
                exchange=info.get('exchange'),
            )
            
            _set_cache(cache_key, stock)
            return stock
            
        except Exception as e:
            print(f"Failed to get info for {symbol}: {e}")
            return None
    
    @classmethod
    def get_sectors(cls) -> List[Dict[str, Any]]:
        """获取所有 GICS 板块"""
        cache_key = "all_sectors"
        cached = _get_from_cache(cache_key)
        if cached:
            return cached
        
        sectors = []
        for key, name in cls.SECTOR_KEY_MAP.items():
            try:
                sector = yf.Sector(key)
                top_companies = sector.top_companies
                company_count = len(top_companies) if hasattr(top_companies, '__len__') else 0
                
                sectors.append({
                    'key': key,
                    'name': name,
                    'name_zh': cls._get_sector_name_zh(name),
                    'company_count': company_count,
                })
            except Exception as e:
                print(f"Failed to get sector {key}: {e}")
        
        _set_cache(cache_key, sectors)
        return sectors
    
    @classmethod
    def get_industries_by_sector(cls, sector_key: str) -> List[Dict[str, Any]]:
        """获取板块下的所有子行业"""
        cache_key = f"industries:{sector_key}"
        cached = _get_from_cache(cache_key)
        if cached:
            return cached
        
        if sector_key not in cls.SECTOR_KEY_MAP:
            return []
        
        try:
            sector = yf.Sector(sector_key)
            industries_df = sector.industries
            
            industries = []
            for idx, row in industries_df.iterrows():
                name = str(row.get('name', ''))
                # 生成 industry key
                industry_key = cls._name_to_key(name)
                
                industries.append({
                    'key': industry_key,
                    'name': name,
                    'symbol': str(row.get('symbol', '')),
                    'market_weight': row.get('market weight'),
                })
            
            _set_cache(cache_key, industries)
            return industries
            
        except Exception as e:
            print(f"Failed to get industries for {sector_key}: {e}")
            return []
    
    @classmethod
    def get_top_companies_by_sector(
        cls,
        sector_key: str,
        count: int = 20,
        sort_by: str = 'market_cap'
    ) -> List[StockInfo]:
        """
        获取板块内市值最高的公司

        使用 yfinance.Sector.top_companies 获取板块龙头。
        直接使用 DataFrame 中的 name，避免逐个 symbol 调用 Ticker 导致过慢。
        """
        cache_key = f"top_sector:{sector_key}:{count}:{sort_by}"
        cached = _get_from_cache(cache_key)
        if cached:
            return cached

        if sector_key not in cls.SECTOR_KEY_MAP:
            return []

        try:
            sector = yf.Sector(sector_key)
            top_companies = sector.top_companies

            stocks = []
            if hasattr(top_companies, 'iterrows'):
                for symbol, row in list(top_companies.iterrows())[:count]:
                    name = row.get('name', symbol) if hasattr(row, 'get') else getattr(row, 'name', symbol)
                    stocks.append(StockInfo(
                        symbol=str(symbol),
                        name=str(name),
                        sector=cls.SECTOR_KEY_MAP.get(sector_key),
                        market_cap=None,
                        trailing_pe=None,
                        price=None,
                        currency='USD',
                        exchange=None,
                    ))

            # 客户端排序
            def sort_key(stock):
                if sort_by == 'name':
                    return stock.name
                elif sort_by == 'ticker':
                    return stock.symbol
                return stock.symbol

            if sort_by in ('name', 'ticker'):
                stocks = sorted(stocks, key=sort_key, reverse=False)
            _set_cache(cache_key, stocks)
            return stocks

        except Exception as e:
            print(f"Failed to get top companies for sector {sector_key}: {e}")
            return []
    
    @classmethod
    def get_top_companies_by_industry(
        cls,
        industry_key: str,
        count: int = 10
    ) -> List[StockInfo]:
        """获取子行业内的龙头公司"""
        cache_key = f"top_industry:{industry_key}:{count}"
        cached = _get_from_cache(cache_key)
        if cached:
            return cached

        try:
            industry = yf.Industry(industry_key)
            top_companies = industry.top_companies

            stocks = []
            if hasattr(top_companies, 'iterrows'):
                for symbol, row in list(top_companies.iterrows())[:count]:
                    name = row.get('name', symbol) if hasattr(row, 'get') else getattr(row, 'name', symbol)
                    stocks.append(StockInfo(
                        symbol=str(symbol),
                        name=str(name),
                        industry=industry_key,
                        market_cap=None,
                        trailing_pe=None,
                        price=None,
                        currency='USD',
                        exchange=None,
                    ))

            _set_cache(cache_key, stocks)
            return stocks

        except Exception as e:
            print(f"Failed to get top companies for industry {industry_key}: {e}")
            return []
    
    @classmethod
    def get_predefined_tickers(cls) -> List[StockInfo]:
        """获取预定义股票池的所有信息"""
        stocks = []
        for symbol in PREDEFINED_TICKERS.keys():
            stock = cls._get_stock_info(symbol)
            if stock:
                stocks.append(stock)
        return stocks
    
    @staticmethod
    def _name_to_key(name: str) -> str:
        """将名称转换为 key"""
        return name.lower().replace(' ', '-').replace('&', '').replace('--', '-').strip('-')
    
    @staticmethod
    def _get_sector_name_zh(name: str) -> str:
        """获取板块中文名"""
        zh_names = {
            'Technology': '信息技术',
            'Financials': '金融',
            'Health Care': '医疗保健',
            'Consumer Discretionary': '可选消费',
            'Communication Services': '通信服务',
            'Industrials': '工业',
            'Consumer Staples': '必需消费',
            'Energy': '能源',
            'Materials': '原材料',
            'Real Estate': '房地产',
            'Utilities': '公用事业',
        }
        return zh_names.get(name, name)


# 单例实例
yfinance_service = YFinanceSearchService()
