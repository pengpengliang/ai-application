# LangChain 后端服务器

基于 FastAPI 构建的 LangChain 应用后端服务器，支持文档处理和智能聊天功能。

## 核心功能

- 📄 **文档上传与处理**：支持 TXT、DOC、DOCX 格式文件
- 💬 **带历史记录的聊天**：为每个会话维护独立的对话历史
- 🔍 **文档问答**：使用 RAG（检索增强生成）技术查询上传的文档
- 🚀 **流式响应**：通过 Server-Sent Events (SSE) 实时返回 AI 回复
- 📊 **会话管理**：创建和管理多个独立的聊天会话

## 技术栈

- **FastAPI**：现代、高性能的 Web 框架
- **LangChain**：开发语言模型应用的框架
- **Chroma**：用于文档检索的向量数据库
- **Uvicorn**：运行 FastAPI 的 ASGI 服务器

## 安装步骤

```bash
# 安装依赖
uv pip install -r requirements.txt

# 或使用 uv（推荐）
uv sync
```

## 启动服务器

```bash
python main.py
```

服务器将在 `http://localhost:8000` 启动

## API 接口

### 会话管理

#### 创建会话
```http
POST /chat_session/create
```

**响应：**
```json
{
  "session_id": "uuid-string"
}
```

### 聊天功能

#### 流式聊天
```http
POST /chat/stream
Content-Type: multipart/form-data
```

**表单数据：**
- `session_id`: 会话 ID
- `input_text`: 用户输入内容

**响应：** Server-Sent Events (SSE) 流，实时返回 AI 回复

### 文件上传

#### 上传文档
```http
POST /upload/
Content-Type: multipart/form-data
```

**表单数据：**
- `file`: 上传的文件（txt/doc/docx 格式）
- `session_id`: 会话 ID
- `process_method`: 处理方法（"basic"）

### 聊天历史

#### 获取聊天历史
```http
GET /chat-history/{session_id}
```

**响应：**
```json
{
  "session_id": "uuid-string",
  "message_count": 5,
  "has_document": true,
  "messages": [
    {
      "content": "你好",
      "type": "human",
      "timestamp": "2024-01-01T00:00:00Z"
    }
  ]
}
```

### 健康检查

```http
GET /health
```

**响应：**
```json
{
  "status": "healthy"
}
```

## 文档处理流程

服务器处理上传文档的步骤：
1. **文本分割**：使用递归字符分割，块大小为 1024
2. **摘要生成**：为每个文档块生成摘要
3. **向量存储**：将文档嵌入存储在 Chroma 向量数据库中
4. **检索查询**：根据用户查询检索相关文档块

## 系统架构

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  客户端     │────>│  FastAPI    │────>│  LangChain  │
│  （浏览器）  │     │  服务器     │     │  处理链     │
└─────────────┘     └─────────────┘     └─────────────┘
          │                     │
          ▼                     ▼
┌─────────────┐     ┌─────────────┐
│  聊天历史   │     │  文档存储   │
└─────────────┘     └─────────────┘
```

## 开发计划

### 短期任务
- [ ] 完善 DOC/DOCX 文件处理功能（如支持表格、图片等）
- [ ] 添加文件大小限制
- [ ] 添加错误处理和日志记录

### 中期任务
- [ ] 集成 Redis 存储会话历史
- [ ] 实现文档缓存机制
- [ ] 添加文档版本管理

## 配置说明

### 环境变量

- `DASHSCOPE_API_KEY`: 阿里云百炼 API 密钥

## 注意事项

- 默认情况下，聊天历史存储在内存中。生产环境建议使用 Redis。
- 文档处理在内存中进行。对于大型文档，建议使用任务队列。
- 服务器包含 CORS 头，允许前端应用跨域请求。

## 许可证

MIT