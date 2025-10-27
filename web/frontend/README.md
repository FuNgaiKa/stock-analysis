# 金融工具平台 - 前端 / Financial Tools Platform - Frontend

[![Vue](https://img.shields.io/badge/Vue-3.3-brightgreen.svg)](https://vuejs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.2-blue.svg)](https://www.typescriptlang.org/)
[![Element Plus](https://img.shields.io/badge/Element%20Plus-2.3-409EFF.svg)](https://element-plus.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

A professional financial analysis platform built with Vue 3 + TypeScript + Element Plus.

基于 Vue 3 + TypeScript + Element Plus 构建的专业金融分析平台。

## ✨ Features / 特性

- 🎯 **Multi-Index Analysis** - Support SPX, NASDAQ, NDX, VIX, DJI, RUT
  多指数分析 - 支持标普500、纳斯达克等6大指数

- 🔥 **VIX Panic Index** - Real-time fear gauge analysis
  VIX恐慌指数 - 实时恐慌情绪分析

- 🔄 **Sector Rotation** - 11 major sector ETF tracking
  行业轮动 - 跟踪11个主要行业ETF

- 📊 **Deep Analysis** - Phase 1/2/3 progressive analysis modes
  深度分析 - Phase 1/2/3渐进式分析模式

- 🌍 **Internationalization** - Support English & Simplified Chinese
  国际化 - 支持英语和简体中文

- 🌓 **Dark Mode** - Beautiful dark theme
  暗黑模式 - 精美的暗黑主题

- 📱 **Responsive** - Mobile-friendly design
  响应式 - 移动端友好设计

## 🚀 Quick Start / 快速开始

### Prerequisites / 前置要求

- Node.js >= 16.0.0
- npm >= 8.0.0

### Installation / 安装

```bash
# Install dependencies / 安装依赖
npm install

# Start development server / 启动开发服务器
npm run dev

# Build for production / 生产构建
npm run build

# Preview production build / 预览生产构建
npm run preview
```

### Configuration / 配置

Create `.env.development` for development:
```
VITE_API_URL=http://localhost:8000
VITE_APP_TITLE=金融工具平台
```

Create `.env.production` for production:
```
VITE_API_URL=https://your-api-domain.com
VITE_APP_TITLE=Financial Tools Platform
```

## 📦 Tech Stack / 技术栈

### Core / 核心
- **Vue 3.3** - Progressive JavaScript Framework
- **TypeScript 5.2** - Typed JavaScript
- **Vite 4.4** - Next Generation Frontend Tooling

### UI & Components / UI组件
- **Element Plus 2.3** - Vue 3 UI Library
- **ECharts 5.4** - Data Visualization
- **Element Plus Icons** - Icon Set

### State & Routing / 状态路由
- **Vue Router 4.2** - Official Router
- **Pinia 2.1** - State Management
- **Vue I18n 9.4** - Internationalization

### HTTP & Utils / HTTP工具
- **Axios 1.5** - HTTP Client

## 📁 Project Structure / 项目结构

```
frontend/
├── public/              # Static assets / 静态资源
├── src/
│   ├── assets/         # Assets (images, styles) / 资源文件
│   │   └── styles/     # Global styles / 全局样式
│   ├── components/     # Components / 组件
│   │   ├── layout/     # Layout components / 布局组件
│   │   ├── charts/     # Chart components / 图表组件
│   │   ├── cards/      # Card components / 卡片组件
│   │   └── analysis/   # Analysis components / 分析组件
│   ├── views/          # Pages / 页面
│   │   ├── IndexAnalysis.vue     # Index analysis / 指数分析
│   │   ├── VixAnalysis.vue       # VIX analysis / VIX分析
│   │   ├── SectorRotation.vue    # Sector rotation / 行业轮动
│   │   ├── Backtest.vue          # Backtest / 历史回测
│   │   └── Docs.vue              # Docs / 文档
│   ├── router/         # Router config / 路由配置
│   ├── stores/         # Pinia stores / 状态管理
│   ├── services/       # API services / API服务
│   ├── locales/        # i18n language files / 国际化语言文件
│   ├── types/          # TypeScript types / TypeScript类型
│   ├── App.vue         # Root component / 根组件
│   └── main.ts         # Entry point / 入口文件
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
└── README.md
```

## 🌐 API Integration / API集成

This frontend connects to the FastAPI backend at `/api`:

前端通过 `/api` 连接到FastAPI后端:

- `GET /api/indices` - Get supported indices / 获取支持的指数
- `POST /api/analyze/single` - Single index analysis / 单指数分析
- `POST /api/analyze/multiple` - Multiple indices analysis / 多指数分析

## 🎨 Features / 功能特性

### 1. Internationalization (i18n) / 国际化

Supports English and Simplified Chinese with auto-detection based on browser language.

支持英语和简体中文，根据浏览器语言自动检测。

```typescript
// Usage in components / 组件中使用
<template>
  <h1>{{ $t('menu.indexAnalysis') }}</h1>
</template>

<script setup>
import { useI18n } from 'vue-i18n'
const { t } = useI18n()
</script>
```

### 2. Dark Mode / 暗黑模式

Automatic dark mode with system preference detection and manual toggle.

自动暗黑模式，支持系统偏好检测和手动切换。

### 3. Responsive Design / 响应式设计

Mobile-first responsive layout that works on all devices.

移动优先的响应式布局，适配所有设备。

## 📚 Development / 开发

### Code Style / 代码风格

- Use TypeScript for type safety / 使用TypeScript保证类型安全
- Follow Vue 3 Composition API / 遵循Vue 3 组合式API
- Use Element Plus components / 使用Element Plus组件

### Adding New Pages / 添加新页面

1. Create component in `src/views/`
2. Add route in `src/router/index.ts`
3. Add menu item in `src/components/layout/Sidebar.vue`
4. Add i18n keys in `src/locales/`

## 🚢 Deployment / 部署

### Vercel (Recommended / 推荐)

```bash
# Build / 构建
npm run build

# Deploy to Vercel / 部署到Vercel
vercel --prod
```

### Other Platforms / 其他平台

- **Netlify**: Supports Vite out of the box / 开箱即用支持Vite
- **GitHub Pages**: Use `vite build` and deploy `dist/` / 构建并部署dist目录
- **Docker**: See `Dockerfile` for containerization / 参见Dockerfile

## 📄 License / 许可证

MIT License

## 🤝 Contributing / 贡献

Contributions are welcome! Please open an issue or submit a PR.

欢迎贡献！请提issue或提交PR。

## 📧 Contact / 联系

- GitHub: [@your-username](https://github.com/your-username)
- Email: your-email@example.com

---

**Made with ❤️ using Vue 3**
