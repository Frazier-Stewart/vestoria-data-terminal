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
      {/* Category Tabs */}
      <div style={{ marginBottom: '32px' }}>
        <CategoryTabs 
          activeCategory={activeCategory} 
          onChange={setActiveCategory} 
        />
      </div>

      {/* Panel Content */}
      {activeCategory === 'equities' && <EquitiesPanel />}
      {activeCategory === 'crypto' && <CryptoPanel />}
      {activeCategory === 'commodities' && <CommoditiesPanel />}
    </div>
  );
}
