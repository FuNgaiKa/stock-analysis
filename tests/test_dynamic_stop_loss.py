#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
动态止损功能单元测试
测试 RiskManager 的 ATR 计算和动态止损建议功能
"""

import pytest
import numpy as np
import pandas as pd
from russ_trading.managers.risk_manager import RiskManager


class TestATRCalculation:
    """测试ATR计算功能"""

    def setup_method(self):
        """每个测试方法前执行"""
        self.rm = RiskManager()

    def test_atr_basic_calculation(self):
        """测试基本ATR计算"""
        # 模拟价格数据
        prices = [100, 102, 101, 103, 102, 104, 103, 105, 104, 106]
        highs = [101, 103, 102, 104, 103, 105, 104, 106, 105, 107]
        lows = [99, 101, 100, 102, 101, 103, 102, 104, 103, 105]

        atr = self.rm.calculate_atr(prices, highs, lows, period=5)

        # ATR应该大于0
        assert atr > 0, "ATR应该大于0"
        # ATR应该在合理范围内 (对于这个数据,应该在1-3之间)
        assert 1 < atr < 3, f"ATR值{atr}不在预期范围内"

    def test_atr_zero_volatility(self):
        """测试零波动的ATR"""
        # 价格完全不变
        prices = [100] * 21
        highs = [100] * 21
        lows = [100] * 21

        atr = self.rm.calculate_atr(prices, highs, lows, period=20)

        # 零波动应该得到0
        assert atr == 0, "零波动应该得到ATR=0"

    def test_atr_high_volatility(self):
        """测试高波动的ATR"""
        # 剧烈波动的价格
        prices = [100 + i*(-1)**i * 5 for i in range(21)]
        highs = [p + 5 for p in prices]
        lows = [p - 5 for p in prices]

        atr = self.rm.calculate_atr(prices, highs, lows, period=20)

        # 高波动应该得到较大的ATR
        assert atr > 5, f"高波动应该得到较大的ATR,实际为{atr}"

    def test_atr_insufficient_data(self):
        """测试数据不足的情况"""
        # 数据长度不足
        prices = [100, 101, 102]
        highs = [101, 102, 103]
        lows = [99, 100, 101]

        atr = self.rm.calculate_atr(prices, highs, lows, period=20)

        # 数据不足应该返回0
        assert atr == 0, "数据不足应该返回0"


class TestDynamicStopLoss:
    """测试动态止损功能"""

    def setup_method(self):
        """每个测试方法前执行"""
        self.rm = RiskManager()

    def create_price_dataframe(self, volatility: str = 'medium'):
        """
        创建测试用的价格数据

        Args:
            volatility: 波动率级别 ('low', 'medium', 'high')
        """
        np.random.seed(42)  # 固定随机种子,保证测试可重复

        if volatility == 'low':
            # 低波动: 价格在100附近小幅波动
            prices = 100 + np.random.normal(0, 0.5, 30)
        elif volatility == 'medium':
            # 中波动: 价格在100附近中等波动
            prices = 100 + np.random.normal(0, 2, 30)
        else:  # high
            # 高波动: 价格在100附近剧烈波动
            prices = 100 + np.random.normal(0, 4, 30)

        # 生成High/Low (在Close基础上加减1-2%)
        highs = prices * (1 + np.random.uniform(0.005, 0.015, 30))
        lows = prices * (1 - np.random.uniform(0.005, 0.015, 30))

        df = pd.DataFrame({
            'Close': prices,
            'High': highs,
            'Low': lows
        })

        return df

    def test_low_volatility_stop_loss(self):
        """测试低波动标的的动态止损"""
        price_data = self.create_price_dataframe('low')

        result = self.rm.calculate_dynamic_stop_loss(
            symbol='TEST_LOW',
            current_price=101,
            entry_price=100,
            price_data=price_data
        )

        # 验证返回值完整性
        assert 'symbol' in result
        assert 'atr_pct' in result
        assert 'dynamic_stop_loss' in result
        assert 'volatility_level' in result

        # 低波动应该被识别
        assert result['volatility_level'] == '低', f"应该识别为低波动,实际为{result['volatility_level']}"

        # 动态止损应该比固定止损(-15%)更紧
        assert result['dynamic_stop_loss'] > -0.15, \
            f"低波动应该收紧止损,实际止损{result['dynamic_stop_loss']*100:.1f}%"

    def test_high_volatility_stop_loss(self):
        """测试高波动标的的动态止损"""
        price_data = self.create_price_dataframe('high')

        result = self.rm.calculate_dynamic_stop_loss(
            symbol='TEST_HIGH',
            current_price=101,
            entry_price=100,
            price_data=price_data
        )

        # 高波动应该被识别
        assert result['volatility_level'] == '高', f"应该识别为高波动,实际为{result['volatility_level']}"

        # 动态止损应该比固定止损(-15%)更宽松
        assert result['dynamic_stop_loss'] < -0.15, \
            f"高波动应该放宽止损,实际止损{result['dynamic_stop_loss']*100:.1f}%"

    def test_stop_loss_trigger(self):
        """测试止损触发逻辑"""
        price_data = self.create_price_dataframe('medium')

        # 当前价格大幅低于买入价,应该触发止损
        result = self.rm.calculate_dynamic_stop_loss(
            symbol='TEST_TRIGGER',
            current_price=80,  # 跌了20%
            entry_price=100,
            price_data=price_data
        )

        # 应该触发止损
        assert result['is_triggered'], "跌20%应该触发止损"
        assert '触发止损' in result['recommendation'], "建议中应该包含'触发止损'"

    def test_stop_loss_not_trigger(self):
        """测试未触发止损的情况"""
        price_data = self.create_price_dataframe('medium')

        # 当前价格略高于买入价,不应该触发止损
        result = self.rm.calculate_dynamic_stop_loss(
            symbol='TEST_NO_TRIGGER',
            current_price=102,  # 涨了2%
            entry_price=100,
            price_data=price_data
        )

        # 不应该触发止损
        assert not result['is_triggered'], "盈利状态不应该触发止损"

    def test_stop_loss_price_calculation(self):
        """测试止损价格计算"""
        price_data = self.create_price_dataframe('medium')

        result = self.rm.calculate_dynamic_stop_loss(
            symbol='TEST_PRICE',
            current_price=100,
            entry_price=100,
            price_data=price_data
        )

        # 止损价格应该低于买入价
        assert result['stop_loss_price'] < result['entry_price'], \
            "止损价格应该低于买入价"

        # 止损价格应该符合止损比例
        expected_price = result['entry_price'] * (1 + result['dynamic_stop_loss'])
        assert abs(result['stop_loss_price'] - expected_price) < 0.01, \
            f"止损价格计算错误,预期{expected_price:.2f},实际{result['stop_loss_price']:.2f}"

    def test_missing_columns(self):
        """测试缺少必需列的情况"""
        # 缺少High列
        df = pd.DataFrame({
            'Close': [100, 101, 102],
            'Low': [99, 100, 101]
        })

        result = self.rm.calculate_dynamic_stop_loss(
            symbol='TEST_MISSING',
            current_price=100,
            entry_price=100,
            price_data=df
        )

        # 应该返回错误
        assert 'error' in result, "缺少必需列应该返回错误"
        assert 'dynamic_stop_loss' in result, "应该返回默认止损线"

    def test_recommendation_consistency(self):
        """测试建议的一致性"""
        price_data = self.create_price_dataframe('low')

        result = self.rm.calculate_dynamic_stop_loss(
            symbol='TEST_CONSISTENCY',
            current_price=98,  # 亏损2%
            entry_price=100,
            price_data=price_data
        )

        # 建议字段应该存在且非空
        assert result['recommendation'], "建议不应该为空"
        assert result['reason'], "原因不应该为空"

        # 建议应该包含具体的止损比例
        assert f"{result['dynamic_stop_loss']*100:.0f}%" in result['recommendation'] or \
               '触发止损' in result['recommendation'], \
            "建议应该包含具体的止损比例或触发提示"


class TestDynamicStopLossEdgeCases:
    """测试边界情况"""

    def setup_method(self):
        """每个测试方法前执行"""
        self.rm = RiskManager()

    def test_extreme_stop_loss_boundary(self):
        """测试极端止损边界"""
        # 创建极低波动数据
        df = pd.DataFrame({
            'Close': [100] * 30,
            'High': [100.1] * 30,
            'Low': [99.9] * 30
        })

        result = self.rm.calculate_dynamic_stop_loss(
            symbol='TEST_BOUNDARY',
            current_price=100,
            entry_price=100,
            price_data=df
        )

        # 动态止损应该在[-5%, -30%]范围内
        assert -0.30 <= result['dynamic_stop_loss'] <= -0.05, \
            f"动态止损{result['dynamic_stop_loss']*100:.1f}%超出合理范围"

    def test_zero_price(self):
        """测试价格为0的边界情况"""
        df = pd.DataFrame({
            'Close': [100] * 30,
            'High': [101] * 30,
            'Low': [99] * 30
        })

        result = self.rm.calculate_dynamic_stop_loss(
            symbol='TEST_ZERO',
            current_price=0,  # 异常价格
            entry_price=100,
            price_data=df
        )

        # 应该返回错误
        assert 'error' in result, "价格为0应该返回错误"


class TestDynamicStopLossIntegration:
    """集成测试"""

    def setup_method(self):
        """每个测试方法前执行"""
        self.rm = RiskManager()

    def test_real_world_scenario(self):
        """测试真实场景"""
        # 模拟一个真实的价格走势
        np.random.seed(123)

        # 创建一个上升趋势带波动的价格序列
        base_prices = np.linspace(100, 110, 30)
        noise = np.random.normal(0, 1.5, 30)
        prices = base_prices + noise

        df = pd.DataFrame({
            'Close': prices,
            'High': prices * 1.01,
            'Low': prices * 0.99
        })

        result = self.rm.calculate_dynamic_stop_loss(
            symbol='510300.SS',
            current_price=108,
            entry_price=100,
            price_data=df
        )

        # 验证所有关键字段存在
        required_fields = [
            'symbol', 'atr', 'atr_pct', 'volatility_level',
            'dynamic_stop_loss', 'stop_loss_price', 'current_loss',
            'is_triggered', 'recommendation', 'reason'
        ]

        for field in required_fields:
            assert field in result, f"缺少必需字段: {field}"

        # 盈利状态不应该触发止损
        assert not result['is_triggered'], "盈利8%不应该触发止损"

        # 打印结果供人工检查
        print("\n真实场景测试结果:")
        print(f"标的: {result['symbol']}")
        print(f"ATR: {result['atr']:.2f} ({result['atr_pct']*100:.2f}%)")
        print(f"波动率等级: {result['volatility_level']}")
        print(f"动态止损: {result['dynamic_stop_loss']*100:.1f}%")
        print(f"建议: {result['recommendation']}")
        print(f"原因: {result['reason']}")


if __name__ == '__main__':
    # 运行测试
    pytest.main([__file__, '-v', '-s'])
