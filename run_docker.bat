@echo off
cd /d %~dp0
echo Building and running Docker containers...
docker compose -f docker/docker-compose.yml up --build 