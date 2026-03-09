# LangChain 后端服务器

基于 FastAPI 构建的 LangChain 应用后端服务器，支持文档处理和智能聊天功能。

## 核心功能

- � **知识库管理**：创建、删除、更新知识库，支持多文件上传
- � **文档上传与处理**：支持 TXT、DOC、DOCX 格式文件
- 💬 **带历史记录的聊天**：为每个会话维护独立的对话历史
- 🔍 **文档问答**：使用 RAG（检索增强生成）技术查询上传的文档
-  **会话管理**：创建和管理多个独立的聊天会话
- 📝 **聊天历史**：完整记录所有对话内容
- 🛡️ **错误处理**：完善的异常处理和日志记录

## 技术栈

### 核心框架
- **FastAPI**：现代、高性能的 Web 框架
- **LangChain**：开发语言模型应用的框架
- **Chroma**：用于文档检索的向量数据库
- **Uvicorn**：运行 FastAPI 的 ASGI 服务器

### 数据库
- **SQLAlchemy**：ORM 框架，用于数据库操作
- **MySQL**：关系型数据库，存储知识库和会话信息

### 依赖库
- **dashscope**：阿里云百炼 API 客户端
- **python-docx**：处理 DOCX 文件
- **loguru**：日志管理
- **sqlalchemy**：数据库 ORM
- **uvicorn**：ASGI 服务器

## 安装步骤

### 环境准备
- Python 3.13+
- MySQL 8.0+

### 依赖安装
```bash
# 使用 uv（推荐）
uv sync
```

### 数据库配置
1. 创建 MySQL 数据库
2. 修改 `database.py` 中的数据库连接配置

## 启动服务器

```bash
uv run python main.py
```

服务器将在 `http://localhost:8000` 启动

## API 接口

### 知识库管理

#### 创建知识库
```http
POST /api/v1/knowledge-base/create
```

**请求参数：**
- `name`: 知识库名称
- `description`: 知识库描述（可选）

**响应：**
```json
{
  "id": 1,
  "name": "我的知识库",
  "status": "created"
}
```

#### 上传文件到知识库
```http
POST /api/v1/knowledge-base/upload-file
Content-Type: multipart/form-data
```

**表单数据：**
- `knowledge_base_id`: 知识库 ID
- `file`: 上传的文件（txt/doc/docx 格式）

#### 删除知识库
```http
POST /api/v1/knowledge-base/delete
```

**请求参数：**
- `knowledge_base_id`: 知识库 ID

#### 获取知识库列表
```http
GET /api/v1/knowledge-base/list
```

**响应：**
```json
{
  "knowledge_bases": [
    {
      "id": 1,
      "name": "我的知识库",
      "description": "示例知识库"
    }
  ]
}
```

### 会话管理

#### 创建会话
```http
POST /api/v1/chat-session/create
```

**请求参数：**
- `knowledge_base_id`: 关联的知识库 ID（可选）
- `title`: 会话标题（默认："新会话"）

**响应：**
```json
{
  "session_id": "abc123",
  "title": "新会话"
}
```

#### 获取会话列表
```http
GET /api/v1/chat-sessions/list
```

**响应：**
```json
{
  "sessions": [
    {
      "id": "abc123",
      "title": "新会话",
      "kb_id": 1,
      "created_at": "2024-01-01T00:00:00Z",
      "message_count": 5
    }
  ]
}
```

#### 获取会话详情
```http
GET /api/v1/chat-session/{session_id}
```

**响应：**
```json
{
  "session": {
    "id": "abc123",
    "title": "新会话",
    "kb_id": 1
  },
  "messages": [
    {
      "id": 1,
      "role": "user",
      "content": "你好",
      "timestamp": "2024-01-01T00:00:00Z"
    }
  ]
}
```

### 聊天功能

#### 知识库聊天
```http
POST /api/v1/knowledge-base/chat
Content-Type: multipart/form-data
```

**表单数据：**
- `knowledge_base_id`: 知识库 ID
- `query`: 用户查询内容
- `session_id`: 会话 ID（可选）

**响应：**
```json
{
  "status": "success",
  "data": {
    "answer": "这是AI的回答",
    "sources": []
  }
}
```

## 文档处理流程

服务器处理上传文档的完整流程：
1. **文件存储**：按知识库ID分类保存文件到本地文件系统
2. **文档加载**：使用 `MyCustomLoader` 加载不同格式文档
3. **文本分割**：使用递归字符分割，块大小为 1024
4. **增量索引**：通过 SQLRecordManager 实现文档增量更新
5. **向量存储**：将文档嵌入存储在 Chroma 向量数据库中
6. **混合检索**：结合向量检索与 BM25 检索实现混合查询
7. **结果压缩**：使用 LLMChainFilter 过滤无关文档
8. **查询重述**：通过 RePhraseQueryRetriever 优化查询表达

## 系统架构

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  客户端     │────>│  FastAPI    │────>│  LangChain  │
│  （浏览器）  │     │  服务器     │     │  处理链     │
└─────────────┘     └─────────────┘     └─────────────┘
          │                     │                     │
          ▼                     ▼                     ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  MySQL      │     │  Chroma     │     │  文件系统   │
│  数据库     │     │  向量库     │     │  存储       │
└─────────────┘     └─────────────┘     └─────────────┘
```

## 开发计划

### 已完成任务
- ✅ 实现知识库增删改查功能
- ✅ 支持多文件上传到知识库
- ✅ 实现会话管理功能
- ✅ 集成 SQLAlchemy ORM 框架
- ✅ 实现聊天历史记录
- ✅ 添加日志管理功能

### 短期任务
- [ ] 完善 DOC/DOCX 文件处理功能（如支持表格、图片等）
- [ ] 添加文件大小限制

### 中期任务
- [ ] 添加文档版本管理

## 配置说明

### 环境变量

- `DASHSCOPE_API_KEY`: 阿里云百炼 API 密钥

### 数据库配置

在 `util.py` 中修改数据库连接信息：

```python
DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': 'mysql123',
    'database': 'rag_knowledge_db'
}
```

## 注意事项

- 聊天历史存储在 MySQL 数据库中，重启服务器不会丢失
- 文档处理在内存中进行。对于大型文档，建议使用任务队列。
- 服务器默认监听 localhost:8000，可通过修改 main.py 调整端口
- 支持跨域请求，可直接与前端应用集成

## 许可证

MIT