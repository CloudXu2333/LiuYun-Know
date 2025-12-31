@echo off
echo Starting Celery Worker...
echo.
echo Multi-worker mode with Redis distributed lock:
echo   - Multiple workers can run simultaneously
echo   - Same knowledge base tasks are processed sequentially (via Redis lock)
echo   - Different knowledge base tasks can be processed in parallel
echo.
echo Usage:
echo   run_celery.bat           - Start one worker
echo   run_celery.bat 3         - Start 3 workers
echo.

set NUM_WORKERS=%1
if "%NUM_WORKERS%"=="" set NUM_WORKERS=1

if %NUM_WORKERS%==1 (
    echo Starting 1 worker...
    celery -A app.core.celery_app worker --loglevel=info --pool=solo
) else (
    echo Starting %NUM_WORKERS% workers...
    for /L %%i in (1,1,%NUM_WORKERS%) do (
        start "Celery Worker %%i" cmd /k "cd /d %~dp0 && celery -A app.core.celery_app worker --loglevel=info --pool=solo -n worker%%i@%%h"
    )
    echo.
    echo Started %NUM_WORKERS% workers in separate windows.
)
