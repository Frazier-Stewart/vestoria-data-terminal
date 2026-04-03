import { useState, useEffect } from 'react';
import { Search, Filter, ArrowUpDown, Plus, Loader2, Check } from 'lucide-react';
import axios from 'axios';
import {
  GicsSector,
  YFinanceSearchResult,
  SectorConfig,
  SECTOR_CONFIG,
  SORT_OPTIONS,
} from '@/types/assets';

// API 基础 URL
const API_BASE_URL = import.meta.env.VITE_API_URL || '';

// Sector 响应类型
interface SectorResponse {
  key: string;
  name: string;
  name_zh: string;
  company_count: number;
}

// Industry 响应类型
interface IndustryResponse {
  key: string;
  name: string;
  symbol: string;
  market_weight?: number;
}

export default function EquitiesPanel() {
  // ============ State ============
  // 搜索状态
  const [searchQuery, setSearchQuery] = useState('');
  const [results, setResults] = useState<YFinanceSearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);

  // 筛选状态
  const [sectors, setSectors] = useState<SectorConfig[]>(SECTOR_CONFIG);
  const [sectorsLoading, setSectorsLoading] = useState(false);
  const [selectedSector, setSelectedSector] = useState<GicsSector | ''>('');
  const [selectedIndustry, setSelectedIndustry] = useState('');
  const [industries, setIndustries] = useState<IndustryResponse[]>([]);
  const [industriesLoading, setIndustriesLoading] = useState(false);

  // 排序状态
  const [sortBy, setSortBy] = useState<'market_cap' | 'trailing_pe' | 'name' | 'ticker'>('market_cap');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

  // 添加状态
  const [addingSymbol, setAddingSymbol] = useState<string | null>(null);
  const [addedSymbols, setAddedSymbols] = useState<Set<string>>(new Set());

  // ============ Effects ============
  // 加载 Sector 列表
  useEffect(() => {
    loadSectors();
  }, []);

  // Sector 变化时加载 Industries
  useEffect(() => {
    if (selectedSector) {
      loadIndustries(selectedSector);
    } else {
      setIndustries([]);
      setSelectedIndustry('');
    }
  }, [selectedSector]);

  // ============ API Functions ============
  // 加载 Sectors
  const loadSectors = async () => {
    setSectorsLoading(true);
    try {
      const response = await axios.get<SectorResponse[]>(`${API_BASE_URL}/api/v1/assets/sectors`);
      // 合并后端数据与前端配置
      const mergedSectors = response.data.map((s) => {
        const config = SECTOR_CONFIG.find((c) => c.key === s.name);
        return {
          key: s.name as GicsSector,
          label: s.name,
          labelZh: s.name_zh || config?.labelZh || s.name,
          color: config?.color || '#6366f1',
          bg: config?.bg || 'rgba(99, 102, 241, 0.1)',
        };
      });
      setSectors(mergedSectors);
    } catch (error) {
      console.error('Failed to load sectors:', error);
      // 失败时使用默认配置
      setSectors(SECTOR_CONFIG);
    } finally {
      setSectorsLoading(false);
    }
  };

  // 加载 Industries
  const loadIndustries = async (sectorKey: GicsSector) => {
    setIndustriesLoading(true);
    try {
      // 转换 GICS 名称为 yfinance key
      const sectorKeyMap: Record<string, string> = {
        'Technology': 'technology',
        'Financials': 'financial-services',
        'Health Care': 'healthcare',
        'Consumer Discretionary': 'consumer-cyclical',
        'Communication Services': 'communication-services',
        'Industrials': 'industrials',
        'Consumer Staples': 'consumer-defensive',
        'Energy': 'energy',
        'Materials': 'basic-materials',
        'Real Estate': 'real-estate',
        'Utilities': 'utilities',
      };
      const yfKey = sectorKeyMap[sectorKey] || sectorKey.toLowerCase().replace(/\s+/g, '-');
      
      const response = await axios.get<IndustryResponse[]>(
        `${API_BASE_URL}/api/v1/assets/sectors/${yfKey}/industries`
      );
      setIndustries(response.data);
    } catch (error) {
      console.error('Failed to load industries:', error);
      setIndustries([]);
    } finally {
      setIndustriesLoading(false);
    }
  };

  // 搜索股票
  const searchStocks = async () => {
    if (!searchQuery.trim() && !selectedSector && !selectedIndustry) return;

    setLoading(true);
    setHasSearched(true);

    try {
      let searchResults: YFinanceSearchResult[] = [];

      // 如果有搜索词，使用搜索 API
      if (searchQuery.trim()) {
        const response = await axios.get(`${API_BASE_URL}/api/v1/assets/search/yfinance`, {
          params: {
            q: searchQuery,
            limit: 50,
          },
        });
        searchResults = response.data.results || [];
      }

      // 如果有选择 Sector，获取该板块龙头
      if (selectedSector) {
        const sectorKeyMap: Record<string, string> = {
          'Technology': 'technology',
          'Financials': 'financial-services',
          'Health Care': 'healthcare',
          'Consumer Discretionary': 'consumer-cyclical',
          'Communication Services': 'communication-services',
          'Industrials': 'industrials',
          'Consumer Staples': 'consumer-defensive',
          'Energy': 'energy',
          'Materials': 'basic-materials',
          'Real Estate': 'real-estate',
          'Utilities': 'utilities',
        };
        const yfKey = sectorKeyMap[selectedSector] || selectedSector.toLowerCase().replace(/\s+/g, '-');

        const response = await axios.get(`${API_BASE_URL}/api/v1/assets/sectors/${yfKey}/top-companies`, {
          params: { count: 50 },
        });

        if (!searchQuery.trim()) {
          // 只有 sector 筛选时，直接使用板块结果
          searchResults = response.data || [];
        } else {
          // 合并结果（去重）
          const sectorSymbols = new Set((response.data || []).map((s: YFinanceSearchResult) => s.symbol));
          searchResults = searchResults.filter((s) => sectorSymbols.has(s.symbol));
        }
      }

      // 如果有选择 Industry，获取该子行业龙头
      if (selectedIndustry) {
        const response = await axios.get(`${API_BASE_URL}/api/v1/assets/industries/${selectedIndustry}/top-companies`, {
          params: { count: 50 },
        });

        if (!searchQuery.trim() && !selectedSector) {
          // 只有 industry 筛选时，直接使用行业结果
          searchResults = response.data || [];
        } else {
          // 合并结果（去重）
          const industrySymbols = new Set((response.data || []).map((s: YFinanceSearchResult) => s.symbol));
          searchResults = searchResults.filter((s) => industrySymbols.has(s.symbol));
        }
      }

      // 客户端排序
      const sortedResults = sortResults(searchResults, sortBy, sortOrder);
      setResults(sortedResults);
    } catch (error) {
      console.error('Search failed:', error);
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  // 排序结果
  const sortResults = (
    items: YFinanceSearchResult[],
    sortField: string,
    order: 'asc' | 'desc'
  ): YFinanceSearchResult[] => {
    return [...items].sort((a, b) => {
      let aVal: number | string | undefined;
      let bVal: number | string | undefined;
      
      switch (sortField) {
        case 'market_cap':
          aVal = a.marketCap;
          bVal = b.marketCap;
          break;
        case 'trailing_pe':
          aVal = a.trailingPE;
          bVal = b.trailingPE;
          break;
        case 'name':
          aVal = a.name;
          bVal = b.name;
          break;
        case 'ticker':
          aVal = a.symbol;
          bVal = b.symbol;
          break;
        default:
          aVal = a.marketCap;
          bVal = b.marketCap;
      }
      
      if (aVal === undefined && bVal === undefined) return 0;
      if (aVal === undefined) return 1;
      if (bVal === undefined) return -1;
      
      const comparison = aVal < bVal ? -1 : aVal > bVal ? 1 : 0;
      return order === 'asc' ? comparison : -comparison;
    });
  };

  // 添加到追踪列表
  const handleAddToWatchlist = async (stock: YFinanceSearchResult) => {
    if (addingSymbol || addedSymbols.has(stock.symbol)) return;
    
    setAddingSymbol(stock.symbol);
    try {
      // Step 1: Create asset
      await axios.post(`${API_BASE_URL}/api/v1/assets`, {
        id: stock.symbol,
        symbol: stock.symbol,
        name: stock.name,
        asset_type: 'equity',
        exchange: stock.exchange || 'US',
        currency: stock.currency || 'USD',
        data_source: 'yfinance',
        source_symbol: stock.symbol,
        is_active: true,
      });
      
      setAddedSymbols((prev) => new Set([...prev, stock.symbol]));
      
      // Step 2: Auto-fetch price data (background, don't block UI)
      try {
        await axios.post(`${API_BASE_URL}/api/v1/update/backfill/${stock.symbol}?days=365`);
        console.log(`Auto-fetched price data for ${stock.symbol}`);
      } catch (backfillError) {
        // Don't block UI if backfill fails
        console.warn(`Auto-backfill failed for ${stock.symbol}:`, backfillError);
      }
    } catch (error) {
      console.error('Failed to add asset:', error);
      // 如果已经存在（409），也算成功
      if (axios.isAxiosError(error) && error.response?.status === 409) {
        setAddedSymbols((prev) => new Set([...prev, stock.symbol]));
      }
    } finally {
      setAddingSymbol(null);
    }
  };

  // 格式化市值
  const formatMarketCap = (value?: number) => {
    if (!value) return '-';
    if (value >= 1e12) return `$${(value / 1e12).toFixed(2)}T`;
    if (value >= 1e9) return `$${(value / 1e9).toFixed(2)}B`;
    if (value >= 1e6) return `$${(value / 1e6).toFixed(2)}M`;
    return `$${value.toLocaleString()}`;
  };

  // 获取 sector 配置
  const getSectorConfig = (sector?: string) => {
    return sectors.find((s) => s.key === sector) || {
      label: sector || 'Unknown',
      labelZh: sector || '未知',
      color: '#6366f1',
      bg: 'rgba(99, 102, 241, 0.1)',
    };
  };

  return (
    <div>
      {/* 搜索和筛选栏 */}
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          gap: '16px',
          marginBottom: '24px',
          padding: '20px',
          background: 'var(--bg-secondary)',
          borderRadius: '16px',
          border: '1px solid var(--border-color)',
        }}
      >
        {/* 搜索框 */}
        <div style={{ display: 'flex', gap: '12px' }}>
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
              placeholder="搜索股票代码或名称 (如: AAPL, Apple)..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && searchStocks()}
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
            onClick={searchStocks}
            disabled={loading || (!searchQuery.trim() && !selectedSector && !selectedIndustry)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              padding: '12px 24px',
              borderRadius: '12px',
              border: 'none',
              background: 'var(--primary-color)',
              color: 'white',
              fontSize: '14px',
              fontWeight: 600,
              cursor: loading ? 'not-allowed' : 'pointer',
              opacity: loading ? 0.7 : 1,
            }}
          >
            {loading ? <Loader2 size={18} className="animate-spin" /> : <Search size={18} />}
            搜索
          </button>
        </div>

        {/* 筛选器 */}
        <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
          {/* Sector 筛选 */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Filter size={16} color="var(--text-muted)" />
            <select
              value={selectedSector}
              onChange={(e) => setSelectedSector(e.target.value as GicsSector | '')}
              disabled={sectorsLoading}
              style={{
                padding: '8px 12px',
                borderRadius: '8px',
                border: '1px solid var(--border-color)',
                background: 'var(--bg-primary)',
                fontSize: '13px',
                color: 'var(--text-primary)',
                cursor: sectorsLoading ? 'not-allowed' : 'pointer',
                opacity: sectorsLoading ? 0.7 : 1,
              }}
            >
              <option value="">所有板块</option>
              {sectors.map((sector) => (
                <option key={sector.key} value={sector.key}>
                  {sector.labelZh}
                </option>
              ))}
            </select>
          </div>

          {/* Industry 筛选 */}
          {selectedSector && (
            <select
              value={selectedIndustry}
              onChange={(e) => setSelectedIndustry(e.target.value)}
              disabled={industriesLoading}
              style={{
                padding: '8px 12px',
                borderRadius: '8px',
                border: '1px solid var(--border-color)',
                background: 'var(--bg-primary)',
                fontSize: '13px',
                color: 'var(--text-primary)',
                cursor: industriesLoading ? 'not-allowed' : 'pointer',
                opacity: industriesLoading ? 0.7 : 1,
              }}
            >
              <option value="">所有行业</option>
              {industries.map((ind) => (
                <option key={ind.key} value={ind.key}>
                  {ind.name}
                </option>
              ))}
            </select>
          )}

          {/* 排序 */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginLeft: 'auto' }}>
            <ArrowUpDown size={16} color="var(--text-muted)" />
            <select
              value={sortBy}
              onChange={(e) => {
                const newSortBy = e.target.value as typeof sortBy;
                setSortBy(newSortBy);
                if (results.length > 0) {
                  setResults(sortResults(results, newSortBy, sortOrder));
                }
              }}
              style={{
                padding: '8px 12px',
                borderRadius: '8px',
                border: '1px solid var(--border-color)',
                background: 'var(--bg-primary)',
                fontSize: '13px',
                color: 'var(--text-primary)',
                cursor: 'pointer',
              }}
            >
              {SORT_OPTIONS.map((opt) => (
                <option key={opt.key} value={opt.key}>
                  {opt.labelZh}
                </option>
              ))}
            </select>
            <button
              onClick={() => {
                const newOrder = sortOrder === 'asc' ? 'desc' : 'asc';
                setSortOrder(newOrder);
                if (results.length > 0) {
                  setResults(sortResults(results, sortBy, newOrder));
                }
              }}
              style={{
                padding: '8px 12px',
                borderRadius: '8px',
                border: '1px solid var(--border-color)',
                background: 'var(--bg-primary)',
                fontSize: '13px',
                color: 'var(--text-primary)',
                cursor: 'pointer',
              }}
            >
              {sortOrder === 'asc' ? '↑' : '↓'}
            </button>
          </div>
        </div>
      </div>

      {/* 搜索结果 */}
      {hasSearched && (
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
              <p>搜索中...</p>
            </div>
          ) : results.length === 0 ? (
            <div style={{ padding: '60px', textAlign: 'center', color: 'var(--text-muted)' }}>
              <p>未找到匹配的股票</p>
            </div>
          ) : (
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ background: 'var(--bg-secondary)' }}>
                    <th style={thStyle}>股票</th>
                    <th style={thStyle}>板块</th>
                    <th style={{ ...thStyle, textAlign: 'right' }}>市值</th>
                    <th style={{ ...thStyle, textAlign: 'right' }}>市盈率 (PE)</th>
                    <th style={{ ...thStyle, textAlign: 'right' }}>价格</th>
                    <th style={{ ...thStyle, textAlign: 'center' }}>操作</th>
                  </tr>
                </thead>
                <tbody>
                  {results.map((stock, index) => {
                    const sectorConfig = getSectorConfig(stock.sector);
                    const isAdded = addedSymbols.has(stock.symbol);
                    const isAdding = addingSymbol === stock.symbol;
                    
                    return (
                      <tr
                        key={stock.symbol}
                        style={{
                          borderBottom:
                            index < results.length - 1 ? '1px solid var(--border-color)' : 'none',
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
                                background: sectorConfig.bg,
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                color: sectorConfig.color,
                                fontSize: '12px',
                                fontWeight: 600,
                              }}
                            >
                              {stock.symbol.slice(0, 2)}
                            </div>
                            <div>
                              <p
                                style={{
                                  fontSize: '15px',
                                  fontWeight: 600,
                                  color: 'var(--text-primary)',
                                  margin: '0 0 2px 0',
                                }}
                              >
                                {stock.symbol}
                              </p>
                              <p
                                style={{
                                  fontSize: '13px',
                                  color: 'var(--text-muted)',
                                  margin: 0,
                                }}
                              >
                                {stock.name}
                              </p>
                            </div>
                          </div>
                        </td>
                        <td style={tdStyle}>
                          <span
                            style={{
                              fontSize: '12px',
                              fontWeight: 500,
                              padding: '4px 10px',
                              borderRadius: '6px',
                              background: sectorConfig.bg,
                              color: sectorConfig.color,
                            }}
                          >
                            {sectorConfig.labelZh}
                          </span>
                        </td>
                        <td style={{ ...tdStyle, textAlign: 'right' }}>
                          <span
                            style={{ fontSize: '14px', color: 'var(--text-primary)' }}
                          >
                            {formatMarketCap(stock.marketCap)}
                          </span>
                        </td>
                        <td style={{ ...tdStyle, textAlign: 'right' }}>
                          <span style={{ fontSize: '14px', color: 'var(--text-primary)' }}>
                            {stock.trailingPE?.toFixed(2) || '-'}
                          </span>
                        </td>
                        <td style={{ ...tdStyle, textAlign: 'right' }}>
                          <span style={{ fontSize: '14px', color: 'var(--text-primary)' }}>
                            ${stock.price?.toFixed(2) || '-'}
                          </span>
                        </td>
                        <td style={{ ...tdStyle, textAlign: 'center' }}>
                          <button
                            onClick={() => handleAddToWatchlist(stock)}
                            disabled={isAdding || isAdded}
                            style={{
                              display: 'inline-flex',
                              alignItems: 'center',
                              gap: '4px',
                              padding: '6px 12px',
                              borderRadius: '6px',
                              border: 'none',
                              background: isAdded 
                                ? 'var(--success-color, #22c55e)' 
                                : 'var(--primary-color)',
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
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// 样式常量
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
