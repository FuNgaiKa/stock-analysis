#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
美股市场分析系统 - Streamlit Web界面
纯Python实现,无需Vue/React
"""

import streamlit as st
import sys
import pandas as pd
from datetime import datetime

sys.path.append('.')

from position_analysis.us_market_analyzer import USMarketAnalyzer, US_INDICES, DEFAULT_US_INDICES

# 页面配置
st.set_page_config(
    page_title="美股市场分析系统",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        color: #1f77b4;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .success-signal {
        color: #28a745;
        font-weight: bold;
    }
    .warning-signal {
        color: #ffc107;
        font-weight: bold;
    }
    .danger-signal {
        color: #dc3545;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# 主标题
st.markdown('<p class="main-header">📊 美股市场分析系统</p>', unsafe_allow_html=True)

# 侧边栏配置
st.sidebar.header("⚙️ 分析配置")

# 指数选择
indices = st.sidebar.multiselect(
    "选择指数",
    options=list(US_INDICES.keys()),
    default=DEFAULT_US_INDICES,
    format_func=lambda x: f"{US_INDICES[x].name} ({x})",
    help="可以选择多个指数进行对比分析"
)

# 分析模式
phase = st.sidebar.radio(
    "分析模式",
    options=['Phase 1', 'Phase 2', 'Phase 3'],
    index=2,
    help="""
    - Phase 1: 基础价格匹配
    - Phase 2: 技术指标增强
    - Phase 3: 多维度深度分析(VIX+行业+成交量)
    """
)

# 相似度容差
tolerance = st.sidebar.slider(
    "相似度容差 (%)",
    min_value=1.0,
    max_value=10.0,
    value=5.0,
    step=0.5,
    help="价格匹配的容差范围,默认±5%"
) / 100

# 分析周期
periods = st.sidebar.multiselect(
    "预测周期(天)",
    options=[5, 10, 20, 60],
    default=[5, 10, 20, 60],
    help="计算未来N日的收益率概率"
)

# 详细分析选项
detail = st.sidebar.checkbox("显示详细信息", value=True)

st.sidebar.markdown("---")

# 关于信息
with st.sidebar.expander("ℹ️ 关于系统"):
    st.markdown("""
    **美股市场分析系统 v3.0**

    基于历史数据的量化投资决策辅助工具

    - 🎯 Phase 1: 基础价格匹配
    - 🔍 Phase 2: 技术指标增强
    - 🚀 Phase 3: 深度分析

    **数据来源**: Yahoo Finance
    **更新频率**: 实时
    """)

# 主要内容区域
if not indices:
    st.warning("⚠️ 请至少选择一个指数进行分析")
    st.stop()

# 运行分析按钮
if st.sidebar.button("🚀 开始分析", type="primary", use_container_width=True):

    # 显示分析配置
    with st.expander("📋 分析配置", expanded=False):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.info(f"**分析指数**: {', '.join([US_INDICES[i].name for i in indices])}")
        with col2:
            st.info(f"**分析模式**: {phase}")
        with col3:
            st.info(f"**相似容差**: ±{tolerance*100:.1f}%")

    # 进度条
    progress_bar = st.progress(0)
    status_text = st.empty()

    try:
        # 初始化分析器
        status_text.text("🔄 初始化分析器...")
        progress_bar.progress(10)

        analyzer = USMarketAnalyzer()

        # 确定分析参数
        use_phase2 = phase in ['Phase 2', 'Phase 3']
        use_phase3 = phase == 'Phase 3'

        # 运行分析
        status_text.text("📊 正在分析数据...")
        progress_bar.progress(30)

        if len(indices) == 1:
            # 单指数详细分析
            result = analyzer.analyze_single_index(
                indices[0],
                tolerance=tolerance,
                periods=periods,
                use_phase2=use_phase2,
                use_phase3=use_phase3
            )
            results_list = [(indices[0], result)]
        else:
            # 多指数联合分析
            multi_result = analyzer.analyze_multiple_indices(
                indices=indices,
                tolerance=tolerance,
                periods=periods,
                use_phase2=use_phase2,
                use_phase3=use_phase3
            )
            results_list = list(multi_result['individual_analysis'].items())

        progress_bar.progress(70)
        status_text.text("✅ 分析完成,正在生成报告...")

        # 显示结果
        progress_bar.progress(100)
        status_text.empty()
        progress_bar.empty()

        st.success("✅ 分析完成!")

        # 遍历每个指数
        for idx_code, analysis in results_list:

            if 'error' in analysis:
                st.error(f"❌ {analysis['index_name']} 分析失败: {analysis['error']}")
                continue

            if 'warning' in analysis:
                st.warning(f"⚠️ {analysis['index_name']}: {analysis['warning']}")
                continue

            # 指数标题
            st.markdown(f"## 📈 {analysis['index_name']}")

            # 当前点位信息
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                change_pct = analysis['current_change_pct']
                delta_color = "normal" if change_pct >= 0 else "inverse"
                st.metric(
                    "当前价格",
                    f"{analysis['current_price']:.2f}",
                    f"{change_pct:+.2f}%",
                    delta_color=delta_color
                )

            with col2:
                st.metric(
                    "数据日期",
                    analysis['current_date']
                )

            with col3:
                st.metric(
                    "相似时期",
                    f"{analysis.get('similar_periods_count', 0)} 个"
                )

            with col4:
                st.metric(
                    "分析模式",
                    phase
                )

            # Phase 2 市场环境
            if 'market_environment' in analysis:
                env = analysis['market_environment']

                with st.expander("🎯 市场环境识别 (Phase 2)", expanded=True):
                    col1, col2, col3, col4 = st.columns(4)

                    with col1:
                        st.metric("环境类型", env['environment'])
                    with col2:
                        st.metric("RSI", f"{env['rsi']:.1f}")
                    with col3:
                        st.metric("距52周高点", f"{env['dist_to_high_pct']:.1f}%")
                    with col4:
                        st.metric("均线状态", env['ma_state'])

            # 周期分析表格
            if 'period_analysis' in analysis and detail:
                with st.expander("📊 各周期分析详情", expanded=True):

                    # 构建数据表
                    table_data = []
                    for period_key in ['5d', '10d', '20d', '60d']:
                        if period_key in analysis['period_analysis']:
                            stats = analysis['period_analysis'][period_key]

                            row = {
                                '周期': period_key.replace('d', '日'),
                                '样本数': stats['sample_size'],
                                '上涨概率': f"{stats['up_prob']:.1%}",
                                '平均收益': f"{stats['mean_return']:+.2%}",
                                '中位收益': f"{stats['median_return']:+.2%}",
                                '置信度': f"{stats.get('confidence', 0):.1%}"
                            }

                            if 'position_advice' in stats:
                                advice = stats['position_advice']
                                row['建议仓位'] = f"{advice['recommended_position']:.1%}"
                                row['操作信号'] = advice['signal']

                            table_data.append(row)

                    if table_data:
                        df_table = pd.DataFrame(table_data)
                        st.dataframe(df_table, use_container_width=True, hide_index=True)

            # 20日核心结论
            if 'period_analysis' in analysis and '20d' in analysis['period_analysis']:
                stats_20d = analysis['period_analysis']['20d']

                st.markdown("### 💡 20日周期核心结论")

                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    up_prob = stats_20d['up_prob']
                    st.metric(
                        "上涨概率",
                        f"{up_prob:.1%}",
                        f"↑{stats_20d['up_count']} ↓{stats_20d['down_count']}"
                    )

                with col2:
                    mean_return = stats_20d['mean_return']
                    st.metric(
                        "预期收益",
                        f"{mean_return:+.2%}",
                        f"中位 {stats_20d['median_return']:+.2%}"
                    )

                with col3:
                    st.metric(
                        "收益区间",
                        f"[{stats_20d['min_return']:.2%}, {stats_20d['max_return']:.2%}]"
                    )

                with col4:
                    confidence = stats_20d.get('confidence', 0)
                    st.metric(
                        "置信度",
                        f"{confidence:.1%}"
                    )

                # 仓位建议
                if 'position_advice' in stats_20d:
                    advice = stats_20d['position_advice']

                    st.markdown("#### 🎯 操作建议")

                    signal = advice['signal']
                    signal_class = "success-signal" if "买入" in signal else "danger-signal" if "卖出" in signal else "warning-signal"

                    st.markdown(f"""
                    <div class="metric-card">
                        <p class="{signal_class}">【{signal}】{advice['description']}</p>
                    </div>
                    """, unsafe_allow_html=True)

                    if 'warning' in advice:
                        st.warning(f"⚠️ {advice['warning']}")

            # Phase 3 深度分析
            if 'phase3_analysis' in analysis:
                phase3 = analysis['phase3_analysis']

                st.markdown("### 🚀 Phase 3 深度分析")

                # VIX分析
                if 'vix' in phase3:
                    with st.expander("🔥 VIX恐慌指数分析", expanded=True):
                        vix = phase3['vix']

                        if 'current_state' in vix:
                            vix_state = vix['current_state']

                            col1, col2, col3, col4 = st.columns(4)

                            with col1:
                                st.metric(
                                    "VIX当前值",
                                    f"{vix_state['vix_value']:.2f}",
                                    f"{vix_state['change']:+.2f}"
                                )

                            with col2:
                                st.metric("VIX状态", vix_state['status'])

                            with col3:
                                st.metric(
                                    "日变化",
                                    f"{vix_state['change_pct']:+.2f}%"
                                )

                            with col4:
                                if 'week_change_pct' in vix_state:
                                    st.metric(
                                        "周变化",
                                        f"{vix_state['week_change_pct']:+.2f}%"
                                    )

                        if 'signal' in vix:
                            vix_signal = vix['signal']
                            st.info(f"""
                            **交易信号**: {vix_signal['signal']}

                            **描述**: {vix_signal['description']}

                            **操作建议**: {vix_signal['action']}
                            """)

                # 行业轮动分析
                if 'sector_rotation' in phase3:
                    with st.expander("🔄 行业轮动分析", expanded=True):
                        sector = phase3['sector_rotation']

                        if 'rotation_pattern' in sector:
                            pattern = sector['rotation_pattern']

                            st.markdown(f"**轮动模式**: {pattern['pattern']}")
                            st.markdown(f"**模式描述**: {pattern['description']}")

                        if 'allocation_recommendation' in sector:
                            alloc = sector['allocation_recommendation']

                            st.markdown(f"**配置建议**: {alloc['recommendation']}")

                            if 'recommended_sectors' in alloc:
                                st.markdown(f"**推荐行业**: {', '.join(alloc['recommended_sectors'])}")

                # 成交量分析
                if 'volume' in phase3:
                    with st.expander("📊 成交量分析", expanded=True):
                        volume = phase3['volume']

                        if 'volume_status' in volume:
                            vol_status = volume['volume_status']

                            col1, col2 = st.columns(2)

                            with col1:
                                st.metric("成交量状态", vol_status['status'])

                            with col2:
                                if 'volume_ratio' in vol_status:
                                    st.metric(
                                        "量比",
                                        f"{vol_status['volume_ratio']:.2f}倍"
                                    )

                            st.info(vol_status['description'])

                        if 'signal' in volume:
                            vol_signal = volume['signal']
                            st.markdown(f"**交易信号**: {vol_signal['signal']}")
                            st.markdown(f"**描述**: {vol_signal['description']}")

            st.markdown("---")

        # 分析完成提示
        st.balloons()

    except Exception as e:
        st.error(f"❌ 分析过程中发生错误: {str(e)}")
        import traceback
        with st.expander("查看错误详情"):
            st.code(traceback.format_exc())

else:
    # 首次访问时的引导
    st.info("""
    ### 👋 欢迎使用美股市场分析系统!

    **使用步骤**:
    1. 👈 在左侧选择要分析的指数
    2. 🎛️ 调整分析参数
    3. 🚀 点击"开始分析"按钮
    4. 📊 查看详细的分析报告

    **系统特色**:
    - ✅ Phase 1/2/3 渐进式分析
    - ✅ 多维度深度分析(VIX+行业+成交量)
    - ✅ 历史回测验证
    - ✅ 智能仓位建议
    """)

    # 显示示例
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("### Phase 1")
        st.markdown("基础价格匹配")
        st.markdown("- 历史点位对比")
        st.markdown("- 概率统计")
        st.markdown("- Kelly仓位")

    with col2:
        st.markdown("### Phase 2")
        st.markdown("技术指标增强")
        st.markdown("- RSI过滤")
        st.markdown("- 市场环境识别")
        st.markdown("- 智能仓位调整")

    with col3:
        st.markdown("### Phase 3")
        st.markdown("多维度深度分析")
        st.markdown("- VIX恐慌指数")
        st.markdown("- 行业轮动")
        st.markdown("- 成交量分析")

# 页脚
st.markdown("---")
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("**📊 数据来源**: Yahoo Finance")

with col2:
    st.markdown("**⏰ 更新频率**: 实时")

with col3:
    st.markdown("**🤖 Powered by**: Python + Streamlit")
