@echo off
rem ================================================================
rem  FALAR NA TELA NOVA (testar o microfone).
rem
rem  Isto NAO e' o programa que voce usa. E' a tela nova em HTML,
rem  aberta so para voce testar o microfone de verdade.
rem
rem  O que ele faz:
rem    - abre a tela nova no SEGUNDO monitor (nao tapa a sua tela);
rem    - o microfone e' o DE VERDADE: clique no botao do microfone (ou
rem      Ctrl+M) para gravar, clique de novo para parar;
rem    - a IA responde de verdade, usando a sua chave.
rem
rem  O que ele NAO faz (de proposito):
rem    - nao salva nenhuma conversa sua;
rem    - nao mexe na sua memoria.
rem
rem  O programa de sempre continua funcionando normalmente.
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

".venv\Scripts\python.exe" "app_web.py" --demo --voz

echo.
echo A tela nova foi fechada. Para voltar ao programa de sempre, abra
echo o atalho "Pesquisa IA" da Area de Trabalho.
echo.
pause