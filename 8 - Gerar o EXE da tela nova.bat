@echo off
rem ================================================================
rem  GERAR O .EXE DA TELA NOVA.
rem
rem  Isto cria o "Pesquisa IA Tela Nova.exe": a tela NOVA em HTML,
rem  num arquivo so, que roda sem o Python instalado.
rem
rem  IMPORTANTE: este .exe NAO substitui o seu programa de sempre.
rem  O "Pesquisa IA.exe" (o de sempre, em tkinter) continua como esta,
rem  com o mesmo atalho. Os dois convivem.
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

echo [2/2] Gerando o .exe da tela nova (leva alguns minutos)...
".venv\Scripts\python.exe" -m PyInstaller --noconfirm --clean "Pesquisa IA Tela Nova.spec"
if errorlevel 1 (
    echo O PyInstaller falhou. Veja as mensagens acima.
    pause
    exit /b 1
)

echo.
echo Pronto! O arquivo novo esta em:
echo     dist\Pesquisa IA Tela Nova.exe
echo.
echo Copie para a Area de Trabalho, ao lado do programa de sempre
echo (NAO no lugar dele: os dois convivem).
echo.
pause