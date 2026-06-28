@echo off
cd /d "%~dp0"
set "PYTHONPATH=%CD%\src;%CD%"
echo [Redis]
python -m skysh_kulab.ingestion.main ping-redis
echo.
echo [Snapshot worker one-shot]
python -m app.snapshot_worker once
echo.
echo [Backend markets]
powershell -NoProfile -Command "try { Invoke-RestMethod http://127.0.0.1:8000/api/markets | ConvertTo-Json -Compress } catch { Write-Host $_.Exception.Message; exit 1 }"

