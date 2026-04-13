# RAG Agent - 智能知识库助手

基于 RAG (Retrieval-Augmented Generation) 技术的智能对话系统</b><br>
  支持文档上传、向量检索和智能问答，采用自适应查询重写策略


---

## 功能特性

-  **智能对话** - 基于 LangGraph 的多轮对话管理，支持会话隔离和历史记录
-  **文档管理** - 支持 PDF、Word、TXT、Markdown、代码文件等多种格式
-  **自适应 RAG** - 智能查询重写（Step-back + HyDE），提升检索质量
-  **向量检索** - 基于 Milvus 的高效相似度搜索
-  **持久化存储** - PostgreSQL 存储对话历史，支持多用户会话
-  **现代前端** - React + TypeScript + Tailwind CSS

---

## 技术栈

### 后端
| 技术 | 用途 |
|------|------|
| [FastAPI](https://fastapi.tiangolo.com/) | Web 框架 |
| [LangGraph](https://langchain-ai.github.io/langgraph/) | AI 工作流编排 |
| [LangChain](https://python.langchain.com/) | LLM 应用开发 |
| [Milvus](https://milvus.io/) | 向量数据库 |
| [PostgreSQL](https://www.postgresql.org/) | 关系数据库 |
| [SQLAlchemy](https://www.sqlalchemy.org/) | ORM 框架 |

### 前端
| 技术 | 用途 |
|------|------|
| [React 18](https://react.dev/) | UI 框架 |
| [TypeScript](https://www.typescriptlang.org/) | 类型安全 |
| [Vite](https://vitejs.dev/) | 构建工具 |
| [Tailwind CSS](https://tailwindcss.com/) | 样式框架 |
| [Lucide React](https://lucide.dev/) | 图标库 |

### 基础设施
| 技术 | 用途 |
|------|------|
| [Docker](https://www.docker.com/) | 容器化 |
| [uv](https://docs.astral.sh/uv/) | Python 包管理 |

---

## 快速开始

### 前置要求

- Python 3.12+
- Node.js 18+
- Docker & Docker Compose

### 1. 克隆项目

```bash
git clone https://github.com/yourusername/rag-agent.git
cd rag-agent
```

### 2. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env` 文件，填入你的 API 密钥：

```env
# LLM 配置 (支持 OpenAI、Moonshot 等)
OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4

# Embedding 配置 (支持 DashScope 等)
EMBEDDING_API_KEY=your_embedding_key_here
EMBEDDING_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
EMBEDDING_MODEL=text-embedding-v3

# 数据库配置
DATABASE_URL=postgresql://rag_user:rag_password@localhost:5432/rag_db
MILVUS_HOST=localhost
MILVUS_PORT=19530
```

### 3. 启动基础设施

```bash
docker-compose -f docker/docker-compose.yml up -d
```

等待 30-60 秒，检查服务状态：

```bash
docker ps
```

### 4. 安装依赖

**Python 依赖（使用 uv）：**

```bash
# 安装 uv（如果尚未安装）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 安装项目依赖
uv sync
```

**前端依赖：**

```bash
cd frontend
npm install
```

### 5. 启动服务

**启动后端：**

```bash
# 在项目根目录执行
uvicorn backend.api.main:app --host 0.0.0.0 --port 8000 --reload
```


**启动前端（新终端）：**

```bash
cd frontend
npm run dev
```

### 6. 访问系统

| 服务 | 地址 |
|------|------|
| 前端界面 | http://localhost:5173 |
| API 文档 | http://localhost:8000/docs |
| 健康检查 | http://localhost:8000/health |

---

## 项目结构

```
rag-agent/
├── backend/                 # 后端服务
│   ├── api/                # FastAPI 接口
│   │   ├── main.py         # 应用入口
│   │   ├── models.py       # 数据模型
│   │   └── routes/         # API 路由
│   │       ├── chat.py     # 对话接口
│   │       └── documents.py # 文档接口
│   ├── src/                # 核心业务逻辑
│   │   ├── agent.py        # AI Agent 主逻辑
│   │   ├── rag_graph.py    # RAG 工作流
│   │   ├── document_processor.py  # 文档处理
│   │   ├── embeddings.py   # 向量嵌入
│   │   ├── text_splitter.py       # 文本分块
│   │   └── document_loaders.py    # 文档加载
│   ├── db/                 # 数据库层
│   │   ├── models/         # ORM 模型
│   │   ├── repositories/   # 数据仓库
│   │   └── services/       # 业务服务
│   └── milvus/             # Milvus 客户端
├── frontend/               # React 前端
│   ├── src/
│   │   ├── api/            # API 客户端
│   │   ├── components/     # 可复用组件
│   │   ├── pages/          # 页面组件
│   │   ├── types/          # TypeScript 类型
│   │   └── utils/          # 工具函数
│   └── package.json
├── docker/                 # Docker 配置
│   └── docker-compose.yml
├── scripts/                # 工具脚本
│   ├── run_api.py
│   └── ingest.py
├── tests/                  # 测试文件
├── pyproject.toml          # Python 项目配置
├── uv.lock                 # 依赖锁定文件
└── .env.example            # 环境变量示例
```

---

## 使用方法

### 上传文档

1. 打开前端界面 http://localhost:5173
2. 进入"文档管理"页面
3. 拖拽或点击上传文件（支持 PDF、Word、TXT、Markdown 等）
4. 设置分块大小和重叠参数
5. 点击"开始导入"

### 智能对话

1. 进入"对话"页面
2. 在输入框中输入问题
3. 系统会自动检索知识库并生成回答
4. 支持多轮对话，自动保存历史记录

### API 调用示例

```bash
# 对话接口
curl -X POST http://localhost:8000/chat/ \
  -H "Content-Type: application/json" \
  -d '{
    "query": "什么是 RAG？",
    "user_id": "user_123",
    "session_id": "session_456"
  }'

# 上传文档
curl -X POST http://localhost:8000/documents/upload \
  -F "file=@document.pdf" \
  -F "chunk_size=1000" \
  -F "chunk_overlap=200"

# 获取文档统计
curl http://localhost:8000/documents/stats
```

---

## RAG 工作流程

```
用户查询
    |
    v
初始检索 (Milvus 向量搜索)
    |
    v
文档评分 ──→ 相关性足够 ──→ 生成答案
    |
    v
查询重写 (Step-back / HyDE)
    |
    v
扩展检索 ──→ 合并结果 ──→ 生成答案
```

**查询重写策略：**

- **Step-back**: 退一步思考，从通用概念层面提问
- **HyDE**: 生成假设的理想回答文档，用于扩展检索
- **Complex**: 组合策略，结合 Step-back + HyDE

---


## 路线图

- [x] 基础 RAG 流程
- [x] 文档上传和管理
- [x] 多轮对话支持
- [x] 自适应查询重写
- [x] 前端界面
- [ ] 用户认证系统
- [ ] 对话分享功能
- [ ] RAG 评估系统
- [ ] 多租户支持
- [ ] 增量文档更新

