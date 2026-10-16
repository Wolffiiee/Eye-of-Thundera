@echo off
rem ================================================================
rem  Abre o programa Eye of Thundera.
rem  Basta dar um duplo clique neste arquivo.
rem ================================================================
cd /d "%~dp0"

if not exist ".venv\Scripts\pythonw.exe" (
    echo.
    echo O ambiente do programa nao foi encontrado.
    echo Rode primeiro o arquivo  "1 - Instalar.bat"  e depois este.
    echo.
    pause
    exit /b 1
)

start "" ".venv\Scripts\pythonw.exe" "app_web.py"
