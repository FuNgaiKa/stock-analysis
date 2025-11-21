"""
因子合成模块

提供多因子模型的合成方法:
1. Schmidt正交化: 消除因子间相关性
2. 等权合成: 稳健的因子加权方法

Author: Claude (Quantitative Research Analyst)
Date: 2025-11-21
Version: 1.0

References:
- 天风金工. "因子正交全攻略 —— 理论、框架与实践"
- Grinold & Kahn (1999). "Active Portfolio Management"
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class FactorSynthesizer:
    """
    因子合成器

    实现机构级多因子合成方法:
    - Schmidt正交化: 消除因子相关性,避免重复计分
    - 等权合成: 业界验证的稳健方法

    Examples:
        >>> synthesizer = FactorSynthesizer()
        >>> factors = {
        ...     '历史点位': 93.8,
        ...     '技术面': 75.0,
        ...     '估值面': 50.0,
        ...     '资金面': 50.0,
        ...     '成交量': 50.0,
        ...     '市场情绪': 50.0
        ... }
        >>> priority = ['估值面', '历史点位', '技术面', '资金面', '成交量', '市场情绪']
        >>> factors_orth, score = synthesizer.synthesize(factors, priority)
        >>> print(f"正交化后总分: {score:.1f}")
    """

    def __init__(self):
        """初始化因子合成器"""
        self.logger = logging.getLogger(self.__class__.__name__)

    def schmidt_orthogonalization(
        self,
        factors: Dict[str, float],
        priority_order: List[str],
        normalize: bool = True
    ) -> Tuple[Dict[str, float], Dict[str, float]]:
        """
        Schmidt正交化

        消除因子间的相关性,避免重复计分。

        原理:
        1. 按优先级顺序处理因子
        2. 第一个因子保持不变
        3. 后续因子去掉与前面所有因子的相关部分
        4. 结果:所有因子两两正交(相关性=0)

        Args:
            factors: 原始因子字典 {'因子名': 分值}
            priority_order: 因子优先级顺序(重要性从高到低)
                建议顺序: ['估值面', '历史点位', '技术面', '资金面', '成交量', '市场情绪']
                理由:
                - 估值面: 基本面之本,长期有效
                - 历史点位: 统计规律,季节性强
                - 技术面: 趋势确认,中频信号
                - 资金面: 驱动力(与技术部分重复)
                - 成交量: 量能验证(与资金/技术重复)
                - 市场情绪: 短期扰动(与多因子相关)
            normalize: 是否归一化到0-100范围

        Returns:
            (factors_orth, factors_raw_ordered):
                - factors_orth: 正交化后的因子字典
                - factors_raw_ordered: 按优先级排序的原始因子字典

        Note:
            - 先序因子保持原样,后序因子被修改更多
            - 如果因子间相关性高,后序因子值会显著降低
            - 这正是正交化的目的:去除重复信息
        """
        if not factors:
            self.logger.warning("输入因子为空")
            return {}, {}

        # 按优先级提取因子
        factor_names = []
        factor_values = []

        for name in priority_order:
            if name in factors:
                factor_names.append(name)
                factor_values.append(factors[name])

        if len(factor_names) == 0:
            self.logger.warning("没有匹配的因子")
            return {}, {}

        # 转为numpy数组
        vectors = np.array(factor_values, dtype=float)

        # Schmidt正交化
        orth_vectors = np.zeros_like(vectors)

        for i in range(len(vectors)):
            # 从原始向量开始
            orth_vec = vectors[i]

            # 减去与前面所有正交向量的投影
            for j in range(i):
                if np.linalg.norm(orth_vectors[j]) > 1e-10:
                    # projection = <v, u_j> / <u_j, u_j> * u_j
                    projection_coef = np.dot(vectors[i], orth_vectors[j]) / np.dot(orth_vectors[j], orth_vectors[j])
                    orth_vec = orth_vec - projection_coef * orth_vectors[j]

            orth_vectors[i] = orth_vec

        # 归一化(可选)
        if normalize:
            # 将正交化后的向量映射回0-100范围
            # 使用min-max归一化,保持相对关系
            min_val = orth_vectors.min()
            max_val = orth_vectors.max()

            if max_val - min_val > 1e-10:
                orth_vectors = 50 + (orth_vectors - min_val) / (max_val - min_val) * 50
                # 映射到[0, 100],中心点50
            else:
                # 所有值相同,保持50
                orth_vectors = np.full_like(orth_vectors, 50.0)

        # 转回字典
        factors_orth = dict(zip(factor_names, orth_vectors))
        factors_raw_ordered = dict(zip(factor_names, factor_values))

        # 记录正交化信息
        self.logger.info("Schmidt正交化完成:")
        for name in factor_names:
            raw = factors_raw_ordered[name]
            orth = factors_orth[name]
            delta = orth - raw
            self.logger.info(f"  {name}: {raw:.1f} → {orth:.1f} (Δ{delta:+.1f})")

        return factors_orth, factors_raw_ordered

    def equal_weight_synthesis(
        self,
        factors: Dict[str, float]
    ) -> float:
        """
        等权合成

        对所有因子赋予相同权重,简单平均。

        优点:
        - 简单稳健,不依赖参数估计
        - 避免过拟合
        - 业界实证:很多情况下不输复杂方法

        Args:
            factors: 因子字典 {'因子名': 分值}

        Returns:
            加权后的总分(0-100)

        References:
            雪球量化社区实测: "试了IC/ICIR加权,最后都不如等权"
        """
        if not factors:
            self.logger.warning("输入因子为空,返回中性分50")
            return 50.0

        values = list(factors.values())
        score = np.mean(values)

        self.logger.info(f"等权合成: {len(factors)}个因子 → 总分{score:.1f}")

        return float(score)

    def synthesize(
        self,
        factors: Dict[str, float],
        priority_order: List[str],
        method: str = 'equal_weight',
        normalize: bool = True
    ) -> Tuple[Dict[str, float], float]:
        """
        统一因子合成接口

        完整流程:
        1. Schmidt正交化: 消除因子相关性
        2. 等权合成: 稳健加权

        Args:
            factors: 原始因子字典
            priority_order: 因子优先级顺序
            method: 合成方法,当前仅支持'equal_weight'
            normalize: 是否归一化

        Returns:
            (factors_orth, final_score):
                - factors_orth: 正交化后的因子字典
                - final_score: 最终综合得分(0-100)

        Example:
            >>> synthesizer = FactorSynthesizer()
            >>> factors = {'估值面': 50, '技术面': 75, '资金面': 70}
            >>> priority = ['估值面', '技术面', '资金面']
            >>> factors_orth, score = synthesizer.synthesize(factors, priority)
        """
        # 第一步: 正交化
        factors_orth, factors_raw = self.schmidt_orthogonalization(
            factors,
            priority_order,
            normalize=normalize
        )

        # 第二步: 合成
        if method == 'equal_weight':
            final_score = self.equal_weight_synthesis(factors_orth)
        else:
            raise ValueError(f"不支持的合成方法: {method}")

        return factors_orth, final_score

    def calculate_factor_correlation(
        self,
        factors_dict: Dict[str, List[float]]
    ) -> Dict[Tuple[str, str], float]:
        """
        计算因子间的相关性矩阵

        用于诊断哪些因子高度相关,需要正交化。

        Args:
            factors_dict: 因子历史序列 {'因子名': [值1, 值2, ...]}

        Returns:
            相关性字典 {('因子A', '因子B'): 相关系数}

        Example:
            >>> correlations = synthesizer.calculate_factor_correlation({
            ...     '技术面': [75, 80, 70, 85],
            ...     '资金面': [70, 78, 68, 82]
            ... })
            >>> print(correlations[('技术面', '资金面')])  # 预期高相关
        """
        factor_names = list(factors_dict.keys())
        correlations = {}

        for i, name1 in enumerate(factor_names):
            for j, name2 in enumerate(factor_names):
                if i < j:  # 只计算上三角
                    series1 = np.array(factors_dict[name1])
                    series2 = np.array(factors_dict[name2])

                    if len(series1) == len(series2) and len(series1) > 1:
                        corr = np.corrcoef(series1, series2)[0, 1]
                        correlations[(name1, name2)] = corr
                    else:
                        self.logger.warning(f"因子{name1}和{name2}序列长度不匹配")

        return correlations


# 默认因子优先级配置
DEFAULT_FACTOR_PRIORITY = [
    '估值面',      # 1. 基本面核心(长期有效)
    '历史点位',    # 2. 统计规律(季节性强)
    '技术面',      # 3. 趋势确认(中频信号)
    '资金面',      # 4. 驱动力(与技术部分重复)
    '成交量',      # 5. 量能验证(与资金/技术重复)
    '市场情绪'     # 6. 短期扰动(与多因子相关)
]


def synthesize_factors(
    factors: Dict[str, float],
    priority_order: Optional[List[str]] = None
) -> Tuple[Dict[str, float], float]:
    """
    便捷函数: 因子合成

    使用默认配置进行因子正交化和合成。

    Args:
        factors: 原始因子字典
        priority_order: 因子优先级,默认使用DEFAULT_FACTOR_PRIORITY

    Returns:
        (factors_orth, score): 正交化因子和最终得分

    Example:
        >>> from russ_trading.core.factor_synthesis import synthesize_factors
        >>> factors = {'历史点位': 93.8, '技术面': 75, '估值面': 50}
        >>> factors_orth, score = synthesize_factors(factors)
    """
    if priority_order is None:
        priority_order = DEFAULT_FACTOR_PRIORITY

    synthesizer = FactorSynthesizer()
    return synthesizer.synthesize(factors, priority_order)


if __name__ == '__main__':
    # 测试代码
    logging.basicConfig(level=logging.INFO)

    # 测试案例: 纳斯达克因子
    factors = {
        '历史点位': 93.8,
        '技术面': 75.0,
        '估值面': 50.0,
        '成交量': 50.0,
        '资金面': 50.0,
        '市场情绪': 50.0
    }

    print("=" * 60)
    print("测试: Schmidt正交化 + 等权合成")
    print("=" * 60)

    synthesizer = FactorSynthesizer()
    factors_orth, score = synthesizer.synthesize(
        factors,
        DEFAULT_FACTOR_PRIORITY
    )

    print("\n原始因子:")
    for name in DEFAULT_FACTOR_PRIORITY:
        if name in factors:
            print(f"  {name}: {factors[name]:.1f}")

    print("\n正交化后因子:")
    for name, value in factors_orth.items():
        print(f"  {name}: {value:.1f}")

    print(f"\n最终得分: {score:.1f}")

    # 测试相关性计算
    print("\n" + "=" * 60)
    print("测试: 因子相关性分析")
    print("=" * 60)

    # 模拟历史数据(假设技术面和资金面高度相关)
    factors_history = {
        '技术面': [75, 80, 70, 85, 78],
        '资金面': [70, 78, 68, 82, 76],  # 与技术面相似
        '估值面': [50, 50, 50, 50, 50]   # 稳定
    }

    correlations = synthesizer.calculate_factor_correlation(factors_history)

    print("\n因子相关性矩阵:")
    for (name1, name2), corr in sorted(correlations.items()):
        print(f"  {name1} <-> {name2}: {corr:.3f}")
