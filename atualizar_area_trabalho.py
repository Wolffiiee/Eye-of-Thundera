"""Garante UM atalho na Area de Trabalho para a Eye of Thundera (UI nova em HTML).

O atalho aponta para o EXE do PyInstaller (dist/Eye of Thundera.exe), que ja
tem o nome e o icone corretos para o Gerenciador de Tarefas. O EXE e'
recompilado apos cada mudanca no codigo (verificar.py + pyinstaller).

Se o EXE nao existir, cai para a copia renomeada do pythonw.exe.
"""
import os
import shutil
import subprocess
from pathlib import Path

PASTA = Path(r"D:\Projetos\PesquisaIA")
DESKTOP = Path.home() / "Desktop"
LNK = DESKTOP / "Eye of Thundera.lnk"
ICONE = PASTA / "icone.ico"
EXE_DIST = PASTA / "dist" / "Eye of Thundera" / "Eye of Thundera.exe"
PYW_ORIGINAL = PASTA / ".venv" / "Scripts" / "pythonw.exe"
PYW_RENOMEADO = PASTA / ".venv" / "Scripts" / "Eye of Thundera.exe"

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

# Decide qual executavel usar: preferir o EXE do PyInstaller (tem icone e
# nome corretos no Gerenciador de Tarefas). Se nao existir, usa a copia
# renomeada do pythonw.exe.
if EXE_DIST.exists():
    TARGET = EXE_DIST
    print("[OK] usando EXE do PyInstaller: " + TARGET.name)
else:
    # Garante que a copia renomeada existe
    if not PYW_RENOMEADO.exists() and PYW_ORIGINAL.exists():
        shutil.copy2(str(PYW_ORIGINAL), str(PYW_RENOMEADO))
        print("[OK] copia renomeada criada: " + PYW_RENOMEADO.name)
    TARGET = PYW_RENOMEADO
    print("[AVISO] EXE do PyInstaller nao encontrado, usando copia renomeada")

# Recria atalho unico via PowerShell (nao depende de win32com)
ps_script = (
    "$s = New-Object -ComObject WScript.Shell; "
    "$lnk = $s.CreateShortcut('"
    + str(LNK)
    + "'); "
    "$lnk.TargetPath = '"
    + str(TARGET)
    + "'; "
    "$lnk.Arguments = ''; "
    "$lnk.WorkingDirectory = '"
    + str(PASTA)
    + "'; "
    "$lnk.IconLocation = '"
    + str(ICONE)
    + "'; "
    "$lnk.Description = 'Eye of Thundera'; "
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
