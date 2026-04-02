import { useState } from 'react';
import { AssetCategory } from '@/types/assets';
import CategoryTabs from '@/components/assets/CategoryTabs';
import EquitiesPanel from '@/components/assets/EquitiesPanel';
import CryptoPanel from '@/components/assets/CryptoPanel';
import CommoditiesPanel from '@/components/assets/CommoditiesPanel';

export default function Assets() {
  const [activeCategory, setActiveCategory] = useState<AssetCategory>('equities');

  return (
    <div className="animate-fade-in">
      {/* Header */}
      <div style={{ marginBottom: '32px' }}>
        <h1
          style={{
            fontSize: '32px',
            fontWeight: 700,
            color: 'var(--text-primary)',
            margin: '0 0 8px 0',
            letterSpacing: '-0.5px',
          }}
        >
          标的列表
        </h1>
        <p style={{ fontSize: '15px', color: 'var(--text-muted)', margin: 0 }}>
          搜索并添加各类资产到追踪列表
        </p>
      </div>

      {/* Category Tabs */}
      <CategoryTabs 
        activeCategory={activeCategory} 
        onChange={setActiveCategory} 
      />

      {/* Panel Content */}
      {activeCategory === 'equities' && <EquitiesPanel />}
      {activeCategory === 'crypto' && <CryptoPanel />}
      {activeCategory === 'commodities' && <CommoditiesPanel />}
    </div>
  );
}
