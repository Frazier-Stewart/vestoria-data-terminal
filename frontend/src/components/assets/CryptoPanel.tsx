import { Search, Bitcoin, Loader2 } from 'lucide-react';
import { useState } from 'react';

export default function CryptoPanel() {
  const [searchQuery, setSearchQuery] = useState('');
  const [activeSource, setActiveSource] = useState<'binance' | 'onchain'>('binance');

  return (
    <div>
      {/* 数据源选择 */}
      <div
        style={{
          display: 'flex',
          gap: '8px',
          marginBottom: '20px',
        }}
      >
        <button
          onClick={() => setActiveSource('binance')}
          style={{
            padding: '10px 20px',
            borderRadius: '10px',
            border: 'none',
            background: activeSource === 'binance' ? '#f0b90b' : 'var(--bg-secondary)',
            color: activeSource === 'binance' ? 'white' : 'var(--text-secondary)',
            fontSize: '14px',
            fontWeight: 600,
            cursor: 'pointer',
          }}
        >
          Binance
        </button>
        <button
          onClick={() => setActiveSource('onchain')}
          style={{
            padding: '10px 20px',
            borderRadius: '10px',
            border: 'none',
            background: activeSource === 'onchain' ? '#627eea' : 'var(--bg-secondary)',
            color: activeSource === 'onchain' ? 'white' : 'var(--text-secondary)',
            fontSize: '14px',
            fontWeight: 600,
            cursor: 'pointer',
          }}
        >
          链上资产
        </button>
      </div>

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
            placeholder={activeSource === 'binance' ? '搜索币种 (如: BTC, ETH)...' : '输入合约地址...'}
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
          <Bitcoin size={18} />
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
        <Bitcoin size={48} color="var(--text-muted)" style={{ marginBottom: '16px', opacity: 0.5 }} />
        <p style={{ color: 'var(--text-muted)', fontSize: '16px', marginBottom: '8px' }}>
          加密货币搜索功能开发中
        </p>
        <p style={{ color: 'var(--text-secondary)', fontSize: '14px' }}>
          Phase 2: 接入 Binance API & On-chain 数据
        </p>
      </div>
    </div>
  );
}
