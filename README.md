# 股票分析项目

一个专业的股票分析和复合收益计算工具，支持多数据源和技术分析。

## 项目结构

```
stock-analysis/
├── stock/                          # 股票分析模块
│   ├── __init__.py                # 模块初始化
│   ├── stock.py                   # 基础股票分析器
│   ├── enhanced_stock_analyzer.py # 增强版分析器
│   ├── enhanced_data_sources.py   # 多数据源支持
│   ├── joinquant.py              # 聚宽数据源
│   ├── comparison_demo.py        # 功能演示
│   ├── stock.md                  # 股票模块文档
│   ├── joinquant.md              # 聚宽使用说明
│   └── requirements_enhanced.txt # 原始依赖文件
├── compound_interest/             # 复合收益计算模块
│   ├── __init__.py               # 模块初始化
│   └── compound_calculator.py    # 复合收益计算器
├── requirements.txt              # 项目依赖
├── main.py                      # 主入口文件
├── README.md                    # 项目说明
└── .gitignore                   # Git忽略文件
```

## 功能特性

### 股票分析
- **多数据源支持**（Ashare、AKShare、YFinance、Tushare、聚宽）
- **Ashare主力数据源** - 轻量级、高稳定性、完全免费
- 技术指标计算（MA、RSI、MACD、布林带等）
- 市场热度分析
- 数据回测功能
- 可视化图表
- **自动故障切换** - 多数据源备份机制

### 复合收益计算
- 复合利率计算
- 投资收益预测
- 定投收益分析

## 数据源优势

### 🚀 Ashare - 主力数据源
- ✅ **完全免费** - 无需注册、无API限制
- ✅ **极简集成** - 单文件，零配置
- ✅ **高稳定性** - 双核心备份（新浪+腾讯）
- ✅ **实时数据** - 支持分钟级K线
- ✅ **专注A股** - 数据完整性优秀

### 🛡️ 多层备份机制
1. **Ashare** (主力) - 最稳定的免费数据源
2. **AKShare** (备用1) - 原有数据源，功能丰富
3. **新浪财经** (备用2) - 传统稳定接口
4. **网易财经** (备用3) - 补充数据源
5. **Yahoo Finance** (备用4) - 国际市场数据

### 📊 数据质量保证
- 自动数据验证
- 故障自动切换
- 缓存机制优化
- 数据格式统一

## 快速开始

### 1. 创建虚拟环境
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\\Scripts\\activate    # Windows
```

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 运行示例
```bash
python main.py
```

## 使用说明

### 股票分析示例
```python
from stock.enhanced_stock_analyzer import EnhancedStockAnalyzer

# 创建分析器实例
analyzer = EnhancedStockAnalyzer()

# 分析股票
analyzer.analyze_stock("000001", period="1y")
```

### 复合收益计算
```python
from compound_interest.compound_calculator import CompoundCalculator

# 计算复合收益
calculator = CompoundCalculator()
result = calculator.calculate(principal=10000, rate=0.08, years=10)
```

## 配置说明

### API密钥配置
在使用前，请根据需要配置相关API密钥：

1. **Tushare Token**
   - 访问 [Tushare官网](https://tushare.pro/) 注册账户
   - 获取token后在代码中配置

2. **聚宽账户**
   - 访问 [聚宽官网](https://www.joinquant.com/) 注册账户
   - 配置账户信息

### TA-Lib安装说明
TA-Lib库需要额外的系统依赖：

**MacOS:**
```bash
brew install ta-lib
```

**Ubuntu/Debian:**
```bash
sudo apt-get install libta-lib0-dev
```

**Windows:**
下载预编译包或使用conda：
```bash
conda install -c conda-forge ta-lib
```

## 注意事项

- 部分数据源需要注册账户并获取API密钥
- TA-Lib库需要额外的系统依赖，请参考上述安装说明
- 建议使用Python 3.8+版本
- 首次运行需要安装所有依赖，可能需要一些时间
- 股票数据获取可能受到网络和API限制影响

## 常见问题

**Q: TA-Lib安装失败？**
A: 请先安装系统依赖，然后使用pip install TA-Lib

**Q: 无法获取股票数据？**
A: 检查网络连接和API密钥配置

**Q: 模块导入错误？**
A: 确保已激活虚拟环境并安装所有依赖

## 贡献指南

欢迎提交Issue和Pull Request来改进项目！

## 许可证

本项目仅供学习和研究使用。