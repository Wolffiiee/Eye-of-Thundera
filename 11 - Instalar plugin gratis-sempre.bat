@echo off
rem Instala (ou atualiza) o plugin gratis-sempre no OpenCode. Duplo clique.
rem Ele troca de modelo gratis sozinho quando o limite estoura.
cd /d "%~dp0"
if not exist "%USERPROFILE%\.config\opencode\plugin" mkdir "%USERPROFILE%\.config\opencode\plugin"
copy /y "ferramentas\opencode-gratis-sempre.js" "%USERPROFILE%\.config\opencode\plugin\gratis-sempre.js"
echo.
echo Pronto. Feche e abra o OpenCode de novo para ele carregar o plugin.
pause
