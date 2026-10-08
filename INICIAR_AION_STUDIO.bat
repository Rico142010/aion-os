@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>&1
if errorlevel 1 (
  echo No se encontro Python. Instala Python 3.11 o superior y vuelve a abrir este archivo.
  pause
  exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
  echo Preparando el entorno de AION STUDIO...
  py -3 -m venv .venv
  if errorlevel 1 goto error
)

echo Instalando o verificando dependencias...
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto error

if not exist ".env" (
  copy ".env.example" ".env" >nul
  echo Se creo .env desde .env.example. Agrega tus claves privadas en ese archivo si usaras IA o integraciones.
)

echo Iniciando AION STUDIO en http://localhost:8000
start "" "http://localhost:8000"
".venv\Scripts\python.exe" app.py
echo.
echo AION STUDIO se detuvo. Revisa el mensaje anterior para ver el motivo.
pause
exit /b 0

:error
echo No se pudo preparar o iniciar AION STUDIO. Revisa la conexion a Internet y el mensaje de error.
pause
exit /b 1
