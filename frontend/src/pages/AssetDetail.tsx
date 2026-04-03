import { useParams, Link } from 'react-router-dom';
import { useEffect, useState, useMemo, useCallback } from 'react';
import axios from 'axios';
import { createChart, CandlestickSeries, HistogramSeries, ColorType } from 'lightweight-charts';
import { ArrowLeft, TrendingUp, Calendar, Activity, Database, Globe, DollarSign, Circle } from 'lucide-react';
import dayjs from 'dayjs';

const API_BASE_URL = import.meta.env.VITE_API_URL || '';

interface Asset {
  id: string;
  symbol: string;
  name: string;
  asset_type: string;
  exchange: string;
  currency: string;
  data_source: string;
  is_active: boolean;
}

interface PriceData {
  id: number;
  asset_id: string;
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

type TimeRange = '1M' | '3M' | '6M' | '1Y' | 'ALL';

interface StatCardProps {
  title: string;
  value: string;
  icon: React.ElementType;
  color: string;
}

function StatCard({ title, value, icon: Icon, color }: StatCardProps) {
  return (
    <div
      style={{
        background: 'var(--bg-primary)',
        borderRadius: '20px',
        padding: '20px',
        border: '1px solid var(--border-color)',
        transition: 'all 0.3s ease',
      }}
      className="hover-lift"
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <div
          style={{
            width: '44px',
            height: '44px',
            borderRadius: '12px',
            background: `${color}15`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: color,
            flexShrink: 0,
          }}
        >
          <Icon size={22} />
        </div>
        <div>
          <p style={{ fontSize: '13px', color: 'var(--text-muted)', margin: '0 0 4px 0', fontWeight: 500 }}>
            {title}
          </p>
          <p style={{ fontSize: '18px', fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>
            {value}
          </p>
        </div>
      </div>
    </div>
  );
}

function getChartColors() {
  const isDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
  return {
    textColor: isDark ? '#64748b' : '#94a3b8',
    gridColor: isDark ? 'rgba(51, 65, 85, 0.5)' : 'rgba(226, 232, 240, 0.8)',
    borderColor: isDark ? '#334155' : '#e2e8f0',
    crosshairColor: isDark ? '#94a3b8' : '#64748b',
  };
}

export default function AssetDetail() {
  const { id } = useParams<{ id: string }>();
  const [asset, setAsset] = useState<Asset | null>(null);
  const [prices, setPrices] = useState<PriceData[]>([]);
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState<TimeRange>('3M');
  const [chartContainer, setChartContainer] = useState<HTMLDivElement | null>(null);

  const chartContainerRef = useCallback((node: HTMLDivElement | null) => {
    setChartContainer(node);
  }, []);

  useEffect(() => {
    if (id) {
      fetchAsset(id);
      fetchPrices(id);
    }
  }, [id]);

  const fetchAsset = async (assetId: string) => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/v1/assets/${assetId}`);
      setAsset(response.data);
    } catch (error) {
      console.error('Failed to fetch asset:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchPrices = async (assetId: string) => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/v1/prices?asset_id=${assetId}&limit=9999`);
      const sorted = response.data.sort((a: PriceData, b: PriceData) =>
        new Date(a.date).getTime() - new Date(b.date).getTime()
      );
      setPrices(sorted);
    } catch (error) {
      console.error('Failed to fetch prices:', error);
    }
  };

  const filteredPrices = useMemo(() => {
    if (timeRange === 'ALL') return prices;

    const now = dayjs();
    const ranges: Record<TimeRange, number> = {
      '1M': 30, '3M': 90, '6M': 180, '1Y': 365, 'ALL': 9999,
    };

    const cutoff = now.subtract(ranges[timeRange], 'day');
    return prices.filter(p => dayjs(p.date).isAfter(cutoff));
  }, [prices, timeRange]);

