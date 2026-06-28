@echo off
setlocal
cd /d "%~dp0"

echo [skysh] Starting Redis container...
docker compose up -d redis
if errorlevel 1 (
  echo [skysh] Redis start failed. Make sure Docker Desktop is running.
  pause
  exit /b 1
)

echo [skysh] Opening worker and app windows...
start "skysh ingestion" cmd /k call "%~dp0run_ingestion.cmd"
start "skysh snapshot worker" cmd /k call "%~dp0run_snapshot_worker.cmd"
start "skysh backend" cmd /k call "%~dp0run_backend.cmd"
start "skysh frontend" cmd /k call "%~dp0run_frontend.cmd"

echo [skysh] Done.
echo [skysh] Frontend: http://127.0.0.1:5173
echo [skysh] Backend:  http://127.0.0.1:8000
pause

