# LiuYun-Know 配置指南

## 📝 环境变量配置

### 后端配置文件

在 `backend` 目录下创建 `.env` 文件，内容如下：

```env
# ========================================
# LiuYun-Know 环境配置
# ========================================

# ========================================
# 应用配置
# ========================================
APP_NAME=LiuYun-Know
APP_VERSION=1.0.0
DEBUG=True
API_PREFIX=/api

# ========================================
# 安全配置（必填）
# ========================================
# 生成方式: python -c "import secrets; print(secrets.token_urlsafe(32))"
SECRET_KEY=your-super-secret-key-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# ========================================
# 数据库配置
# ========================================
# SQLite 数据库路径
DATABASE_URL=sqlite+aiosqlite:///./data/sqlite/liuyun_know.db

# ========================================
# Redis 配置
# ========================================
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# ========================================
# MinIO 对象存储配置
# ========================================
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET_NAME=liuyun-know
MINIO_SECURE=False

# ========================================
# Chroma 向量数据库配置
# ========================================
CHROMA_HOST=localhost
CHROMA_PORT=8000
CHROMA_PERSIST_DIRECTORY=./data/chroma

# ========================================
# Neo4j 图数据库配置
# ========================================
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password

# ========================================
# Celery 消息队列配置
# ========================================
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# ========================================
# 对话模型 API 配置（必填）
# ========================================
# OpenAI API Key（对话用）
OPENAI_API_KEY=sk-your-openai-api-key-here
OPENAI_API_BASE=https://api.openai.com/v1
DEFAULT_MODEL=gpt-3.5-turbo

# 如果使用国内API或其他兼容服务，可修改 OPENAI_API_BASE
# 例如：
# OPENAI_API_BASE=https://api.deepseek.com/v1
# DEFAULT_MODEL=deepseek-chat

# ========================================
# Embedding 模型 API 配置（推荐千问）
# ========================================
# 千问 API Key（Embedding 专用，推荐）
QWEN_API_KEY=sk-your-qwen-api-key-here
QWEN_API_BASE=https://dashscope.aliyuncs.com/compatible-mode/v1
EMBEDDING_MODEL=text-embedding-v4

# 注：如果不配置 QWEN_API_KEY，会使用对话模型的 API 生成 Embedding
# 但千问 Embedding 价格便宜10倍，强烈推荐单独配置！

# ========================================
# 文档解析 API 配置（可选）
# ========================================
# Firecrawl API Key（用于网页爬取）
FIRECRAWL_API_KEY=

# Tavily API Key（用于实时搜索）
TAVILY_API_KEY=

# ========================================
# CORS 配置
# ========================================
# 允许的前端源
CORS_ORIGINS=http://localhost:5173,http://localhost:3000

# ========================================
# PaddlePaddle 配置（可选）
# ========================================
# 是否使用GPU
USE_GPU=False
# OCR 语言
OCR_LANG=ch
```

---

## 🔑 必填配置项

在启动项目前，必须配置以下项：

### 1. SECRET_KEY（必填）

用于 JWT Token 签名的密钥。

**生成方法：**

```bash
# 方法1: 使用 Python
python -c "import secrets; print(secrets.token_urlsafe(32))"

# 方法2: 使用 OpenSSL
openssl rand -base64 32
```

**示例：**
```env
SECRET_KEY=xMpCQmRyb3N0YXRpY19rZXlfZm9yX3Byb2R1Y3Rpb24
```

### 2. OPENAI_API_KEY（必填）

对话模型的 API 密钥，用于 AI 对话功能。

**获取方法：**

1. 访问 https://platform.openai.com/api-keys
2. 创建新的 API Key
3. 复制到 `.env` 文件

**示例：**
```env
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**使用国内替代服务：**

如果无法访问 OpenAI，可以使用兼容 OpenAI API 的国内服务：

```env
# DeepSeek（推荐，性价比高）
OPENAI_API_BASE=https://api.deepseek.com/v1
OPENAI_API_KEY=your-deepseek-api-key
DEFAULT_MODEL=deepseek-chat

