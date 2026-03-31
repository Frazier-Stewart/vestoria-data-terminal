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
    def search_by_symbol(query: str) -> List[StockInfo]:
        """
        按代码或名称搜索股票
        
        1. 先查预定义股票池
        2. 再用 yfinance.Ticker 获取详情
        """
        results = []
        query_upper = query.upper()
        
        # 1. 检查预定义池
        for symbol, info in PREDEFINED_TICKERS.items():
            if query_upper in symbol or query_upper in info["name"].upper():
                stock = YFinanceSearchService._get_stock_info(symbol)
                if stock:
                    results.append(stock)
        
        # 2. 直接尝试获取 ticker 信息 (如果输入像是有效代码)
        if len(query) <= 5 and query.isalpha():
            stock = YFinanceSearchService._get_stock_info(query_upper)
            if stock and stock not in results:
                results.append(stock)
        
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
        
        使用 yfinance.screen 进行板块筛选
        """
        cache_key = f"top_sector:{sector_key}:{count}:{sort_by}"
        cached = _get_from_cache(cache_key)
        if cached:
            return cached
        
        if sector_key not in cls.SECTOR_KEY_MAP:
            return []
        
        try:
            # 构建查询: sector + US market
            sector_name = cls.SECTOR_KEY_MAP[sector_key].replace(' ', '')
            query = EquityQuery('and', [
                EquityQuery('eq', ['sector', sector_name]),
                EquityQuery('eq', ['region', 'us'])
            ])
            
            # 排序字段映射
            sort_field_map = {
                'market_cap': 'intradaymarketcap',
                'trailing_pe': 'trailingpe',
                'name': 'shortname',
            }
            sort_field = sort_field_map.get(sort_by, 'intradaymarketcap')
            
            result = yf.screen(query, size=max(count, 100), sortField=sort_field, sortAsc=False)
            quotes = result.get('quotes', [])
            
            stocks = []
            for item in quotes[:count]:
                symbol = item.get('symbol')
                if symbol:
                    stocks.append(StockInfo(
                        symbol=symbol,
                        name=item.get('longName') or item.get('shortName', symbol),
                        sector=cls.SECTOR_KEY_MAP.get(sector_key),
                        market_cap=item.get('marketCap'),
                        trailing_pe=item.get('trailingPE'),
                        price=item.get('regularMarketPrice'),
                        currency='USD',
                    ))
            
            _set_cache(cache_key, stocks)
            return stocks
            
        except Exception as e:
            print(f"Failed to screen sector {sector_key}: {e}")
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
                for symbol, _ in list(top_companies.iterrows())[:count]:
                    stock = cls._get_stock_info(symbol)
                    if stock:
                        stocks.append(stock)
            
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
