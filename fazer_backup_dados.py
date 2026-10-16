"""Copia de seguranca dos DADOS do Wolf (conversas, memoria, chaves).

Roda em segundo plano, com o programa aberto ou fechado. NAO altera nada:
so le e copia. Este arquivo e' a "porta de entrada" para quem clicar
nele; a logica esta em `pesquisa_ia.fazer_backup_dados`, que e' a mesma
que o botao dentro do programa usa.
"""
import io
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
sys.path.insert(0, str(RAIZ))
if sys.stdout is not None:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import pesquisa_ia as p

LOG = Path(__file__).resolve().parent / "_arquivo_morto" / "ultimo_backup_dados.txt"


def main():
    linhas = []
    try:
        caminho, nomes = p.fazer_backup_dados()
        linhas.append("copiado: %s" % caminho)
        linhas.append("arquivos: %d" % len(nomes))
        for nome in nomes:
            linhas.append("  - %s" % nome)
    except Exception as erro:
        linhas.append("NAO DEU: %s" % erro)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    io.open(LOG, "w", encoding="utf-8").write("\n".join(linhas))
    print("\n".join(linhas))


if __name__ == "__main__":
    main()