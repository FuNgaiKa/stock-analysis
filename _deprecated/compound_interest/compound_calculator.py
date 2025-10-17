#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
复合收益计算器
输入年化收益率、初始资产，计算n年后的资产总额，并生成可视化图表
"""

import matplotlib.pyplot as plt
import numpy as np
import matplotlib as mpl

# 设置中文字体
mpl.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
mpl.rcParams['axes.unicode_minus'] = False

def calculate_compound_interest(principal, annual_rate, years):
    """
    计算复合收益
    
    Args:
        principal: 初始资产（元）
        annual_rate: 年化收益率（小数，如0.1表示10%）
        years: 投资年数
        
    Returns:
        final_amount: n年后的总资产
    """
    final_amount = principal * (1 + annual_rate) ** years
    return final_amount

def generate_growth_data(principal, annual_rate, years):
    """
    生成资产增长数据
    
    Args:
        principal: 初始资产
        annual_rate: 年化收益率
        years: 年数
        
    Returns:
        years_list: 年份列表
        amounts_list: 对应的资产总额列表
    """
    years_list = list(range(years + 1))
    amounts_list = [principal * (1 + annual_rate) ** year for year in years_list]
    return years_list, amounts_list

def calculate_million_intervals(principal, annual_rate, years):
    """
    计算每赚100万需要多少年
    
    Args:
        principal: 初始资产
        annual_rate: 年化收益率
        years: 总年数
        
    Returns:
        intervals: 每赚100万的时间间隔列表
    """
    intervals = []
    current_target = principal + 1000000  # 第一个100万目标
    
    for year in range(1, years + 1):
        current_amount = principal * (1 + annual_rate) ** year
        
        # 检查是否达到当前目标
        while current_amount >= current_target:
            intervals.append((current_target, year))
            current_target += 1000000  # 下一个100万目标
            
    return intervals

def plot_compound_growth(years_list, amounts_list, principal, annual_rate, years):
    """
    绘制复合收益增长图
    """
    plt.figure(figsize=(12, 8))
    
    # 主图：资产增长曲线
    plt.subplot(2, 1, 1)
    plt.plot(years_list, amounts_list, 'b-', linewidth=2, marker='o', markersize=4)
    plt.title(f'复合收益增长图（年化收益率: {annual_rate*100:.1f}%）', fontsize=16, fontweight='bold')
    plt.xlabel('年份', fontsize=12)
    plt.ylabel('资产总额（元）', fontsize=12)
    plt.grid(True, alpha=0.3)
    
    # 格式化Y轴显示
    plt.gca().yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x/10000:.0f}万'))
    
    # 添加起始点和终点标注
    plt.annotate(f'起始: {principal/10000:.0f}万元', 
                xy=(0, principal), xytext=(years*0.1, principal*1.5),
                arrowprops=dict(arrowstyle='->', color='red'),
                fontsize=10, color='red')
    
    final_amount = amounts_list[-1]
    plt.annotate(f'{years}年后: {final_amount/10000:.0f}万元', 
                xy=(years, final_amount), xytext=(years*0.7, final_amount*0.8),
                arrowprops=dict(arrowstyle='->', color='green'),
                fontsize=10, color='green')
    
    # 子图：每年收益增长
    plt.subplot(2, 1, 2)
    yearly_gains = [amounts_list[i] - amounts_list[i-1] for i in range(1, len(amounts_list))]
    plt.bar(years_list[1:], yearly_gains, color='skyblue', alpha=0.7)
    plt.title('每年收益增长', fontsize=14)
    plt.xlabel('年份', fontsize=12)
    plt.ylabel('年收益（元）', fontsize=12)
    plt.grid(True, alpha=0.3)
    plt.gca().yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x/10000:.0f}万'))
    
    plt.tight_layout()
    plt.show()

def main():
    """主函数"""
    print("=" * 50)
    print("        复合收益计算器")
    print("=" * 50)
    
    try:
        import sys
        # 如果有命令行参数，使用命令行参数；否则使用交互式输入
        if len(sys.argv) == 4:
            principal = float(sys.argv[1])
            annual_rate_percent = float(sys.argv[2])
            years = int(sys.argv[3])
        else:
            # 获取用户输入
            principal = float(input("请输入初始资产（元）: "))
            annual_rate_percent = float(input("请输入年化收益率（%）: "))
            years = int(input("请输入投资年数: "))
        
        # 转换百分比为小数
        annual_rate = annual_rate_percent / 100
        
        print("\n" + "=" * 50)
        print("计算结果:")
        print("=" * 50)
        
        # 计算最终资产
        final_amount = calculate_compound_interest(principal, annual_rate, years)
        total_gain = final_amount - principal
        
        print(f"初始资产: {principal:,.0f} 元 ({principal/10000:.1f}万元)")
        print(f"年化收益率: {annual_rate_percent}%")
        print(f"投资年数: {years} 年")
        print(f"{years}年后总资产: {final_amount:,.0f} 元 ({final_amount/10000:.1f}万元)")
        print(f"总收益: {total_gain:,.0f} 元 ({total_gain/10000:.1f}万元)")
        print(f"收益倍数: {final_amount/principal:.2f}倍")
        
        # 计算每赚100万需要的时间
        million_intervals = calculate_million_intervals(principal, annual_rate, years)
        
        if million_intervals:
            print("\n" + "-" * 30)
            print("每赚100万所需时间:")
            print("-" * 30)
            
            prev_year = 0
            for i, (target_amount, year) in enumerate(million_intervals):
                interval = year - prev_year
                print(f"第{i+1}个100万: {interval} 年 (第{year}年达到{target_amount/10000:.0f}万)")
                prev_year = year
        else:
            print(f"\n在{years}年内未能赚取100万元")
        
        # 生成并绘制图表
        years_list, amounts_list = generate_growth_data(principal, annual_rate, years)
        plot_compound_growth(years_list, amounts_list, principal, annual_rate, years)
        
        # 保存数据到文件
        with open('compound_interest/calculation_result.txt', 'w', encoding='utf-8') as f:
            f.write(f"复合收益计算结果\n")
            f.write(f"=" * 30 + "\n")
            f.write(f"初始资产: {principal:,.0f} 元\n")
            f.write(f"年化收益率: {annual_rate_percent}%\n")
            f.write(f"投资年数: {years} 年\n")
            f.write(f"最终资产: {final_amount:,.0f} 元\n")
            f.write(f"总收益: {total_gain:,.0f} 元\n")
            f.write(f"收益倍数: {final_amount/principal:.2f}倍\n\n")
            
            if million_intervals:
                f.write("每赚100万所需时间:\n")
                prev_year = 0
                for i, (target_amount, year) in enumerate(million_intervals):
                    interval = year - prev_year
                    f.write(f"第{i+1}个100万: {interval} 年\n")
                    prev_year = year
        
        print(f"\n计算结果已保存到 compound_interest/calculation_result.txt")
        
    except ValueError:
        print("输入错误，请输入有效的数字！")
    except Exception as e:
        print(f"发生错误: {e}")

class CompoundCalculator:
    """复合收益计算器类"""

    def calculate(self, principal, annual_rate, years):
        """计算复合收益"""
        return calculate_compound_interest(principal, annual_rate, years)

    def generate_growth_data(self, principal, annual_rate, years):
        """生成增长数据"""
        return generate_growth_data(principal, annual_rate, years)

    def save_result(self, principal, annual_rate, years):
        """保存计算结果到文件"""
        final_amount = self.calculate(principal, annual_rate, years)
        years_list, amounts_list = self.generate_growth_data(principal, annual_rate, years)
        million_intervals = calculate_million_intervals(principal, annual_rate, years)
        save_calculation_result(principal, annual_rate, years, final_amount, million_intervals)
        return final_amount


if __name__ == "__main__":
    main()