@echo off
rem ================================================================
rem  USAR A TELA NOVA DE VERDADE (com as SUAS conversas).
rem
rem  ATENCAO: esta e' a tela nova em HTML, ainda em construcao. Ela
rem  conversa de verdade e SALVA suas conversas e sua memoria no mesmo
rem  lugar que o programa de sempre - entao:
rem
rem    - o que voce perguntar aqui aparece na barra da esquerda do
rem      programa de sempre (e vice-versa);
rem    - a aba Memoria, as chaves e as opcoes sao as mesmas.
rem
rem  Se algo parecer errado, e so fechar esta janela e abrir o programa
rem  de sempre: ele continua funcionando como sempre.
rem
rem  Para sair, feche a janela.
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

".venv\Scripts\python.exe" "app_web.py"

echo.
echo A tela nova foi fechada.
echo.
pause