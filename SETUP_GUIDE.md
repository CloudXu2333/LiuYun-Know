# LiuYun-Know 快速安装指南

## 📋 目录

- [前置准备](#前置准备)
- [快速开始（5分钟）](#快速开始5分钟)
- [详细步骤](#详细步骤)
- [验证安装](#验证安装)
- [常见问题](#常见问题)

---

## 前置准备

### 必需软件

- ✅ **Python 3.12+** - [下载地址](https://www.python.org/downloads/)
- ✅ **Node.js 18+** - [下载地址](https://nodejs.org/)
- ✅ **Docker Desktop** (可选，用于运行 Redis/MinIO/Neo4j) - [下载地址](https://www.docker.com/products/docker-desktop)

### 检查安装

```bash
# 检查 Python 版本
python --version
# 应该显示: Python 3.12.x 或更高

# 检查 Node.js 版本
node --version
# 应该显示: v18.x.x 或更高

# 检查 npm 版本
npm --version
# 应该显示: 9.x.x 或更高

# 检查 Docker (可选)
docker --version
```

---

## 快速开始（5分钟）

### Windows 用户

```cmd
# 1. 启动 Docker 服务（需要先安装 Docker Desktop）
docker-compose up -d

# 2. 配置后端环境
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# 创建 .env 文件（复制以下内容）
echo SECRET_KEY=your-secret-key-here > .env
echo DATABASE_URL=sqlite+aiosqlite:///./data/sqlite/liuyun_know.db >> .env
echo OPENAI_API_KEY=your-openai-api-key >> .env

# 3. 启动后端
run_dev.bat

# 4. 新开一个终端，启动前端
cd frontend
npm install
npm run dev
```

### Linux/Mac 用户

```bash
# 1. 启动 Docker 服务
docker-compose up -d

# 2. 配置后端环境
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 创建 .env 文件
cat > .env << EOF
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite+aiosqlite:///./data/sqlite/liuyun_know.db
OPENAI_API_KEY=your-openai-api-key
EOF

# 3. 启动后端
chmod +x run_dev.sh
./run_dev.sh

# 4. 新开一个终端，启动前端
cd frontend
npm install
npm run dev
```

---

## 详细步骤

### 步骤 1: 克隆/下载项目

```bash
# 如果使用 Git
git clone <repository-url>
cd LiuYun-Know

# 或直接下载 ZIP 并解压
```

### 步骤 2: 启动 Docker 服务

```bash
# 启动 Redis、MinIO、Neo4j
docker-compose up -d

# 查看服务状态
docker-compose ps

# 应该看到 3 个服务在运行：
# - liuyun-know-redis
# - liuyun-know-minio
# - liuyun-know-neo4j
```

**如果没有 Docker：**

你需要手动安装并启动这些服务：
- Redis: https://redis.io/download
- MinIO: https://min.io/download
- Neo4j: https://neo4j.com/download

### 步骤 3: 配置后端

#### 3.1 创建虚拟环境

```bash
cd backend

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 虚拟环境激活后，命令行前面会显示 (venv)
```

#### 3.2 安装依赖

```bash
# 安装核心依赖
pip install -r requirements.txt

# 这会安装大约 50+ 个包，可能需要 2-5 分钟
```

**如果安装失败：**

```bash
# 尝试升级 pip
python -m pip install --upgrade pip

# 然后重新安装
pip install -r requirements.txt
```

#### 3.3 配置环境变量

在 `backend` 目录下创建 `.env` 文件：

**Windows:**
```cmd
copy nul .env
notepad .env
```

**Linux/Mac:**
```bash
touch .env
nano .env
```

**复制以下内容到 .env 文件：**

```env
# ========================================
# 必填配置
# ========================================

# 安全密钥（请修改为随机字符串）
SECRET_KEY=change-this-to-a-secure-random-key-at-least-32-characters

# 数据库路径
DATABASE_URL=sqlite+aiosqlite:///./data/sqlite/liuyun_know.db

# OpenAI API Key（必填）
OPENAI_API_KEY=your-openai-api-key-here

# ========================================
# 可选配置（使用默认值即可）
# ========================================

# 应用配置
DEBUG=True
API_PREFIX=/api

# Redis 配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# MinIO 配置
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET_NAME=liuyun-know
MINIO_SECURE=False

# Neo4j 配置
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password

# LLM 配置
OPENAI_API_BASE=https://api.openai.com/v1
DEFAULT_MODEL=gpt-3.5-turbo
EMBEDDING_MODEL=text-embedding-ada-002

# CORS 配置
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

**生成安全的 SECRET_KEY:**

```bash
# 方法1: 使用 Python
python -c "import secrets; print(secrets.token_urlsafe(32))"

# 方法2: 使用 OpenSSL (Linux/Mac)
openssl rand -base64 32
```

**获取 OPENAI_API_KEY:**

1. 访问 https://platform.openai.com/api-keys
2. 登录/注册 OpenAI 账号
3. 创建新的 API Key
4. 复制 Key 到 `.env` 文件

**国内用户替代方案：**

如果无法访问 OpenAI，可以使用国内兼容服务：

```env
# DeepSeek (推荐)
OPENAI_API_BASE=https://api.deepseek.com/v1
OPENAI_API_KEY=your-deepseek-api-key
DEFAULT_MODEL=deepseek-chat

# 或 智谱 AI
OPENAI_API_BASE=https://open.bigmodel.cn/api/paas/v4
OPENAI_API_KEY=your-zhipu-api-key
DEFAULT_MODEL=glm-4
```

#### 3.4 创建数据目录

```bash
# 在项目根目录创建数据目录
cd ..
mkdir -p data/sqlite
mkdir -p data/chroma

# 返回 backend 目录
cd backend
```

### 步骤 4: 启动后端服务

#### Windows:

```cmd
# 确保虚拟环境已激活
venv\Scripts\activate

# 启动服务
run_dev.bat
```

#### Linux/Mac:

```bash
# 确保虚拟环境已激活
source venv/bin/activate

# 给脚本执行权限
chmod +x run_dev.sh

# 启动服务
./run_dev.sh
```

#### 或者直接使用 Python:

```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**成功启动后会看到：**

```
🚀 正在启动应用...
✅ 数据库初始化完成
✅ Redis 连接成功
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### 步骤 5: 配置前端

**打开新的终端窗口：**

```bash
# 进入前端目录
cd frontend

# 安装依赖（第一次需要）
npm install

# 这会安装大约 200+ 个包，可能需要 3-5 分钟
```

### 步骤 6: 启动前端服务

```bash
# 在 frontend 目录下
npm run dev
```

**成功启动后会看到：**

```
  VITE v5.0.11  ready in 500 ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
  ➜  press h + enter to show help
```

---

## 验证安装

### 1. 检查服务状态

打开浏览器，访问以下地址：

| 服务 | 地址 | 状态 |
|------|------|------|
| **前端界面** | http://localhost:5173 | 应该看到登录页面 |
| **后端 API** | http://localhost:8000 | 应该显示欢迎信息 |
| **API 文档** | http://localhost:8000/docs | 应该显示 Swagger 文档 |
| **健康检查** | http://localhost:8000/health | 应该返回 `{"status":"healthy"}` |
| **MinIO 控制台** | http://localhost:9001 | 用户名/密码: minioadmin/minioadmin |
| **Neo4j 浏览器** | http://localhost:7474 | 用户名/密码: neo4j/password |

### 2. 测试用户注册

1. 访问 http://localhost:5173
2. 点击"立即注册"
3. 填写信息：
   - 用户名: `testuser`
   - 邮箱: `test@example.com`
   - 密码: `test123456`
4. 点击"注册"
5. 注册成功后会跳转到登录页

### 3. 测试用户登录

1. 使用刚注册的账号登录
2. 登录成功后会进入主界面

### 4. 测试 AI 对话

1. 点击左侧菜单"AI 对话"
2. 输入问题：`你好，请介绍一下自己`
3. 点击发送
4. 应该能看到 AI 的回复

**如果对话失败：**
- 检查 `.env` 文件中的 `OPENAI_API_KEY` 是否正确
- 检查 API Key 是否有余额
- 查看后端日志的错误信息

---

## 常见问题

### Q1: 后端启动失败 - ModuleNotFoundError

**错误信息：**
```
ModuleNotFoundError: No module named 'fastapi'
```

**解决方案：**
```bash
# 确保虚拟环境已激活
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 重新安装依赖
pip install -r requirements.txt
```

### Q2: Redis 连接失败

**错误信息：**
```
ConnectionRefusedError: [Errno 111] Connection refused
```

**解决方案：**
```bash
# 检查 Docker 服务是否运行
docker-compose ps

# 如果没有运行，启动服务
docker-compose up -d redis

# 查看 Redis 日志
docker-compose logs redis
```

### Q3: 数据库初始化失败

**错误信息：**
```
OperationalError: unable to open database file
```

**解决方案：**
```bash
# 创建数据目录
mkdir -p data/sqlite

# 检查目录权限 (Linux/Mac)
chmod 755 data/sqlite

# Windows: 确保当前用户有写入权限
```

### Q4: 前端启动失败 - 端口被占用

**错误信息：**
```
Error: listen EADDRINUSE: address already in use :::5173
```

**解决方案：**
```bash
# 方法1: 修改端口
npm run dev -- --port 5174

# 方法2: 杀掉占用端口的进程
# Windows:
netstat -ano | findstr :5173
taskkill /PID <进程ID> /F

# Linux/Mac:
lsof -ti:5173 | xargs kill -9
```

### Q5: npm install 失败

**错误信息：**
```
npm ERR! network timeout
```

**解决方案：**
```bash
# 切换到淘宝镜像
npm config set registry https://registry.npmmirror.com

# 清理缓存
npm cache clean --force

# 重新安装
npm install
```

### Q6: OpenAI API 调用失败

**错误信息：**
```
AuthenticationError: Incorrect API key provided
```

**解决方案：**

1. **检查 API Key 是否正确**
   - 访问 https://platform.openai.com/api-keys
   - 确认 Key 有效且未过期

2. **检查余额**
   - 访问 https://platform.openai.com/usage
   - 确认账户有余额

3. **使用国内替代服务**
   ```env
   # DeepSeek (性价比高)
   OPENAI_API_BASE=https://api.deepseek.com/v1
   OPENAI_API_KEY=your-deepseek-api-key
   DEFAULT_MODEL=deepseek-chat
   ```

4. **检查网络连接**
   - 如果在国内，可能需要代理
   - 或使用国内兼容的 API 服务

### Q7: Docker 启动失败

**错误信息：**
```
ERROR: Cannot connect to the Docker daemon
```

**解决方案：**

1. **Windows/Mac:**
   - 打开 Docker Desktop 应用
   - 等待 Docker 启动完成（托盘图标不再跳动）

2. **Linux:**
   ```bash
   # 启动 Docker 服务
   sudo systemctl start docker
   
   # 设置开机自启
   sudo systemctl enable docker
   ```

3. **检查 Docker 状态：**
   ```bash
   docker info
   ```

### Q8: 虚拟环境激活失败

**Windows 错误：**
```
无法加载文件 venv\Scripts\Activate.ps1，因为在此系统上禁止运行脚本
```

**解决方案：**
```powershell
# 以管理员身份运行 PowerShell
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser

# 然后重新激活
venv\Scripts\activate
```

**或使用 CMD 而不是 PowerShell：**
```cmd
venv\Scripts\activate.bat
```

---

## 项目目录结构

安装完成后的目录结构：

```
LiuYun-Know/
├── backend/                # 后端项目
│   ├── venv/              # Python 虚拟环境
│   ├── app/               # 应用代码
│   ├── .env               # 环境变量配置（需要创建）
│   ├── requirements.txt   # Python 依赖
│   ├── run_dev.sh         # Linux/Mac 启动脚本
│   └── run_dev.bat        # Windows 启动脚本
├── frontend/              # 前端项目
│   ├── node_modules/      # Node.js 依赖
│   ├── src/               # 源代码
│   ├── package.json       # 前端依赖配置
│   └── vite.config.js     # Vite 配置
├── data/                  # 数据目录
│   ├── sqlite/            # SQLite 数据库
│   └── chroma/            # Chroma 向量数据库
├── docker-compose.yml     # Docker 编排配置
├── SETUP_GUIDE.md         # 本安装指南
├── CONFIG_GUIDE.md        # 配置指南
├── ARCHITECTURE.md        # 架构文档
└── README.md              # 项目说明
```

---

## 下一步

✅ 安装完成后，你可以：

1. 📖 阅读 [系统架构文档](./ARCHITECTURE.md) 了解系统设计
2. 📖 阅读 [配置指南](./CONFIG_GUIDE.md) 了解详细配置
3. 🎨 探索前端界面，熟悉功能
4. 🔧 查看 API 文档: http://localhost:8000/docs
5. 💻 开始开发新功能

---

## 获取帮助

- 📚 查看项目文档目录
- 🐛 提交 Issue 到 GitHub
- 💬 联系项目维护者

**祝你使用愉快！🎉**

