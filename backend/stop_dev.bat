@echo off
REM 停止 LiuYun-Know 开发服务器

echo ========================================
echo Stopping LiuYun-Know Servers
echo ========================================
echo.

REM 停止后端服务器 (端口 8001)
echo Stopping backend server on port 8001...
for /f "tokens=5" %%a in ('netstat -aon ^| find ":8001" ^| find "LISTENING"') do (
    taskkill /F /PID %%a 2>nul
)

REM 停止前端服务器 (端口 5173)
echo Stopping frontend server on port 5173...
for /f "tokens=5" %%a in ('netstat -aon ^| find ":5173" ^| find "LISTENING"') do (
    taskkill /F /PID %%a 2>nul
)

echo.
echo [SUCCESS] All servers stopped!
echo.