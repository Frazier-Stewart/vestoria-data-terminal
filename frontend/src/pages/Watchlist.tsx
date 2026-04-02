import { useState, useEffect } from 'react';
import { Star, Plus, TrendingUp, TrendingDown, Trash2, ExternalLink } from 'lucide-react';
import { Link } from 'react-router-dom';
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || '';

interface Asset {
  id: string;
  symbol: string;
  name: string;
  asset_type: string;
  exchange?: string;
  currency?: string;
  is_active: boolean;
  created_at: string;
}

export default function Watchlist() {
  const [assets, setAssets] = useState<Asset[]>([]);
  const [loading, setLoading] = useState(true);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  // 加载关注列表
  useEffect(() => {
    loadWatchlist();
  }, []);

  const loadWatchlist = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API_BASE_URL}/api/v1/assets`);
      setAssets(response.data || []);
    } catch (error) {
      console.error('Failed to load watchlist:', error);
      setAssets([]);
    } finally {
      setLoading(false);
    }
  };

  // 删除资产
  const handleDelete = async (id: string) => {
    if (deletingId) return;
    
    setDeletingId(id);
    try {
      await axios.delete(`${API_BASE_URL}/api/v1/assets/${id}`);
      setAssets((prev) => prev.filter((a) => a.id !== id));
    } catch (error) {
      console.error('Failed to delete asset:', error);
    } finally {
      setDeletingId(null);
    }
  };

  // 获取资产类型显示
  const getAssetTypeLabel = (type: string) => {
    const labels: Record<string, string> = {
      equity: '股票',
      crypto: '加密货币',
      etf: 'ETF',
      commodity: '大宗商品',
      forex: '外汇',
    };
    return labels[type] || type;
  };

  // 获取资产类型颜色
  const getAssetTypeColor = (type: string) => {
    const colors: Record<string, { bg: string; color: string }> = {
      equity: { bg: 'rgba(99, 102, 241, 0.1)', color: '#6366f1' },
      crypto: { bg: 'rgba(245, 158, 11, 0.1)', color: '#f59e0b' },
      etf: { bg: 'rgba(34, 197, 94, 0.1)', color: '#22c55e' },
      commodity: { bg: 'rgba(239, 68, 68, 0.1)', color: '#ef4444' },
      forex: { bg: 'rgba(6, 182, 212, 0.1)', color: '#06b6d4' },
    };
    return colors[type] || { bg: 'rgba(99, 102, 241, 0.1)', color: '#6366f1' };
  };

  const hasWatchlist = assets.length > 0;

  return (
    <div className="animate-fade-in">
      {/* Header */}
      <div style={{ marginBottom: '32px', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end' }}>
        <div>
          <h1
            style={{
              fontSize: '32px',
              fontWeight: 700,
              color: 'var(--text-primary)',
              margin: '0 0 8px 0',
              letterSpacing: '-0.5px',
            }}
          >
            关注列表
          </h1>
          <p style={{ fontSize: '15px', color: 'var(--text-muted)', margin: 0 }}>
            管理你关注的标的 ({assets.length})
          </p>
        </div>
        <Link
          to="/assets"
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '8px',
            padding: '10px 20px',
            borderRadius: '12px',
            border: 'none',
            background: 'var(--primary-color)',
            color: 'white',
            fontSize: '14px',
            fontWeight: 600,
            textDecoration: 'none',
            transition: 'all 0.3s ease',
          }}
        >
          <Plus size={18} />
          添加标的
        </Link>
      </div>

      {/* Watchlist Content */}
      {loading ? (
        <div
          style={{
            background: 'var(--bg-primary)',
            borderRadius: '20px',
            border: '1px solid var(--border-color)',
            padding: '60px',
            textAlign: 'center',
          }}
        >
          <p style={{ color: 'var(--text-muted)' }}>加载中...</p>
        </div>
      ) : !hasWatchlist ? (
        <div
          style={{
            background: 'var(--bg-primary)',
            borderRadius: '20px',
            border: '1px solid var(--border-color)',
            padding: '60px',
          }}
        >
          <div style={{ textAlign: 'center' }}>
            <div
              style={{
                width: '80px',
                height: '80px',
                borderRadius: '20px',
                background: 'var(--bg-secondary)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                margin: '0 auto 20px',
              }}
            >
              <Star size={32} color="var(--text-muted)" />
            </div>
            <p
              style={{
                fontSize: '16px',
                fontWeight: 600,
                color: 'var(--text-primary)',
                marginBottom: '8px',
              }}
            >
              暂无关注标的
            </p>
            <p style={{ color: 'var(--text-muted)', marginBottom: '24px' }}>
              添加你感兴趣的标的到关注列表
            </p>
            <Link
              to="/assets"
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '8px',
                padding: '12px 24px',
                borderRadius: '12px',
                border: 'none',
                background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
                color: 'white',
                fontSize: '14px',
                fontWeight: 600,
                textDecoration: 'none',
                transition: 'all 0.3s ease',
                boxShadow: '0 4px 14px rgba(99, 102, 241, 0.4)',
              }}
            >
              <Plus size={18} />
              去添加标的
            </Link>
          </div>
        </div>
      ) : (
        <div
          style={{
            background: 'var(--bg-primary)',
            borderRadius: '20px',
            border: '1px solid var(--border-color)',
            overflow: 'hidden',
          }}
        >
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ background: 'var(--bg-secondary)' }}>
                <th style={thStyle}>标的</th>
                <th style={thStyle}>类型</th>
                <th style={thStyle}>交易所</th>
                <th style={thStyle}>货币</th>
                <th style={{ ...thStyle, textAlign: 'center' }}>操作</th>
              </tr>
            </thead>
            <tbody>
              {assets.map((asset, index) => {
                const typeStyle = getAssetTypeColor(asset.asset_type);
                return (
                  <tr
                    key={asset.id}
                    style={{
                      borderBottom:
                        index < assets.length - 1 ? '1px solid var(--border-color)' : 'none',
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
                            background: typeStyle.bg,
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            color: typeStyle.color,
                            fontSize: '12px',
                            fontWeight: 600,
                          }}
                        >
                          {asset.symbol.slice(0, 2)}
                        </div>
                        <div>
                          <Link
                            to={`/assets/${asset.id}`}
                            style={{
                              fontSize: '15px',
                              fontWeight: 600,
                              color: 'var(--text-primary)',
                              textDecoration: 'none',
                              margin: '0 0 2px 0',
                              display: 'block',
                            }}
                          >
                            {asset.symbol}
                          </Link>
                          <p
                            style={{
                              fontSize: '13px',
                              color: 'var(--text-muted)',
                              margin: 0,
                            }}
                          >
                            {asset.name}
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
                          background: typeStyle.bg,
                          color: typeStyle.color,
                        }}
                      >
                        {getAssetTypeLabel(asset.asset_type)}
                      </span>
                    </td>
                    <td style={tdStyle}>
                      <span style={{ fontSize: '14px', color: 'var(--text-primary)' }}>
                        {asset.exchange || '-'}
                      </span>
                    </td>
                    <td style={tdStyle}>
                      <span style={{ fontSize: '14px', color: 'var(--text-primary)' }}>
                        {asset.currency || '-'}
                      </span>
                    </td>
                    <td style={{ ...tdStyle, textAlign: 'center' }}>
                      <div style={{ display: 'flex', gap: '8px', justifyContent: 'center' }}>
                        <Link
                          to={`/assets/${asset.id}`}
                          style={{
                            padding: '8px',
                            borderRadius: '8px',
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
                          <ExternalLink size={16} />
                        </Link>
                        <button
                          onClick={() => handleDelete(asset.id)}
                          disabled={deletingId === asset.id}
                          style={{
                            padding: '8px',
                            borderRadius: '8px',
                            border: 'none',
                            background: 'rgba(239, 68, 68, 0.1)',
                            color: '#ef4444',
                            cursor: deletingId === asset.id ? 'not-allowed' : 'pointer',
                            opacity: deletingId === asset.id ? 0.7 : 1,
                            display: 'inline-flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                          }}
                          title="删除"
                        >
                          <Trash2 size={16} />
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
