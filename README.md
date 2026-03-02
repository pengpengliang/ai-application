# LangChain Vue 项目

## 项目简介

这是一个基于 Vue 3 和 LangChain 构建的 AI 应用项目，集成了大语言模型能力，提供了聊天机器人和翻译工具等功能。项目采用现代化的前端技术栈，实现了前后端分离的架构设计。

## 使用的技术栈

### 前端技术
- **Vue 3**: 渐进式 JavaScript 框架，使用 Composition API 和 `<script setup>` 语法
- **TypeScript**: 类型安全的 JavaScript 超集
- **Vite**: 下一代前端构建工具
- **Element Plus**: 基于 Vue 3 的 UI 组件库
- **Vue Router 5**: Vue.js 官方路由管理器
- **Pinia**: Vue 官方状态管理库
- **Less**: CSS 预处理器

### AI 技术
- **LangChain**: 大语言模型应用开发框架
- **@langchain/openai**: OpenAI 模型集成
- **通义千问**: 阿里云大语言模型

### 后端技术（具体见 backend-server 目录）
- **Python**: 后端服务开发语言
- **FastAPI**: 基于 Python 的现代 Web 框架，用于构建 API 服务
- **CORS**: 跨域资源共享中间件
- **Axios**: HTTP 客户端
- **SSE (Server-Sent Events)**: 服务器推送事件，实现流式响应


### 核心功能
1. **翻译工具**
- ✅ 支持中文与英文、日文、韩文、法文、德文、西班牙文、葡萄牙文、俄文之间的互译
- ✅ 基于 LangChain 实现的链式调用流程
- ✅ 实时翻译结果展示
- ✅ 加载状态提示

2. **聊天机器人**
- ✅ 左侧聊天列表：支持新增、删除、修改会话，快速查看历史记录
- ✅ 中间对话区：实时展示聊天记录，并具备上下文记忆能力
- ✅ 流式响应：实现打字机效果，实时显示 AI 回复内容
- ✅ 异步生成器：使用 `async*` 和 `yield` 实现高效的流处理
- ✅ 请求后端API获取聊天历史
- ✅ 文档上传：支持用户上传文档，用于 RAG 功能
- ✅ 左侧聊天列表 API 接口开发
- 🚧 知识库管理前端界面与后台接口
- ✅ RAG (检索增强生成) 功能：基于上传的文档，实现对用户问题的上下文理解和回答
- 🚧 预检索优化：
  1. **优化索引**：摘要索引、父子索引、假设性问题索引、元数据索引
  2. **查询优化**：Multi-Query多路召回、Enrich完善问题、Decomposition问题分解
- 🚧 检索优化：混合检索
  1. **向量检索**: 基于向量相似度的检索，适用于语义理解和上下文相关的问题
  2. **关键字检索**: 基于关键词匹配的检索，适用于简单的文本查询
  3. **全文检索**: 基于文档内容的检索，适用于需要全面匹配的场景
  4. **SQL检索**: 基于数据库查询的检索，适用于需要结构化数据的问题
- 🚧 后检索优化：
  1. **重排序**：根据相关性和上下文重要性对检索结果进行排序
  2. **RAG-Fusion**：将向量检索、关键字检索、全文检索、SQL检索的结果进行融合，生成最终的回答
  3. **上下文压缩和过滤**：对检索结果进行压缩，过滤掉irrelevant信息
- 🚧 RAG应用的评估（RAGas）
  1. **检索评估**
  2. **响应评估**

### 基础架构
- Vue 3 + TypeScript 项目结构搭建
- Vite 开发环境配置
- Element Plus UI 组件集成
- Vue Router 路由配置
- Pinia 状态管理
- 环境变量配置

## 项目使用

### 环境要求
- Node.js >= 18.0.0
- npm >= 9.0.0

### 安装依赖

```bash
npm install
```

### 配置环境变量

在项目根目录创建 `.env` 文件，并配置以下内容：

```env
VITE_API_KEY=阿里云百炼 API 密钥
```

### 构建生产版本

```bash
npm run build
```

### 预览生产构建

```bash
npm run preview
```

## 项目结构

```
src/
├── assets/          # 静态资源
├── components/      # 公共组件
├── router/         # 路由配置
├── services/       # 业务服务
├── stores/         # 状态管理
├── types/          # TypeScript 类型定义
├── utils/          # 工具函数
├── views/          # 页面组件
│   ├── tools/      # 工具页面
│   │   ├── ChatRobot.vue
│   │   └── TranslateTool.vue
│   └── Home.vue
├── App.vue         # 根组件
├── main.ts         # 入口文件
└── style.css       # 全局样式
```

## 开发规范

- 使用 Composition API 和 `<script setup>` 语法
- 遵循 TypeScript 类型安全原则
- 采用 Element Plus 组件库实现 UI
- 保持代码风格统一
- 编写清晰的注释和文档

## 贡献指南

欢迎提交 Issue 和 Pull Request 来改进项目。

## 许可证

MIT License