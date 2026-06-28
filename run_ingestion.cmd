@echo off
cd /d "%~dp0"
set "PYTHONPATH=%CD%\src;%CD%"
python -m skysh_kulab.ingestion.main run

