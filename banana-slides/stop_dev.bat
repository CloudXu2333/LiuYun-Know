@echo off
REM 停止 Banana-Slides 开发服务器

echo ========================================
echo Stopping Banana-Slides Servers
echo ========================================
echo.

REM 停止后端服务器 (监听 0.0.0.0:5001)
echo Stopping backend server on 0.0.0.0:5001...
for /f "tokens=5" %%a in ('netstat -aon ^| find ":5001" ^| find "LISTENING"') do (
    taskkill /F /PID %%a 2>nul
)

REM 停止前端服务器 (监听 0.0.0.0:5174)
echo Stopping frontend server on 0.0.0.0:5174...
for /f "tokens=5" %%a in ('netstat -aon ^| find ":5174" ^| find "LISTENING"') do (
    taskkill /F /PID %%a 2>nul
)

echo.
echo [SUCCESS] All servers stopped!
echo.