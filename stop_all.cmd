@echo off
setlocal
cd /d "%~dp0"

echo [skysh] Stopping app processes on ports 5173 and 8000...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ports = 5173,8000; foreach ($port in $ports) { Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue | Where-Object { $_.State -eq 'Listen' -and $_.OwningProcess -ne 0 } | ForEach-Object { Write-Host ('Stopping PID ' + $_.OwningProcess + ' on port ' + $port); Stop-Process -Id $_.OwningProcess -Force } }"

echo [skysh] Stopping ingestion and snapshot worker Python processes...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "Get-CimInstance Win32_Process | Where-Object { $_.Name -match 'python' -and $_.CommandLine -match 'skysh_kulab.ingestion.main|app.snapshot_worker|uvicorn' } | ForEach-Object { Write-Host ('Stopping PID ' + $_.ProcessId + ' ' + $_.CommandLine); Stop-Process -Id $_.ProcessId -Force }"

echo [skysh] Closing run command windows...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'cmd.exe' -and $_.CommandLine -match 'run_ingestion.cmd|run_snapshot_worker.cmd|run_backend.cmd|run_frontend.cmd' } | ForEach-Object { Write-Host ('Closing command window PID ' + $_.ProcessId); Stop-Process -Id $_.ProcessId -Force }"

echo [skysh] Stopping Redis container...
docker compose stop redis

echo [skysh] Done.
pause
