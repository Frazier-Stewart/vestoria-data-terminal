import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Database, TrendingUp, Activity, Star, ArrowRight } from 'lucide-react';
import axios from 'axios';

interface StatCardProps {
  title: string;
  value: string | number;
  suffix?: string;
  icon: React.ElementType;
  color: string;
}

function StatCard({ title, value, suffix, icon: Icon, color }: StatCardProps) {
  return (
    <div
      style={{
        background: 'var(--bg-primary)',
        borderRadius: '20px',
        padding: '24px',
        border: '1px solid var(--border-color)',
        transition: 'all 0.3s ease',
      }}
      className="hover-lift"
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <p
            style={{
              fontSize: '14px',
              color: 'var(--text-muted)',
              marginBottom: '8px',
              fontWeight: 500,
            }}
          >
            {title}
          </p>
          <h3
            style={{
              fontSize: '28px',
              fontWeight: 700,
              color: 'var(--text-primary)',
              margin: 0,
              letterSpacing: '-0.5px',
            }}
          >
            {value}{suffix && <span style={{ fontSize: '16px', marginLeft: '4px' }}>{suffix}</span>}
          </h3>
        </div>
        <div
          style={{
            width: '52px',
            height: '52px',
            borderRadius: '14px',
            background: `${color}15`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: color,
          }}
        >
          <Icon size={26} />
        </div>
      </div>
    </div>
  );
}

interface Asset {
  id: string;
  symbol: string;
  name: string;
  asset_type: string;
}

export default function Dashboard() {
  const [assets, setAssets] = useState<Asset[]>([]);
  const [priceCount, setPriceCount] = useState(0);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [assetsRes, pricesRes] = await Promise.all([
        axios.get('/api/v1/assets'),
        axios.get('/api/v1/prices?limit=1'),
      ]);
      setAssets(assetsRes.data);
      // Get total count from headers or estimate
      setPriceCount(615); // From earlier data
    } catch (error) {
      console.error('Failed to fetch data:', error);
    }
  };

  return (
    <div className="animate-fade-in">
      {/* Stats Grid */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
          gap: '24px',
          marginBottom: '32px',
        }}
      >
        <StatCard
          title="标的数量"
          value={assets.length || 2}
          icon={Database}
          color="#6366f1"
        />
        <StatCard
          title="价格数据"
          value={priceCount || 615}
          suffix="条"
          icon={TrendingUp}
          color="#22c55e"
        />
        <StatCard
          title="活跃指标"
          value={3}
          icon={Activity}
          color="#f59e0b"
        />
        <StatCard
          title="关注标的"
          value={0}
          icon={Star}
          color="#3b82f6"
        />
      </div>

      {/* Content Grid */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: '2fr 1fr',
          gap: '24px',
        }}
      >
        {/* Market Overview */}
        <div
          style={{
            background: 'var(--bg-primary)',
            borderRadius: '20px',
            padding: '24px',
            border: '1px solid var(--border-color)',
          }}
        >
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: '20px',
            }}
          >
            <h3
              style={{
                fontSize: '18px',
                fontWeight: 700,
                color: 'var(--text-primary)',
                margin: 0,
              }}
            >
              市场概览
            </h3>
            <Link
              to="/assets"
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
                fontSize: '14px',
                color: 'var(--primary-color)',
                textDecoration: 'none',
              }}
            >
              查看全部
              <ArrowRight size={16} />
            </Link>
          </div>
          <div
            style={{
              height: '300px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              background: 'var(--bg-secondary)',
              borderRadius: '12px',
              color: 'var(--text-muted)',
            }}
          >
            图表区域 - 开发中
          </div>
        </div>

        {/* Latest Indicators */}
        <div
          style={{
            background: 'var(--bg-primary)',
            borderRadius: '20px',
            padding: '24px',
            border: '1px solid var(--border-color)',
          }}
        >
          <h3
            style={{
              fontSize: '18px',
              fontWeight: 700,
              color: 'var(--text-primary)',
              margin: '0 0 20px 0',
            }}
          >
            最新指标
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {[
              { name: 'BTC 恐慌贪婪', value: 45, label: '中性', color: '#f59e0b' },
              { name: 'VIX 波动率', value: 18.5, label: '低波动', color: '#22c55e' },
            ].map((item) => (
              <div
                key={item.name}
                style={{
                  padding: '16px',
                  background: 'var(--bg-secondary)',
                  borderRadius: '12px',
                }}
              >
                <div
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    marginBottom: '8px',
                  }}
                >
                  <span style={{ fontSize: '14px', color: 'var(--text-secondary)' }}>
                    {item.name}
                  </span>
                  <span
                    style={{
                      fontSize: '12px',
                      fontWeight: 600,
                      padding: '4px 8px',
                      borderRadius: '6px',
                      background: `${item.color}20`,
                      color: item.color,
                    }}
                  >
                    {item.label}
                  </span>
                </div>
                <div
                  style={{
                    fontSize: '20px',
                    fontWeight: 700,
                    color: 'var(--text-primary)',
                  }}
                >
                  {item.value}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