# 或 智谱 AI
OPENAI_API_BASE=https://open.bigmodel.cn/api/paas/v4
OPENAI_API_KEY=your-zhipu-api-key
DEFAULT_MODEL=glm-4

# 或 通义千问
OPENAI_API_BASE=https://dashscope.aliyuncs.com/compatible-mode/v1
OPENAI_API_KEY=your-qwen-api-key
DEFAULT_MODEL=qwen-turbo
```

### 3. QWEN_API_KEY（强烈推荐）

千问 API 密钥，专门用于 Embedding（向量化）功能。

**为什么要单独配置 Embedding？**

- ✅ **价格便宜**：千问 Embedding 仅 0.7元/百万tokens，OpenAI 要 10元
- ✅ **效果好**：针对中文优化
- ✅ **速度快**：国内访问快
- ✅ **灵活配置**：对话和 Embedding 可以用不同服务

**获取千问 API Key：**

1. 访问 https://dashscope.console.aliyun.com/
2. 登录/注册阿里云账号
3. 点击 "API-KEY 管理"
4. 创建新的 API Key
5. 复制到 `.env` 文件

**示例配置：**

```env
# 对话用 DeepSeek（便宜）
OPENAI_API_KEY=your-deepseek-key
OPENAI_API_BASE=https://api.deepseek.com/v1
DEFAULT_MODEL=deepseek-chat

# Embedding 用千问（更便宜）
QWEN_API_KEY=your-qwen-key
QWEN_API_BASE=https://dashscope.aliyuncs.com/compatible-mode/v1
EMBEDDING_MODEL=text-embedding-v4
```

**注意：** 如果不配置 `QWEN_API_KEY`，系统会使用 `OPENAI_API_KEY` 生成 Embedding，但价格会贵很多。

详细配置说明请查看：[千问 Embedding 配置指南](backend/QWEN_EMBEDDING_GUIDE.md)

---

## 🔧 可选配置项

### Redis 配置

如果 Redis 不在默认端口或需要密码：

```env
REDIS_HOST=your-redis-host
REDIS_PORT=6380
REDIS_PASSWORD=your-redis-password
```

### MinIO 配置

如果使用远程 MinIO 或修改了默认配置：

```env
MINIO_ENDPOINT=your-minio-endpoint:9000
MINIO_ACCESS_KEY=your-access-key
MINIO_SECRET_KEY=your-secret-key
MINIO_SECURE=True  # 使用 HTTPS
```

### Neo4j 配置

如果修改了 Neo4j 密码：

```env
NEO4J_URI=bolt://your-neo4j-host:7687
NEO4J_PASSWORD=your-new-password
```

---

## 📂 数据目录配置

### 创建数据目录

项目需要以下数据目录：

```bash
# 在项目根目录下执行
mkdir -p data/sqlite
mkdir -p data/chroma
mkdir -p data/minio
mkdir -p data/neo4j
```

### 目录结构

```
LiuYun-Know/
├── data/
│   ├── sqlite/           # SQLite 数据库文件
│   ├── chroma/           # Chroma 向量数据库
│   ├── minio/            # MinIO 本地存储（如果不用Docker）
│   └── neo4j/            # Neo4j 数据（如果不用Docker）
```

---

## 🐳 Docker 配置

### docker-compose.yml 配置说明

项目已包含 `docker-compose.yml`，默认配置：

| 服务 | 端口 | 默认账号 |
|------|------|----------|
| Redis | 6379 | 无需认证 |
| MinIO | 9000, 9001 | minioadmin / minioadmin |
| Neo4j | 7474, 7687 | neo4j / password |

### 修改 Docker 配置

如需修改默认配置，编辑 `docker-compose.yml`:

```yaml
# 修改 MinIO 密码
minio:
  environment:
    MINIO_ROOT_USER: your-username
    MINIO_ROOT_PASSWORD: your-password

# 修改 Neo4j 密码
neo4j:
  environment:
    NEO4J_AUTH: neo4j/your-new-password
```

修改后，同步更新 `backend/.env` 中的对应配置。

---

## 🔐 生产环境配置

### 安全加固

在生产环境部署时，务必修改以下配置：

```env
# 关闭调试模式
DEBUG=False

