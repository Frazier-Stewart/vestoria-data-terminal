"""
可视化工具
"""

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from pathlib import Path


# 设置 matplotlib 支持英文标签（避免中文显示问题）
plt.rcParams['font.family'] = ['sans-serif']
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial']
plt.rcParams['axes.unicode_minus'] = False


def plot_net_value(
    strategy_values: np.ndarray,
    dates: pd.DatetimeIndex,
    baseline_values: Optional[np.ndarray] = None,
    asset_values: Optional[Dict[str, np.ndarray]] = None,
    rebalance_dates: Optional[List[pd.Timestamp]] = None,
    title: str = 'Portfolio Net Value',
    figsize: tuple = (14, 7),
    save_path: Optional[str] = None
) -> plt.Figure:
    """
    绘制净值曲线

    Args:
        strategy_values: 策略净值数组
        dates: 日期数组
        baseline_values: 基准净值数组（可选，兼容旧接口）
        asset_values: 各资产净值字典 {'BTC': array, 'GOLD': array, ...}
        rebalance_dates: 再平衡日期列表（可选）
        title: 图表标题
        figsize: 图表大小
        save_path: 保存路径（可选）

    Returns:
        matplotlib Figure 对象
    """
    fig, ax = plt.subplots(figsize=figsize)

    # 绘制策略曲线
    ax.plot(dates, strategy_values, label='Strategy', linewidth=2.5, alpha=0.9, color='blue')

    # 绘制各资产曲线
    if asset_values:
        # 绘制各资产净值（归一化到初始值100，然后按策略初始资金缩放）
        initial_strategy = strategy_values[0]
        for asset, values in asset_values.items():
            if values is not None and len(values) > 0:
                # 归一化到策略的初始值
                normalized = values / values[0] * initial_strategy
                ax.plot(dates, normalized, label=f'{asset} (Single)', linewidth=1.5, alpha=0.7, linestyle='--')

    # 绘制基准曲线（兼容旧接口）
    if baseline_values is not None and not asset_values:
        ax.plot(dates, baseline_values, label='Baseline (SPY)', linewidth=2, alpha=0.6, linestyle='--')

    # 绘制再平衡标记
    if rebalance_dates:
        for rebalance_date in rebalance_dates[::4]:  # 每隔4个显示一次，避免太密集
            ax.axvline(x=rebalance_date, color='gray', linestyle='--', alpha=0.3)

    ax.set_title(title, fontsize=13, fontweight='bold')
    ax.set_xlabel('Date')
    ax.set_ylabel('Portfolio Value ($)')
    ax.legend(loc='upper left', ncol=2)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"✓ Saved: {save_path}")

    return fig


def plot_allocation_heatmap(
    allocations: List[Dict[str, float]],
    dates: pd.DatetimeIndex,
    title: str = 'Asset Allocation Over Time',
    figsize: tuple = (12, 6),
    save_path: Optional[str] = None
) -> plt.Figure:
    """
    绘制资产配置热力图（按年份）

    Args:
        allocations: 资产配置列表（每个元素是 {资产: 价值} 的字典）
        dates: 日期数组
        title: 图表标题
        figsize: 图表大小
        save_path: 保存路径（可选）

    Returns:
        matplotlib Figure 对象
    """
    # 按年份汇总配置
    yearly_allocations = {}
    for i, alloc in enumerate(allocations):
        year = dates[i].year
        if year not in yearly_allocations:
            yearly_allocations[year] = {}
        for asset, value in alloc.items():
            if value > 0:
                yearly_allocations[year][asset] = yearly_allocations[year].get(asset, 0) + value

    # 转换为 DataFrame
    df = pd.DataFrame.from_dict(yearly_allocations, orient='index')
    df = df.div(df.sum(axis=1), axis=0)  # 转换为百分比

    fig, ax = plt.subplots(figsize=figsize)

    # 绘制热力图
    im = ax.imshow(df.values, cmap='YlOrRd', aspect='auto')

    # 设置坐标轴
    ax.set_xticks(range(len(df.columns)))
    ax.set_yticks(range(len(df.index)))
    ax.set_xticklabels(df.columns, rotation=45)
    ax.set_yticklabels(df.index)

    # 添加数值标签
    for i in range(len(df.index)):
        for j in range(len(df.columns)):
            text = ax.text(j, i, f'{df.values[i, j]*100:.0f}%',
                          ha="center", va="center", color="black" if df.values[i, j] < 0.5 else "white")

    ax.set_title(title, fontsize=12, fontweight='bold')
    fig.colorbar(im, ax=ax, label='Allocation %')

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"✓ Saved: {save_path}")

    return fig


