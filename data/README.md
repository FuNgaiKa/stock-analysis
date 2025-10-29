# 数据目录说明

## 📁 文件结构

```
data/
├── positions_example.json    # ✅ 示例持仓文件（已提交）
├── positions_YYYYMMDD.json   # ❌ 实际持仓文件（已忽略）
├── cache/                    # ❌ 缓存目录（已忽略）
└── README.md                 # ✅ 本说明文件
```

## 🔧 使用方法

### 1. 首次使用

复制示例文件并修改为你的实际持仓：

```bash
cp data/positions_example.json data/positions_20251029.json
```

然后编辑 `positions_20251029.json`，填入你的实际持仓数据。

### 2. 持仓文件格式

```json
[
  {
    "asset_name": "资产名称",
    "asset_code": "资产代码",
    "asset_key": "资产key（通常与code相同）",
    "position_ratio": 0.28,      // 仓位占比（0-1之间）
    "current_value": 140000      // 当前市值（元）
  }
]
```

### 3. 字段说明

| 字段 | 类型 | 说明 | 示例 |
|-----|------|------|------|
| asset_name | string | 资产名称 | "恒生科技ETF" |
| asset_code | string | 资产代码 | "513180" |
| asset_key | string | 资产key | "513180" |
| position_ratio | float | 仓位占比 | 0.28 (即28%) |
| current_value | float | 当前市值（元） | 140000 |

### 4. 注意事项

- ⚠️ 实际持仓文件（`positions_*.json`）已被 `.gitignore` 忽略，不会被提交到版本控制
- ✅ 每次更新持仓后，建议使用日期命名：`positions_YYYYMMDD.json`
- ✅ 所有 `position_ratio` 之和应该小于等于1（剩余部分为现金）
- ✅ `current_value` 应该反映实时市值（可通过自动脚本更新）

## 🔒 隐私保护

本项目已配置 `.gitignore`，以下敏感数据不会被提交：
- ❌ 实际持仓文件
- ❌ 每日报告（包含实际金额）
- ❌ 敏感配置文件
- ✅ 仅提交示例文件和模板
