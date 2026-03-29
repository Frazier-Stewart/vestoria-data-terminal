import { useParams, Link } from 'react-router-dom';
import { useEffect, useState, useMemo, useCallback } from 'react';
import axios from 'axios';
import { createChart, AreaSeries, ColorType } from 'lightweight-charts';
import { ArrowLeft, Activity, AlertCircle, TrendingUp, Gauge, Database } from 'lucide-react';
import dayjs from 'dayjs';

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

const typeConfig: Record<string, { label: string; color: string; bg: string; icon: React.ElementType }> = {
  fear_greed: { label: '恐慌贪婪', color: '#8b5cf6', bg: 'rgba(139, 92, 246, 0.1)', icon: AlertCircle },
  vix: { label: 'VIX', color: '#f59e0b', bg: 'rgba(245, 158, 11, 0.1)', icon: Gauge },
  ma200: { label: 'MA200', color: '#3b82f6', bg: 'rgba(59, 130, 246, 0.1)', icon: TrendingUp },
  pe: { label: '市盈率', color: '#22c55e', bg: 'rgba(34, 197, 94, 0.1)', icon: Activity },
  metric: { label: '技术指标', color: '#6366f1', bg: 'rgba(99, 102, 241, 0.1)', icon: Database },
  sentiment: { label: '情绪指标', color: '#ec4899', bg: 'rgba(236, 72, 153, 0.1)', icon: Activity },
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

export default function IndicatorDetail() {
  const { id } = useParams<{ id: string }>();
  const [indicator, setIndicator] = useState<Indicator | null>(null);
  const [values, setValues] = useState<IndicatorValue[]>([]);
  const [loading, setLoading] = useState(true);
  const [chartContainer, setChartContainer] = useState<HTMLDivElement | null>(null);

  const chartContainerRef = useCallback((node: HTMLDivElement | null) => {
    setChartContainer(node);
  }, []);

  useEffect(() => {
    if (id) {
      fetchIndicator(parseInt(id));
      fetchValues(parseInt(id));
    }
  }, [id]);

  const fetchIndicator = async (indicatorId: number) => {
    try {
      const response = await axios.get(`/api/v1/indicators/${indicatorId}`);
      setIndicator(response.data);
    } catch (error) {
      console.error('Failed to fetch indicator:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchValues = async (indicatorId: number) => {
    try {
      const response = await axios.get(`/api/v1/indicators/${indicatorId}/values?limit=500`);
      const sorted = response.data.sort((a: IndicatorValue, b: IndicatorValue) =>
        new Date(a.date).getTime() - new Date(b.date).getTime()
      );
      setValues(sorted);
    } catch (error) {
      console.error('Failed to fetch values:', error);
    }
  };

  const isFearGreed = indicator?.template?.indicator_type === 'fear_greed' || indicator?.template?.id === 'BTC_FEAR_GREED';

  const indicatorColor = useMemo(() => {
    if (!indicator) return '#6366f1';
    const config = typeConfig[indicator.indicator_type] || typeConfig['metric'];
    return config.color;
  }, [indicator]);

  // Single effect: create chart + set data
  useEffect(() => {
    if (!chartContainer || values.length === 0) return;

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
      height: 350,
      crosshair: {
        vertLine: { color: colors.crosshairColor, width: 1, style: 3, labelBackgroundColor: '#6366f1' },
        horzLine: { color: colors.crosshairColor, width: 1, style: 3, labelBackgroundColor: '#6366f1' },
      },
      rightPriceScale: {
        borderColor: colors.borderColor,
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

    const chartData = values.map(v => ({
      time: v.date as string,
      value: v.value,
    }));

    series.setData(chartData);

    // Reference lines for Fear & Greed
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
  }, [chartContainer, values, indicatorColor, isFearGreed]);

  const stats = useMemo(() => {
    if (values.length === 0) return null;
    const latest = values[values.length - 1];
    const allValues = values.map(v => v.value);
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
      count: values.length,
    };
  }, [values]);

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

  const config = typeConfig[indicator.indicator_type] || typeConfig['metric'];
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

        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
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

          {stats && (
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

      {/* Stats Cards */}
      {stats && (
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

      {/* Chart */}
      <div style={{ background: 'var(--bg-primary)', borderRadius: '20px', padding: '24px', border: '1px solid var(--border-color)', marginBottom: '24px' }}>
        <h3 style={{ fontSize: '18px', fontWeight: 700, color: 'var(--text-primary)', margin: '0 0 20px 0' }}>
          历史走势
        </h3>

        <div style={{ position: 'relative', width: '100%', height: '350px' }}>
          <div ref={chartContainerRef} style={{ width: '100%', height: '100%' }} />
          {values.length === 0 && (
            <div style={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', background: 'var(--bg-primary)' }}>
              暂无历史数据
            </div>
          )}
        </div>
      </div>

      {/* Recent Values Table */}
      <div style={{ background: 'var(--bg-primary)', borderRadius: '20px', padding: '24px', border: '1px solid var(--border-color)' }}>
        <h3 style={{ fontSize: '18px', fontWeight: 700, color: 'var(--text-primary)', margin: '0 0 20px 0' }}>
          近期数据
        </h3>

        {values.length > 0 ? (
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
                {[...values].reverse().slice(0, 10).map((v, index) => {
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
    </div>
  );
}
