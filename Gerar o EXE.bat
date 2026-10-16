@echo off
rem ================================================================
rem  GERAR O .EXE — ESTE E' O PROGRAMA DE HOJE.
rem
rem  Isto cria o "Eye of Thundera.exe": a tela em HTML, num
rem  arquivo so, que roda sem o Python instalado. E' o programa que
rem  esta na sua Area de Trabalho.
rem
rem  So e preciso rodar isto se mexermos no codigo da tela nova.
rem ================================================================
chcp 65001 >nul
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo O Python do projeto nao esta instalado.
    echo Rode antes o arquivo "1 - Instalar.bat".
    echo.
    pause
    exit /b 1
)

echo [1/2] Conferindo se falta alguma biblioteca...
".venv\Scripts\python.exe" -m pip install -q -r requirements-dev.txt
if errorlevel 1 (
    echo Nao deu para instalar as bibliotecas. Veja a mensagem acima.
    pause
    exit /b 1
)

echo [2/2] Gerando o .exe (leva alguns minutos)...
".venv\Scripts\python.exe" -m PyInstaller --noconfirm --clean "Eye of Thundera.spec"
if errorlevel 1 (
    echo O PyInstaller falhou. Veja as mensagens acima.
    pause
    exit /b 1
)

echo.
echo Pronto! O arquivo novo esta em:
echo     dist\Eye of Thundera.exe
echo.
echo Copie para a Area de Trabalho.
echo.
pause
