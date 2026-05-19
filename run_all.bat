@echo off
title Labotik - Servidores Integrados
cls
echo ===================================================
echo             INICIANDO SERVIDORES LABOTIK
echo ===================================================
echo.

:: 1. Iniciar el Backend (FastAPI) en una nueva ventana
echo [+] Iniciando Backend (FastAPI) en http://127.0.0.1:8000...
start "Labotik - Backend (FastAPI)" cmd /k "cd backend && ..\venv\Scripts\python.exe -m uvicorn app.main:app --reload"

:: 2. Esperar 2 segundos para dar tiempo al backend a iniciar
timeout /t 2 /nobreak >nul

:: 3. Iniciar el Frontend (Django) en la ventana actual
echo [+] Iniciando Frontend (Django) en http://127.0.0.1:8080...
cd frontend
..\venv\Scripts\python.exe manage.py runserver 8080
