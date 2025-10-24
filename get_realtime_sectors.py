#!/usr/bin/env python3
"""
实时板块数据获取脚本
建议运行时间: 交易日 9:30 - 15:00

使用方法: python get_realtime_sectors.py
"""

import akshare as ak
import pandas as pd
from datetime import datetime


def get_sector_data():
    """获取实时板块数据"""
    print(f"{'='*70}")
    print(f"  板块轮动实时数据")
    print(f"  获取时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*70}\n")

    # 1. 概念板块
    print("【概念板块排行】\n")
    try:
        df_concept = ak.stock_board_concept_name_em()

        if df_concept is not None and len(df_concept) > 0:
            print(f"✓ 成功获取 {len(df_concept)} 个概念板块\n")

            # 涨幅榜
            print("📈 涨幅 TOP 10:")
            print("-" * 70)
            top10 = df_concept.nlargest(10, '涨跌幅')
            for idx, row in top10.iterrows():
                print(f"  {row['板块名称']:15s} "
                      f"{row['涨跌幅']:>6.2f}%  "
                      f"领涨股:{row['领涨股票']:8s}({row['领涨股票涨跌幅']:>6.2f}%)  "
                      f"上涨/下跌:{row['上涨家数']:>3}/{row['下跌家数']:<3}")

            # 跌幅榜
            print("\n📉 跌幅 TOP 10:")
            print("-" * 70)
            bottom10 = df_concept.nsmallest(10, '涨跌幅')
            for idx, row in bottom10.iterrows():
                print(f"  {row['板块名称']:15s} "
                      f"{row['涨跌幅']:>6.2f}%  "
                      f"上涨/下跌:{row['上涨家数']:>3}/{row['下跌家数']:<3}")

            # 统计
            print(f"\n{'='*70}")
            print(f"【统计概览】")
            print(f"  上涨板块: {len(df_concept[df_concept['涨跌幅'] > 0]):3} 个")
            print(f"  下跌板块: {len(df_concept[df_concept['涨跌幅'] < 0]):3} 个")
            print(f"  平均涨幅: {df_concept['涨跌幅'].mean():>6.2f}%")
            print(f"  中位涨幅: {df_concept['涨跌幅'].median():>6.2f}%")

            # 分析轮动信号
            print(f"\n{'='*70}")
            print("【轮动信号分析】")

            top_sectors = top10['板块名称'].tolist()[:3]
            bottom_sectors = bottom10['板块名称'].tolist()[:3]

            # 科技相关
            tech_keywords = ['芯片', '半导体', '人工智能', 'AI', '云计算', '5G', '新能源', '光伏', '锂电池']
            tech_leading = any(any(kw in sector for kw in tech_keywords) for sector in top_sectors)

            # 防御性板块
            defensive_keywords = ['银行', '保险', '公用事业', '食品', '医药', '消费']
            defensive_leading = any(any(kw in sector for kw in defensive_keywords) for sector in top_sectors)

            if tech_leading:
                print("  ✅ 进攻信号 - 科技/成长板块领涨")
            elif defensive_leading:
                print("  ⚠️  防御信号 - 防御性板块领涨")
            else:
                print("  ➡️  中性信号 - 板块轮动不明显")

            print(f"\n  领涨板块: {', '.join(top_sectors)}")
            print(f"  领跌板块: {', '.join(bottom_sectors)}")

        else:
            print("✗ 数据为空\n")

    except Exception as e:
        print(f"✗ 获取失败: {type(e).__name__}: {str(e)}\n")

    # 2. 行业板块
    print(f"\n{'='*70}")
    print("\n【行业板块排行】\n")
    try:
        df_industry = ak.stock_board_industry_name_em()

        if df_industry is not None and len(df_industry) > 0:
            print(f"✓ 成功获取 {len(df_industry)} 个行业板块\n")

            print("📈 涨幅 TOP 10:")
            print("-" * 70)
            top10 = df_industry.nlargest(10, '涨跌幅')
            for idx, row in top10.iterrows():
                print(f"  {row['板块名称']:15s} "
                      f"{row['涨跌幅']:>6.2f}%  "
                      f"上涨/下跌:{row['上涨家数']:>3}/{row['下跌家数']:<3}")

            print("\n📉 跌幅 TOP 10:")
            print("-" * 70)
            bottom10 = df_industry.nsmallest(10, '涨跌幅')
            for idx, row in bottom10.iterrows():
                print(f"  {row['板块名称']:15s} "
                      f"{row['涨跌幅']:>6.2f}%  "
                      f"上涨/下跌:{row['上涨家数']:>3}/{row['下跌家数']:<3}")
        else:
            print("✗ 数据为空\n")

    except Exception as e:
        print(f"✗ 获取失败: {type(e).__name__}: {str(e)}\n")

    print(f"\n{'='*70}")
    print("提示: 建议在交易日 9:30-15:00 运行以获取最准确数据")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    try:
        get_sector_data()
    except KeyboardInterrupt:
        print("\n\n用户中断")
    except Exception as e:
        print(f"\n错误: {e}")
