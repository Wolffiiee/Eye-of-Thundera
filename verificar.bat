@echo off
rem ================================================================
rem  Confere se o programa continua inteiro depois de uma alteracao.
rem  Duplo clique aqui. Tem que terminar com "TUDO CERTO".
rem ================================================================
chcp 65001 >nul
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo O ambiente do programa nao foi encontrado.
    echo Rode primeiro o arquivo  "1 - Instalar.bat".
    pause
    exit /b 1
)

".venv\Scripts\python.exe" verificar.py
echo.
pause
