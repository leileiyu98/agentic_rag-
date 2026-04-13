# RAG Agent React Frontend

基于 React + TypeScript + Tailwind CSS 的 RAG Agent 前端界面。

## 技术栈

- **框架**: React 18
- **语言**: TypeScript
- **构建工具**: Vite
- **样式**: Tailwind CSS
- **图标**: Lucide React
- **HTTP 客户端**: Axios
- **日期处理**: date-fns

## 项目结构

```
frontend-react/
├── public/              # 静态资源
├── src/
│   ├── api/            # API 客户端
│   │   ├── client.ts   # Axios 封装
│   │   └── index.ts
│   ├── components/     # 可复用组件
│   │   ├── Button.tsx
│   │   ├── Input.tsx
│   │   ├── MessageBubble.tsx
│   │   ├── SessionItem.tsx
│   │   ├── StatCard.tsx
│   │   ├── Card.tsx
│   │   ├── Layout/
│   │   │   ├── Layout.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   └── index.ts
│   │   └── index.ts
│   ├── pages/          # 页面组件
│   │   ├── ChatPage.tsx
│   │   ├── DocumentsPage.tsx
│   │   ├── HistoryPage.tsx
│   │   └── index.ts
│   ├── types/          # TypeScript 类型
│   │   └── index.ts
│   ├── utils/          # 工具函数
│   │   ├── helpers.ts
│   │   └── index.ts
│   ├── styles/         # 样式文件
│   │   └── index.css
│   ├── App.tsx         # 主应用组件
│   ├── main.tsx        # 应用入口
│   └── vite-env.d.ts   # Vite 类型声明
├── index.html
├── package.json
├── tsconfig.json
├── tsconfig.app.json
├── tsconfig.node.json
├── tailwind.config.js
└── vite.config.ts
```

## 安装依赖

```bash
cd frontend-react
npm install
```

## 启动开发服务器

```bash
npm run dev
```

访问 http://localhost:5173

## 构建生产版本

```bash
npm run build
```

构建输出位于 `dist/` 目录。

## 功能特性

### 1. 对话页面 (ChatPage)
- 类 ChatGPT 的聊天界面
- 消息气泡展示（用户/助手区分）
- 自动滚动到底部
- 支持 Enter 发送、Shift+Enter 换行
- 对话导出为 Markdown
- 清除当前会话

### 2. 文档管理页面 (DocumentsPage)
- 知识库统计展示
- 支持单文件/目录导入
- 自定义分块大小和重叠
- 集合列表展示

### 3. 历史记录页面 (HistoryPage)
- 会话列表展示
- 关键词搜索对话内容
- 快速打开历史会话

### 4. 设计特点
- Apple Design System 风格
- 圆角设计、大量留白
- 响应式布局
- 精致的阴影和过渡动画

## 环境变量

在项目根目录创建 `.env` 文件：

```env
VITE_API_BASE_URL=http://localhost:8000
```

## API 接口

前端与后端 FastAPI 服务通信，主要接口：

| 接口 | 方法 | 描述 |
|------|------|------|
| `/chat/` | POST | 与 Agent 对话 |
| `/chat/history` | POST | 获取对话历史 |
| `/chat/conversations/{user_id}` | GET | 获取用户会话列表 |
| `/chat/clear` | POST | 清除对话历史 |
| `/chat/search` | POST | 搜索对话内容 |
| `/documents/ingest` | POST | 导入文档 |
| `/documents/stats` | GET | 获取文档统计 |
| `/documents/delete` | POST | 删除文档 |
| `/health` | GET | 健康检查 |

## 组件说明

### Button
可复用的按钮组件，支持多种变体和状态：
- `variant`: 'primary' | 'secondary' | 'ghost'
- `size`: 'sm' | 'md' | 'lg'
- `isLoading`: 加载状态

### MessageBubble
消息气泡组件，自动区分用户和助手消息样式。

### SessionItem
会话列表项组件，展示会话摘要信息。

### StatCard
统计卡片组件，用于展示数据指标。

### Card
通用卡片容器组件。

## 状态管理

使用 React 的 `useState` 和 `useCallback` 进行状态管理：
- 用户 ID（本地存储持久化）
- 当前会话 ID
- 消息列表
- 会话列表

## 后续优化方向

- [ ] 使用 Zustand/Redux 进行状态管理
- [ ] 添加用户认证系统
- [ ] 支持文件上传拖拽
- [ ] 添加消息 Markdown 渲染
- [ ] 支持代码高亮
- [ ] 添加主题切换（深色模式）
- [ ] 消息流式输出
- [ ] 添加单元测试
