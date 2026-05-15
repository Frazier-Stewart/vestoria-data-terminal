import { useParams, Link } from 'react-router-dom';
import { useEffect, useState, useMemo, useCallback } from 'react';
import axios from 'axios';
import { createChart, AreaSeries, LineSeries, CandlestickSeries, ColorType, PriceScaleMode } from 'lightweight-charts';
import { ArrowLeft, Activity, AlertCircle, TrendingUp, Gauge, Database, Loader2, Plus, RefreshCw, AlertTriangle } from 'lucide-react';
import dayjs from 'dayjs';

const API_BASE_URL = import.meta.env.VITE_API_URL || '';

interface Indicator {
  id: number;
  name: string;
  indicator_type: string;
  asset_id?: string;
  description?: string;
  template?: {
    id: string;
    indicator_type: string;
  };
  config?: {
    multipliers: number[];
    labels: string[];
    colors: string[];
  };
}

interface IndicatorValue {
  id: number;
  date: string;
  value: number;
  value_text?: string;
  grade?: string;
  grade_label?: string;
  extra_data?: {
    ma_value?: number;
    current_price?: number;
  };
}

interface PriceChartData {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume?: number;
  ma_value?: number;
}

interface PriceDataCheck {
  asset_id: string;
  total_records: number;
  earliest_date?: string;
  latest_date?: string;
  has_enough_data: boolean;
  days_coverage: number;
  max_continuous_days: number;
  max_continuous_start?: string;
  max_continuous_end?: string;
  gaps: Array<{ start_date: string; end_date: string; days: number }>;
  needs_backfill: boolean;
  message: string;
}

type TimeRange = '1M' | '3M' | '6M' | '1Y' | 'ALL';

const typeConfig: Record<string, { label: string; color: string; bg: string; icon: React.ElementType }> = {
  fear_greed: { label: '恐慌贪婪', color: '#8b5cf6', bg: 'rgba(139, 92, 246, 0.1)', icon: AlertCircle },
  vix: { label: 'VIX', color: '#f59e0b', bg: 'rgba(245, 158, 11, 0.1)', icon: Gauge },
  ma200: { label: 'MA200', color: '#3b82f6', bg: 'rgba(59, 130, 246, 0.1)', icon: TrendingUp },
  pe: { label: '市盈率', color: '#22c55e', bg: 'rgba(34, 197, 94, 0.1)', icon: Activity },
  metric: { label: '技术指标', color: '#3b82f6', bg: 'rgba(59, 130, 246, 0.1)', icon: TrendingUp },
  sentiment: { label: '情绪指标', color: '#8b5cf6', bg: 'rgba(139, 92, 246, 0.1)', icon: AlertCircle },
  volatility: { label: '波动率', color: '#f59e0b', bg: 'rgba(245, 158, 11, 0.1)', icon: Gauge },
};

const gradeConfig: Record<string, { label: string; color: string; bg: string }> = {
  extreme_fear: { label: '极度恐惧', color: '#7f1d1d', bg: 'rgba(127, 29, 29, 0.15)' },
  fear: { label: '恐惧', color: '#dc2626', bg: 'rgba(220, 38, 38, 0.15)' },
  neutral: { label: '中性', color: '#ca8a04', bg: 'rgba(202, 138, 4, 0.15)' },
  greed: { label: '贪婪', color: '#16a34a', bg: 'rgba(22, 163, 74, 0.15)' },
  extreme_greed: { label: '极度贪婪', color: '#14532d', bg: 'rgba(20, 83, 45, 0.15)' },
  very_low: { label: '极度低估', color: '#16a34a', bg: 'rgba(22, 163, 74, 0.15)' },
  low: { label: '低估', color: '#22c55e', bg: 'rgba(34, 197, 94, 0.15)' },
  medium_low: { label: '偏低', color: '#84cc16', bg: 'rgba(132, 204, 22, 0.15)' },
  medium: { label: '合理', color: '#6b7280', bg: 'rgba(107, 114, 128, 0.15)' },
  medium_high: { label: '偏高', color: '#f59e0b', bg: 'rgba(245, 158, 11, 0.15)' },
  high: { label: '高估', color: '#ef4444', bg: 'rgba(239, 68, 68, 0.15)' },
  very_high: { label: '极度高估', color: '#dc2626', bg: 'rgba(220, 38, 38, 0.15)' },
};

