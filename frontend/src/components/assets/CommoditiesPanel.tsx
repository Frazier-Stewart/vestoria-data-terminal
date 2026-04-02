import { Search, Gem, TrendingUp } from 'lucide-react';
import { useState } from 'react';

export default function CommoditiesPanel() {
  const [searchQuery, setSearchQuery] = useState('');

  return (
    <div>
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
            placeholder="搜索大宗商品 (如: GOLD, OIL)..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
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
          disabled
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '12px 24px',
            borderRadius: '12px',
            border: 'none',
            background: 'var(--bg-tertiary)',
            color: 'var(--text-muted)',
            fontSize: '14px',
            fontWeight: 600,
            cursor: 'not-allowed',
          }}
        >
          <TrendingUp size={18} />
          搜索
        </button>
      </div>

      {/* 占位提示 */}
      <div
        style={{
          padding: '80px',
          textAlign: 'center',
          background: 'var(--bg-secondary)',
          borderRadius: '16px',
          border: '1px dashed var(--border-color)',
        }}
      >
        <Gem size={48} color="var(--text-muted)" style={{ marginBottom: '16px', opacity: 0.5 }} />
        <p style={{ color: 'var(--text-muted)', fontSize: '16px', marginBottom: '8px' }}>
          大宗商品搜索功能开发中
        </p>
        <p style={{ color: 'var(--text-secondary)', fontSize: '14px' }}>
          Phase 3: 接入黄金、白银、原油等期货数据
        </p>
      </div>
    </div>
  );
}
