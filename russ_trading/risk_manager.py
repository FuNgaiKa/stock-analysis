#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
风险管理模块

机构级风险管理工具,包含:
1. 最大回撤计算 (Max Drawdown)
2. 波动率分析 (Volatility)
3. 夏普比率 (Sharpe Ratio)
4. VaR风险价值 (Value at Risk)
5. 贝塔系数 (Beta)
6. 相关性分析 (Correlation)
7. 止损检查 (Stop Loss)
8. 索提诺比率 (Sortino Ratio)
9. 卡玛比率 (Calmar Ratio)
10. 信息比率 (Information Ratio)
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from scipy import stats


class RiskManager:
    """风险管理器 - 机构级风险控制"""

    def __init__(self, risk_free_rate: float = 0.03):
        """
        初始化风险管理器

        Args:
            risk_free_rate: 无风险利率,默认3%(国债收益率)
        """
        self.risk_free_rate = risk_free_rate

    # ==================== 核心风险指标 ====================

    def calculate_max_drawdown(self, equity_curve: List[float]) -> Dict:
        """
        计算最大回撤 (Max Drawdown) - 最重要的风险指标

        最大回撤 = (谷底价值 - 峰值价值) / 峰值价值

        Args:
            equity_curve: 净值曲线 (资金曲线)

        Returns:
            包含最大回撤、峰值点、谷底点、回撤持续时间等信息
        """
        if not equity_curve or len(equity_curve) < 2:
            return {
                'max_drawdown': 0.0,
                'max_drawdown_pct': '0.00%',
                'peak_value': 0,
                'trough_value': 0,
                'peak_date': None,
                'trough_date': None,
                'duration_days': 0,
                'current_drawdown': 0.0,
                'current_drawdown_pct': '0.00%'
            }

        equity = np.array(equity_curve)

        # 计算累积最大值
        cummax = np.maximum.accumulate(equity)

        # 计算回撤序列
        drawdown = (equity - cummax) / cummax

        # 最大回撤
        max_dd = np.min(drawdown)
        max_dd_idx = np.argmin(drawdown)

        # 找到峰值点(回撤开始点)
        peak_idx = np.argmax(cummax[:max_dd_idx+1])
        peak_value = equity[peak_idx]
        trough_value = equity[max_dd_idx]

        # 回撤持续时间
        duration = max_dd_idx - peak_idx

        # 当前回撤
        current_dd = drawdown[-1]

        return {
            'max_drawdown': max_dd,
            'max_drawdown_pct': f"{max_dd * 100:.2f}%",
            'peak_value': peak_value,
            'trough_value': trough_value,
            'peak_date': peak_idx,
            'trough_date': max_dd_idx,
            'duration_days': duration,
            'current_drawdown': current_dd,
            'current_drawdown_pct': f"{current_dd * 100:.2f}%",
            'drawdown_series': drawdown.tolist()  # 完整回撤序列
        }

    def calculate_volatility(self, returns: List[float], annualize: bool = True) -> Dict:
        """
        计算波动率 (Volatility)

        波动率 = 收益率的标准差
        年化波动率 = 标准差 × sqrt(252)  # 252个交易日

        Args:
            returns: 收益率序列
            annualize: 是否年化

        Returns:
            包含波动率、下行波动率等
        """
        if not returns or len(returns) < 2:
            return {
                'volatility': 0.0,
                'volatility_pct': '0.00%',
                'downside_volatility': 0.0,
                'downside_volatility_pct': '0.00%'
            }

        returns_arr = np.array(returns)

        # 标准波动率
        vol = np.std(returns_arr, ddof=1)

        # 下行波动率(只考虑负收益)
        downside_returns = returns_arr[returns_arr < 0]
        downside_vol = np.std(downside_returns, ddof=1) if len(downside_returns) > 0 else 0

        # 年化
        if annualize:
            vol = vol * np.sqrt(252)
            downside_vol = downside_vol * np.sqrt(252)

        return {
            'volatility': vol,
            'volatility_pct': f"{vol * 100:.2f}%",
            'downside_volatility': downside_vol,
            'downside_volatility_pct': f"{downside_vol * 100:.2f}%"
        }

    def calculate_sharpe_ratio(
        self,
        returns: List[float],
        risk_free_rate: Optional[float] = None
    ) -> Dict:
        """
        计算夏普比率 (Sharpe Ratio) - 风险调整后收益的黄金指标

        Sharpe Ratio = (平均收益 - 无风险收益) / 收益标准差

        夏普比率解读:
        - > 3: 极优
        - > 2: 优秀
        - > 1: 良好
        - > 0.5: 一般
        - < 0.5: 较差
        - < 0: 负期望

        Args:
            returns: 日收益率序列
            risk_free_rate: 无风险利率(年化),不提供则使用初始化值

        Returns:
            夏普比率相关指标
        """
        if not returns or len(returns) < 2:
            return {
                'sharpe_ratio': 0.0,
                'evaluation': '数据不足',
                'excess_return': 0.0,
                'excess_return_pct': '0.00%'
            }

        returns_arr = np.array(returns)

        # 年化收益率
        annual_return = np.mean(returns_arr) * 252

        # 年化波动率
        annual_vol = np.std(returns_arr, ddof=1) * np.sqrt(252)

        # 无风险利率
        rf = risk_free_rate if risk_free_rate is not None else self.risk_free_rate

        # 超额收益
        excess_return = annual_return - rf

        # 夏普比率
        sharpe = excess_return / annual_vol if annual_vol > 0 else 0

        # 评级
        if sharpe > 3:
            evaluation = '极优秀'
        elif sharpe > 2:
            evaluation = '优秀'
        elif sharpe > 1:
            evaluation = '良好'
        elif sharpe > 0.5:
            evaluation = '一般'
        elif sharpe > 0:
            evaluation = '较差'
        else:
            evaluation = '负期望'

        return {
            'sharpe_ratio': sharpe,
            'evaluation': evaluation,
            'excess_return': excess_return,
            'excess_return_pct': f"{excess_return * 100:.2f}%",
            'annual_return': annual_return,
            'annual_volatility': annual_vol
        }

    def calculate_sortino_ratio(
        self,
        returns: List[float],
        target_return: float = 0.0
    ) -> Dict:
        """
        计算索提诺比率 (Sortino Ratio) - 改进版夏普比率

        只考虑下行波动率,更合理
        Sortino Ratio = (平均收益 - 目标收益) / 下行标准差

        Args:
            returns: 日收益率序列
            target_return: 目标收益率,默认0(保本)

        Returns:
            索提诺比率相关指标
        """
        if not returns or len(returns) < 2:
            return {
                'sortino_ratio': 0.0,
                'evaluation': '数据不足'
            }

        returns_arr = np.array(returns)

        # 年化收益率
        annual_return = np.mean(returns_arr) * 252

        # 下行标准差
        downside_returns = returns_arr[returns_arr < target_return]
        downside_std = np.std(downside_returns, ddof=1) * np.sqrt(252) if len(downside_returns) > 0 else 0

        # 索提诺比率
        sortino = (annual_return - target_return) / downside_std if downside_std > 0 else 0

        # 评级
        if sortino > 3:
            evaluation = '极优秀'
        elif sortino > 2:
            evaluation = '优秀'
        elif sortino > 1:
            evaluation = '良好'
        else:
            evaluation = '一般'

        return {
            'sortino_ratio': sortino,
            'evaluation': evaluation,
            'downside_std': downside_std
        }

    def calculate_calmar_ratio(
        self,
        annual_return: float,
        max_drawdown: float
    ) -> Dict:
        """
        计算卡玛比率 (Calmar Ratio)

        Calmar = 年化收益率 / |最大回撤|
        衡量回撤风险下的收益能力

        Args:
            annual_return: 年化收益率
            max_drawdown: 最大回撤(负数)

        Returns:
            卡玛比率相关指标
        """
        if max_drawdown >= 0:
            return {
                'calmar_ratio': 0.0,
                'evaluation': '无回撤或数据异常'
            }

        calmar = annual_return / abs(max_drawdown)

        # 评级
        if calmar > 5:
            evaluation = '极优秀'
        elif calmar > 3:
            evaluation = '优秀'
        elif calmar > 1:
            evaluation = '良好'
        else:
            evaluation = '一般'

        return {
            'calmar_ratio': calmar,
            'evaluation': evaluation
        }

    def calculate_var(
        self,
        returns: List[float],
        confidence: float = 0.95,
        method: str = 'historical'
    ) -> Dict:
        """
        计算VaR (Value at Risk) 风险价值

        VaR: 在给定置信度下,未来一定时期内的最大可能损失
        例如: 95%置信度下,日VaR = -2%,表示有95%的概率日亏损不超过2%

        Args:
            returns: 收益率序列
            confidence: 置信度,默认95%
            method: 计算方法 ('historical'历史法, 'parametric'参数法)

        Returns:
            VaR相关指标
        """
        if not returns or len(returns) < 2:
            return {
                'var': 0.0,
                'var_pct': '0.00%',
                'cvar': 0.0,
                'cvar_pct': '0.00%',
                'confidence': confidence
            }

        returns_arr = np.array(returns)

        if method == 'historical':
            # 历史模拟法
            var = np.percentile(returns_arr, (1 - confidence) * 100)
        else:
            # 参数法(假设正态分布)
            mean = np.mean(returns_arr)
            std = np.std(returns_arr, ddof=1)
            var = mean + std * stats.norm.ppf(1 - confidence)

        # CVaR (条件VaR / 期望损失)
        # 超过VaR的平均损失
        tail_losses = returns_arr[returns_arr < var]
        cvar = np.mean(tail_losses) if len(tail_losses) > 0 else var

        return {
            'var': var,
            'var_pct': f"{var * 100:.2f}%",
            'cvar': cvar,
            'cvar_pct': f"{cvar * 100:.2f}%",
            'confidence': confidence,
            'method': method
        }

    # ==================== 市场风险指标 ====================

    def calculate_beta(
        self,
        portfolio_returns: List[float],
        market_returns: List[float]
    ) -> Dict:
        """
        计算贝塔系数 (Beta) - 系统性风险

        Beta = Cov(组合, 市场) / Var(市场)

        Beta解读:
        - Beta = 1: 与市场同步
        - Beta > 1: 波动大于市场(高风险高收益)
        - Beta < 1: 波动小于市场(低风险低收益)
        - Beta < 0: 与市场反向(对冲工具)

        Args:
            portfolio_returns: 组合收益率
            market_returns: 市场收益率(如沪深300)

        Returns:
            贝塔系数及相关指标
        """
        if len(portfolio_returns) != len(market_returns) or len(portfolio_returns) < 2:
            return {
                'beta': 1.0,
                'alpha': 0.0,
                'r_squared': 0.0,
                'interpretation': '数据不足'
            }

        port_arr = np.array(portfolio_returns)
        mkt_arr = np.array(market_returns)

        # 计算贝塔
        covariance = np.cov(port_arr, mkt_arr)[0][1]
        market_variance = np.var(mkt_arr, ddof=1)

        beta = covariance / market_variance if market_variance > 0 else 1.0

        # 计算阿尔法(截距)
        alpha = np.mean(port_arr) - beta * np.mean(mkt_arr)

        # 计算R²(拟合优度)
        correlation = np.corrcoef(port_arr, mkt_arr)[0][1]
        r_squared = correlation ** 2

        # 解读
        if beta > 1.5:
            interpretation = '高贝塔(激进型),市场涨1%组合涨{:.2f}%'.format(beta)
        elif beta > 1:
            interpretation = '高于市场波动,偏进取'
        elif beta > 0.5:
            interpretation = '低于市场波动,偏防守'
        elif beta > 0:
            interpretation = '低贝塔(防守型)'
        else:
            interpretation = '负贝塔(对冲工具)'

        return {
            'beta': beta,
            'alpha': alpha,
            'alpha_pct': f"{alpha * 100:.2f}%",
            'r_squared': r_squared,
            'correlation': correlation,
            'interpretation': interpretation
        }

    def calculate_information_ratio(
        self,
        portfolio_returns: List[float],
        benchmark_returns: List[float]
    ) -> Dict:
        """
        计算信息比率 (Information Ratio) - 主动管理能力

        IR = (组合收益 - 基准收益) / 追踪误差

        衡量单位追踪误差下的超额收益

        Args:
            portfolio_returns: 组合收益率
            benchmark_returns: 基准收益率

        Returns:
            信息比率相关指标
        """
        if len(portfolio_returns) != len(benchmark_returns) or len(portfolio_returns) < 2:
            return {
                'information_ratio': 0.0,
                'tracking_error': 0.0,
                'evaluation': '数据不足'
            }

        port_arr = np.array(portfolio_returns)
        bench_arr = np.array(benchmark_returns)

        # 超额收益
        excess_returns = port_arr - bench_arr

        # 年化超额收益
        annual_excess = np.mean(excess_returns) * 252

        # 追踪误差(超额收益的标准差)
        tracking_error = np.std(excess_returns, ddof=1) * np.sqrt(252)

        # 信息比率
        ir = annual_excess / tracking_error if tracking_error > 0 else 0

        # 评级
        if ir > 1:
            evaluation = '优秀的主动管理'
        elif ir > 0.5:
            evaluation = '良好的主动管理'
        elif ir > 0:
            evaluation = '一般'
        else:
            evaluation = '跑输基准'

        return {
            'information_ratio': ir,
            'tracking_error': tracking_error,
            'tracking_error_pct': f"{tracking_error * 100:.2f}%",
            'annual_excess_return': annual_excess,
            'annual_excess_return_pct': f"{annual_excess * 100:.2f}%",
            'evaluation': evaluation
        }

    # ==================== 相关性分析 ====================

    def calculate_correlation_matrix(
        self,
        positions_returns: Dict[str, List[float]]
    ) -> Dict:
        """
        计算持仓之间的相关性矩阵

        识别"伪分散" - 多个标的高度相关,实际风险没有分散

        Args:
            positions_returns: {标的名称: 收益率序列}

        Returns:
            相关性矩阵及分析结果
        """
        if len(positions_returns) < 2:
            return {
                'correlation_matrix': {},
                'average_correlation': 0.0,
                'max_correlation': 0.0,
                'diversification_score': 100.0,
                'warnings': []
            }

        # 构建DataFrame
        df = pd.DataFrame(positions_returns)

        # 计算相关性矩阵
        corr_matrix = df.corr()

        # 提取上三角(排除对角线)
        mask = np.triu(np.ones_like(corr_matrix), k=1).astype(bool)
        upper_triangle = corr_matrix.where(mask)

        # 平均相关性
        avg_corr = upper_triangle.stack().mean()

        # 最大相关性
        max_corr = upper_triangle.stack().max()

        # 分散度评分(相关性越低越好)
        diversification_score = (1 - avg_corr) * 100

        # 警告信息
        warnings = []
        if max_corr > 0.8:
            warnings.append(f"⚠️ 存在高度相关的标的(相关系数>{max_corr:.2f}),分散度不足")
        if avg_corr > 0.6:
            warnings.append(f"⚠️ 平均相关性{avg_corr:.2f}偏高,可能是伪分散")
        if diversification_score < 30:
            warnings.append("🚨 分散度评分<30,建议增加低相关性资产")

        return {
            'correlation_matrix': corr_matrix.to_dict(),
            'average_correlation': avg_corr,
            'max_correlation': max_corr,
            'diversification_score': diversification_score,
            'warnings': warnings
        }

    # ==================== 止损检查 ====================

    def check_stop_loss(
        self,
        positions: List[Dict],
        stop_loss_pct: float = 0.15,
        trailing_stop: bool = False
    ) -> Dict:
        """
        检查止损触发

        Args:
            positions: 持仓列表,每个包含:
                - asset_name: 标的名称
                - entry_price: 入场价格
                - current_price: 当前价格
                - highest_price: 历史最高价(用于追踪止损)
            stop_loss_pct: 止损比例,默认15%
            trailing_stop: 是否启用追踪止损

        Returns:
            止损检查结果
        """
        triggered = []
        warnings = []

        for pos in positions:
            asset_name = pos.get('asset_name', 'Unknown')
            entry_price = pos.get('entry_price', 0)
            current_price = pos.get('current_price', 0)
            highest_price = pos.get('highest_price', entry_price)

            if entry_price == 0 or current_price == 0:
                continue

            # 固定止损
            loss_from_entry = (current_price - entry_price) / entry_price

            if loss_from_entry < -stop_loss_pct:
                triggered.append({
                    'asset_name': asset_name,
                    'type': '固定止损',
                    'entry_price': entry_price,
                    'current_price': current_price,
                    'loss': loss_from_entry,
                    'loss_pct': f"{loss_from_entry * 100:.2f}%",
                    'action': '建议止损'
                })

            # 追踪止损
            if trailing_stop and highest_price > entry_price:
                loss_from_high = (current_price - highest_price) / highest_price

                if loss_from_high < -stop_loss_pct:
                    triggered.append({
                        'asset_name': asset_name,
                        'type': '追踪止损',
                        'highest_price': highest_price,
                        'current_price': current_price,
                        'loss': loss_from_high,
                        'loss_pct': f"{loss_from_high * 100:.2f}%",
                        'action': '建议止损(从高点回撤)'
                    })

            # 预警(接近止损线)
            if -stop_loss_pct < loss_from_entry < -stop_loss_pct * 0.8:
                warnings.append({
                    'asset_name': asset_name,
                    'loss_pct': f"{loss_from_entry * 100:.2f}%",
                    'distance_to_stop': f"{(stop_loss_pct + loss_from_entry) * 100:.1f}%",
                    'message': f'⚠️ {asset_name}接近止损线,请密切关注'
                })

        return {
            'triggered_count': len(triggered),
            'triggered_positions': triggered,
            'warnings_count': len(warnings),
            'warnings': warnings,
            'has_stop_loss': len(triggered) > 0
        }

    # ==================== 综合风险报告 ====================

    def generate_risk_report(
        self,
        equity_curve: List[float],
        returns: List[float],
        positions: Optional[List[Dict]] = None,
        market_returns: Optional[List[float]] = None
    ) -> Dict:
        """
        生成综合风险报告

        Args:
            equity_curve: 净值曲线
            returns: 收益率序列
            positions: 持仓列表(可选)
            market_returns: 市场收益率(可选)

        Returns:
            完整的风险分析报告
        """
        report = {
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'metrics': {}
        }

        # 1. 最大回撤
        report['metrics']['max_drawdown'] = self.calculate_max_drawdown(equity_curve)

        # 2. 波动率
        report['metrics']['volatility'] = self.calculate_volatility(returns)

        # 3. 夏普比率
        report['metrics']['sharpe_ratio'] = self.calculate_sharpe_ratio(returns)

        # 4. 索提诺比率
        report['metrics']['sortino_ratio'] = self.calculate_sortino_ratio(returns)

        # 5. 卡玛比率
        annual_return = np.mean(returns) * 252
        max_dd = report['metrics']['max_drawdown']['max_drawdown']
        report['metrics']['calmar_ratio'] = self.calculate_calmar_ratio(annual_return, max_dd)

        # 6. VaR
        report['metrics']['var'] = self.calculate_var(returns, confidence=0.95)

        # 7. 贝塔(如果有市场数据)
        if market_returns and len(market_returns) == len(returns):
            report['metrics']['beta'] = self.calculate_beta(returns, market_returns)
            report['metrics']['information_ratio'] = self.calculate_information_ratio(returns, market_returns)

        # 8. 止损检查(如果有持仓数据)
        if positions:
            report['metrics']['stop_loss'] = self.check_stop_loss(positions)

        # 9. 风险等级评估
        report['risk_level'] = self._evaluate_risk_level(report['metrics'])

        return report

    def _evaluate_risk_level(self, metrics: Dict) -> Dict:
        """
        综合评估风险等级

        Returns:
            风险等级及建议
        """
        score = 100  # 初始分数

        # 最大回撤扣分
        max_dd = abs(metrics.get('max_drawdown', {}).get('max_drawdown', 0))
        if max_dd > 0.5:
            score -= 40
        elif max_dd > 0.3:
            score -= 25
        elif max_dd > 0.2:
            score -= 15
        elif max_dd > 0.1:
            score -= 5

        # 夏普比率加分/扣分
        sharpe = metrics.get('sharpe_ratio', {}).get('sharpe_ratio', 0)
        if sharpe > 2:
            score += 10
        elif sharpe < 0.5:
            score -= 20

        # 波动率扣分
        vol = metrics.get('volatility', {}).get('volatility', 0)
        if vol > 0.4:
            score -= 30
        elif vol > 0.3:
            score -= 15
        elif vol > 0.2:
            score -= 5

        # 确定风险等级
        if score >= 80:
            level = '低风险'
            color = '🟢'
            suggestion = '当前风险可控,继续保持'
        elif score >= 60:
            level = '中等风险'
            color = '🟡'
            suggestion = '注意控制仓位,关注市场变化'
        elif score >= 40:
            level = '较高风险'
            color = '🟠'
            suggestion = '建议降低仓位,设置止损'
        else:
            level = '高风险'
            color = '🔴'
            suggestion = '风险过高!立即降低仓位或清仓'

        return {
            'level': level,
            'score': score,
            'color': color,
            'suggestion': suggestion
        }

    def format_risk_report(self, report: Dict, format_type: str = 'markdown') -> str:
        """
        格式化风险报告

        Args:
            report: generate_risk_report()返回的报告
            format_type: 格式类型('markdown' 或 'text')

        Returns:
            格式化后的报告文本
        """
        if format_type == 'markdown':
            return self._format_markdown_risk_report(report)
        else:
            return self._format_text_risk_report(report)

    def _format_markdown_risk_report(self, report: Dict) -> str:
        """生成Markdown格式的风险报告"""
        lines = []

        lines.append("## 🛡️ 风险管理报告")
        lines.append("")
        lines.append(f"**生成时间**: {report['generated_at']}")
        lines.append("")

        metrics = report['metrics']

        # 风险等级
        risk_level = report['risk_level']
        lines.append(f"### {risk_level['color']} 综合风险等级: {risk_level['level']} (评分: {risk_level['score']}/100)")
        lines.append("")
        lines.append(f"**建议**: {risk_level['suggestion']}")
        lines.append("")
        lines.append("---")
        lines.append("")

        # 核心风险指标
        lines.append("### 📊 核心风险指标")
        lines.append("")

        # 最大回撤
        if 'max_drawdown' in metrics:
            md = metrics['max_drawdown']
            lines.append(f"#### 最大回撤 (Max Drawdown)")
            lines.append(f"- **最大回撤**: {md['max_drawdown_pct']}")
            lines.append(f"- **当前回撤**: {md['current_drawdown_pct']}")
            lines.append(f"- **回撤持续**: {md['duration_days']}天")
            lines.append("")

        # 波动率
        if 'volatility' in metrics:
            vol = metrics['volatility']
            lines.append(f"#### 波动率 (Volatility)")
            lines.append(f"- **年化波动率**: {vol['volatility_pct']}")
            lines.append(f"- **下行波动率**: {vol['downside_volatility_pct']}")
            lines.append("")

        # 夏普比率
        if 'sharpe_ratio' in metrics:
            sharpe = metrics['sharpe_ratio']
            lines.append(f"#### 夏普比率 (Sharpe Ratio)")
            lines.append(f"- **夏普比率**: {sharpe['sharpe_ratio']:.2f}")
            lines.append(f"- **评级**: {sharpe['evaluation']}")
            lines.append(f"- **超额收益**: {sharpe['excess_return_pct']}")
            lines.append("")

        # 索提诺比率
        if 'sortino_ratio' in metrics:
            sortino = metrics['sortino_ratio']
            lines.append(f"#### 索提诺比率 (Sortino Ratio)")
            lines.append(f"- **索提诺比率**: {sortino['sortino_ratio']:.2f}")
            lines.append(f"- **评级**: {sortino['evaluation']}")
            lines.append("")

        # 卡玛比率
        if 'calmar_ratio' in metrics:
            calmar = metrics['calmar_ratio']
            lines.append(f"#### 卡玛比率 (Calmar Ratio)")
            lines.append(f"- **卡玛比率**: {calmar['calmar_ratio']:.2f}")
            lines.append(f"- **评级**: {calmar['evaluation']}")
            lines.append("")

        # VaR
        if 'var' in metrics:
            var = metrics['var']
            lines.append(f"#### VaR风险价值 ({var['confidence']*100:.0f}%置信度)")
            lines.append(f"- **VaR**: {var['var_pct']}")
            lines.append(f"- **CVaR**: {var['cvar_pct']}")
            lines.append(f"- **解读**: {var['confidence']*100:.0f}%的概率下,日亏损不超过{abs(float(var['var_pct'][:-1])):.2f}%")
            lines.append("")

        # 贝塔系数
        if 'beta' in metrics:
            beta = metrics['beta']
            lines.append(f"#### 贝塔系数 (Beta)")
            lines.append(f"- **贝塔**: {beta['beta']:.2f}")
            lines.append(f"- **阿尔法**: {beta['alpha_pct']}")
            lines.append(f"- **R²**: {beta['r_squared']:.2f}")
            lines.append(f"- **解读**: {beta['interpretation']}")
            lines.append("")

        # 信息比率
        if 'information_ratio' in metrics:
            ir = metrics['information_ratio']
            lines.append(f"#### 信息比率 (Information Ratio)")
            lines.append(f"- **信息比率**: {ir['information_ratio']:.2f}")
            lines.append(f"- **追踪误差**: {ir['tracking_error_pct']}")
            lines.append(f"- **评级**: {ir['evaluation']}")
            lines.append("")

        # 止损检查
        if 'stop_loss' in metrics:
            sl = metrics['stop_loss']
            lines.append("---")
            lines.append("")
            lines.append("### 🚨 止损检查")
            lines.append("")

            if sl['has_stop_loss']:
                lines.append(f"**触发止损**: {sl['triggered_count']}个标的")
                lines.append("")
                for trigger in sl['triggered_positions']:
                    lines.append(f"#### {trigger['asset_name']}")
                    lines.append(f"- **类型**: {trigger['type']}")
                    lines.append(f"- **亏损**: {trigger['loss_pct']}")
                    lines.append(f"- **行动**: {trigger['action']}")
                    lines.append("")
            else:
                lines.append("✅ 当前无触发止损的标的")
                lines.append("")

            if sl['warnings']:
                lines.append("**预警信息**:")
                lines.append("")
                for warn in sl['warnings']:
                    lines.append(f"- {warn['message']} (距止损线{warn['distance_to_stop']})")
                lines.append("")

        return "\n".join(lines)

    def _format_text_risk_report(self, report: Dict) -> str:
        """生成纯文本格式的风险报告"""
        lines = []

        lines.append("=" * 60)
        lines.append("风险管理报告")
        lines.append("=" * 60)
        lines.append(f"生成时间: {report['generated_at']}")
        lines.append("")

        risk_level = report['risk_level']
        lines.append(f"综合风险等级: {risk_level['level']} ({risk_level['score']}/100)")
        lines.append(f"建议: {risk_level['suggestion']}")
        lines.append("")

        metrics = report['metrics']

        if 'max_drawdown' in metrics:
            md = metrics['max_drawdown']
            lines.append(f"最大回撤: {md['max_drawdown_pct']}")

        if 'sharpe_ratio' in metrics:
            sharpe = metrics['sharpe_ratio']
            lines.append(f"夏普比率: {sharpe['sharpe_ratio']:.2f} ({sharpe['evaluation']})")

        if 'stop_loss' in metrics:
            sl = metrics['stop_loss']
            if sl['has_stop_loss']:
                lines.append(f"\n⚠️ 触发止损: {sl['triggered_count']}个标的")

        lines.append("")
        lines.append("=" * 60)

        return "\n".join(lines)


# 示例用法
if __name__ == "__main__":
    # 创建风险管理器
    rm = RiskManager(risk_free_rate=0.03)

    # 模拟净值曲线
    equity_curve = [
        100000, 102000, 101000, 103000, 105000,
        104000, 106000, 103000, 107000, 110000,
        108000, 112000, 115000, 113000, 120000
    ]

    # 模拟收益率
    returns = [0.02, -0.01, 0.02, 0.019, -0.01, 0.019, -0.028, 0.039, 0.028, -0.018,
               0.037, 0.027, -0.017, 0.062]

    # 生成风险报告
    report = rm.generate_risk_report(
        equity_curve=equity_curve,
        returns=returns
    )

    # 打印报告
    print(rm.format_risk_report(report, format_type='markdown'))
