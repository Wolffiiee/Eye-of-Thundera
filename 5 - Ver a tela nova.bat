@echo off
rem ================================================================
rem  VER A TELA NOVA (ainda em construção).
rem
rem  Isto NAO e' o programa que voce usa. E' uma previa da tela que
rem  vai ser feita em HTML, para voce ver como vai ficar antes de
rem  decidirmos. Ela so LEITURA: nao mexe nas suas conversas, na sua
rem  memoria e nas suas chaves.
rem
rem  O programa de sempre continua funcionando normalmente.
rem
rem  Para sair, feche a janela da tela nova.
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

".venv\Scripts\python.exe" "app_web.py" --previa

echo.
echo A tela nova foi fechada. Para voltar ao programa de sempre, abra
echo o atalho "Pesquisa IA" da Area de Trabalho.
echo.
pause
