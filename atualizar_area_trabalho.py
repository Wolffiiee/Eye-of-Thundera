"""Atualiza a Area de Trabalho: copia o Eye of Thundera.exe e recria o atalho .lnk."""
import shutil
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

# UM icone so na Area de Trabalho: o proprio .exe. Atalho .lnk a mais
# vira icone duplicado, entao se existir um (nosso ou o velho "Wolf") ele
# e' MOVIDO (nunca apagado) para a pasta _arquivo_morto.
morto = PASTA_PROJETO / "_arquivo_morto"
morto.mkdir(exist_ok=True)
for velho in (lnk_desktop, DESKTOP / "Wolf.lnk"):
    if velho.exists():
        shutil.move(str(velho), str(morto / (velho.stem + " (atalho antigo).lnk")))
        print("[OK] atalho extra guardado em _arquivo_morto: " + velho.name)
print("[OK] Area de Trabalho: so o Eye of Thundera.exe (um icone).")

