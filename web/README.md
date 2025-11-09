# 📦 Web 平台目录

> **状态**: 已归档，不维护
> **优化日期**: 2025-11-10
> **node_modules**: 已删除（节省283MB）

---

## 🗂️ 目录说明

```
web/
├── frontend/          # Vue 3 前端（源码保留，依赖已删除）
│   ├── src/           # Vue源码
│   ├── package.json   # 依赖配置
│   └── [node_modules 已删除，节省283MB]
│
└── api/               # FastAPI 后端
    └── main.py        # 美股分析API
```

---

## 🔄 如何恢复开发

如果未来需要重启Web平台开发：

### 1. 恢复前端依赖

```bash
cd web/frontend
npm install
# 或使用更快的 pnpm
pnpm install
```

**预计时间**: 3-5分钟（取决于网速）
**空间需求**: ~283MB

### 2. 启动开发服务器

```bash
# 前端
cd web/frontend
npm run dev
# 访问 http://localhost:3000

# 后端
cd web/api
python main.py
# API文档: http://localhost:8000/docs
```

---

## 💡 优化说明

### 为什么删除 node_modules？

1. **占用空间大**: 283MB（占项目58%）
2. **可重建**: `npm install` 随时恢复
3. **不应提交**: 已在 .gitignore 中

### 保留了什么？

- ✅ 所有源码（src/）
- ✅ 所有配置（package.json, vite.config.ts, tsconfig.json）
- ✅ Git历史
- ✅ README和文档

### 丢失了什么？

- ❌ 无，node_modules可完全重建

---

## 📊 技术栈

### 前端
- Vue 3.3.4
- TypeScript 5.2.2
- Element Plus 2.3.12
- ECharts 5.4.3
- Vite 4.4.9

### 后端
- FastAPI
- yfinance
- pandas

---

## 🔖 项目背景

这是一个**美股/港股/A股**可视化分析平台，包含：
- 📊 多指数历史点位分析
- 😱 VIX恐慌指数监控
- 🔄 行业轮动雷达图
- 📈 策略回测可视化

**当前状态**: 已迁移至 `russ_trading/` 作为主力工具

---

**优化者**: Claude Code
**日期**: 2025-11-10
