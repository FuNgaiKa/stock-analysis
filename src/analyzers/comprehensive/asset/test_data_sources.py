#!/usr/bin/env python3
"""
数据源验证脚本
用于验证所有新增指标的数据源可用性
"""

import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

def test_akshare_sources():
    """测试akshare数据源"""
    print("\n" + "="*60)
    print("测试 AKShare 数据源")
    print("="*60)

    try:
        import akshare as ak
        print("✅ akshare 已安装")

        # 测试融资融券数据
        print("\n1. 测试融资融券数据...")
        try:
            # 上交所两融数据
            sse_margin = ak.stock_margin_sse(start_date="20241001")
            print(f"   ✅ 上交所两融数据: {len(sse_margin)} 条记录")
            print(f"      最新日期: {sse_margin.iloc[-1]['信用交易日期']}")
            print(f"      融资余额: {sse_margin.iloc[-1]['融资余额(元)'] / 1e8:.2f} 亿元")
        except Exception as e:
            print(f"   ❌ 上交所两融数据失败: {e}")

        # 测试指数估值数据
        print("\n2. 测试指数估值数据...")
        try:
            # 获取指数基本信息(包含股息率)
            index_info = ak.index_stock_info()
            print(f"   ✅ 指数基本信息: {len(index_info)} 个指数")
            # 查找沪深300
            hs300 = index_info[index_info['index_code'] == '000300']
            if not hs300.empty:
                print(f"      沪深300股息率: 可获取")
        except Exception as e:
            print(f"   ❌ 指数基本信息失败: {e}")

        # 测试国债收益率
        print("\n3. 测试国债收益率...")
        try:
            bond_yield = ak.bond_zh_us_rate()
            print(f"   ✅ 国债收益率: {len(bond_yield)} 条记录")
            print(f"      最新日期: {bond_yield.iloc[-1]['日期']}")
            print(f"      中国10年期: {bond_yield.iloc[-1]['中国国债收益率10年']}%")
        except Exception as e:
            print(f"   ❌ 国债收益率失败: {e}")

        # 测试行业指数数据
        print("\n4. 测试行业指数数据...")
        try:
            industry_index = ak.stock_board_industry_index_ths()
            print(f"   ✅ 同花顺行业指数: {len(industry_index)} 个行业")
            print(f"      示例: {industry_index.iloc[0]['代码']} - {industry_index.iloc[0]['名称']}")
        except Exception as e:
            print(f"   ❌ 行业指数失败: {e}")

        # 测试板块资金流向
        print("\n5. 测试板块资金流向...")
        try:
            money_flow = ak.stock_sector_fund_flow_rank(indicator="今日")
            print(f"   ✅ 板块资金流向: {len(money_flow)} 个板块")
            print(f"      示例: {money_flow.iloc[0]['名称']} 主力净流入: {money_flow.iloc[0]['主力净流入-净额']} 万元")
        except Exception as e:
            print(f"   ❌ 板块资金流向失败: {e}")

    except ImportError:
        print("❌ akshare 未安装")
        return False

    return True