  // Single effect: create chart + set data (re-runs on container ready, data change, or time range change)
  useEffect(() => {
    if (!chartContainer || filteredPrices.length === 0) return;

    const colors = getChartColors();

    const chart = createChart(chartContainer, {
      layout: {
        background: { type: ColorType.Solid, color: 'transparent' },
        textColor: colors.textColor,
        fontFamily: "'Inter', -apple-system, sans-serif",
      },
      grid: {
        vertLines: { color: colors.gridColor },
        horzLines: { color: colors.gridColor },
      },
      width: chartContainer.clientWidth,
      height: 420,
      crosshair: {
        vertLine: { color: colors.crosshairColor, width: 1, style: 3, labelBackgroundColor: '#6366f1' },
        horzLine: { color: colors.crosshairColor, width: 1, style: 3, labelBackgroundColor: '#6366f1' },
      },
      rightPriceScale: {
        borderColor: colors.borderColor,
        scaleMargins: { top: 0.05, bottom: 0.25 },
      },
      timeScale: {
        borderColor: colors.borderColor,
        timeVisible: false,
        fixLeftEdge: true,
        fixRightEdge: true,
      },
    });

    const candleSeries = chart.addSeries(CandlestickSeries, {
      upColor: '#22c55e',
      downColor: '#ef4444',
      borderVisible: false,
      wickUpColor: '#22c55e',
      wickDownColor: '#ef4444',
    });

    const volumeSeries = chart.addSeries(HistogramSeries, {
      priceFormat: { type: 'volume' },
      priceScaleId: 'volume',
    });

    chart.priceScale('volume').applyOptions({
      scaleMargins: { top: 0.8, bottom: 0 },
    });

    // Set data
    const ohlcData = filteredPrices.map(p => ({
      time: p.date as string,
      open: p.open,
      high: p.high,
      low: p.low,
      close: p.close,
    }));

    const volumeData = filteredPrices.map(p => ({
      time: p.date as string,
      value: p.volume,
      color: p.close >= p.open ? 'rgba(34, 197, 94, 0.4)' : 'rgba(239, 68, 68, 0.4)',
    }));

    candleSeries.setData(ohlcData);
    volumeSeries.setData(volumeData);
    chart.timeScale().fitContent();

    const handleResize = () => {
      chart.applyOptions({ width: chartContainer.clientWidth });
    };
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      chart.remove();
    };
  }, [chartContainer, filteredPrices]);

  const stats = useMemo(() => {
    if (filteredPrices.length === 0) return null;
    const latest = filteredPrices[filteredPrices.length - 1];
    const first = filteredPrices[0];
    const high = Math.max(...filteredPrices.map(p => p.high));
    const low = Math.min(...filteredPrices.map(p => p.low));
    const avgVolume = filteredPrices.reduce((sum, p) => sum + p.volume, 0) / filteredPrices.length;
    const change = latest.close - first.close;
    const changePercent = (change / first.close) * 100;

    return {
      latest: latest.close,
      high,
      low,
      avgVolume: Math.floor(avgVolume),
      change,
      changePercent,
      isPositive: change >= 0,
    };
  }, [filteredPrices]);

  if (loading) {
    return (
      <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
        加载中...
      </div>
    );
  }

  if (!asset) {
    return (
      <div style={{ padding: '40px', textAlign: 'center' }}>
        <p style={{ color: 'var(--text-muted)' }}>标的未找到</p>
        <Link to="/assets" style={{ color: 'var(--primary-color)' }}>返回标的列表</Link>
      </div>
    );
  }

  const typeMap: Record<string, { label: string; color: string; bg: string }> = {
    crypto: { label: '加密货币', color: '#6366f1', bg: 'rgba(99, 102, 241, 0.1)' },
    stock: { label: '股票', color: '#22c55e', bg: 'rgba(34, 197, 94, 0.1)' },
    etf: { label: 'ETF', color: '#f59e0b', bg: 'rgba(245, 158, 11, 0.1)' },
    commodity: { label: '大宗商品', color: '#ef4444', bg: 'rgba(239, 68, 68, 0.1)' },
    fund: { label: '基金', color: '#3b82f6', bg: 'rgba(59, 130, 246, 0.1)' },
  };

  const typeConfig = typeMap[asset.asset_type] || { label: asset.asset_type, color: '#6366f1', bg: 'rgba(99, 102, 241, 0.1)' };

  const timeButtons: { key: TimeRange; label: string }[] = [
    { key: '1M', label: '1月' },
    { key: '3M', label: '3月' },
    { key: '6M', label: '6月' },
    { key: '1Y', label: '1年' },
    { key: 'ALL', label: '全部' },
  ];

  return (
    <div className="animate-fade-in">
      {/* Header */}
      <div style={{ marginBottom: '32px' }}>
        <Link
          to="/assets"
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '6px',
            fontSize: '14px',
            color: 'var(--text-muted)',
            textDecoration: 'none',
            marginBottom: '16px',
          }}
        >
          <ArrowLeft size={16} />
          返回标的列表
        </Link>

        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '8px' }}>
              <h1 style={{ fontSize: '32px', fontWeight: 700, margin: 0, letterSpacing: '-0.5px' }}>
                {asset.symbol}
              </h1>
              <span
                style={{
                  fontSize: '13px',
                  fontWeight: 600,
                  padding: '6px 14px',
                  borderRadius: '8px',
                  background: typeConfig.bg,
                  color: typeConfig.color,
                }}
              >
                {typeConfig.label}
              </span>
            </div>
            <p style={{ fontSize: '15px', color: 'var(--text-muted)', margin: 0 }}>
              {asset.name}
            </p>
          </div>

          {stats && (
            <div style={{ textAlign: 'right' }}>
              <div style={{ fontSize: '32px', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '4px' }}>
                ${stats.latest.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </div>
              <div style={{
                fontSize: '14px',
                fontWeight: 600,
                color: stats.isPositive ? '#22c55e' : '#ef4444',
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
                justifyContent: 'flex-end',
              }}>
                <TrendingUp size={16} />
                {stats.isPositive ? '+' : ''}{stats.change.toFixed(2)} ({stats.isPositive ? '+' : ''}{stats.changePercent.toFixed(2)}%)
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: '16px',
          marginBottom: '24px'
        }}>
          <StatCard title="区间最高" value={`$${stats.high.toLocaleString('en-US', { minimumFractionDigits: 2 })}`} icon={TrendingUp} color="#22c55e" />
          <StatCard title="区间最低" value={`$${stats.low.toLocaleString('en-US', { minimumFractionDigits: 2 })}`} icon={TrendingUp} color="#ef4444" />
          <StatCard title="平均成交量" value={stats.avgVolume.toLocaleString()} icon={Activity} color="#6366f1" />
          <StatCard title="数据天数" value={`${filteredPrices.length} 天`} icon={Calendar} color="#f59e0b" />
        </div>
      )}

      {/* Chart */}
      <div
        style={{
          background: 'var(--bg-primary)',
          borderRadius: '20px',
          padding: '24px',
          border: '1px solid var(--border-color)',
          marginBottom: '24px',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <h3 style={{ fontSize: '18px', fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>
            价格走势
          </h3>
          <div style={{ display: 'flex', gap: '8px' }}>
            {timeButtons.map((btn) => (
              <button
                key={btn.key}
                onClick={() => setTimeRange(btn.key)}
                style={{
                  padding: '8px 16px',
                  borderRadius: '10px',
                  border: '1px solid var(--border-color)',
                  background: timeRange === btn.key ? 'var(--primary-color)' : 'var(--bg-secondary)',
                  color: timeRange === btn.key ? 'white' : 'var(--text-secondary)',
                  fontSize: '13px',
                  fontWeight: 600,
                  cursor: 'pointer',
                  transition: 'all 0.2s',
                }}
              >
                {btn.label}
              </button>
            ))}
          </div>
        </div>

        <div style={{ position: 'relative', width: '100%', height: '420px' }}>
          <div ref={chartContainerRef} style={{ width: '100%', height: '100%' }} />
          {filteredPrices.length === 0 && (
            <div style={{
              position: 'absolute', top: 0, left: 0, right: 0, bottom: 0,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              color: 'var(--text-muted)', background: 'var(--bg-primary)',
            }}>
              暂无历史数据
            </div>
          )}
        </div>
      </div>

      {/* 基本信息 */}
      <div
        style={{
          background: 'var(--bg-primary)',
          borderRadius: '20px',
          padding: '24px',
          border: '1px solid var(--border-color)',
        }}
      >
        <h3 style={{ fontSize: '18px', fontWeight: 700, color: 'var(--text-primary)', margin: '0 0 20px 0' }}>
          基本信息
        </h3>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '16px' }}>
          {[
            { label: '代码', value: asset.symbol, icon: Database },
            { label: '名称', value: asset.name, icon: Database },
            { label: '类型', value: typeConfig.label, icon: Database, color: typeConfig.color },
            { label: '交易所', value: asset.exchange || '-', icon: Globe },
            { label: '货币', value: asset.currency, icon: DollarSign },
            { label: '数据源', value: asset.data_source, icon: Database },
            { label: '状态', value: asset.is_active ? '活跃' : '暂停', icon: Circle, color: asset.is_active ? '#22c55e' : 'var(--text-muted)' },
          ].map((item) => (
            <div
              key={item.label}
              style={{
                padding: '16px',
                background: 'var(--bg-secondary)',
                borderRadius: '12px',
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
              }}
            >
              <div style={{ flex: 1 }}>
                <p style={{ fontSize: '12px', color: 'var(--text-muted)', margin: '0 0 4px 0' }}>{item.label}</p>
                <p style={{ fontSize: '15px', fontWeight: 600, color: item.color || 'var(--text-primary)', margin: 0 }}>{item.value}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
