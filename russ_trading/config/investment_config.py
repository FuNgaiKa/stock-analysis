"""
投资目标配置加载器
Investment Goals Configuration Loader

从 config/investment_goals.yaml 加载投资目标配置
支持环境变量和配置文件的灵活切换
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class InvestmentGoalsConfig:
    """投资目标配置类"""

    def __init__(self, config_path: Optional[str] = None):
        """
        初始化配置

        Args:
            config_path: 配置文件路径，默认为 config/investment_goals.yaml
        """
        if config_path is None:
            # 默认配置路径
            project_root = Path(__file__).parent.parent
            config_path = project_root / "config" / "investment_goals.yaml"

        self.config_path = Path(config_path)
        self._config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        if not self.config_path.exists():
            logger.warning(f"配置文件不存在: {self.config_path}")
            logger.warning("使用默认配置值，建议创建 config/investment_goals.yaml")
            return self._get_default_config()

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            logger.info(f"✅ 已加载投资目标配置: {self.config_path}")
            return config
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            logger.warning("使用默认配置值")
            return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置（示例值）"""
        return {
            'initial_capital': 500000,
            'current_capital': None,
            'stage_targets': [500000, 750000, 1000000],
            'final_target': 1000000,
            'target_annual_return': 0.60,
            'target_total_return': 1.0,
            'base_date': '2025-01-01',
            'hs300_base': 3145.0,
            'cybz_base': 2060.0,
            'kechuang50_base': 955.0,
            'show_absolute_amounts': False,
            'show_target_amounts': False,
            'stage_names': ['初始阶段', '中期目标', '最终目标']
        }

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置项"""
        return self._config.get(key, default)

    @property
    def initial_capital(self) -> float:
        """初始资金"""
        return float(self.get('initial_capital', 500000))

    @property
    def current_capital(self) -> Optional[float]:
        """当前资金（可为None）"""
        val = self.get('current_capital')
        return float(val) if val is not None else None

    @property
    def stage_targets(self) -> list:
        """阶段性目标列表"""
        return self.get('stage_targets', [500000, 750000, 1000000])

    @property
    def final_target(self) -> float:
        """最终目标"""
        return float(self.get('final_target', 1000000))

    @property
    def target_annual_return(self) -> float:
        """目标年化收益率"""
        return float(self.get('target_annual_return', 0.15))

    @property
    def target_total_return(self) -> float:
        """目标总收益率（翻倍=1.0）"""
        return float(self.get('target_total_return', 1.0))

    @property
    def base_date(self) -> str:
        """基准日期"""
        return self.get('base_date', '2025-01-01')

    @property
    def hs300_base(self) -> float:
        """沪深300基准点位"""
        return float(self.get('hs300_base', 3145.0))

    @property
    def cybz_base(self) -> float:
        """创业板指基准点位"""
        return float(self.get('cybz_base', 2060.0))

    @property
    def kechuang50_base(self) -> float:
        """科创50基准点位"""
        return float(self.get('kechuang50_base', 955.0))

    @property
    def show_absolute_amounts(self) -> bool:
        """是否在报告中显示具体金额"""
        return bool(self.get('show_absolute_amounts', False))

    @property
    def show_target_amounts(self) -> bool:
        """是否在报告中显示目标金额"""
        return bool(self.get('show_target_amounts', False))

    @property
    def stage_names(self) -> list:
        """阶段目标名称"""
        return self.get('stage_names', ['初始阶段', '中期目标', '最终目标'])

    def format_amount(self, amount: float) -> str:
        """
        格式化金额显示

        如果 show_absolute_amounts = False，则返回模糊描述
        否则返回具体金额
        """
        if self.show_absolute_amounts:
            if amount >= 10000:
                return f"¥{amount/10000:.1f}万"
            else:
                return f"¥{amount:.0f}"
        else:
            # 返回相对描述
            if amount == self.initial_capital:
                return "初始资金"
            elif amount == self.final_target:
                return "最终目标"
            else:
                # 计算进度百分比
                progress = (amount - self.initial_capital) / (self.final_target - self.initial_capital) * 100
                return f"目标进度{progress:.0f}%"

    def format_target_description(self, target_amount: float, stage_index: int = None) -> str:
        """
        格式化目标描述

        Args:
            target_amount: 目标金额
            stage_index: 阶段索引（0,1,2...）

        Returns:
            目标描述字符串
        """
        if self.show_target_amounts:
            return f"¥{target_amount/10000:.0f}万"
        else:
            if stage_index is not None and stage_index < len(self.stage_names):
                return self.stage_names[stage_index]
            else:
                return "下一阶段目标"


# 全局配置实例（单例模式）
_global_config = None


def get_investment_config(config_path: Optional[str] = None, reload: bool = False) -> InvestmentGoalsConfig:
    """
    获取全局投资目标配置实例

    Args:
        config_path: 配置文件路径
        reload: 是否重新加载配置

    Returns:
        InvestmentGoalsConfig 实例
    """
    global _global_config

    if _global_config is None or reload:
        _global_config = InvestmentGoalsConfig(config_path)

    return _global_config


if __name__ == '__main__':
    # 测试配置加载
    logging.basicConfig(level=logging.INFO)

    config = get_investment_config()

    print("="*60)
    print("投资目标配置测试")
    print("="*60)
    print(f"初始资金: {config.initial_capital}")
    print(f"阶段目标: {config.stage_targets}")
    print(f"最终目标: {config.final_target}")
    print(f"目标年化收益: {config.target_annual_return*100}%")
    print(f"基准日期: {config.base_date}")
    print(f"沪深300基准: {config.hs300_base}")
    print(f"显示具体金额: {config.show_absolute_amounts}")
    print(f"显示目标金额: {config.show_target_amounts}")
    print()
    print("金额格式化测试:")
    print(f"  初始资金: {config.format_amount(config.initial_capital)}")
    print(f"  当前进度: {config.format_amount(515000)}")
    print(f"  最终目标: {config.format_amount(config.final_target)}")
    print()
    print("目标描述测试:")
    for i, target in enumerate(config.stage_targets):
        print(f"  阶段{i+1}: {config.format_target_description(target, i)}")
    print("="*60)
