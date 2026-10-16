"""Garante UM atalho na Area de Trabalho para a Eye of Thundera (UI nova em HTML)."""
import os
import shutil
import subprocess
from pathlib import Path

PASTA = Path(r"D:\Projetos\PesquisaIA")
DESKTOP = Path.home() / "Desktop"
LNK = DESKTOP / "Eye of Thundera.lnk"
ICONE = PASTA / "icone.ico"
PYW = PASTA / ".venv" / "Scripts" / "pythonw.exe"

_base = (PASTA / "_arquivo_morto")
_base.mkdir(exist_ok=True)

# Mover duplicados/extras (nunca apagar)
for dup in (DESKTOP / "Eye of Thundera (Nova Tela).lnk",
            DESKTOP / "Wolf.lnk",
            DESKTOP / "Eye of Thundera.exe"):
    if dup.exists():
        dest = _base / (dup.stem + " (atalho antigo)" + dup.suffix)
        try:
            os.replace(str(dup), str(dest))
            print("[OK] extra guardado em _arquivo_morto: " + dup.name)
        except Exception as e:
            print("AVISO: nao moveu %s: %s" % (dup, e))

# Recria atalho unico via PowerShell (nao depende de win32com)
ps_script = (
    "$s = New-Object -ComObject WScript.Shell; "
    "$lnk = $s.CreateShortcut('"
    + str(LNK)
    + "'); "
    "$lnk.TargetPath = '"
    + str(PYW)
    + "'; "
    "$lnk.Arguments = 'app_web.py'; "
    "$lnk.WorkingDirectory = '"
    + str(PASTA)
    + "'; "
    "$lnk.IconLocation = '"
    + str(ICONE)
    + "'; "
    "$lnk.Description = 'Eye of Thundera - interface nova'; "
    "$lnk.Save(); "
    'Write-Output "ATUALIZADO: " + $lnk.TargetPath'
)
result = subprocess.run(
    ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_script],
    capture_output=True,
    text=True,
)
out = (result.stdout or "").strip()
err = (result.stderr or "").strip()
if out:
    print("[OK] " + out)
if err:
    print("ERRO: " + err)
print("[OK] Atalho final: " + str(LNK))
print("     -> UM icone de Eye of Thundera na Area de Trabalho.")


def foo():
    return 'x'
