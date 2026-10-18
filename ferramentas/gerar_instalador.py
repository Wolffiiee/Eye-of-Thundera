# -*- coding: utf-8 -*-
"""Faz o pacote de instalacao do Eye of Thundera (zip para levar a outro PC).

Uso:  python ferramentas/gerar_instalador.py

O que ele faz, em ordem:
  1. Roda verificar.py (se algum teste falhar, NAO gera o pacote).
  2. Recompila o EXE com o PyInstaller (modo onedir: 1 processo so).
  3. Copia o codigo necessario para a pasta "Instalador\\codigo".
  4. Monta a pasta final:  Eye of Thundera\\  (exe + _internal)
                        Eye of Thundera Instalador\\codigo\\  (fonte, opcional)
                        LEIA-ME.txt
  5. Gera o .zip em _tmp\\.

Nao apaga nada de importante: o zip anterior e substituido, e o resto da
pasta de trabalho fica intacto.
"""
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DESTINO = Path(r"D:\Projetos\Eye of Thundera Instalador")
ZIP = RAIZ / "_tmp" / "Eye of Thundera Instalador.zip"
PYTHON = RAIZ / ".venv" / "Scripts" / "python.exe"


def rodar(comando, titulo):
    print("\n>>> %s" % titulo)
    print("    %s" % " ".join(str(c) for c in comando))
    codigo = subprocess.call([str(c) for c in comando], cwd=str(RAIZ))
    if codigo != 0:
        print("    FALHOU (%s). Parei aqui." % titulo)
        return False
    return True


def main():
    # 1. Testes
    if not rodar([PYTHON, "-u", "verificar.py"], "Rodando os testes"):
        print("Corrige os testes antes de gerar o instalador.")
        return 1

    # 2. Compilar
    if not rodar([PYTHON, "-m", "PyInstaller", "--clean", "--noconfirm",
                  "Eye of Thundera.spec"], "Compilando o EXE"):
        return 1

    # 3. Codigo-fonte
    if not rodar([PYTHON, "ferramentas/gerar_pasta_limpa.py", DESTINO],
                 "Copiando o codigo-fonte"):
        return 1

    # 4. Montar a pasta final
    print("\n>>> Montando a pasta final")
    fonte_exe = RAIZ / "dist" / "Eye of Thundera"
    alvo_exe = DESTINO / "Eye of Thundera"
    if not fonte_exe.is_dir():
        print("    FALHOU: nao achei o EXE compilado em %s" % fonte_exe)
        return 1
    if alvo_exe.exists():
        shutil.rmtree(alvo_exe)
    shutil.copytree(fonte_exe, alvo_exe)
    print("    EXE pronto: %s" % alvo_exe)

    # 5. Zip
    print("\n>>> Gerando o zip")
    ZIP.parent.mkdir(parents=True, exist_ok=True)
    if ZIP.exists():
        ZIP.unlink()
    with zipfile.ZipFile(ZIP, "w", zipfile.ZIP_DEFLATED) as z:
        for pasta, subpastas, arquivos in os.walk(DESTINO):
            subpastas[:] = [s for s in subpastas if s != "__pycache__"]
            for arquivo in arquivos:
                caminho = Path(pasta) / arquivo
                # .antigo/.bloqueado = sobras de versões anteriores, não vão no pacote
                if caminho.suffix in (".antigo", ".bloqueado"):
                    continue
                z.write(caminho, caminho.relative_to(DESTINO).as_posix())

    tamanho = ZIP.stat().st_size / (1024 * 1024)
    print("    %s (%.1f MB)" % (ZIP, tamanho))
    print()
    print("Pronto. O instalador esta em:")
    print("  %s" % ZIP)
    return 0


if __name__ == "__main__":
    sys.exit(main())