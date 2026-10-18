# -*- coding: utf-8 -*-
"""Faz o pacote de instalacao do Eye of Thundera (zip para levar a outro PC).

Uso:  python ferramentas/gerar_instalador.py

O que ele faz, em ordem:
  1. Roda verificar.py (se algum teste falhar, NAO gera o pacote).
  2. Recompila o EXE com o PyInstaller (modo onedir: 1 processo so).
  3. Monta a pasta de trabalho do instalador.
  4. Gera o .zip em _tmp\\.

Como o ZIP fica (uma pasta so, ja com o nome do programa dentro):

    Eye of Thundera\\
        Eye of Thundera.exe      <- o programa (de dois cliques aqui)
        _internal\\              <- o que o EXE precisa para rodar
        codigo\\                 <- o codigo-fonte (opcional, so para olhar)
        LEIA-ME.txt              <- as instrucoes

Assim, ao descompactar, o usuario ve UM item so na area de trabalho: a pasta
"Eye of Thundera". Tudo (o exe, o codigo e o LEIA-ME) fica dentro dela.

Nao apaga nada de importante: o zip anterior e substituido, e o resto da
pasta de trabalho do projeto fica intacto.
"""
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DESTINO = Path(r"D:\Projetos\Eye of Thundera Instalador")
ZIP = RAIZ / "_tmp" / "Eye of Thundera.zip"
PYTHON = RAIZ / ".venv" / "Scripts" / "python.exe"

# Nome da pasta que vai dentro do zip (e que o usuario ve ao descompactar).
NOME_PASTA = "Eye of Thundera"


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

    # A pasta final: tudo dentro dela.
    final = DESTINO / NOME_PASTA
    print("\n>>> Montando a pasta %s" % NOME_PASTA)
    if final.exists():
        shutil.rmtree(final)
    final.mkdir(parents=True)

    # 3. O programa em si (exe + _internal), direto do build.
    fonte_exe = RAIZ / "dist" / NOME_PASTA
    if not fonte_exe.is_dir():
        print("    FALHOU: nao achei o EXE compilado em %s" % fonte_exe)
        return 1
    for item in fonte_exe.iterdir():
        destino = final / item.name
        if item.is_dir():
            shutil.copytree(item, destino)
        else:
            shutil.copy2(item, destino)
    print("    Programa copiado (%s)" % final)

    # 4. O codigo-fonte vai para dentro da mesma pasta, em "codigo\".
    if not rodar([PYTHON, "ferramentas/gerar_pasta_limpa.py", final],
                 "Copiando o codigo-fonte para %s\\codigo" % NOME_PASTA):
        return 1

    # 5. O LEIA-ME na raiz da mesma pasta.
    leia_me = DESTINO / "LEIA-ME.txt"
    if leia_me.is_file():
        shutil.copy2(leia_me, final / "LEIA-ME.txt")
        print("    LEIA-ME copiado")
    else:
        print("    AVISO: nao achei %s" % leia_me)

    # 6. Zip: a pasta "Eye of Thundera" e' o unico item na raiz.
    print("\n>>> Gerando o zip")
    ZIP.parent.mkdir(parents=True, exist_ok=True)
    if ZIP.exists():
        ZIP.unlink()
    with zipfile.ZipFile(ZIP, "w", zipfile.ZIP_DEFLATED) as z:
        for pasta, subpastas, arquivos in os.walk(final):
            subpastas[:] = [s for s in subpastas if s != "__pycache__"]
            for arquivo in arquivos:
                caminho = Path(pasta) / arquivo
                # .antigo/.bloqueado = sobras de versoes anteriores, nao vao no pacote
                if caminho.suffix in (".antigo", ".bloqueado"):
                    continue
                relativo = caminho.relative_to(final).as_posix()
                z.write(caminho, "%s/%s" % (NOME_PASTA, relativo))

    tamanho = ZIP.stat().st_size / (1024 * 1024)
    print("    %s (%.1f MB)" % (ZIP, tamanho))
    print()
    print("Pronto. O instalador esta em:")
    print("  %s" % ZIP)
    print()
    print("Ao descompactar, aparecera UMA pasta: %s" % NOME_PASTA)
    print("Dentro dela: o programa, o codigo-fonte e o LEIA-ME.")
    return 0


if __name__ == "__main__":
    sys.exit(main())