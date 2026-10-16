@echo off
rem Troca o modelo do OpenCode por um GRATIS que esteja respondendo.
rem Duplo clique. Pode demorar ate alguns minutos (testa um por um).
chcp 65001 >nul
cd /d "%~dp0"
".venv\Scripts\python.exe" "ferramentas\trocar_modelo_gratis.py"
echo.
pause
