@echo off
cd /d "%~dp0"
rem ================================================================
rem  Abre o programa Eye of Thundera (versão nova HTML).
rem  Mata processos antigos para garantir interface limpa.
rem ================================================================
rem Mata qualquer instância antiga para garantir limpeza
taskkill /f /im "Eye of Thundera.exe" 2>nul
taskkill /f /im "pythonw.exe" 2>nul
taskkill /f /im "python.exe" 2>nul
rem Pequena pausa para os processos encerrarem completamente
timeout /t 2 /nobreak >nul
rem Lança a versão nova (exe da Área de Trabalho)
start "" ".\\Eye of Thundera.exe"
exit /b 0