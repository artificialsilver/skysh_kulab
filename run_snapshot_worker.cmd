@echo off
cd /d "%~dp0"
set "PYTHONPATH=%CD%\src;%CD%"
python -m app.snapshot_worker run --interval 30

