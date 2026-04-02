import { AssetCategory, CategoryTab } from '@/types/assets';
import { TrendingUp, Bitcoin, Gem } from 'lucide-react';
import { ReactNode } from 'react';

interface CategoryTabsProps {
  activeCategory: AssetCategory;
  onChange: (category: AssetCategory) => void;
}

const tabs: { key: AssetCategory; label: string; icon: ReactNode }[] = [
  { key: 'equities', label: '股票', icon: <TrendingUp size={18} /> },
  { key: 'crypto', label: '加密货币', icon: <Bitcoin size={18} /> },
  { key: 'commodities', label: '大宗商品', icon: <Gem size={18} /> },
];

export default function CategoryTabs({ activeCategory, onChange }: CategoryTabsProps) {
  return (
    <div
      style={{
        display: 'flex',
        gap: '12px',
        marginBottom: '24px',
        borderBottom: '1px solid var(--border-color)',
        paddingBottom: '16px',
      }}
    >
      {tabs.map((tab) => (
        <button
          key={tab.key}
          onClick={() => onChange(tab.key)}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '12px 24px',
            borderRadius: '12px',
            border: 'none',
            background: activeCategory === tab.key 
              ? 'var(--primary-color)' 
              : 'var(--bg-secondary)',
            color: activeCategory === tab.key 
              ? 'white' 
              : 'var(--text-secondary)',
            fontSize: '14px',
            fontWeight: 600,
            cursor: 'pointer',
            transition: 'all 0.2s ease',
            boxShadow: activeCategory === tab.key 
              ? '0 4px 14px rgba(99, 102, 241, 0.4)' 
              : 'none',
          }}
          onMouseEnter={(e) => {
            if (activeCategory !== tab.key) {
              e.currentTarget.style.background = 'var(--bg-tertiary)';
            }
          }}
          onMouseLeave={(e) => {
            if (activeCategory !== tab.key) {
              e.currentTarget.style.background = 'var(--bg-secondary)';
            }
          }}
        >
          {tab.icon}
          {tab.label}
        </button>
      ))}
    </div>
  );
}