const getFearGreedGrade = (value: number): { label: string; color: string } => {
  if (value <= 20) return { label: '极度恐慌', color: '#7f1d1d' };
  if (value <= 40) return { label: '恐慌', color: '#dc2626' };
  if (value <= 60) return { label: '中性', color: '#ca8a04' };
  if (value <= 80) return { label: '贪婪', color: '#16a34a' };
  return { label: '极度贪婪', color: '#14532d' };
};

function getChartColors() {
  const isDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
  return {
    textColor: isDark ? '#64748b' : '#94a3b8',
    gridColor: isDark ? 'rgba(51, 65, 85, 0.5)' : 'rgba(226, 232, 240, 0.8)',
    borderColor: isDark ? '#334155' : '#e2e8f0',
    crosshairColor: isDark ? '#94a3b8' : '#64748b',
  };
}

const timeButtons: { key: TimeRange; label: string }[] = [
  { key: '1M', label: '1月' },
  { key: '3M', label: '3月' },
  { key: '6M', label: '6月' },
  { key: '1Y', label: '1年' },
  { key: 'ALL', label: '全部' },
];

export default function IndicatorDetail() {
  const { id } = useParams<{ id: string }>();
  const [indicator, setIndicator] = useState<Indicator | null>(null);
  const [allValues, setAllValues] = useState<IndicatorValue[]>([]);
  const [timeRange, setTimeRange] = useState<TimeRange>('ALL');
  const [loading, setLoading] = useState(true);
  const [chartContainer, setChartContainer] = useState<HTMLDivElement | null>(null);
  const [priceChartContainer, setPriceChartContainer] = useState<HTMLDivElement | null>(null);
  const [recalculating, setRecalculating] = useState(false);
  const [backfilling, setBackfilling] = useState(false);
  const [priceCheck, setPriceCheck] = useState<PriceDataCheck | null>(null);
  const [priceChartData, setPriceChartData] = useState<PriceChartData[]>([]);
  const [showBackfillModal, setShowBackfillModal] = useState(false);
  const [backfillStart, setBackfillStart] = useState('');
  const [backfillEnd, setBackfillEnd] = useState('');
  const [isLogScale, setIsLogScale] = useState(false);
  const [isPriceLogScale, setIsPriceLogScale] = useState(false);

  const chartContainerRef = useCallback((node: HTMLDivElement | null) => {
    setChartContainer(node);
  }, []);
  const priceChartContainerRef = useCallback((node: HTMLDivElement | null) => {
    setPriceChartContainer(node);
  }, []);

  useEffect(() => {
    if (id) {
      fetchIndicator(parseInt(id));
      fetchValues(parseInt(id));
      fetchPriceDataCheck(parseInt(id));
      fetchPriceChartData(parseInt(id));
    }
  }, [id]);

  const fetchIndicator = async (indicatorId: number) => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/v1/indicators/${indicatorId}`);
      setIndicator(response.data);
    } catch (error) {
      console.error('Failed to fetch indicator:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchValues = async (indicatorId: number) => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/v1/indicators/${indicatorId}/values?limit=5000`);
      const sorted = response.data.sort((a: IndicatorValue, b: IndicatorValue) =>
        new Date(a.date).getTime() - new Date(b.date).getTime()
      );
      setAllValues(sorted);
    } catch (error) {
      console.error('Failed to fetch values:', error);
    }
  };

  const fetchPriceChartData = async (indicatorId: number) => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/v1/indicators/${indicatorId}/price-chart-data`);
      setPriceChartData(response.data);
    } catch (error) {
      console.error('Failed to fetch price chart data:', error);
    }
  };

  const fetchPriceDataCheck = async (indicatorId: number) => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/v1/indicators/${indicatorId}/price-data-check`);
      setPriceCheck(response.data);
      // Auto-set backfill dates if needed
      if (response.data.needs_backfill && response.data.latest_date) {
        const latest = dayjs(response.data.latest_date);
        const sixYearsAgo = dayjs().subtract(6, 'year');
        setBackfillStart(sixYearsAgo.format('YYYY-MM-DD'));
        setBackfillEnd(latest.format('YYYY-MM-DD'));
      }
    } catch (error) {
      console.error('Failed to check price data:', error);
    }
  };

  const handleRecalculate = async () => {
    if (!id) return;
    setRecalculating(true);
    try {
      // Use earliest price data date for full calculation
      let startDate: string;
      if (priceCheck?.earliest_date) {
        startDate = priceCheck.earliest_date;
      } else {
        startDate = dayjs().subtract(6, 'year').format('YYYY-MM-DD');
      }
      const today = dayjs().format('YYYY-MM-DD');
      await axios.post(`${API_BASE_URL}/api/v1/indicators/${id}/recalculate`, {
        start: startDate,
        end: today,
      });
      await fetchValues(parseInt(id));
      await fetchPriceChartData(parseInt(id));
    } catch (error) {
      console.error('Failed to recalculate:', error);
      if (axios.isAxiosError(error) && error.response?.data?.detail) {
        alert(`重新计算失败: ${error.response.data.detail}`);
      } else {
        alert('重新计算失败，请检查价格数据是否充足');
      }
    } finally {
      setRecalculating(false);
    }
  };

  const handleBackfillPrices = async () => {
    if (!indicator?.asset_id || !backfillStart || !backfillEnd) return;
    setBackfilling(true);
    try {
      const response = await axios.post(
        `${API_BASE_URL}/api/v1/prices/backfill-range?asset_id=${indicator.asset_id}`,
        {
          start_date: backfillStart,
          end_date: backfillEnd,
        }
      );
      setShowBackfillModal(false);
      alert(`数据增补完成！共获取 ${response.data.days_filled} 天数据`);
      await fetchPriceDataCheck(parseInt(id!));
    } catch (error) {
      console.error('Failed to backfill:', error);
      if (axios.isAxiosError(error) && error.response?.data?.detail) {
        alert(`增补数据失败: ${error.response.data.detail}`);
      } else {
        alert('增补数据失败，请重试');
      }
    } finally {
      setBackfilling(false);
    }
  };

  const filteredValues = useMemo(() => {
    if (timeRange === 'ALL') return allValues;
    const now = dayjs();
    const ranges: Record<TimeRange, number> = {
      '1M': 30, '3M': 90, '6M': 180, '1Y': 365, 'ALL': 99999,
    };
    const cutoff = now.subtract(ranges[timeRange], 'day');
    return allValues.filter(v => dayjs(v.date).isAfter(cutoff));
  }, [allValues, timeRange]);

  const filteredPriceChartData = useMemo(() => {
    if (timeRange === 'ALL') return priceChartData;
    const now = dayjs();
    const ranges: Record<TimeRange, number> = {
      '1M': 30, '3M': 90, '6M': 180, '1Y': 365, 'ALL': 99999,
    };
    const cutoff = now.subtract(ranges[timeRange], 'day');
    return priceChartData.filter(d => dayjs(d.date).isAfter(cutoff));
  }, [priceChartData, timeRange]);

  const isFearGreed = indicator?.template?.indicator_type === 'fear_greed' || indicator?.template?.id === 'BTC_FEAR_GREED';
  const isMA200 = indicator?.template?.id === 'MA200';

  const indicatorColor = useMemo(() => {
    if (!indicator) return '#6366f1';
    const config = typeConfig[indicator.template?.indicator_type || 'metric'] || typeConfig['metric'];
    return config.color;
  }, [indicator]);

  // Chart effect
  useEffect(() => {
    if (!chartContainer || filteredValues.length === 0) return;

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
      height: 525,
      crosshair: {
        vertLine: { color: colors.crosshairColor, width: 1, style: 3, labelBackgroundColor: '#6366f1' },
        horzLine: { color: colors.crosshairColor, width: 1, style: 3, labelBackgroundColor: '#6366f1' },
      },
      rightPriceScale: {
        borderColor: colors.borderColor,
        mode: isLogScale ? PriceScaleMode.Logarithmic : PriceScaleMode.Normal,
      },
      timeScale: {
        borderColor: colors.borderColor,
        timeVisible: false,
        fixLeftEdge: true,
        fixRightEdge: true,
      },
    });

    const series = chart.addSeries(AreaSeries, {
      lineColor: indicatorColor,
      topColor: `${indicatorColor}40`,
      bottomColor: `${indicatorColor}05`,
      lineWidth: 2,
      priceFormat: {
        type: 'price',
        precision: 2,
        minMove: 0.01,
      },
    });

    const chartData = filteredValues.map(v => ({
      time: v.date as string,
      value: v.value,
    }));

    series.setData(chartData);

    if (isFearGreed) {
      series.createPriceLine({ price: 20, color: 'rgba(220, 38, 38, 0.5)', lineWidth: 1, lineStyle: 2, axisLabelVisible: true, title: '极度恐慌' });
      series.createPriceLine({ price: 50, color: 'rgba(100, 116, 139, 0.4)', lineWidth: 1, lineStyle: 2, axisLabelVisible: true, title: '中性' });
      series.createPriceLine({ price: 80, color: 'rgba(22, 163, 74, 0.5)', lineWidth: 1, lineStyle: 2, axisLabelVisible: true, title: '极度贪婪' });
    }

    chart.timeScale().fitContent();

    const handleResize = () => {
      chart.applyOptions({ width: chartContainer.clientWidth });
    };
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      chart.remove();
    };
  }, [chartContainer, filteredValues, indicatorColor, isFearGreed, isLogScale]);

  // Price + MA200W chart effect (only for MA200 indicators)
  useEffect(() => {
    if (!isMA200 || !priceChartContainer || priceChartData.length === 0) return;

    const colors = getChartColors();

    const chart = createChart(priceChartContainer, {
      layout: {
        background: { type: ColorType.Solid, color: 'transparent' },
        textColor: colors.textColor,
        fontFamily: "'Inter', -apple-system, sans-serif",
      },
      grid: {
        vertLines: { color: colors.gridColor },
        horzLines: { color: colors.gridColor },
      },
      width: priceChartContainer.clientWidth,
      height: 525,
      crosshair: {
        vertLine: { color: colors.crosshairColor, width: 1, style: 3, labelBackgroundColor: '#6366f1' },
        horzLine: { color: colors.crosshairColor, width: 1, style: 3, labelBackgroundColor: '#6366f1' },
      },
      rightPriceScale: {
        borderColor: colors.borderColor,
        mode: isPriceLogScale ? PriceScaleMode.Logarithmic : PriceScaleMode.Normal,
      },
      timeScale: {
        borderColor: colors.borderColor,
        timeVisible: false,
        fixLeftEdge: true,
        fixRightEdge: true,
      },
    });

    // Candlestick (OHLC) - hide last value label
    const candleSeries = chart.addSeries(CandlestickSeries, {
      upColor: '#22c55e',
      downColor: '#ef4444',
      borderUpColor: '#22c55e',
      borderDownColor: '#ef4444',
      wickUpColor: '#22c55e',
      wickDownColor: '#ef4444',
      lastValueVisible: false,
    });
    candleSeries.setData(
      filteredPriceChartData
        .filter(d => d.open != null && d.high != null && d.low != null && d.close != null)
        .map(d => ({
          time: d.date,
          open: d.open,
          high: d.high,
          low: d.low,
          close: d.close,
        }))
    );

    // MA200W line (blue solid) - hide last value label
    const maSeries = chart.addSeries(LineSeries, {
      color: '#3b82f6',
      lineWidth: 2,
      lastValueVisible: false,
      priceFormat: {
        type: 'price',
        precision: 2,
        minMove: 0.01,
      },
    });
    const maData = filteredPriceChartData
      .filter(d => d.ma_value != null)
      .map(d => ({
        time: d.date,
        value: d.ma_value!,
      }));
    maSeries.setData(maData);

    // Get multiplier config from indicator or use default
    const maConfig = indicator?.config;
    const multipliers = maConfig?.multipliers || [1.0, 1.5, 2.0, 2.5, 3.0];
    const labels = maConfig?.labels || ["极度低估", "低估", "合理估值", "高估", "极度高估"];
    const maColors = maConfig?.colors || ["#3b82f6", "#22c55e", "#eab308", "#f97316", "#dc2626"];

    // Create multiplier series dynamically
    const multiplierSeries: Array<ReturnType<typeof chart.addSeries>> = [];
    for (let i = 1; i < multipliers.length; i++) {
      const series = chart.addSeries(LineSeries, {
        color: maColors[i],
        lineWidth: 2,
        lastValueVisible: false,
        priceFormat: { type: 'price', precision: 2, minMove: 0.01 },
      });
      series.setData(maData.map(d => ({ time: d.time, value: d.value * multipliers[i] })));
      multiplierSeries.push(series);
    }

    // Price lines for reference levels with valuation labels
    const latestMA = maData.length > 0 ? maData[maData.length - 1].value : null;
    if (latestMA != null) {
      // MA base line (1x)
      maSeries.createPriceLine({
        price: latestMA,
        color: maColors[0],
        lineWidth: 1,
        lineStyle: 2,
        axisLabelVisible: true,
        title: labels[0],
      });
      // Multiplier lines
      for (let i = 0; i < multiplierSeries.length; i++) {
        multiplierSeries[i].createPriceLine({
          price: latestMA * multipliers[i + 1],
          color: maColors[i + 1],
          lineWidth: 1,
          lineStyle: 2,
          axisLabelVisible: true,
          title: labels[i + 1],
        });
      }
    }

    chart.timeScale().fitContent();

    const handleResize = () => {
      chart.applyOptions({ width: priceChartContainer.clientWidth });
    };
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      chart.remove();
    };
  }, [priceChartContainer, filteredPriceChartData, isMA200, isPriceLogScale]);

  const stats = useMemo(() => {
    if (filteredValues.length === 0) return null;
    const latest = filteredValues[filteredValues.length - 1];
    const allValues = filteredValues.map(v => v.value);
    const max = Math.max(...allValues);
    const min = Math.min(...allValues);
    const avg = allValues.reduce((a, b) => a + b, 0) / allValues.length;

    return {
      latest: latest.value,
      latestGrade: latest.grade,
      latestLabel: latest.grade_label,
      max,
      min,
      avg: avg.toFixed(2),
      count: filteredValues.length,
    };
  }, [filteredValues]);

  if (loading) {
    return (
      <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
        加载中...
      </div>
    );
  }

  if (!indicator) {
    return (
      <div style={{ padding: '40px', textAlign: 'center' }}>
        <p style={{ color: 'var(--text-muted)' }}>指标未找到</p>
        <Link to="/indicators" style={{ color: 'var(--primary-color)' }}>返回指标列表</Link>
      </div>
    );
  }

  const config = typeConfig[indicator.template?.indicator_type || 'metric'] || typeConfig['metric'];
  const Icon = config.icon;
  const latestGrade = stats?.latestGrade ? gradeConfig[stats.latestGrade] : null;
  const latestFearGreed = isFearGreed && stats ? getFearGreedGrade(stats.latest) : null;

  return (
    <div className="animate-fade-in">
      {/* Header */}
      <div style={{ marginBottom: '32px' }}>
        <Link
          to="/indicators"
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
          返回指标列表
        </Link>

        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '16px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '8px' }}>
              <div
                style={{
                  width: '52px',
                  height: '52px',
                  borderRadius: '14px',
                  background: config.bg,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: config.color,
                }}
              >
                <Icon size={26} />
              </div>
              <div>
                <h1 style={{ fontSize: '28px', fontWeight: 700, margin: 0, letterSpacing: '-0.5px' }}>
                  {indicator.name}
                </h1>
                <p style={{ fontSize: '14px', color: 'var(--text-muted)', margin: '4px 0 0 0' }}>
                  {indicator.asset_id || '全局指标'}
                </p>
              </div>
            </div>
          </div>

          {stats && !isMA200 && (
            <div style={{ textAlign: 'right' }}>
              <div style={{ fontSize: '36px', fontWeight: 700, color: 'var(--text-primary)' }}>
                {stats.latest.toFixed(1)}
              </div>
              {latestFearGreed ? (
                <div style={{ fontSize: '14px', fontWeight: 600, padding: '6px 14px', borderRadius: '20px', background: `${latestFearGreed.color}20`, color: latestFearGreed.color, display: 'inline-block', marginTop: '8px' }}>
                  {latestFearGreed.label}
                </div>
              ) : latestGrade ? (
                <div style={{ fontSize: '14px', fontWeight: 600, padding: '6px 14px', borderRadius: '20px', background: latestGrade.bg, color: latestGrade.color, display: 'inline-block', marginTop: '8px' }}>
                  {latestGrade.label}
                </div>
              ) : null}
            </div>
          )}
        </div>
      </div>

      {/* Data insufficient warning */}
      {priceCheck?.needs_backfill && indicator.asset_id && (
        <div style={{
          background: 'rgba(239, 68, 68, 0.1)',
          border: '1px solid rgba(239, 68, 68, 0.3)',
          borderRadius: '12px',
          padding: '16px 20px',
          marginBottom: '20px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '16px',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flex: 1, minWidth: 0 }}>
            <AlertTriangle size={20} color="#ef4444" />
            <div style={{ minWidth: 0 }}>
              <div style={{ color: '#ef4444', fontSize: '14px', fontWeight: 600, marginBottom: '4px' }}>
                价格数据不足6年
              </div>
              <div style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>
                {priceCheck.gaps && priceCheck.gaps.length > 0 ? (
                  <>
                    总覆盖 {priceCheck.days_coverage} 天，但最大连续区间仅 {priceCheck.max_continuous_days} 天
                    （约 {(priceCheck.max_continuous_days / 365).toFixed(1)} 年），存在 {priceCheck.gaps.length} 处数据断档。
                    200周均线需要至少6年连续数据。
                  </>
                ) : (
                  <>
                    当前仅 {priceCheck.max_continuous_days} 天（约 {(priceCheck.max_continuous_days / 365).toFixed(1)} 年），200周均线需要至少6年数据
                  </>
                )}
              </div>
              {priceCheck.gaps && priceCheck.gaps.length > 0 && (
                <div style={{ marginTop: '6px', fontSize: '12px', color: 'var(--text-muted)' }}>
                  断档：
                  {priceCheck.gaps.slice(0, 3).map((g, i) => (
                    <span key={i} style={{ marginRight: '12px' }}>
                      {g.start_date} ~ {g.end_date}（缺 {g.days} 天）
                    </span>
                  ))}
                  {priceCheck.gaps.length > 3 && `等共 ${priceCheck.gaps.length} 处`}
                </div>
              )}
            </div>
          </div>
          <button
            onClick={() => setShowBackfillModal(true)}
            disabled={backfilling}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              padding: '8px 16px',
              borderRadius: '8px',
              border: 'none',
              background: '#ef4444',
              color: 'white',
              fontSize: '14px',
              fontWeight: 600,
              cursor: backfilling ? 'not-allowed' : 'pointer',
              opacity: backfilling ? 0.7 : 1,
              transition: 'all 0.2s',
              whiteSpace: 'nowrap',
            }}
          >
            {backfilling ? (
              <Loader2 size={16} style={{ animation: 'spin 1s linear infinite' }} />
            ) : (
              <>
                <Plus size={16} />
                补充数据
              </>
            )}
          </button>
        </div>
      )}

      {/* Stats Cards */}
      {stats && !isMA200 && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: '16px', marginBottom: '24px' }}>
          {[
            { label: '最大值', value: stats.max.toFixed(1), color: '#22c55e' },
            { label: '最小值', value: stats.min.toFixed(1), color: '#ef4444' },
            { label: '平均值', value: stats.avg, color: '#6366f1' },
            { label: '数据点数', value: `${stats.count} 天`, color: '#f59e0b' },
          ].map((stat) => (
            <div key={stat.label} style={{ background: 'var(--bg-primary)', borderRadius: '16px', padding: '16px 20px', border: '1px solid var(--border-color)' }}>
              <p style={{ fontSize: '12px', color: 'var(--text-muted)', margin: '0 0 6px 0' }}>{stat.label}</p>
              <p style={{ fontSize: '20px', fontWeight: 700, color: stat.color, margin: 0 }}>{stat.value}</p>
            </div>
          ))}
        </div>
      )}

      {/* Chart - only for non-MA200 indicators */}
      {!isMA200 && (
        <div style={{ background: 'var(--bg-primary)', borderRadius: '20px', padding: '24px', border: '1px solid var(--border-color)', marginBottom: '24px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', flexWrap: 'wrap', gap: '12px' }}>
            <h3 style={{ fontSize: '18px', fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>
              历史走势
            </h3>
            <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
              <button
                onClick={() => setIsLogScale(!isLogScale)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  padding: '8px 16px',
                  borderRadius: '10px',
                  border: '1px solid var(--border-color)',
                  background: isLogScale ? 'var(--primary-color)' : 'var(--bg-secondary)',
                  color: isLogScale ? 'white' : 'var(--text-secondary)',
                  fontSize: '13px',
                  fontWeight: 600,
                  cursor: 'pointer',
                  transition: 'all 0.2s',
                }}
              >
                {isLogScale ? '对数' : '线性'}
              </button>
              <button
                onClick={handleRecalculate}
                disabled={recalculating}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  padding: '8px 16px',
                  borderRadius: '10px',
                  border: '1px solid var(--border-color)',
                  background: 'var(--bg-secondary)',
                  color: 'var(--text-secondary)',
                  fontSize: '13px',
                  fontWeight: 600,
                  cursor: recalculating ? 'not-allowed' : 'pointer',
                  opacity: recalculating ? 0.7 : 1,
                  transition: 'all 0.2s',
                }}
              >
                {recalculating ? (
                  <Loader2 size={14} style={{ animation: 'spin 1s linear infinite' }} />
                ) : (
                  <RefreshCw size={14} />
                )}
                重新计算
              </button>
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

          <div style={{ position: 'relative', width: '100%', height: '525px' }}>
            <div ref={chartContainerRef} style={{ width: '100%', height: '100%' }} />
            {filteredValues.length === 0 && (
              <div style={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', background: 'var(--bg-primary)' }}>
                暂无历史数据
              </div>
            )}
          </div>
        </div>
      )}

      {/* Price + MA200W Chart */}
      {isMA200 && (
        <div style={{ background: 'var(--bg-primary)', borderRadius: '20px', padding: '24px', border: '1px solid var(--border-color)', marginBottom: '24px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', flexWrap: 'wrap', gap: '12px' }}>
            <h3 style={{ fontSize: '18px', fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>
              价格与200周均线
            </h3>
            <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
              <button
                onClick={() => setIsPriceLogScale(!isPriceLogScale)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  padding: '8px 16px',
                  borderRadius: '10px',
                  border: '1px solid var(--border-color)',
                  background: isPriceLogScale ? 'var(--primary-color)' : 'var(--bg-secondary)',
                  color: isPriceLogScale ? 'white' : 'var(--text-secondary)',
                  fontSize: '13px',
                  fontWeight: 600,
                  cursor: 'pointer',
                  transition: 'all 0.2s',
                }}
              >
                {isPriceLogScale ? '对数' : '线性'}
              </button>
              <button
                onClick={handleRecalculate}
                disabled={recalculating}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  padding: '8px 16px',
                  borderRadius: '10px',
                  border: '1px solid var(--border-color)',
                  background: 'var(--bg-secondary)',
                  color: 'var(--text-secondary)',
                  fontSize: '13px',
                  fontWeight: 600,
                  cursor: recalculating ? 'not-allowed' : 'pointer',
                  opacity: recalculating ? 0.7 : 1,
                  transition: 'all 0.2s',
                }}
              >
                {recalculating ? (
                  <Loader2 size={14} style={{ animation: 'spin 1s linear infinite' }} />
                ) : (
                  <RefreshCw size={14} />
                )}
                重新计算
              </button>
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
          {/* Dynamic legend based on config */}
          <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap', marginBottom: '12px', fontSize: '12px', color: 'var(--text-secondary)' }}>
            {(indicator?.config ? [
              { label: 'MA200W', color: indicator.config.colors?.[0] || '#3b82f6' },
              ...indicator.config.multipliers.slice(1).map((m, i) => ({
                label: `${m}×`,
                color: indicator.config.colors?.[i + 1] || '#64748b'
              }))
            ] : [
              { label: 'MA200W', color: '#3b82f6' },
              { label: '1.5×', color: '#22c55e' },
              { label: '2×', color: '#eab308' },
              { label: '2.5×', color: '#f97316' },
              { label: '3×', color: '#dc2626' },
            ]).map((item, i) => (
              <span key={i} style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span style={{ width: '20px', height: '3px', background: item.color, borderRadius: '2px' }} />
                {item.label}
              </span>
            ))}
            <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span style={{ width: '12px', height: '12px', background: '#22c55e', borderRadius: '2px', opacity: 0.7 }} />
              <span style={{ width: '12px', height: '12px', background: '#ef4444', borderRadius: '2px', opacity: 0.7 }} />
              K线
            </span>
          </div>
          <div style={{ position: 'relative', width: '100%', height: '525px' }}>
            <div ref={priceChartContainerRef} style={{ width: '100%', height: '100%' }} />
            {priceChartData.length === 0 && (
              <div style={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', background: 'var(--bg-primary)' }}>
                暂无价格数据
              </div>
            )}
          </div>
        </div>
      )}

      {/* Recent Values Table - hidden for MA200 */}
      {!isMA200 && (
        <div style={{ background: 'var(--bg-primary)', borderRadius: '20px', padding: '24px', border: '1px solid var(--border-color)' }}>
          <h3 style={{ fontSize: '18px', fontWeight: 700, color: 'var(--text-primary)', margin: '0 0 20px 0' }}>
            近期数据
          </h3>

          {filteredValues.length > 0 ? (
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ background: 'var(--bg-secondary)' }}>
                    <th style={{ padding: '12px 16px', textAlign: 'left', fontSize: '12px', fontWeight: 600, color: 'var(--text-secondary)' }}>日期</th>
                    <th style={{ padding: '12px 16px', textAlign: 'left', fontSize: '12px', fontWeight: 600, color: 'var(--text-secondary)' }}>数值</th>
                    <th style={{ padding: '12px 16px', textAlign: 'center', fontSize: '12px', fontWeight: 600, color: 'var(--text-secondary)' }}>档位</th>
                    <th style={{ padding: '12px 16px', textAlign: 'left', fontSize: '12px', fontWeight: 600, color: 'var(--text-secondary)' }}>说明</th>
                  </tr>
                </thead>
                <tbody>
                  {[...filteredValues].reverse().slice(0, 10).map((v, index) => {
                    const grade = v.grade ? gradeConfig[v.grade] : null;
                    const fearGreedGrade = isFearGreed ? getFearGreedGrade(v.value) : null;
                    const displayGrade = isFearGreed ? fearGreedGrade : grade;

                    return (
                      <tr key={v.id} style={{ borderBottom: index < 9 ? '1px solid var(--border-color)' : 'none' }}>
                        <td style={{ padding: '14px 16px', fontSize: '14px', color: 'var(--text-primary)' }}>{v.date}</td>
                        <td style={{ padding: '14px 16px', fontSize: '15px', fontWeight: 600, color: 'var(--text-primary)' }}>{v.value.toFixed(2)}</td>
                        <td style={{ padding: '14px 16px', textAlign: 'center' }}>
                          {displayGrade ? (
                            <span style={{ fontSize: '12px', fontWeight: 600, padding: '4px 10px', borderRadius: '20px', background: `${displayGrade.color}20`, color: displayGrade.color }}>
                              {displayGrade.label}
                            </span>
                          ) : '-'}
                        </td>
                        <td style={{ padding: '14px 16px', fontSize: '14px', color: 'var(--text-secondary)' }}>{v.value_text || '-'}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          ) : (
            <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>暂无数据</div>
          )}
        </div>
      )}

      {/* Backfill Modal */}
      {showBackfillModal && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          background: 'rgba(0, 0, 0, 0.5)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          zIndex: 1000,
        }}>
          <div style={{
            background: 'var(--bg-primary)', borderRadius: '16px', padding: '24px',
            width: '100%', maxWidth: '400px', margin: '20px',
            border: '1px solid var(--border-color)',
          }}>
            <h3 style={{ fontSize: '18px', fontWeight: 700, color: 'var(--text-primary)', margin: '0 0 20px 0' }}>
              增补历史价格数据
            </h3>
            <p style={{ fontSize: '13px', color: 'var(--text-muted)', marginBottom: '16px' }}>
              将拉取 {indicator.asset_id} 从 {backfillStart} 到 {backfillEnd} 的价格数据，用于计算200周均线。
            </p>

            <div style={{ marginBottom: '16px' }}>
              <label style={{ display: 'block', fontSize: '14px', color: 'var(--text-secondary)', marginBottom: '8px' }}>开始日期</label>
              <input
                type="date"
                value={backfillStart}
                onChange={(e) => setBackfillStart(e.target.value)}
                style={{
                  width: '100%', padding: '10px 12px', borderRadius: '8px',
                  border: '1px solid var(--border-color)', background: 'var(--bg-secondary)',
                  color: 'var(--text-primary)', fontSize: '14px',
                }}
              />
            </div>

            <div style={{ marginBottom: '24px' }}>
              <label style={{ display: 'block', fontSize: '14px', color: 'var(--text-secondary)', marginBottom: '8px' }}>结束日期</label>
              <input
                type="date"
                value={backfillEnd}
                onChange={(e) => setBackfillEnd(e.target.value)}
                style={{
                  width: '100%', padding: '10px 12px', borderRadius: '8px',
                  border: '1px solid var(--border-color)', background: 'var(--bg-secondary)',
                  color: 'var(--text-primary)', fontSize: '14px',
                }}
              />
            </div>

            <div style={{ display: 'flex', gap: '12px' }}>
              <button
                onClick={() => setShowBackfillModal(false)}
                style={{
                  flex: 1, padding: '10px', borderRadius: '8px',
                  border: '1px solid var(--border-color)', background: 'var(--bg-secondary)',
                  color: 'var(--text-secondary)', fontSize: '14px', fontWeight: 600, cursor: 'pointer',
                }}
              >
                取消
              </button>
              <button
                onClick={handleBackfillPrices}
                disabled={backfilling || !backfillStart || !backfillEnd}
                style={{
                  flex: 1, padding: '10px', borderRadius: '8px',
                  border: 'none', background: 'var(--primary-color)', color: 'white',
                  fontSize: '14px', fontWeight: 600,
                  cursor: backfilling || !backfillStart || !backfillEnd ? 'not-allowed' : 'pointer',
                  opacity: backfilling || !backfillStart || !backfillEnd ? 0.7 : 1,
                }}
              >
                {backfilling ? '处理中...' : '确认增补'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
