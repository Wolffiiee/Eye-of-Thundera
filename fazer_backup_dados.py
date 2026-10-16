"""Copia de seguranca dos DADOS do Wolf (conversas, memoria, chaves).

Roda em segundo plano, com o programa aberto ou fechado. NAO altera nada:
so le e copia. Uso unico, em _tmp.
"""
import io
import os
import sys
import zipfile
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ORIGEM = Path(os.environ["LOCALAPPDATA"]) / "PesquisaIA"
DESTINO = Path(r"C:\Users\Igor\OneDrive") / "Backup Pesquisa IA" / "dados"
LOG = Path(r"C:\Projetos\PesquisaIA\_arquivo_morto") / "ultimo_backup_dados.txt"


def main():
    linhas = []
    if not ORIGEM.exists():
        linhas.append("a pasta de dados nao existe: %s" % ORIGEM)
        LOG.write_text("\n".join(linhas), encoding="utf-8")
        return
    DESTINO.mkdir(parents=True, exist_ok=True)
    carimbo = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    alvo = DESTINO / ("dados_%s.zip" % carimbo)
    arquivos = sorted(x for x in ORIGEM.iterdir() if x.is_file())
    with zipfile.ZipFile(alvo, "w", zipfile.ZIP_DEFLATED) as z:
        for arquivo in arquivos:
            z.write(arquivo, arquivo.name)
    linhas.append("copiado: %s" % alvo)
    linhas.append("arquivos: %d" % len(arquivos))
    for arquivo in arquivos:
        linhas.append("  %-28s %8d bytes" % (arquivo.name, arquivo.stat().st_size))
    # apaga o .zip antigo quando passar de 15 (o backup nao enche a maquina)
    velhos = sorted(DESTINO.glob("dados_*.zip"), reverse=True)[15:]
    for velho in velhos:
        velho.unlink()
        linhas.append("apagado (velho): %s" % velho.name)
    LOG.write_text("\n".join(linhas), encoding="utf-8")


if __name__ == "__main__":
    main()