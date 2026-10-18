# -*- coding: utf-8 -*-
"""
Faz uma cópia de segurança do Eye of Thundera.

Guarda o projeto (código + histórico do Git) num .zip dentro da pasta
"Backup Eye of Thundera" do OneDrive, que é sincronizada com a nuvem. Assim
o código continua existindo mesmo que este computador queime, seja
formatado ou perca a pasta.

O que NÃO entra (não faz falta e ocuparia gigabytes):
  .venv, dist, build, __pycache__, _tmp, _arquivo_morto, *.exe, *.log
Tudo o que importa (o código, os guias e o histórico do Git) entra.

Uso (pelo duplo clique em "4 - Fazer backup.bat"):
    .venv\\Scripts\\python.exe fazer_backup.py
"""

import os
import sys
import zipfile
from datetime import datetime
from pathlib import Path

PASTA = Path(__file__).resolve().parent
if sys.stdout is not None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Onde ficam as cópias. OneDrive é sincronizado com a nuvem.
DESTINO = Path.home() / "OneDrive" / "Backup Eye of Thundera"
NOME_DESTINO = "eye-of-thundera"
MAXIMO_DE_COPIAS = 10          # só as 10 últimas, para não encher o OneDrive

# Pastas e arquivos que não entram na cópia.
IGNORAR_PASTAS = {
    ".venv", "dist", "build", "__pycache__", "_tmp", "_arquivo_morto",
    ".git/lfs", ".idea", ".vscode",
}
IGNORAR_ARQUIVOS = {".pyc", ".pyo", ".log", ".exe"}


def tamanho_legivel(numero):
    for unidade in ("B", "KB", "MB", "GB"):
        if numero < 1024 or unidade == "GB":
            return "%.1f %s" % (numero, unidade)
        numero /= 1024.0


def coletar(raiz):
    """Lista os arquivos que entram na cópia."""
    achados = []
    for pasta, subpastas, arquivos in os.walk(raiz):
        relative = Path(pasta).relative_to(raiz)
        partes = set(relative.parts) if relative.parts else set()
        # não desce nas pastas ignoradas
        subpastas[:] = [s for s in subpastas
                        if s not in IGNORAR_PASTAS
                        and str((relative / s).as_posix()) not in IGNORAR_PASTAS]
        if partes & IGNORAR_PASTAS:
            continue
        for arquivo in arquivos:
            caminho = Path(pasta) / arquivo
            if caminho.suffix.lower() in IGNORAR_ARQUIVOS:
                continue
            if arquivo == Path(__file__).name:
                pass                      # o proprio script pode entrar
            achados.append(caminho)
    return achados


def main():
    arquivos = coletar(PASTA)
    if not arquivos:
        print("Nao achei nenhum arquivo para copiar. Algo esta errado.")
        return 1

    total = sum(p.stat().st_size for p in arquivos)
    print("Vou copiar %d arquivos (%s)..." % (len(arquivos),
                                              tamanho_legivel(total)))

    try:
        DESTINO.mkdir(parents=True, exist_ok=True)
    except Exception as erro:
        print("Nao consegui criar a pasta de backup:")
        print("  %s" % DESTINO)
        print("  %s" % erro)
        print()
        print("Se voce nao usa o OneDrive, avise que eu mudo o destino.")
        return 1

    carimbo = datetime.now().strftime("%Y-%m-%d_%H%M")
    destino = DESTINO / ("%s_%s.zip" % (NOME_DESTINO, carimbo))
    try:
        with zipfile.ZipFile(destino, "w", zipfile.ZIP_DEFLATED) as zip:
            for arquivo in arquivos:
                zip.write(arquivo, arquivo.relative_to(PASTA).as_posix())
    except Exception as erro:
        print("Nao consegui criar o zip: %s" % erro)
        return 1

    # confere que o zip abre e tem o historico do git dentro
    try:
        with zipfile.ZipFile(destino) as zip:
            ruim = zip.testzip()
            nomes = set(zip.namelist())
        if ruim is not None:
            print("O zip saiu corrompido (%s). Nao confio nele." % ruim)
            return 1
        if ".git/HEAD" not in nomes:
            print("O zip NAO tem o historico do Git. Algo deu errado.")
            return 1
        quantos = len([n for n in nomes if n.endswith(".py")])
    except Exception as erro:
        print("Nao consegui conferir o zip: %s" % erro)
        return 1

    # apaga as copias mais antigas, mantendo as MAXIMO_DE_COPIAS
    copias = sorted(DESTINO.glob("%s_*.zip" % NOME_DESTINO),
                   key=lambda p: p.name, reverse=True)
    apagadas = 0
    for velha in copias[MAXIMO_DE_COPIAS:]:
        try:
            velha.unlink()
            apagadas += 1
        except Exception:
            pass

    print()
    print("Backup feito com sucesso.")
    print("  Arquivo : %s (%s)" % (destino.name,
                                  tamanho_legivel(destino.stat().st_size)))
    print("  Onde    : %s" % DESTINO)
    print("  Dentro  : %d arquivos .py e todo o historico do Git"
          % quantos)
    if apagadas:
        print("  Apaguei %d copia(s) antiga(s) (ficam as %d mais novas)."
              % (apagadas, MAXIMO_DE_COPIAS))
    print()
    print("Se precisar voltar atras: e so descompactar esse zip numa pasta")
    print("e pronto. O codigo e o historico voltam como estavam.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
