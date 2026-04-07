import { Search, Bitcoin, Loader2, Plus, Check, ExternalLink, TrendingUp, TrendingDown } from 'lucide-react';
import { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || '';

interface BinanceTicker {
  symbol: string;
  baseAsset: string;
  quoteAsset: string;
  price: number;
  priceChange: number;
  priceChangePercent: number;
  volume: number;
  quoteVolume: number;
  high: number;
  low: number;
}

export default function CryptoPanel() {
  const [searchQuery, setSearchQuery] = useState('');
  const [activeSource, setActiveSource] = useState<'binance' | 'onchain'>('binance');
  
  // Binance data
  const [tickers, setTickers] = useState<BinanceTicker[]>([]);
  const [loading, setLoading] = useState(false);
  const [searching, setSearching] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);
  const [addingSymbol, setAddingSymbol] = useState<string | null>(null);
  const [addedSymbols, setAddedSymbols] = useState<Set<string>>(new Set());

  // Load top tickers on mount
  useEffect(() => {
    if (activeSource === 'binance') {
      loadTopTickers();
    }
  }, [activeSource]);

  const loadTopTickers = async () => {
    setLoading(true);
    try {
      const response = await axios.get<BinanceTicker[]>(
        `${API_BASE_URL}/api/v1/binance/ticker/24hr?quote_asset=USDT&limit=50`
      );
      setTickers(response.data);
    } catch (error) {
      console.error('Failed to load tickers:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = useCallback(async () => {
    if (!searchQuery.trim()) {
      setHasSearched(false);
      loadTopTickers();
      return;
    }

    setSearching(true);
    setHasSearched(true);
    try {
      const response = await axios.get<BinanceTicker[]>(
        `${API_BASE_URL}/api/v1/binance/search?q=${encodeURIComponent(searchQuery)}&quote_asset=USDT&limit=20`
      );
      setTickers(response.data);
    } catch (error) {
      console.error('Search failed:', error);
      setTickers([]);
    } finally {
      setSearching(false);
    }
  }, [searchQuery]);

  const handleAddToWatchlist = async (ticker: BinanceTicker) => {
    if (addingSymbol || addedSymbols.has(ticker.symbol)) return;
    
    setAddingSymbol(ticker.symbol);
    try {
      // Create asset
      await axios.post(`${API_BASE_URL}/api/v1/assets`, {
        id: ticker.symbol,
        symbol: ticker.baseAsset,
        name: `${ticker.baseAsset} / ${ticker.quoteAsset}`,
        asset_type: 'crypto',
        exchange: 'BINANCE',
        currency: ticker.quoteAsset,
        data_source: 'binance',
        source_symbol: ticker.symbol,
        is_active: true,
      });
      
      setAddedSymbols(prev => new Set([...prev, ticker.symbol]));
      
      // Auto-fetch price data
      try {
        await axios.post(`${API_BASE_URL}/api/v1/update/backfill/${ticker.symbol}?days=365`);
      } catch (e) {
        console.warn('Auto-backfill failed:', e);
      }
    } catch (error) {
      console.error('Failed to add:', error);
      if (axios.isAxiosError(error) && error.response?.status === 409) {
        setAddedSymbols(prev => new Set([...prev, ticker.symbol]));
      }
    } finally {
      setAddingSymbol(null);
    }
  };

  const formatPrice = (price: number) => {
    if (price >= 1000) {
      return `$${price.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    } else if (price >= 1) {
      return `$${price.toFixed(2)}`;
    } else {
      return `$${price.toFixed(6)}`;
    }
  };

  const formatVolume = (vol: number) => {
    if (vol >= 1e9) return `$${(vol / 1e9).toFixed(2)}B`;
    if (vol >= 1e6) return `$${(vol / 1e6).toFixed(2)}M`;
    return `$${(vol / 1e3).toFixed(2)}K`;
  };

  const formatChange = (change: number) => {
    const isPositive = change >= 0;
    const color = isPositive ? '#22c55e' : '#ef4444';
    const bg = isPositive ? 'rgba(34, 197, 94, 0.1)' : 'rgba(239, 68, 68, 0.1)';
    const Icon = isPositive ? TrendingUp : TrendingDown;
    
    return (
      <span
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '4px',
          padding: '4px 8px',
          borderRadius: '6px',
          background: bg,
          color: color,
          fontSize: '13px',
          fontWeight: 600,
        }}
      >
        <Icon size={14} />
        {isPositive ? '+' : ''}{change.toFixed(2)}%
      </span>
    );
  };

  if (activeSource === 'onchain') {
    return (
      <div>
        {/* 数据源选择 */}
        <div style={{ display: 'flex', gap: '10px', marginBottom: '20px' }}>
          <button
            onClick={() => setActiveSource('binance')}
            style={{
              padding: '10px 20px',
              borderRadius: '10px',
              border: 'none',
              background: 'var(--bg-secondary)',
              color: 'var(--text-secondary)',
              fontSize: '14px',
              fontWeight: 600,
              cursor: 'pointer',
            }}
          >
            Binance
          </button>
          <button
            onClick={() => setActiveSource('onchain')}
            style={{
              padding: '10px 20px',
              borderRadius: '10px',
              border: 'none',
              background: '#627eea',
              color: 'white',
              fontSize: '14px',
              fontWeight: 600,
              cursor: 'pointer',
            }}
          >
            链上资产
          </button>
        </div>

        <div
          style={{
            padding: '80px',
            textAlign: 'center',
            background: 'var(--bg-secondary)',
            borderRadius: '16px',
            border: '1px dashed var(--border-color)',
          }}
        >
          <Bitcoin size={48} color="var(--text-muted)" style={{ marginBottom: '16px', opacity: 0.5 }} />
          <p style={{ color: 'var(--text-muted)', fontSize: '16px' }}>
            链上资产搜索功能开发中
          </p>
        </div>
      </div>
    );
  }

  return (
    <div>
      {/* 数据源选择 */}
      <div style={{ display: 'flex', gap: '10px', marginBottom: '20px' }}>
        <button
          onClick={() => setActiveSource('binance')}
          style={{
            padding: '10px 20px',
            borderRadius: '10px',
            border: 'none',
            background: '#f0b90b',
            color: 'white',
            fontSize: '14px',
            fontWeight: 600,
            cursor: 'pointer',
          }}
        >
          Binance
        </button>
        <button
          onClick={() => setActiveSource('onchain')}
          style={{
            padding: '10px 20px',
            borderRadius: '10px',
            border: 'none',
            background: 'var(--bg-secondary)',
            color: 'var(--text-secondary)',
            fontSize: '14px',
            fontWeight: 600,
            cursor: 'pointer',
          }}
        >
          链上资产
        </button>
      </div>

      {/* 搜索栏 */}
      <div
        style={{
          display: 'flex',
          gap: '12px',
          marginBottom: '24px',
          padding: '20px',
          background: 'var(--bg-secondary)',
          borderRadius: '16px',
          border: '1px solid var(--border-color)',
        }}
      >
        <div
          style={{
            flex: 1,
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
            padding: '12px 16px',
            background: 'var(--bg-primary)',
            borderRadius: '12px',
            border: '1px solid var(--border-color)',
          }}
        >
          <Search size={20} color="var(--text-muted)" />
          <input
            type="text"
            placeholder="搜索币种 (如: BTC, ETH)..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            style={{
              flex: 1,
              border: 'none',
              background: 'transparent',
              outline: 'none',
              fontSize: '15px',
              color: 'var(--text-primary)',
            }}
          />
        </div>
        <button
          onClick={handleSearch}
          disabled={searching}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '12px 24px',
            borderRadius: '12px',
            border: 'none',
            background: '#f0b90b',
            color: 'white',
            fontSize: '14px',
            fontWeight: 600,
            cursor: searching ? 'not-allowed' : 'pointer',
            opacity: searching ? 0.7 : 1,
          }}
        >
          {searching ? <Loader2 size={18} className="animate-spin" /> : <Bitcoin size={18} />}
          搜索
        </button>
      </div>

      {/* 结果列表 */}
      <div
        style={{
          background: 'var(--bg-primary)',
          borderRadius: '16px',
          border: '1px solid var(--border-color)',
          overflow: 'hidden',
        }}
      >
        {loading ? (
          <div style={{ padding: '60px', textAlign: 'center', color: 'var(--text-muted)' }}>
            <Loader2 size={32} style={{ marginBottom: '16px', animation: 'spin 1s linear infinite' }} />
            <p>加载中...</p>
          </div>
        ) : tickers.length === 0 ? (
          <div style={{ padding: '60px', textAlign: 'center', color: 'var(--text-muted)' }}>
            <p>暂无数据</p>
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ background: 'var(--bg-secondary)' }}>
                  <th style={thStyle}>币种</th>
                  <th style={{ ...thStyle, textAlign: 'right' }}>价格</th>
                  <th style={{ ...thStyle, textAlign: 'right' }}>24h 涨跌</th>
                  <th style={{ ...thStyle, textAlign: 'right' }}>24h 成交量</th>
                  <th style={{ ...thStyle, textAlign: 'center' }}>操作</th>
                </tr>
              </thead>
              <tbody>
                {tickers.map((ticker, index) => {
                  const isAdded = addedSymbols.has(ticker.symbol);
                  const isAdding = addingSymbol === ticker.symbol;
                  
                  return (
                    <tr
                      key={ticker.symbol}
                      style={{
                        borderBottom:
                          index < tickers.length - 1 ? '1px solid var(--border-color)' : 'none',
                        transition: 'background 0.2s',
                      }}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.background = 'var(--bg-secondary)';
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.background = 'transparent';
                      }}
                    >
                      <td style={tdStyle}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                          <div
                            style={{
                              width: '40px',
                              height: '40px',
                              borderRadius: '10px',
                              background: 'rgba(240, 185, 11, 0.1)',
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center',
                              color: '#f0b90b',
                              fontSize: '12px',
                              fontWeight: 600,
                            }}
                          >
                            {ticker.baseAsset.slice(0, 2)}
                          </div>
                          <div>
                            <span
                              style={{
                                fontSize: '15px',
                                fontWeight: 600,
                                color: 'var(--text-primary)',
                              }}
                            >
                              {ticker.baseAsset}
                            </span>
                            <span
                              style={{
                                fontSize: '13px',
                                color: 'var(--text-muted)',
                                marginLeft: '4px',
                              }}
                            >
                              /{ticker.quoteAsset}
                            </span>
                          </div>
                        </div>
                      </td>
                      <td style={{ ...tdStyle, textAlign: 'right' }}>
                        <span style={{ fontSize: '15px', fontWeight: 600, color: 'var(--text-primary)' }}>
                          {formatPrice(ticker.price)}
                        </span>
                      </td>
                      <td style={{ ...tdStyle, textAlign: 'right' }}>
                        {formatChange(ticker.priceChangePercent)}
                      </td>
                      <td style={{ ...tdStyle, textAlign: 'right' }}>
                        <span style={{ fontSize: '14px', color: 'var(--text-muted)' }}>
                          {formatVolume(ticker.quoteVolume)}
                        </span>
                      </td>
                      <td style={{ ...tdStyle, textAlign: 'center' }}>
                        <div style={{ display: 'flex', gap: '8px', justifyContent: 'center' }}>
                          <Link
                            to={`/assets/${ticker.symbol}`}
                            state={{ from: 'crypto' }}
                            style={{
                              padding: '6px',
                              borderRadius: '6px',
                              border: 'none',
                              background: 'var(--bg-secondary)',
                              color: 'var(--text-secondary)',
                              cursor: 'pointer',
                              display: 'inline-flex',
                              alignItems: 'center',
                              justifyContent: 'center',
                            }}
                            title="查看详情"
                          >
                            <ExternalLink size={14} />
                          </Link>
                          <button
                            onClick={() => handleAddToWatchlist(ticker)}
                            disabled={isAdding || isAdded}
                            style={{
                              display: 'inline-flex',
                              alignItems: 'center',
                              gap: '4px',
                              padding: '6px 12px',
                              borderRadius: '6px',
                              border: 'none',
                              background: isAdded ? '#22c55e' : '#f0b90b',
                              color: 'white',
                              fontSize: '12px',
                              fontWeight: 500,
                              cursor: (isAdding || isAdded) ? 'not-allowed' : 'pointer',
                              opacity: (isAdding || isAdded) ? 0.7 : 1,
                            }}
                          >
                            {isAdding ? (
                              <Loader2 size={14} style={{ animation: 'spin 1s linear infinite' }} />
                            ) : isAdded ? (
                              <Check size={14} />
                            ) : (
                              <Plus size={14} />
                            )}
                            {isAdded ? '已添加' : '添加'}
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* 说明 */}
      {!hasSearched && tickers.length > 0 && (
        <div
          style={{
            marginTop: '16px',
            padding: '12px 16px',
            background: 'var(--bg-secondary)',
            borderRadius: '12px',
            fontSize: '13px',
            color: 'var(--text-muted)',
          }}
        >
          按 24h 成交量排序显示前 50 个币种
        </div>
      )}
    </div>
  );
}

const thStyle: React.CSSProperties = {
  padding: '14px 16px',
  textAlign: 'left',
  fontSize: '12px',
  fontWeight: 600,
  color: 'var(--text-secondary)',
  textTransform: 'uppercase',
  letterSpacing: '0.5px',
};

const tdStyle: React.CSSProperties = {
  padding: '14px 16px',
};
