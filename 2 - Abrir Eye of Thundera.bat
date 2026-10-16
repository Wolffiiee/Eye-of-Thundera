@echo off
cd /d "%~dp0"
rem ================================================================
rem  Abre o programa Eye of Thundera (interface nova em HTML).
rem  Mata instancias anteriores para garantir versao nova, nao antiga.
rem ================================================================

rem --- Encerra instancias anteriores do Eye of Thundera ---
taskkill /f /im "Eye of Thundera.exe" >nul 2>nul
taskkill /f /im "pythonw.exe" >nul 2>nul

rem --- pequena pausa para liberacao ---
timeout /t 2 /nobreak >nul

rem --- Garante venv ---
if not exist ".venv\Scripts\pythonw.exe" (
    echo.
    echo O ambiente do programa nao foi encontrado.
    echo Rode primeiro "1 - Instalar.bat" e depois este.
    echo.
    pause
    exit /b 1
)

rem --- Inicia a edicao nova (app_web.py) ---
start "" ".venv\Scripts\pythonw.exe" "app_web.py"
exit /b 0