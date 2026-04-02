"""
配置管理
"""

import json
import hashlib
from typing import Dict


class PortfolioConfig:
    """投资组合配置类"""

    # 默认权重
    DEFAULT_WEIGHTS = {
        'BTC': 0.10,
        'GOLD': 0.30,
        'SPY': 0.40,
        'CASH': 0.20
    }

    # 资产代码映射
    ASSET_TICKERS = {
        'BTC': 'BTC-USD',
        'GOLD': 'GLD',
        'SPY': 'SPY',
        'HS300': '000300.SS',  # 沪深300指数
        'CASH': 'CASH'  # 现金，价格永远是 100
    }

    def __init__(self, weights: Dict[str, float] = None, rebalance_freq: str = 'quarterly'):
        """
        初始化配置

        Args:
            weights: 资产权重字典，如 {'BTC': 0.10, 'GOLD': 0.30, ...}
            rebalance_freq: 再平衡频率，'quarterly' | 'monthly' | 'weekly' | 'daily'
        """
        if weights is None:
            weights = self.DEFAULT_WEIGHTS.copy()

        # 验证权重
        total = sum(weights.values())
        if not (0.99 <= total <= 1.01):  # 允许 1% 的误差
            raise ValueError(f"权重总和必须为 1.0，当前为 {total:.3f}")

        # 验证再平衡频率
        valid_freqs = ['quarterly', 'monthly', 'weekly', 'daily']
        if rebalance_freq not in valid_freqs:
            raise ValueError(f"无效的再平衡频率: {rebalance_freq}，必须是 {valid_freqs}")

        self.weights = weights
        self.rebalance_freq = rebalance_freq

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'weights': self.weights,
            'rebalance_freq': self.rebalance_freq
        }

    def to_json(self, indent: int = 2) -> str:
        """转换为 JSON 字符串"""
        return json.dumps(self.to_dict(), indent=indent)

    @staticmethod
    def from_dict(d: Dict) -> 'PortfolioConfig':
        """从字典创建配置"""
        return PortfolioConfig(
            weights=d['weights'],
            rebalance_freq=d.get('rebalance_freq', 'quarterly')
        )

    @staticmethod
    def from_json(json_str: str) -> 'PortfolioConfig':
        """从 JSON 字符串创建配置"""
        return PortfolioConfig.from_dict(json.loads(json_str))

    @staticmethod
    def from_file(file_path: str) -> 'PortfolioConfig':
        """从 JSON 文件读取配置"""
        with open(file_path, 'r') as f:
            return PortfolioConfig.from_dict(json.load(f))

    def to_file(self, file_path: str):
        """保存配置到 JSON 文件"""
        with open(file_path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)

    @staticmethod
    def from_string(s: str) -> 'PortfolioConfig':
        """
        从字符串解析配置，如 "btc10_gold30_spy40_tlt20"

        Args:
            s: 配置字符串

        Returns:
            PortfolioConfig 实例
        """
        if s == 'default':
            return PortfolioConfig()

        parts = s.split('_')
        weights = {}

        for part in parts:
            # 提取资产名和权重
            asset = None
            weight = None

            # 尝试匹配每个资产
            for asset_name in PortfolioConfig.ASSET_TICKERS.keys():
                asset_lower = asset_name.lower()
                if part.startswith(asset_lower):
                    try:
                        weight = float(part[len(asset_lower):]) / 100
                        asset = asset_name
                        break
                    except ValueError:
                        continue

            if asset and weight is not None:
                weights[asset] = weight

        if not weights:
            raise ValueError(f"无法解析配置字符串: {s}")

        return PortfolioConfig(weights=weights)

    def to_string(self) -> str:
        """
        生成配置字符串，如 "btc10_gold30_spy40_tlt20"

        Returns:
            配置字符串
        """
        parts = []
        for asset, weight in sorted(self.weights.items()):
            parts.append(f"{asset.lower()}{int(weight * 100)}")
        return '_'.join(parts)

    def get_hash(self) -> str:
        """
        生成配置哈希（用于回测记录命名）

        Returns:
            配置字符串
        """
        return self.to_string()

    def __repr__(self):
        return f"PortfolioConfig(weights={self.weights}, rebalance_freq='{self.rebalance_freq}')"

    def __eq__(self, other):
        if not isinstance(other, PortfolioConfig):
            return False
        return (self.weights == other.weights and
                self.rebalance_freq == other.rebalance_freq)


# 创建默认配置实例
DEFAULT_CONFIG = PortfolioConfig()
