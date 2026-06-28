@echo off
cd /d "%~dp0"
docker compose up -d redis
docker ps --filter "name=skysh-kulab-redis"