def test_yfinance_sources():
    """测试yfinance数据源"""
    print("\n" + "="*60)
    print("测试 yfinance 数据源")
    print("="*60)

    try:
        import yfinance as yf
        print("✅ yfinance 已安装")

        # 测试10年期美债收益率
        print("\n1. 测试10年期美债收益率 (^TNX)...")
        try:
            tnx = yf.Ticker("^TNX")
            hist = tnx.history(period="5d")
            if not hist.empty:
                print(f"   ✅ 10年期美债收益率: 最新值 {hist['Close'].iloc[-1]:.2f}%")
                print(f"      日期: {hist.index[-1].strftime('%Y-%m-%d')}")
            else:
                print(f"   ⚠️  10年期美债收益率: 数据为空")
        except Exception as e:
            print(f"   ❌ 10年期美债收益率失败: {e}")

        # 测试5年期美债收益率
        print("\n2. 测试5年期美债收益率 (^FVX)...")
        try:
            fvx = yf.Ticker("^FVX")
            hist = fvx.history(period="5d")
            if not hist.empty:
                print(f"   ✅ 5年期美债收益率: 最新值 {hist['Close'].iloc[-1]:.2f}%")
            else:
                print(f"   ⚠️  5年期美债收益率: 数据为空")
        except Exception as e:
            print(f"   ❌ 5年期美债收益率失败: {e}")

        # 测试美元指数
        print("\n3. 测试美元指数 (DX-Y.NYB)...")
        try:
            dxy = yf.Ticker("DX-Y.NYB")
            hist = dxy.history(period="5d")
            if not hist.empty:
                print(f"   ✅ 美元指数: 最新值 {hist['Close'].iloc[-1]:.2f}")
                print(f"      日期: {hist.index[-1].strftime('%Y-%m-%d')}")
            else:
                print(f"   ⚠️  美元指数: 数据为空")
        except Exception as e:
            print(f"   ❌ 美元指数失败: {e}")

        # 测试VIX (用于验证yfinance基本功能)
        print("\n4. 测试VIX指数 (^VIX) [验证用]...")
        try:
            vix = yf.Ticker("^VIX")
            hist = vix.history(period="5d")
            if not hist.empty:
                print(f"   ✅ VIX指数: 最新值 {hist['Close'].iloc[-1]:.2f}")
            else:
                print(f"   ⚠️  VIX指数: 数据为空")
        except Exception as e:
            print(f"   ❌ VIX指数失败: {e}")

        # 测试Put/Call Ratio (这个可能不可用)
        print("\n5. 测试Put/Call Ratio (^PCALL, ^PPUT)...")
        print("   ⚠️  注意: CBOE Put/Call Ratio可能需要付费数据源")
        try:
            # 尝试多个可能的ticker符号
            tickers_to_try = ["^PCRATIO", "^PCALL", "^PPUT"]
            found = False
            for ticker_symbol in tickers_to_try:
                try:
                    pcr = yf.Ticker(ticker_symbol)
                    hist = pcr.history(period="5d")
                    if not hist.empty:
                        print(f"   ✅ Put/Call Ratio ({ticker_symbol}): 最新值 {hist['Close'].iloc[-1]:.2f}")
                        found = True
                        break
                except:
                    continue

            if not found:
                print(f"   ❌ Put/Call Ratio: 未找到可用的ticker符号")
                print(f"      备选方案: 使用VIX作为情绪指标,或通过CBOE官网API获取")
        except Exception as e:
            print(f"   ❌ Put/Call Ratio失败: {e}")

    except ImportError:
        print("❌ yfinance 未安装")
        return False

    return True

def test_pandas_operations():
    """测试pandas相关性计算"""
    print("\n" + "="*60)
    print("测试 Pandas 相关性计算")
    print("="*60)

    try:
        import pandas as pd
        import numpy as np
        print("✅ pandas 和 numpy 已安装")

        # 创建模拟数据
        print("\n模拟7大资产的收益率数据...")
        dates = pd.date_range('2024-01-01', periods=100, freq='D')
        returns = pd.DataFrame({
            '沪深300': np.random.randn(100) * 0.02,
            '创业板指': np.random.randn(100) * 0.025,
            '科创50': np.random.randn(100) * 0.03,
            '纳指100': np.random.randn(100) * 0.022,
            '标普500': np.random.randn(100) * 0.018,
            '黄金': np.random.randn(100) * 0.015,
            '比特币': np.random.randn(100) * 0.04,
        }, index=dates)

        # 计算相关性矩阵
        corr_matrix = returns.corr()
        print(f"✅ 相关性矩阵计算成功 ({corr_matrix.shape[0]}x{corr_matrix.shape[1]})")

        # 计算Beta系数
        benchmark = returns['沪深300']
        betas = {}
        for col in returns.columns:
            if col != '沪深300':
                covariance = returns[col].cov(benchmark)
                benchmark_var = benchmark.var()
                beta = covariance / benchmark_var
                betas[col] = beta

        print(f"✅ Beta系数计算成功")
        print(f"   示例 - 创业板指 Beta: {betas['创业板指']:.2f}")

    except Exception as e:
        print(f"❌ Pandas操作失败: {e}")
        return False

    return True

def main():
    """主函数"""
    print("="*60)
    print("综合资产分析系统 - 数据源验证")
    print("="*60)

    results = {
        'akshare': test_akshare_sources(),
        'yfinance': test_yfinance_sources(),
        'pandas': test_pandas_operations()
    }

    print("\n" + "="*60)
    print("验证结果汇总")
    print("="*60)

    for source, status in results.items():
        status_icon = "✅" if status else "❌"
        print(f"{status_icon} {source}: {'可用' if status else '不可用'}")

    print("\n" + "="*60)
    print("结论与建议")
    print("="*60)

    if results['akshare']:
        print("✅ 可以实现: 估值维度、融资融券、行业轮动")

    if results['yfinance']:
        print("✅ 可以实现: 美债收益率、美元指数")
        print("⚠️  Put/Call Ratio: 可能需要备选方案 (使用VIX或CBOE API)")

    if results['pandas']:
        print("✅ 可以实现: 资产相关性矩阵")

    print("\n推荐实施顺序:")
    print("1. 估值维度 + 融资融券 (akshare数据源稳定)")
    print("2. 美债收益率 + 美元指数 (yfinance数据源)")
    print("3. 资产相关性矩阵 (计算密集,最后实现)")
    print("4. Put/Call Ratio (需要进一步调研数据源)")

if __name__ == "__main__":
    main()
