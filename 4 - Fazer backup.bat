@echo off
rem ================================================================
rem  Copia de seguranca do Pesquisa IA.
rem
rem  Guarda o codigo e o historico do Git num .zip dentro do OneDrive
rem  (que vai para a nuvem). Se este computador queimar ou a pasta for
rem  apagada, e so descompactar o zip de volta.
rem
rem  Faca isto de tempos em tempos (por exemplo, todo fim de semana,
rem  ou depois de cada coisa grande que o programa ganhar).
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

".venv\Scripts\python.exe" "fazer_backup.py"

if errorlevel 1 (
    echo.
    echo O backup NAO foi feito. Leia a mensagem acima.
) else (
    echo.
    echo Terminou. Pode fechar esta janela.
)
echo.
pause
