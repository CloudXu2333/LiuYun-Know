# LiuYun-Know 流云

一个基于 LangGraph 的智能知识库问答系统，支持 RAG 检索增强生成、联网搜索、MCP 工具调用和长期记忆管理。

## ✨ 核心功能

- **智能对话** - 基于 LangGraph 状态机的多轮对话，支持流式输出
- **知识库管理** - 基于 LightRAG 的知识图谱 + 向量检索混合 RAG
- **联网搜索** - 集成 Tavily/Firecrawl，AI 自动提取搜索关键词
- **MCP 工具** - 支持自定义 MCP (Model Context Protocol) 工具，AI 智能决策调用
- **长期记忆** - 用户级长期记忆存储与检索，支持核心记忆标记
- **上下文压缩** - 自动压缩历史对话，优化 Token 使用
- **多模型支持** - 兼容 OpenAI API 格式，支持 DeepSeek/Claude/GPT/Gemini 等

## 🏗️ 技术架构

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend (Vue 3)                       │
│         Element Plus + Tailwind CSS + Vite                  │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                    Backend (FastAPI)                        │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              LangGraph Agent 状态机                  │   │
│  │  analyze → web_search → kb_query → mcp → generate   │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────────┐    │
│  │ LightRAG │ │ MCP 适配 │ │ 上下文   │ │ 长期记忆   │    │
│  │ 知识图谱 │ │ 工具调用 │ │ 管理器   │ │ 服务      │    │
│  └──────────┘ └──────────┘ └──────────┘ └────────────┘    │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                      存储层                                  │
│   SQLite (数据)  │  Neo4j (图谱)  │  Redis (缓存/队列)      │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 快速开始

### 环境要求

- Python 3.10+
- Node.js 18+
- Redis
- Neo4j (可选，用于知识图谱)

### 后端安装

```bash
cd backend

# 创建虚拟环境
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
copy .env.example .env
# 编辑 .env 填入必要配置

# 初始化数据库（首次运行）
python init_db.py

# 启动服务
python -m uvicorn app.main:app --reload --port 8000
```

首次运行 `init_db.py` 会创建数据库表并生成默认管理员账号：
- 用户名：`admin`
- 密码：`admin`
- ⚠️ 请登录后立即修改密码！

### 前端安装

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

访问 http://localhost:5173

## ⚙️ 环境变量配置

在 `backend/.env` 中配置环境变量。复制 `.env.example` 并修改：

```bash
copy .env.example .env
```

### 必需配置

```bash
# 安全密钥（必须修改）
SECRET_KEY=your-secret-key-here-change-in-production

# 数据库
DATABASE_URL=sqlite+aiosqlite:///./data/sqlite/liuyun_know.db

# Embedding 模型（知识库必需）
QWEN_API_KEY=sk-your-dashscope-api-key
QWEN_API_BASE=https://dashscope.aliyuncs.com/compatible-mode/v1
EMBEDDING_MODEL=text-embedding-v4
```

### 对话模型配置

> **注意**：对话模型的 API Key 可以在前端界面配置，支持用户级和平台级两种方式，无需在 `.env` 中配置。

如需使用 DeepSeek 作为默认模型（可选）：

```bash
DEEPSEEK_API_KEY=sk-your-deepseek-api-key
DEEPSEEK_API_BASE=https://api.deepseek.com
```

### 基础服务配置

```bash
# Redis（缓存和消息队列）
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# Celery 异步任务
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# Neo4j 知识图谱
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_neo4j_password

# MinIO 对象存储
MINIO_ENDPOINT=localhost:9091
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET_NAME=liuyun-know

# PaddleOCR 文档解析（可选）
PADDLEOCR_API_URL=https://xbmbgatds3k3k5d5.aistudio-app.com/layout-parsing
PADDLEOCR_TOKEN=your_paddleocr_token
```

### 可选服务配置

```bash

# 联网搜索（可选）
TAVILY_API_KEY=your-tavily-api-key
FIRECRAWL_API_KEY=your-firecrawl-api-key

# CORS
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

### 模型配置说明

系统支持两种方式配置对话模型：

1. **平台级配置**（管理员）：在管理后台添加，所有用户可用
2. **用户级配置**：用户在前端自行添加自己的 API Key

支持的模型提供商：
- DeepSeek（国内推荐）
- 302.AI（支持 Claude/GPT/Gemini）
- OpenAI
- 其他 OpenAI 兼容 API

## 📁 项目结构

```
├── backend/
│   ├── app/
│   │   ├── ai/              # AI 核心
│   │   │   ├── agent.py     # LangGraph Agent
│   │   │   ├── context_manager.py  # 上下文管理
│   │   │   ├── mcp_adapter.py      # MCP 工具适配
│   │   │   └── llm_manager.py      # LLM 调用
│   │   ├── api/             # API 路由
│   │   ├── models/          # 数据模型
│   │   ├── schemas/         # Pydantic Schema
│   │   └── services/        # 业务服务
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── views/           # 页面组件
│   │   ├── api/             # API 调用
│   │   └── components/      # 通用组件
│   └── package.json
└── README.md
```

## 🔄 Agent 流程

```
┌─────────┐
│ analyze │ 分析问题
└────┬────┘
     ▼
┌────────────┐  用户开启
│ web_search │  ────────→ 联网搜索
└────┬───────┘
     ▼
┌──────────┐   选择知识库
│ kb_query │   ────────→ RAG 检索
└────┬─────┘
     ▼
┌───────────┐  勾选工具
│ mcp_think │  ────────→ AI 决定是否调用
└────┬──────┘
     │ ↔ mcp_act (循环调用)
     ▼
┌──────────┐
│ generate │  整合上下文 + 长期记忆 → 生成回复
└──────────┘
```

## 🛠️ MCP 工具配置

支持 stdio 方式的 MCP Server，配置示例：

```json
{
  "name": "时间工具",
  "command": "uvx",
  "args": ["mcp-server-time"],
  "env": {}
}
```

## � 致谢

本项目参考了以下优秀开源项目：

- [LightRAG](https://github.com/HKUDS/LightRAG) - 知识库 RAG 核心实现，知识图谱 + 向量检索混合方案，环境配置请参考该项目文档
- [Yuxi-Know](https://github.com/xerrors/Yuxi-Know) - 项目架构思路参考

## 📝 License

MIT