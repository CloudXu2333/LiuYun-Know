@echo off
REM LiuYun-Know Backend Development Server
REM Windows 启动脚本

echo ========================================
echo Starting LiuYun-Know Backend Server
echo ========================================
echo.


REM 检查 .env 文件
if not exist ".env" (
    echo [WARNING] .env file not found!
    echo Please create .env file based on CONFIG_GUIDE.md
    echo.
    pause
)

REM 激活虚拟环境
call venv\Scripts\activate.bat

REM 检查依赖
echo Checking dependencies...
python -c "import fastapi" 2>nul
if errorlevel 1 (
    echo [ERROR] Dependencies not installed!
    echo Please run: pip install -r requirements.txt
    pause
    exit /b 1
)

echo.
echo ========================================
echo Server starting at http://localhost:8001
echo API Docs: http://localhost:8001/docs
echo ========================================
echo.
echo Press Ctrl+C to stop the server
echo.

REM 启动服务器
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8001

pause