def plot_drawdown(
    values: np.ndarray,
    dates: pd.DatetimeIndex,
    title: str = 'Drawdown Analysis',
    figsize: tuple = (12, 4),
    save_path: Optional[str] = None
) -> plt.Figure:
    """
    绘制回撤分析图

    Args:
        values: 净值数组
        dates: 日期数组
        title: 图表标题
        figsize: 图表大小
        save_path: 保存路径（可选）

    Returns:
        matplotlib Figure 对象
    """
    # 计算回撤
    cummax = np.maximum.accumulate(values)
    drawdown = (values - cummax) / cummax

    fig, ax = plt.subplots(figsize=figsize)

    # 绘制填充回撤
    ax.fill_between(dates, drawdown * 100, 0, alpha=0.3, color='red', label='Drawdown')
    ax.plot(dates, drawdown * 100, color='red', linewidth=1)

    ax.set_title(title, fontsize=12, fontweight='bold')
    ax.set_xlabel('Date')
    ax.set_ylabel('Drawdown (%)')
    ax.legend(loc='upper left')
    ax.grid(True, alpha=0.3)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"✓ Saved: {save_path}")

    return fig


def plot_return_distribution(
    returns: np.ndarray,
    title: str = 'Daily Return Distribution',
    figsize: tuple = (12, 4),
    save_path: Optional[str] = None
) -> plt.Figure:
    """
    绘制日收益率分布直方图

    Args:
        returns: 日收益率数组
        title: 图表标题
        figsize: 图表大小
        save_path: 保存路径（可选）

    Returns:
        matplotlib Figure 对象
    """
    fig, ax = plt.subplots(figsize=figsize)

    # 绘制直方图
    ax.hist(returns * 100, bins=50, alpha=0.7, edgecolor='black')
    ax.axvline(x=np.mean(returns) * 100, color='green', linestyle='--',
               label=f'Mean: {np.mean(returns)*100:.3f}%')

    ax.set_title(title, fontsize=12, fontweight='bold')
    ax.set_xlabel('Daily Return (%)')
    ax.set_ylabel('Frequency')
    ax.legend(loc='upper right')
    ax.grid(True, alpha=0.3, axis='y')

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"✓ Saved: {save_path}")

    return fig


def plot_asset_net_value(
    asset_values: Dict[str, np.ndarray],
    dates: pd.DatetimeIndex,
    title: str = 'Individual Asset Net Value',
    figsize: tuple = (12, 6),
    save_path: Optional[str] = None
) -> plt.Figure:
    """
    绘制各资产单独净值曲线（归一化到初始值100）

    Args:
        asset_values: 各资产净值字典 {资产名: 净值数组}
        dates: 日期数组
        title: 图表标题
        figsize: 图表大小
        save_path: 保存路径（可选）

    Returns:
        matplotlib Figure 对象
    """
    fig, ax = plt.subplots(figsize=figsize)

    # 归一化到初始值100
    for asset, values in asset_values.items():
        normalized = values / values[0] * 100
        ax.plot(dates, normalized, label=asset, linewidth=2, alpha=0.8)

    ax.set_title(title, fontsize=12, fontweight='bold')
    ax.set_xlabel('Date')
    ax.set_ylabel('Net Value (Initial=100)')
    ax.legend(loc='upper left')
    ax.grid(True, alpha=0.3)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"✓ Saved: {save_path}")

    return fig


