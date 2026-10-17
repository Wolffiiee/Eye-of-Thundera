@echo off
rem Atualiza a pasta _troca (prints em modo exemplo + estado) para mandar ao ChatGPT.
chcp 65001 >nul
cd /d "%~dp0"
".venv\Scripts\python.exe" ferramentas\tirar_prints.py
".venv\Scripts\python.exe" ferramentas\gerar_pacote_troca.py
echo.
echo Pronto: anexe a pasta _troca no ChatGPT.
pause

