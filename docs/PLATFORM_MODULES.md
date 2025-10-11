# 金融工具平台 - 功能模块规划

根据现有的Python脚本功能，整合到Web平台

---

## 📊 现有功能模块

### 1. 美股市场分析 (✅ 已完成)
**Python**: `scripts/us_stock_analysis/run_us_analysis.py`
**页面**: `/index-analysis` - IndexAnalysis.vue

**功能**:
- Phase 1/2/3渐进式分析
- 多指数支持(SPX, NASDAQ, NDX, VIX, DJI, RUT)
- VIX恐慌指数分析
- 行业轮动分析(11个行业ETF)
- 成交量分析
- 智能仓位建议

### 2. VIX恐慌指数专页 (🚧 规划中)
**Python**: `scripts/market_indicators/run_vix_analysis.py`
**页面**: `/vix-analysis` - VixAnalysis.vue

**功能**:
- VIX历史走势图
- VIX分位数分析(30d/60d/252d/1260d)
- VIX-SPX相关性分析
- 恐慌等级判断
- 历史恐慌事件标记
- 交易信号

### 3. 行业轮动专页 (🚧 规划中)
**Python**: `scripts/us_stock_analysis/run_us_analysis.py` (Phase 3部分)
**页面**: `/sector-rotation` - SectorRotation.vue

**功能**:
- 11个行业ETF实时表现
- 行业相对强度雷达图
- 行业轮动模式识别(进攻/防守/周期)
- 行业表现排名
- 行业配置建议
- 历史行业表现对比

### 4. 历史回测 (🚧 规划中)
**Python**: `scripts/trading_strategies/run_backtest.py`
**页面**: `/backtest` - Backtest.vue

**功能**:
- 策略回测配置
- 回测结果展示(收益曲线、最大回撤)
- 交易记录详情
- 策略指标统计(夏普比率、盈亏比)
- 策略对比

### 5. 港股分析 (🚧 扩展功能)
**Python**: `scripts/hk_stock_analysis/run_hk_analysis.py`
**页面**: `/hk-analysis` - HKAnalysis.vue

**功能**:
- 恒生指数/恒生科技分析
- 南向资金流向
- 港股AH股溢价
- 估值分析

### 6. A股点位分析 (🚧 扩展功能)
**Python**: `scripts/position_analysis/run_position_analysis.py`
**页面**: `/cn-analysis` - CNAnalysis.vue

**功能**:
- 上证/深证/创业板分析
- 北向资金流向
- 估值百分位
- 行业轮动

### 7. 均线偏离度监控 (🚧 扩展功能)
**Python**: `scripts/position_analysis/run_ma_deviation_monitor.py`
**页面**: `/ma-monitor` - MAMonitor.vue

**功能**:
- MA5/MA10/MA20/MA60偏离度
- 偏离度预警
- 历史偏离度分布
- 回归信号

### 8. 共振策略 (🚧 扩展功能)
**Python**: `scripts/trading_strategies/run_resonance_strategy.py`
**页面**: `/resonance` - ResonanceStrategy.vue

**功能**:
- 多指标共振信号
- 共振历史回测
- 信号强度评分

---

## 🎯 优先级规划

### Phase 1: 核心功能(当前阶段)
- [x] 美股指数分析页面
- [ ] VIX恐慌指数专页
- [ ] 行业轮动专页
- [ ] 历史回测页面

### Phase 2: 扩展市场
- [ ] 港股分析
- [ ] A股分析

### Phase 3: 高级功能
- [ ] 均线偏离度监控
- [ ] 共振策略
- [ ] 自定义策略编辑器

---

## 📱 导航结构建议

```
金融工具平台
├── 🇺🇸 美股市场
│   ├── 指数分析 (/index-analysis) ✅
│   ├── VIX恐慌指数 (/vix-analysis)
│   ├── 行业轮动 (/sector-rotation)
│   └── 历史回测 (/backtest)
├── 🇭🇰 港股市场
│   └── 港股分析 (/hk-analysis)
├── 🇨🇳 A股市场
│   └── A股分析 (/cn-analysis)
├── 🛠️ 工具
│   ├── 均线偏离监控 (/ma-monitor)
│   └── 共振策略 (/resonance)
└── 📚 文档 (/docs)
```

---

## 🔄 后端API需求

### 现有API (FastAPI)
- ✅ `GET /api/indices` - 获取指数列表
- ✅ `POST /api/analyze/single` - 单指数分析
- ✅ `POST /api/analyze/multiple` - 多指数分析

### 需要新增的API

**VIX分析**:
- `GET /api/vix/current` - VIX当前状态
- `GET /api/vix/history` - VIX历史数据
- `GET /api/vix/percentiles` - VIX分位数

**行业轮动**:
- `GET /api/sectors/current` - 当前行业表现
- `GET /api/sectors/history` - 历史行业数据
- `GET /api/sectors/rotation` - 轮动模式分析

**回测**:
- `POST /api/backtest/run` - 运行回测
- `GET /api/backtest/results/{id}` - 获取回测结果
- `GET /api/backtest/list` - 回测历史记录

**港股/A股**:
- `POST /api/hk/analyze` - 港股分析
- `POST /api/cn/analyze` - A股分析

---

## 💡 实现建议

### 1. 前端组件复用

**已创建**:
- `MetricCard.vue` - 指标卡片
- `LineChart.vue` - 折线图

**需要创建**:
- `RadarChart.vue` - 雷达图(行业轮动)
- `BarChart.vue` - 柱状图(行业排名)
- `PercentileChart.vue` - 分位数图(VIX)
- `EquityCurve.vue` - 权益曲线(回测)
- `TradeTable.vue` - 交易记录表

### 2. 状态管理

**现有Stores**:
- `market.ts` - 市场数据

**建议新增**:
- `vix.ts` - VIX数据
- `sector.ts` - 行业数据
- `backtest.ts` - 回测数据

### 3. 国际化

所有新页面都要支持中英文，参考现有的 `locales/zh-CN.ts` 和 `locales/en-US.ts`

---

## 🚀 下一步行动

### 立即开始
1. 完善VIX分析页面
2. 完善行业轮动页面
3. 完善历史回测页面

### 后续计划
- 扩展到港股/A股市场
- 添加更多技术指标
- 实现自定义策略功能

---

**目标**: 打造一个功能完整、易用的金融分析工具平台！🎯
