# LiuYun-Know 流云知

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
# 编辑 .env 填入 API Key 等配置

# 启动服务
python -m uvicorn app.main:app --reload --port 8000
```

### 前端安装

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

访问 http://localhost:5173

## ⚙️ 配置说明

### 必需配置

| 配置项 | 说明 |
|--------|------|
| `SECRET_KEY` | JWT 密钥 |
| `DATABASE_URL` | 数据库连接 |
| `OPENAI_API_KEY` | LLM API Key |
| `QWEN_API_KEY` | Embedding 模型 Key |

### 可选配置

| 配置项 | 说明 |
|--------|------|
| `DEEPSEEK_API_KEY` | DeepSeek API（国内推荐） |
| `TAVILY_API_KEY` | 联网搜索 |
| `FIRECRAWL_API_KEY` | 网页抓取 |
| `NEO4J_*` | 知识图谱存储 |

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

## 📝 License

MIT
