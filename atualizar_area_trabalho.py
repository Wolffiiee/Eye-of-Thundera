"""Atualiza a Area de Trabalho: copia o Eye of Thundera.exe e recria o atalho .lnk."""
import os
import shutil
import subprocess
import sys
from pathlib import Path

PASTA_PROJETO = Path(r"D:\Projetos\PesquisaIA")
DESKTOP = Path.home() / "Desktop"
exe_projeto = PASTA_PROJETO / "dist" / "Eye of Thundera.exe"
exe_desktop = DESKTOP / "Eye of Thundera.exe"
lnk_desktop = DESKTOP / "Eye of Thundera.lnk"

if not exe_projeto.exists():
    sys.stderr.write("AVISO: dist/Eye of Thundera.exe nao encontrado. "
                     "Rode 'Gerar o EXE.bat' antes.\n")
    sys.exit(1)

shutil.copy2(exe_projeto, exe_desktop)
print("[OK] .exe copiado para a Area de Trabalho: " + str(exe_desktop))

ps_script = (
    '$ws = New-Object -ComObject WScript.Shell; '
    '$sc = $ws.CreateShortcut("' + str(lnk_desktop) + '"); '
    '$sc.TargetPath = "' + str(exe_desktop) + '"; '
    '$sc.WorkingDirectory = "' + str(DESKTOP) + '"; '
    '$sc.Description = "Eye of Thundera - programa novo"; '
    '$sc.IconLocation = "' + str(exe_desktop) + ',0"; '
    '$sc.Save()'
)
subprocess.run([
    "powershell.exe", "-ExecutionPolicy", "Unrestricted",
    "-WindowStyle", "Hidden", "-Command", ps_script
], check=True, capture_output=True)
print("[OK] atalho criado: " + str(lnk_desktop))
