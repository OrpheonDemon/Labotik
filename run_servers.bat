@echo off
title Labotik Service Starter
echo ==========================================================
echo           INICIADOR DE SERVIDORES - LABOTIK
echo ==========================================================
echo.

echo [1/3] Verificando Ollama (IA Engine en Puerto 11434)...
netstat -ano | findstr ":11434" >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Ollama ya esta corriendo
) else (
    echo Iniciando Ollama...
    start "Labotik Ollama (IA Engine)" cmd /k "ollama serve"
    timeout /t 2 /nobreak
)

echo.
echo [2/3] Iniciando Backend (FastAPI en Puerto 8000)...
start "Labotik Backend (FastAPI)" cmd /k "venv\Scripts\activate.bat && cd backend && python -m uvicorn app.main:app --reload --port 8000"

echo.
echo [3/3] Iniciando Frontend (Django en Puerto 3000)...
start "Labotik Frontend (Django)" cmd /k "venv\Scripts\activate.bat && cd frontend && python manage.py runserver 3000"

echo.
echo ==========================================================
echo  Servidores iniciados en ventanas independientes:
echo  - Ollama IA:      http://127.0.0.1:11434
echo  - Backend API:    http://127.0.0.1:8000/docs
echo  - Frontend App:   http://127.0.0.1:3000/
echo ==========================================================
echo.
echo NOTA: Asegúrate de haber instalado Ollama primero
echo ejecutando: ollama pull medgemma
echo.
pause
