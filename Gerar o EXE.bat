@echo off
rem ================================================================
rem  GERAR O .EXE DISTRIBUIVEL (NAO E' O ATALHO DE DESENVOLVIMENTO).
rem
rem  Isto cria dist\Eye of Thundera.exe: a tela em HTML empacotada
rem  para distribuicao, sem exigir o Python instalado.
rem  O atalho de desenvolvimento na Area de Trabalho continua abrindo
rem  app_web.py pelo ambiente .venv, para usar o codigo-fonte atual.
rem
rem  Rode somente quando quiser atualizar o pacote distribuivel.
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
echo Pronto! O pacote distribuivel esta em:
echo     dist\Eye of Thundera.exe
echo.
echo O atalho da Area de Trabalho continua abrindo app_web.py pelo ambiente .venv.
echo O script seguinte garante que esse atalho continue sendo o unico icone do app.
echo.
rem
rem --- Atualiza Area de Trabalho ---
".venv\Scripts\python.exe" atualizar_area_trabalho.py
if errorlevel 1 (
    echo Falha ao atualizar a Area de Trabalho.
    pause
    exit /b 1
)

pause