def plot_all_charts(
    strategy_values: np.ndarray,
    dates: pd.DatetimeIndex,
    allocations: List[Dict[str, float]],
    baseline_values: Optional[np.ndarray] = None,
    rebalance_dates: Optional[List[pd.Timestamp]] = None,
    title: str = 'Portfolio Backtest Analysis',
    save_path: Optional[str] = None
) -> plt.Figure:
    """
    绘制4合1综合分析图表

    Args:
        strategy_values: 策略净值数组
        dates: 日期数组
        allocations: 资产配置列表
        baseline_values: 基准净值数组（可选）
        rebalance_dates: 再平衡日期列表（可选）
        title: 图表标题
        save_path: 保存路径（可选）

    Returns:
        matplotlib Figure 对象
    """
    fig, axes = plt.subplots(2, 2, figsize=(16, 10))
    fig.suptitle(title, fontsize=14, fontweight='bold')

    # 1. 净值曲线对比
    ax1 = axes[0, 0]
    ax1.plot(dates, strategy_values, label='Strategy', linewidth=2, alpha=0.8)
    if baseline_values is not None:
        ax1.plot(dates, baseline_values, label='Baseline (SPY)', linewidth=2, alpha=0.6, linestyle='--')
    if rebalance_dates:
        for rebalance_date in rebalance_dates[::4]:
            ax1.axvline(x=rebalance_date, color='gray', linestyle='--', alpha=0.3)
    ax1.set_title('Net Value Comparison', fontsize=11, fontweight='bold')
    ax1.set_xlabel('Date')
    ax1.set_ylabel('Value ($)')
    ax1.legend(loc='upper left')
    ax1.grid(True, alpha=0.3)

    # 2. 资产配置热力图
    ax2 = axes[0, 1]
    yearly_allocations = {}
    for i, alloc in enumerate(allocations):
        year = dates[i].year
        if year not in yearly_allocations:
            yearly_allocations[year] = {}
        for asset, value in alloc.items():
            if value > 0:
                yearly_allocations[year][asset] = yearly_allocations[year].get(asset, 0) + value
    df = pd.DataFrame.from_dict(yearly_allocations, orient='index')
    df = df.div(df.sum(axis=1), axis=0)
    im = ax2.imshow(df.values, cmap='YlOrRd', aspect='auto')
    ax2.set_xticks(range(len(df.columns)))
    ax2.set_yticks(range(len(df.index)))
    ax2.set_xticklabels(df.columns, rotation=45)
    ax2.set_yticklabels(df.index)
    ax2.set_title('Asset Allocation (Yearly)', fontsize=11, fontweight='bold')
    fig.colorbar(im, ax=ax2, label='Allocation %')

    # 3. 日收益率分布
    ax3 = axes[1, 0]
    returns = np.diff(strategy_values) / strategy_values[:-1]
    ax3.hist(returns * 100, bins=50, alpha=0.7, edgecolor='black')
    ax3.axvline(x=np.mean(returns) * 100, color='green', linestyle='--',
               label=f'Mean: {np.mean(returns)*100:.3f}%')
    ax3.set_title('Daily Return Distribution', fontsize=11, fontweight='bold')
    ax3.set_xlabel('Daily Return (%)')
    ax3.set_ylabel('Frequency')
    ax3.legend(loc='upper right')
    ax3.grid(True, alpha=0.3, axis='y')

    # 4. 回撤分析
    ax4 = axes[1, 1]
    cummax = np.maximum.accumulate(strategy_values)
    drawdown = (strategy_values - cummax) / cummax
    ax4.fill_between(dates, drawdown * 100, 0, alpha=0.3, color='red', label='Drawdown')
    ax4.plot(dates, drawdown * 100, color='red', linewidth=1)
    ax4.set_title('Drawdown Analysis', fontsize=11, fontweight='bold')
    ax4.set_xlabel('Date')
    ax4.set_ylabel('Drawdown (%)')
    ax4.legend(loc='upper left')
    ax4.grid(True, alpha=0.3)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"✓ Saved: {save_path}")

    return fig
