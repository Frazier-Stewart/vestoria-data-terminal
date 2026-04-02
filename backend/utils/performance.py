"""
性能指标计算
"""

import numpy as np
from typing import Dict, Tuple, Optional
from dataclasses import dataclass


@dataclass
class PerformanceMetrics:
    """性能指标数据类"""
    initial_capital: float
    final_value: float
    total_return: float
    cagr: float
    volatility: float
    max_drawdown: float
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    years: float

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'initial_capital': self.initial_capital,
            'final_value': self.final_value,
            'total_return': self.total_return,
            'cagr': self.cagr,
            'volatility': self.volatility,
            'max_drawdown': self.max_drawdown,
            'sharpe_ratio': self.sharpe_ratio,
            'sortino_ratio': self.sortino_ratio,
            'calmar_ratio': self.calmar_ratio,
            'years': self.years
        }


def calculate_performance(
    values: np.ndarray,
    dates: np.ndarray,
    initial_capital: float = 100000.0,
    risk_free_rate: float = 0.02
) -> PerformanceMetrics:
    """
    计算投资组合性能指标

    Args:
        values: 组合价值数组
        dates: 日期数组（numpy datetime64 或 Timestamp）
        initial_capital: 初始资金
        risk_free_rate: 无风险利率（年化）

    Returns:
        PerformanceMetrics 实例
    """
    if len(values) == 0:
        raise ValueError("values 不能为空")

    # 计算年数
    n_years = (dates[-1] - dates[0]).days / 365.25

    # 总收益率
    total_return = (values[-1] / values[0]) - 1

    # 年化收益率 (CAGR)
    cagr = (values[-1] / values[0]) ** (1 / n_years) - 1 if n_years > 0 else 0

    # 日收益率
    daily_returns = np.diff(values) / values[:-1]

    # 年化波动率
    volatility = np.std(daily_returns) * np.sqrt(252) if len(daily_returns) > 1 else 0

    # 最大回撤
    cummax = np.maximum.accumulate(values)
    drawdown = (values - cummax) / cummax
    max_drawdown = np.min(drawdown)

    # 夏普比率
    excess_returns = daily_returns - risk_free_rate / 252
    sharpe_ratio = (np.mean(excess_returns) / np.std(daily_returns) * np.sqrt(252)
                    if np.std(daily_returns) > 0 else 0)

    # 索提诺比率（下行风险调整收益）
    downside_returns = daily_returns[daily_returns < 0]
    downside_deviation = np.std(downside_returns) * np.sqrt(252) if len(downside_returns) > 1 else 0
    sortino_ratio = (cagr - risk_free_rate) / downside_deviation if downside_deviation > 0 else 0

    # 卡玛比率（年化收益 / 最大回撤）
    calmar_ratio = abs(cagr / max_drawdown) if max_drawdown != 0 else 0

    return PerformanceMetrics(
        initial_capital=initial_capital,
        final_value=float(values[-1]),
        total_return=float(total_return),
        cagr=float(cagr),
        volatility=float(volatility),
        max_drawdown=float(max_drawdown),
        sharpe_ratio=float(sharpe_ratio),
        sortino_ratio=float(sortino_ratio),
        calmar_ratio=float(calmar_ratio),
        years=float(n_years)
    )


def compare_performance(
    strategy_metrics: PerformanceMetrics,
    baseline_metrics: PerformanceMetrics
) -> Dict:
    """
    对比两个策略的性能指标

    Args:
        strategy_metrics: 策略性能指标
        baseline_metrics: 基准性能指标

    Returns:
        性能对比字典
    """
    return {
        'total_return_diff': strategy_metrics.total_return - baseline_metrics.total_return,
        'cagr_diff': strategy_metrics.cagr - baseline_metrics.cagr,
        'volatility_diff': strategy_metrics.volatility - baseline_metrics.volatility,
        'max_drawdown_diff': strategy_metrics.max_drawdown - baseline_metrics.max_drawdown,
        'sharpe_ratio_diff': strategy_metrics.sharpe_ratio - baseline_metrics.sharpe_ratio,
        'final_value_diff': strategy_metrics.final_value - baseline_metrics.final_value
    }


def format_performance(metrics: PerformanceMetrics) -> str:
    """
    格式化性能指标为可读字符串

    Args:
        metrics: 性能指标

    Returns:
        格式化的字符串
    """
    lines = [
        f"初始资金: ${metrics.initial_capital:,.0f}",
        f"期末价值: ${metrics.final_value:,.0f}",
        f"总收益率: {metrics.total_return*100:.1f}%",
        f"年化收益: {metrics.cagr*100:.1f}%",
        f"年化波动: {metrics.volatility*100:.1f}%",
        f"最大回撤: {metrics.max_drawdown*100:.1f}%",
        f"夏普比率: {metrics.sharpe_ratio:.2f}",
        f"索提诺比率: {metrics.sortino_ratio:.2f}",
        f"卡玛比率: {metrics.calmar_ratio:.2f}",
    ]
    return '\n'.join(lines)


def format_comparison(metrics1: PerformanceMetrics, metrics2: PerformanceMetrics,
                     label1: str = 'Strategy', label2: str = 'Baseline') -> str:
    """
    格式化性能对比表格

    Args:
        metrics1: 策略1性能
        metrics2: 策略2性能
        label1: 策略1标签
        label2: 策略2标签

    Returns:
        格式化的对比字符串
    """
    comparison = compare_performance(metrics1, metrics2)

    lines = [
        f"{'指标':<15} {label1:>15} {label2:>15} {'差异':>15}",
        "-" * 60,
        f"{'期末价值':<15} ${metrics1.final_value:,.0f}  ${metrics2.final_value:,.0f}  ${comparison['final_value_diff']:>10,.0f}",
        f"{'总收益率':<15} {metrics1.total_return*100:>14.1f}% {metrics2.total_return*100:>14.1f}% {comparison['total_return_diff']*100:>13.1f}%",
        f"{'年化收益':<15} {metrics1.cagr*100:>14.1f}% {metrics2.cagr*100:>14.1f}% {comparison['cagr_diff']*100:>13.1f}%",
        f"{'年化波动':<15} {metrics1.volatility*100:>14.1f}% {metrics2.volatility*100:>14.1f}% {comparison['volatility_diff']*100:>13.1f}%",
        f"{'最大回撤':<15} {metrics1.max_drawdown*100:>14.1f}% {metrics2.max_drawdown*100:>14.1f}% {comparison['max_drawdown_diff']*100:>13.1f}%",
        f"{'夏普比率':<15} {metrics1.sharpe_ratio:>14.2f} {metrics2.sharpe_ratio:>14.2f} {comparison['sharpe_ratio_diff']:>13.2f}",
    ]

    return '\n'.join(lines)
