import { ReactNode } from 'react';

// 资产类别
export type AssetCategory = 'equities' | 'crypto' | 'commodities';

// GICS 板块
export type GicsSector =
  | 'Technology'
  | 'Financials'
  | 'Health Care'
  | 'Consumer Discretionary'
  | 'Communication Services'
  | 'Industrials'
  | 'Consumer Staples'
  | 'Energy'
  | 'Utilities'
  | 'Real Estate'
  | 'Materials';

// 排序选项
export type EquitiesSortBy = 'market_cap' | 'trailing_pe' | 'name' | 'ticker';

// Yahoo Finance 搜索参数
export interface YFinanceSearchParams {
  query?: string;
  sector?: GicsSector;
  industry?: string;
  sortBy: EquitiesSortBy;
  sortOrder: 'asc' | 'desc';
  limit?: number;
}

// Yahoo Finance 搜索结果
export interface YFinanceSearchResult {
  symbol: string;
  name: string;
  sector?: GicsSector;
  industry?: string;
  marketCap?: number;
  trailingPE?: number;
  price?: number;
  currency?: string;
  exchange?: string;
}

// Tab 配置
export interface CategoryTab {
  key: AssetCategory;
  label: string;
  icon?: ReactNode;
}

// GICS Sector 配置
export interface SectorConfig {
  key: GicsSector;
  label: string;
  labelZh: string;
  color: string;
  bg: string;
}

// Sector 配置列表
export const SECTOR_CONFIG: SectorConfig[] = [
  { key: 'Technology', label: 'Technology', labelZh: '信息技术', color: '#6366f1', bg: 'rgba(99, 102, 241, 0.1)' },
  { key: 'Financials', label: 'Financials', labelZh: '金融', color: '#22c55e', bg: 'rgba(34, 197, 94, 0.1)' },
  { key: 'Health Care', label: 'Health Care', labelZh: '医疗保健', color: '#ef4444', bg: 'rgba(239, 68, 68, 0.1)' },
  { key: 'Consumer Discretionary', label: 'Consumer Discretionary', labelZh: '可选消费', color: '#f59e0b', bg: 'rgba(245, 158, 11, 0.1)' },
  { key: 'Communication Services', label: 'Communication Services', labelZh: '通信服务', color: '#8b5cf6', bg: 'rgba(139, 92, 246, 0.1)' },
  { key: 'Industrials', label: 'Industrials', labelZh: '工业', color: '#3b82f6', bg: 'rgba(59, 130, 246, 0.1)' },
  { key: 'Consumer Staples', label: 'Consumer Staples', labelZh: '必需消费', color: '#14b8a6', bg: 'rgba(20, 184, 166, 0.1)' },
  { key: 'Energy', label: 'Energy', labelZh: '能源', color: '#f97316', bg: 'rgba(249, 115, 22, 0.1)' },
  { key: 'Utilities', label: 'Utilities', labelZh: '公用事业', color: '#06b6d4', bg: 'rgba(6, 182, 212, 0.1)' },
  { key: 'Real Estate', label: 'Real Estate', labelZh: '房地产', color: '#ec4899', bg: 'rgba(236, 72, 153, 0.1)' },
  { key: 'Materials', label: 'Materials', labelZh: '原材料', color: '#84cc16', bg: 'rgba(132, 204, 22, 0.1)' },
];

// 排序选项配置
export const SORT_OPTIONS = [
  { key: 'market_cap', label: '市值', labelZh: '市值' },
  { key: 'trailing_pe', label: '市盈率 (PE)', labelZh: '市盈率' },
  { key: 'name', label: '名称', labelZh: '名称' },
  { key: 'ticker', label: '代码', labelZh: '代码' },
] as const;
