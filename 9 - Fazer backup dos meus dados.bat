@echo off
rem ================================================================
rem  FAZER BACKUP DOS SEUS DADOS.
rem
rem  Este backup NAO e' o do codigo (esse e' o "4 - Fazer backup.bat").
rem  Este aqui copia as SUAS coisas: as conversas, a memoria e as
rem  chaves, para um .zip dentro da pasta "Backup Eye of Thundera" do seu
rem  OneDrive (que vai para a nuvem).
rem
rem  Quando usar:
rem    - de tempos em tempos (por exemplo, todo fim de semana);
rem    - ANTES de mexer em algo grande no programa.
rem
rem  O programa pode estar aberto: ele so LE e copia, nao mexe em nada.
rem
rem  Como recuperar, se precisar:
rem    1) abra o .zip;
rem    2) tire os arquivos de dentro;
rem    3) copie para a pasta  C:\Users\Igor\AppData\Local\EyeOfThundera
rem       (pode estar oculta: va ate a barra de endereco do Explorer e
rem        digite o caminho).
rem
rem  As copias antigas sao apagadas depois de 15, para o computador
rem  nao encher.
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

".venv\Scripts\python.exe" "fazer_backup_dados.py"
if errorlevel 1 (
    echo.
    echo Nao deu para fazer o backup. Veja a mensagem acima.
    pause
    exit /b 1
)

echo.
echo ================================================================
echo  BACKUP DOS SEUS DADOS FEITO.
echo.
type "_arquivo_morto\ultimo_backup_dados.txt"
echo.
echo ================================================================
echo.
pause