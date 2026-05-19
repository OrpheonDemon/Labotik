@echo off
echo Iniciando servidores de Labotik en segundo plano (silencioso)...
start pythonw start_servers.pyw
echo.
echo Los servidores se estan ejecutando de forma invisible.
echo - Backend API:    http://127.0.0.1:8000/docs
echo - Frontend App:   http://127.0.0.1:3000/
echo.
echo Para detenerlos, ejecute detener.bat
timeout /t 5
