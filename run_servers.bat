@echo off
title Labotik Service Starter
echo ==========================================================
echo           INICIADOR DE SERVIDORES - LABOTIK
echo ==========================================================
echo.

echo [1/2] Iniciando Backend (FastAPI en Puerto 8000)...
start "Labotik Backend (FastAPI)" cmd /k "cd backend && uvicorn app.main:app --reload --port 8000"

echo.
echo [2/2] Iniciando Frontend (Django en Puerto 3000)...
start "Labotik Frontend (Django)" cmd /k "cd frontend && python manage.py runserver 3000"

echo.
echo ==========================================================
echo  Servidores iniciados en ventanas independientes:
echo  - Backend API:    http://127.0.0.1:8000/docs
echo  - Frontend App:   http://127.0.0.1:3000/
echo ==========================================================
echo.
pause
