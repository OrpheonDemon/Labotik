@echo off
title Labotik Backend Starter
echo ==========================================================
echo         INICIANDO BACKEND - LABOTIK
echo ==========================================================
echo.

echo [1/3] Verificando dependencias...
python -c "import fastapi; import uvicorn; print('FastAPI y Uvicorn OK')" 2>nul
if errorlevel 1 (
    echo ERROR: FastAPI o Uvicorn no estan instalados
    echo Ejecuta: pip install -r requirements.txt
    pause
    exit /b 1
)

echo [2/3] Verificando base de datos...
python -c "from app.database import engine; print('Conexion DB OK')" 2>nul
if errorlevel 1 (
    echo ERROR: No se pudo conectar a la base de datos
    echo Verifica el archivo .env y que MySQL este corriendo
    pause
    exit /b 1
)

echo [3/3] Iniciando servidor en puerto 8000...
echo.
echo Backend iniciado en: http://127.0.0.1:8000
echo Documentacion API: http://127.0.0.1:8000/docs
echo ==========================================================
echo.

python -m uvicorn app.main:app --reload --port 8000 --host 127.0.0.1

pause