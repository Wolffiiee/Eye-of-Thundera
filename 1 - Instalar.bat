@echo off
rem ================================================================
rem  Instala o que o programa precisa (so precisa rodar uma vez).
rem ================================================================
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
    echo.
    echo Python nao encontrado neste computador.
    echo Instale primeiro em:  https://www.python.org/downloads/
    echo IMPORTANTE: marque a caixinha "Add Python to PATH" na instalacao.
    echo.
    pause
    exit /b 1
)

echo Criando o ambiente do programa (isso pode levar um minuto)...
python -m venv .venv
if errorlevel 1 (
    echo Nao consegui criar o ambiente.
    pause
    exit /b 1
)

echo Baixando as bibliotecas necessarias...
".venv\Scripts\python.exe" -m pip install --upgrade pip
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
    echo Nao consegui instalar as bibliotecas. Confira sua internet.
    pause
    exit /b 1
)

echo.
echo Tudo pronto! Agora abra o arquivo  "2 - Abrir Pesquisa IA.bat".
echo.
pause
