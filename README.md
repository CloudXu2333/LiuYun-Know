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
- **Docker 部署** - 支持 Docker Compose 一键部署

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

### 方式一：Docker Compose 部署（推荐）

```bash
# 克隆项目
git clone https://github.com/yourusername/liuyun_know.git
cd liuyun_know

# 启动基础服务（Redis + MinIO）
docker-compose up -d redis minio

# 可选：启动 Neo4j 图数据库（取消注释 docker-compose.yml 中的 neo4j 配置）
# docker-compose up -d neo4j

# 构建并启动完整服务
docker-compose up -d

# 访问服务
# 前端：http://localhost
# 后端 API：http://localhost:8000
# API 文档：http://localhost:8000/docs
# MinIO 控制台：http://localhost:9001 (minioadmin/minioadmin)
# Neo4j 浏览器：http://localhost:7474（如果启用）
```

### 方式二：本地开发

#### 后端安装

**Windows:**

```bash
cd backend

# 创建虚拟环境
python -m venv venv
venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
copy .env.example .env
# 编辑 .env 填入必要配置

# 初始化数据库（首次运行）
python init_db.py

# 启动服务
run_dev.bat
# 或
python -m uvicorn app.main:app --reload --port 8000
```

**Linux/Mac:**

```bash
cd backend

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖（使用清华源）
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 填入必要配置

# 初始化数据库（首次运行）
python init_db.py

# 启动服务
./run_dev.sh
# 或
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 启动 Celery Worker

**Windows:**

```bash
# 启动单个 worker
run_celery.bat

# 启动多个 worker（如 3 个）
run_celery.bat 3
```

**Linux/Mac:**

```bash
# 启动单个 worker
./run_celery.sh

# 启动多个 worker（如 3 个）
./run_celery.sh 3
```

#### 前端安装

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
# 或
./run_dev.sh  # Linux/Mac
```

访问 http://localhost:5173

### 默认管理员账号

首次运行 `init_db.py` 会创建默认管理员账号：
- 用户名：`admin`
- 密码：`admin111`
- 邮箱：`admin@outlook.com`
- ⚠️ 请登录后立即修改密码！

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

## 🔧 常见问题

### 1. Embedding 维度错误

如果遇到 "Embedding dimension mismatch" 错误，说明使用的 embedding 模型维度与配置不符。

**解决方案**：
- 确保 `EMBEDDING_MODEL` 配置正确（如 `text-embedding-v4` 是 1024 维）
- 代码已自动适配不同维度，如有问题请检查 [requirements.txt](backend/requirements.txt) 中的模型配置

### 2. Neo4j 数据库创建警告

看到类似警告：
```
WARNING: This Neo4j instance does not support creating databases.
Fallback to use the default database.
```

**说明**：Neo4j 社区版不支持多数据库，但系统会自动回退到默认数据库，并使用 workspace 标签隔离不同知识库的数据，功能完全正常。

**解决**：
- 忽略此警告即可，不影响使用
- 或升级到 Neo4j 企业版以支持多数据库

### 3. SOCKS 代理错误

如果使用 SOCKS5 代理时遇到 "socksio package not installed" 错误：

**解决方案**：
```bash
# 安装 socksio
pip install socksio

# 或临时取消代理
unset HTTP_PROXY HTTPS_PROXY ALL_PROXY
```

### 4. pip 源速度慢

推荐使用国内镜像源：

```bash
# 清华源（推荐）
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

# 或阿里云源
pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/
```

### 5. Celery Worker 无法启动

**检查 Redis 连接**：
```bash
# 确保 Redis 正在运行
docker-compose ps redis
redis-cli ping  # 应返回 PONG
```

**查看 Celery 日志**：
```bash
# Linux
tail -f logs/celery_worker1.log

# Windows
# 查看 Celery Worker 窗口输出
```

### 6. Docker 镜像构建失败

如果遇到网络问题：

```bash
# 使用国内镜像加速
# 编辑 /etc/docker/daemon.json
{
  "registry-mirrors": [
    "https://mirror.ccs.tencentyun.com"
  ]
}

# 重启 Docker
sudo systemctl restart docker
```

## 📦 Docker 部署说明

### Neo4j 图数据库（可选）

如果需要使用知识图谱功能，可以启用 Neo4j：

```bash
# 1. 编辑 docker-compose.yml，取消注释 neo4j 服务
# 2. 修改密码（将 your_neo4j_password 替换为强密码）

# 3. 启动 Neo4j
docker-compose up -d neo4j

# 4. 等待服务启动（约 30 秒）
docker-compose logs -f neo4j

# 5. 访问 Neo4j 浏览器
open http://localhost:7474

# 6. 登录（用户名: neo4j，密码: your_neo4j_password）

# 7. 配置后端 .env 文件
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_neo4j_password
```

**生产环境建议：**
- 使用强密码
- 调整内存限制（根据服务器配置）
- 启用 SSL/TLS
- 定期备份 `neo4j_data` 卷

### 构建镜像

```bash
# 构建后端镜像
docker build -t liuyun-backend:test ./backend

# 构建前端镜像
docker build -t liuyun-frontend:test ./frontend
```

### 使用本地构建的镜像

修改 `docker-compose.yml`，取消注释 `build` 配置：

```yaml
backend:
  build:
    context: ./backend
    dockerfile: Dockerfile
  image: liuyun-backend:test
  # ... 其他配置
```

### 查看日志

```bash
# 查看所有服务日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f backend
docker-compose logs -f celery-worker
docker-compose logs -f redis
docker-compose logs -f neo4j  # 如果启用
```

### 服务管理

```bash
# 停止所有服务
docker-compose stop

# 停止特定服务
docker-compose stop backend

# 重启服务
docker-compose restart

# 删除所有服务（保留数据）
docker-compose down

# 删除所有服务和数据卷（⚠️ 会删除数据）
docker-compose down -v
```

## 🆚 更新日志

### v1.0.0

- ✅ 添加 Docker Compose 部署支持
- ✅ 添加 Linux/Mac 启动脚本
- ✅ 优化 embedding 维度适配（支持 1024/1536 维）
- ✅ 修复 Neo4j 数据库创建警告
- ✅ 添加 SOCKS 代理支持
- ✅ 优化依赖管理，清理未使用的包
- ✅ 更新默认管理员密码为 `admin111`

## 🙏 致谢

本项目参考了以下优秀开源项目：

- [LightRAG](https://github.com/HKUDS/LightRAG) - 知识库 RAG 核心实现，知识图谱 + 向量检索混合方案，环境配置请参考该项目文档
- [Yuxi-Know](https://github.com/xerrors/Yuxi-Know) - 项目架构思路参考

## 📝 License

MIT