@echo off
rem ================================================================
rem  Gera o "Pesquisa IA.exe" novo (pasta dist) a partir do codigo.
rem  So gera se o verificar.py passar. Depois, copie o .exe de dist
rem  para a Area de Trabalho (substitua o antigo).
rem ================================================================
chcp 65001 >nul
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Rode primeiro o arquivo  "1 - Instalar.bat".
    pause
    exit /b 1
)

echo [1/3] Conferindo o programa...
".venv\Scripts\python.exe" verificar.py
if errorlevel 1 (
    echo.
    echo O verificar.py achou problemas. O .exe NAO foi gerado.
    pause
    exit /b 1
)

echo [2/3] Instalando as ferramentas de montagem (so na primeira vez)...
".venv\Scripts\python.exe" -m pip install -q -r requirements-dev.txt

echo [3/3] Gerando o .exe (leva alguns minutos)...
".venv\Scripts\python.exe" -m PyInstaller --noconfirm --clean "Pesquisa IA.spec"
if errorlevel 1 (
    echo O PyInstaller falhou. Veja as mensagens acima.
    pause
    exit /b 1
)

echo.
echo Pronto! O arquivo novo esta em:  dist\Pesquisa IA.exe
echo Copie ele para a Area de Trabalho, no lugar do antigo.
pause
