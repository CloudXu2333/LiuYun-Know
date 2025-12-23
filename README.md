# LiuYun-Know - AI 知识库系统

基于 FastAPI + Vue3 的 AI 驱动智能知识库系统，支持文档解析、向量检索、知识图谱和智能对话。

## 技术栈

### 后端
- **Web 框架**: FastAPI + Python 3.12+
- **认证**: OAuth2 + JWT + Redis
- **数据库**: SQLite (用户数据)
- **对象存储**: MinIO
- **知识存储**: 
  - Chroma (向量数据库)
  - Neo4j (图数据库)
- **智能体框架**: LangGraph
- **文档解析**: 
  - LightRAG
  - PaddlePaddle OCR
  - PP-Structure-V3
  - Firecrawl (网页处理)
- **消息队列**: Celery + Redis
- **搜索增强**: Tavily (实时搜索)

### 前端
- **框架**: Vue.js 3
- **构建工具**: Vite
- **状态管理**: Pinia
- **样式**: TailwindCSS (Gemini 风格设计)
- **路由**: Vue Router
- **HTTP 客户端**: Axios

## 项目结构

```
LiuYun-Know/
├── backend/              # 后端服务
│   ├── app/
│   │   ├── api/         # API 路由
│   │   ├── models/      # 数据库模型
│   │   ├── schemas/     # Pydantic 模型
│   │   ├── services/    # 业务逻辑
│   │   ├── core/        # 核心功能
│   │   ├── tasks/       # Celery 任务
│   │   └── ai/          # AI 功能模块
│   └── requirements.txt
├── frontend/            # 前端项目
│   ├── src/
│   │   ├── views/      # 页面组件
│   │   ├── components/ # 通用组件
│   │   ├── stores/     # 状态管理
│   │   ├── api/        # API 封装
│   │   └── router/     # 路由配置
│   └── package.json
├── data/               # 数据目录
└── docker-compose.yml  # 开发环境编排
```

## 快速开始

### 前置要求

- Python 3.12+
- Node.js 18+
- Redis
- (可选) Docker & Docker Compose

### 1. 克隆项目

```bash
git clone <repository-url>
cd LiuYun-Know
```

### 2. 启动后端

```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 复制环境变量文件（需要配置 API Key）
cp .env.example .env
# 编辑 .env 文件，填入必要的配置

# 启动服务
python -m app.main
```

后端服务将运行在 http://localhost:8000

API 文档: http://localhost:8000/docs

### 3. 启动前端

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端服务将运行在 http://localhost:5173

### 4. 使用 Docker Compose（推荐）

```bash
# 启动所有服务（Redis, MinIO 等）
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

## 功能特性

### ✅ 已实现

- [x] 用户注册与登录（OAuth2 + JWT）
- [x] Token 刷新机制
- [x] Redis 会话管理
- [x] 现代化 UI 设计（Gemini 风格）
- [x] 响应式布局
- [x] 前后端分离架构

### 🚧 开发中

- [ ] AI 对话功能
- [ ] 知识库管理
- [ ] 文档上传与解析
- [ ] 向量检索
- [ ] 知识图谱构建
- [ ] 实时搜索集成

## API 接口

### 认证接口

- `POST /api/auth/register` - 用户注册
- `POST /api/auth/login` - 用户登录
- `POST /api/auth/refresh` - 刷新 token
- `POST /api/auth/logout` - 用户登出
- `GET /api/auth/me` - 获取当前用户信息

### 用户接口

- `GET /api/users/me` - 获取个人信息
- `PUT /api/users/me` - 更新个人信息
- `PUT /api/users/password` - 修改密码

## 配置说明

### 环境变量

在 `backend/.env` 中配置以下环境变量：

```env
# 安全配置
SECRET_KEY=your-secret-key-here

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# LLM API
OPENAI_API_KEY=your-openai-api-key

# Firecrawl API
FIRECRAWL_API_KEY=your-firecrawl-api-key

# Tavily API
TAVILY_API_KEY=your-tavily-api-key
```

## 开发指南

### 后端开发

```bash
cd backend

# 运行测试
pytest

# 代码格式化
black app/

# 代码检查
flake8 app/
```

### 前端开发

```bash
cd frontend

# 构建生产版本
npm run build

# 预览生产构建
npm run preview
```

## 部署

### 后端部署

```bash
cd backend

# 使用 gunicorn 部署
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

### 前端部署

```bash
cd frontend

# 构建
npm run build

# 将 dist/ 目录部署到 Web 服务器
```

## 贡献指南

欢迎提交 Issue 和 Pull Request！

## 许可证

MIT License

## 联系方式

如有问题，请提交 Issue 或联系维护者。

