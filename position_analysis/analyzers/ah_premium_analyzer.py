"""
AH溢价指数分析器
分析A股相对H股的溢价水平,用于跨市场配置决策
"""
import akshare as ak
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class AHPremiumAnalyzer:
    """AH溢价指数分析器"""

    def __init__(self):
        """初始化AH溢价分析器"""
        self.cache = {}
        self.cache_time = {}
        self.cache_duration = 300  # 5分钟缓存

        # 2025年AH溢价合理区间(基于美元指数中枢调整)
        self.reasonable_range = (142, 149)

    def get_ah_premium_data(self, timeout: int = 30) -> Optional[pd.DataFrame]:
        """
        获取AH股票溢价数据

        Args:
            timeout: 超时时间(秒)

        Returns:
            AH股票溢价DataFrame
        """
        cache_key = "ah_premium_spot"

        # 检查缓存
        if cache_key in self.cache:
            if (datetime.now() - self.cache_time[cache_key]).seconds < self.cache_duration:
                logger.info("使用缓存的AH溢价数据")
                return self.cache[cache_key]

        try:
            # 使用线程超时控制
            import signal
            from contextlib import contextmanager

            @contextmanager
            def time_limit(seconds):
                def signal_handler(signum, frame):
                    raise TimeoutError("获取数据超时")
                signal.signal(signal.SIGALRM, signal_handler)
                signal.alarm(seconds)
                try:
                    yield
                finally:
                    signal.alarm(0)

            # 获取AH股实时溢价数据(带超时)
            try:
                with time_limit(timeout):
                    df = ak.stock_zh_ah_spot()
            except TimeoutError:
                logger.warning(f"获取AH溢价数据超时({timeout}秒)")
                return None
            except:  # signal在Windows上不可用
                logger.info("降级到无超时模式")
                df = ak.stock_zh_ah_spot()

            if df.empty:
                logger.warning("获取AH溢价数据为空")
                return None

            # 缓存
            self.cache[cache_key] = df
            self.cache_time[cache_key] = datetime.now()

            logger.info(f"获取AH溢价数据成功: {len(df)}只股票")
            return df

        except Exception as e:
            logger.error(f"获取AH溢价数据失败: {str(e)}")
            return None

    def analyze_ah_premium(self) -> Dict[str, Any]:
        """
        分析AH溢价指数

        Returns:
            AH溢价分析结果
        """
        df = self.get_ah_premium_data()

        if df is None or df.empty:
            return {'error': '无法获取AH溢价数据'}

        try:
            # 根据列位置获取溢价率(通常是第3列,索引2)
            # 数据格式: [代码, 名称, 最新价, A涨跌幅, A涨跌额, A股价, H股价, ...]
            # 溢价率需要手动计算: (A股价 - H股价) / H股价 * 100

            # 尝试通过列名查找(如果可读)
            premium_col = None
            a_price_col = None
            h_price_col = None

            for col in df.columns:
                col_lower = str(col).lower()
                if '溢价' in str(col) or 'premium' in col_lower:
                    premium_col = col
                if 'a股' in str(col) and '价' in str(col):
                    a_price_col = col
                if 'h股' in str(col) and '价' in str(col):
                    h_price_col = col

            # 如果找不到,使用位置索引(根据观察到的数据格式)
            if premium_col is None and len(df.columns) >= 11:
                # 列顺序: 代码, 名称, 最新价, A涨跌幅, A涨跌额, A股价, H股价, ..., 溢价率
                # 溢价率通常在倒数几列
                # 手动计算更可靠
                if a_price_col is None:
                    a_price_col = df.columns[5]  # A股价
                if h_price_col is None:
                    h_price_col = df.columns[6]  # H股价

                # 计算溢价率
                df_valid = df.copy()
                df_valid['premium'] = ((pd.to_numeric(df_valid[a_price_col], errors='coerce') -
                                       pd.to_numeric(df_valid[h_price_col], errors='coerce')) /
                                       pd.to_numeric(df_valid[h_price_col], errors='coerce') * 100)
                premium_col = 'premium'

            # 过滤有效数据
            df_valid = df_valid[pd.to_numeric(df_valid[premium_col], errors='coerce').notna()].copy()
            df_valid[premium_col] = pd.to_numeric(df_valid[premium_col], errors='coerce')

            # 计算平均溢价率(作为AH溢价指数的近似)
            avg_premium = float(df_valid[premium_col].mean())
            median_premium = float(df_valid[premium_col].median())
            std_premium = float(df_valid[premium_col].std())
            max_premium = float(df_valid[premium_col].max())
            min_premium = float(df_valid[premium_col].min())

            # 将百分比转换为指数(假设100为基准)
            # 如果溢价率是30%,则指数为130
            current_premium_index = 100 + avg_premium

            # 溢价等级
            premium_level = self._classify_premium(current_premium_index)

            # 配置建议
            allocation_advice = self._generate_allocation_advice(current_premium_index, premium_level)

            # 风险提示
            risk_alert = self._generate_risk_alert(current_premium_index)

            # 样本分布
            high_premium_count = int((df_valid[premium_col] > 50).sum())
            low_premium_count = int((df_valid[premium_col] < 0).sum())  # 负溢价(H股比A股贵)

            result = {
                'current_premium_index': current_premium_index,
                'avg_premium_pct': avg_premium,
                'median_premium_pct': median_premium,
                'std_premium': std_premium,
                'max_premium_pct': max_premium,
                'min_premium_pct': min_premium,
                'premium_level': premium_level,
                'in_reasonable_range': self.reasonable_range[0] <= current_premium_index <= self.reasonable_range[1],
                'reasonable_range': self.reasonable_range,
                'sample_count': len(df_valid),
                'high_premium_count': high_premium_count,
                'low_premium_count': low_premium_count,
                'allocation_advice': allocation_advice,
                'risk_alert': risk_alert,
                'interpretation': self._generate_interpretation(
                    current_premium_index, premium_level,
                    self.reasonable_range[0] <= current_premium_index <= self.reasonable_range[1]
                )
            }

            return result

        except Exception as e:
            logger.error(f"分析AH溢价失败: {str(e)}")
            return {'error': str(e)}

    def _classify_premium(self, premium_index: float) -> str:
        """溢价等级分类"""
        if premium_index > 160:
            return '极高溢价'
        elif premium_index > 149:
            return '高溢价'
        elif premium_index >= 142:
            return '合理偏高'
        elif premium_index >= 130:
            return '合理'
        elif premium_index >= 120:
            return '低溢价'
        else:
            return '极低溢价'

    def _generate_allocation_advice(self, current_premium: float, level: str) -> str:
        """生成配置建议"""
        if level == '极高溢价':
            return '强烈建议: 增配港股,减配A股 (AH溢价过高,港股性价比突出)'
        elif level == '高溢价':
            return '建议: 倾向港股配置 (AH溢价偏高,港股相对便宜)'
        elif level in ['合理偏高', '合理']:
            return '中性: A股H股均衡配置 (AH溢价在合理区间)'
        elif level == '低溢价':
            return '建议: 倾向A股配置 (AH溢价偏低,A股相对便宜)'
        else:
            return '强烈建议: 增配A股,减配港股 (AH溢价过低,A股性价比突出)'

    def _generate_risk_alert(self, current_premium: float) -> Optional[str]:
        """生成风险提示"""
        alerts = []
        if current_premium > 160:
            alerts.append("⚠️ AH溢价达到极端水平,存在均值回归风险")
        elif current_premium < 120:
            alerts.append("⚠️ AH溢价处于极低水平,可能反映A股流动性风险")

        return '; '.join(alerts) if alerts else None

    def _generate_interpretation(self, current_premium: float, level: str, in_reasonable: bool) -> str:
        """生成解读文本"""
        interpretation = []
        interpretation.append(f"当前AH溢价指数{current_premium:.1f}")

        if in_reasonable:
            interpretation.append("处于合理波动区间(142-149)")
        else:
            if current_premium > 149:
                interpretation.append("超出合理区间上限,A股相对H股偏贵")
            else:
                interpretation.append("低于合理区间下限,A股相对H股偏便宜")

        return '; '.join(interpretation)


if __name__ == '__main__':
    # 测试代码
    logging.basicConfig(level=logging.INFO)

    analyzer = AHPremiumAnalyzer()

    print("=" * 80)
    print("AH溢价指数分析器测试")
    print("=" * 80)

    result = analyzer.analyze_ah_premium()

    if 'error' not in result:
        print(f"当前AH溢价指数: {result['current_premium_index']:.1f}")
        print(f"平均溢价率: {result['avg_premium_pct']:.1f}%")
        print(f"溢价等级: {result['premium_level']}")
        print(f"合理区间: {result['reasonable_range']}")
        print(f"是否在合理区间: {'是' if result['in_reasonable_range'] else '否'}")
        print(f"样本数: {result['sample_count']}只股票")
        print(f"配置建议: {result['allocation_advice']}")
        if result['risk_alert']:
            print(f"风险提示: {result['risk_alert']}")
        print(f"解读: {result['interpretation']}")
    else:
        print(f"分析失败: {result['error']}")

    print("\n" + "=" * 80)