# 使用强密钥
SECRET_KEY=your-very-strong-random-secret-key-at-least-32-chars

# 限制 CORS 源
CORS_ORIGINS=https://yourdomain.com

# 使用 HTTPS
MINIO_SECURE=True

# 设置强密码
REDIS_PASSWORD=your-strong-redis-password
NEO4J_PASSWORD=your-strong-neo4j-password
```

### 数据库配置

生产环境建议使用 PostgreSQL 替代 SQLite：

```env
# PostgreSQL 配置
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/liuyun_know
```

---

## 📋 配置检查清单

在启动项目前，请确认：

- [ ] 已创建 `backend/.env` 文件
- [ ] 已设置 `SECRET_KEY`（必填）
- [ ] 已设置 `OPENAI_API_KEY`（必填）
- [ ] 已创建 `data/sqlite` 目录
- [ ] Docker 服务已启动（`docker-compose up -d`）
- [ ] Redis 可连接（端口 6379）
- [ ] MinIO 可访问（端口 9000/9001）
- [ ] Neo4j 可访问（端口 7474/7687）

---

## 🧪 配置验证

### 1. 验证 Redis 连接

```bash
# 使用 redis-cli
redis-cli ping
# 应该返回: PONG
```

### 2. 验证 MinIO 连接

访问 http://localhost:9001
- 用户名: minioadmin
- 密码: minioadmin

### 3. 验证 Neo4j 连接

访问 http://localhost:7474
- 用户名: neo4j
- 密码: password

### 4. 验证后端配置

```bash
cd backend
python -c "from app.config import settings; print(settings.secret_key[:10] + '...')"
# 应该显示你的 SECRET_KEY 的前10个字符
```

---

## ❓ 常见配置问题

### Q1: 找不到 .env 文件

**解决方案：**
```bash
cd backend
# 手动创建文件
touch .env  # Linux/Mac
# type nul > .env  # Windows

# 然后复制上面的配置内容到文件中
```

### Q2: SECRET_KEY 不生效

**可能原因：**
- 文件名错误（应该是 `.env` 不是 `env.txt`）
- 文件位置错误（应该在 `backend/` 目录下）
- 配置格式错误（不要有引号或空格）

**正确格式：**
```env
SECRET_KEY=xMpCQmRyb3N0YXRpY19rZXk
# 不要写成：
# SECRET_KEY = "xMpCQmRyb3N0YXRpY19rZXk"
```

### Q3: OpenAI API 连接失败

**可能原因：**
1. API Key 错误或过期
2. 余额不足
3. 网络无法访问 OpenAI（国内）
4. API Base URL 配置错误

**解决方案：**
```env
# 1. 检查 API Key 是否正确
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxx

# 2. 如果在国内，使用代理或国内服务
OPENAI_API_BASE=https://api.deepseek.com/v1
DEFAULT_MODEL=deepseek-chat

# 3. 检查 API 余额
# 访问 https://platform.openai.com/usage
```

### Q4: 数据库初始化失败

**解决方案：**
```bash
# 确保数据目录存在
mkdir -p data/sqlite

# 检查目录权限
chmod 755 data/sqlite

# 删除旧数据库（如果存在）
rm data/sqlite/liuyun_know.db

# 重启后端服务
```

---

## 📚 相关文档

- [快速启动指南](./QUICKSTART.md)
- [系统架构文档](./ARCHITECTURE.md)
- [项目总结](./PROJECT_SUMMARY.md)

---

## 💡 配置建议

### 开发环境

```env
DEBUG=True
OPENAI_API_BASE=https://api.openai.com/v1
DEFAULT_MODEL=gpt-3.5-turbo  # 更经济
```

### 测试环境

```env
DEBUG=True
DEFAULT_MODEL=gpt-3.5-turbo
# 使用测试专用的 API Key
```

### 生产环境

```env
DEBUG=False
DEFAULT_MODEL=gpt-4-turbo  # 更好的质量
CORS_ORIGINS=https://yourdomain.com  # 限制来源
SECRET_KEY=<强随机密钥>
```

---

**配置完成后，即可按照 [快速启动指南](./QUICKSTART.md) 启动项目！🚀**

