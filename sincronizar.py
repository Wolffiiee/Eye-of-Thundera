# -*- coding: utf-8 -*-
"""Sincronizacao entre computadores (PLANO-SINCRONIZACAO.md).

Mantem os dados do programa (conversas, memoria, chaves, configuracao,
lembretes) iguais em dois ou mais computadores atraves de uma pasta que o
Windows sincroniza (OneDrive, Dropbox, Google Drive ou qualquer pasta
escolhida).

Regras de ouro:
- Ultima escrita vence, POR ARQUIVO (sem mesclagem): o carimbo de
  modificacao mais novo ganha. Simples e previsivel.
- Nada e apagado do outro lado: so copia. Se o arquivo remoto e mais novo,
  importa; se o local e mais novo, exporta.
- Copia atomica: escreve `.tmp` e renomeia; se fechar no meio, o arquivo
  inteiro continua integro.
- Erro nao derruba: pasta inexistente, vazia, cheia ou sem permissao vira
  aviso (devolve dicionario com "erro"), nunca excecao.
- Dados reais intocados nos testes: tudo em _tmp com caminhos simulados.

Funcoes principais:
- arquivos_de_dados(pasta): lista os arquivos que viajan.
- sincronizar(importar/exportar): copia o que for mais novo.
- sincronizar_tudo(pasta_dados, pasta_sync): importa e exporta, devolve resumo.
"""

import os
import shutil
import time
from pathlib import Path

# O mesmo calculo do eye_of_thundera: %LOCALAPPDATA%\Eye of Thundera. Nao
# importamos eye_of_thundera aqui de proposito (o modulo fica sem dependencias,
# da mesma forma que roteador.py).
# "PesquisaIA" abaixo e o nome ANTIGO da pasta. Fica aqui de proposito: e a
# migration one-time que leva os dados de quem ja usava o programa.
PASTA_DADOS_ANTIGA = Path(
    os.environ.get("LOCALAPPDATA", Path.home())) / "PesquisaIA"
PASTA_DADOS = Path(
    os.environ.get("LOCALAPPDATA", Path.home())) / "Eye of Thundera"
# Migração one-time
try:
    if not PASTA_DADOS.exists() and PASTA_DADOS_ANTIGA.exists():
        PASTA_DADOS.mkdir(parents=True, exist_ok=True)
        for _arq in PASTA_DADOS_ANTIGA.iterdir():
            if _arq.is_file():
                shutil.copy2(str(_arq), str(PASTA_DADOS / _arq.name))
except Exception:
    pass

# Arquivo de diagnostico local: nao deve viajar (e grande e muda sempre).
NAO_VIAJAM = {"erro.log"}


_VARIANTES_LOCALIZADAS = {
    "Documents": "Documentos",
    "Documentos": "Documents",
    "Pictures": "Imagens",
    "Imagens": "Pictures",
    "Downloads": "Downloads",
    "Desktop": "Area de Trabalho",
    "Area de Trabalho": "Desktop",
}


def _pasta_real(pasta):
    """Devolve a pasta que realmente existe no disco.

    No Windows, o nome exibido no Explorer pode ser localizado (ex.:
    "Documentos") enquanto o nome real no disco e' em ingles ("Documents").
    O seletor de pasta do Windows pode retornar um dos dois. Esta funcao
    tenta as duas variantes e devolve a que existe; se nenhuma existir,
    devolve a original (para o chamador criar).
    """
    pasta = Path(pasta)
    if pasta.is_dir():
        return pasta
    pai = pasta.parent
    nome = pasta.name
    alt_nome = _VARIANTES_LOCALIZADAS.get(nome)
    if alt_nome:
        alt = pai / alt_nome
        if alt.is_dir():
            return alt
    return pasta


def pasta_padrao():
    """Onde sugerir criar a pasta de sincronizacao.

    OneDrive primeiro (o Wolf ja usa o OneDrive para o backup); se nao
    houver OneDrive, cai nos Documentos. O usuario pode trocar na aba.
    """
    onedrive = Path.home() / "OneDrive"
    if onedrive.is_dir():
        return onedrive / "Eye of Thundera"
    # Tenta Documents (ingles, nome real no disco em Windows) e Documentos
    # (portugues, exibido pelo Explorer).
    for nome in ("Documents", "Documentos"):
        candidata = Path.home() / nome
        if candidata.is_dir():
            return candidata / "Eye of Thundera"
    return Path.home() / "Documents" / "Eye of Thundera"


def arquivos_de_dados(pasta=None):
    """Lista os arquivos de dados que viajan (json da pasta, menos erro.log).

    Devolve lista de nomes (str), ordenada, sem o caminho completo — e
    assim que a pasta de sincronizacao guarda: só os nomes, na raiz.
    """
    pasta = Path(pasta) if pasta else PASTA_DADOS
    if not pasta.is_dir():
        return []
    return sorted(a.name for a in pasta.iterdir()
                  if a.is_file() and a.suffix.lower() in (".json",)
                  and a.name not in NAO_VIAJAM)


def _destino_valido(pasta):
    """A pasta de destino existe e da para gravar? Devolve None se esta bom."""
    pasta = Path(pasta)
    if not pasta.is_dir():
        return "a pasta %s nao existe" % pasta
    teste = pasta / ".teste_escrita"
    try:
        teste.write_text("ok", encoding="utf-8")
        teste.unlink()
    except OSError as erro:
        return "nao consigo gravar em %s (%s)" % (pasta, erro)
    return None


def _copia_atomica(origem, destino):
    """Copia origem para destino escrevendo `.tmp` antes e renomeando.

    Se o destino ja existe, e sobrescrito. Se a origem for mais nova que o
    destino, copia; senao, nao faz nada (e devolve False). Erro de leitura
    (arquivo em uso) devolve None para "nao deu".
    """
    origem, destino = Path(origem), Path(destino)
    try:
        if destino.exists():
            if destino.stat().st_mtime >= origem.stat().st_mtime:
                return False          # o destino ja esta igual ou mais novo
        tmp = destino.with_name(destino.name + ".tmp")
        shutil.copy2(origem, tmp)     # copy2 preserva o carimbo de modificacao
        os.replace(tmp, destino)      # renomear e' atomico no Windows
        return True
    except OSError:
        return None                   # arquivo em uso, permissao, etc.


def importar(pasta_origem, pasta_destino):
    """Copia de pasta_origem para pasta_destino o que for mais novo la.

    Devolve lista de nomes copiados. Nao apaga nada do destino.
    """
    pasta_origem, pasta_destino = Path(pasta_origem), Path(pasta_destino)
    copiados = []
    for nome in arquivos_de_dados(pasta_origem):
        origem = pasta_origem / nome
        destino = pasta_destino / nome
        try:
            if destino.exists() and destino.stat().st_mtime >= origem.stat().st_mtime:
                continue
        except OSError:
            continue
        if _copia_atomica(origem, destino) is True:
            copiados.append(nome)
    return copiados


def exportar(pasta_origem, pasta_destino):
    """O contrario de importar: copia de pasta_origem para pasta_destino."""
    return importar(pasta_origem, pasta_destino)


def sincronizar_tudo(pasta_dados, pasta_sync):
    """Importa o que for mais novo e exporta o que for mais novo.

    Devolve {"importados": [...], "exportados": [...], "aviso": None ou str}.
    Erro de pasta (nao existe, sem gravacao) NUNCA vira excecao: vira "aviso".
    A pasta de sincronizacao e' criada se nao existir (mkdir parents=True).
    """
    pasta_dados, pasta_sync = Path(pasta_dados), _pasta_real(pasta_sync)
    # Tenta criar a pasta de sincronizacao se nao existir.
    try:
        pasta_sync.mkdir(parents=True, exist_ok=True)
    except OSError as erro:
        return {"importados": [], "exportados": [],
                "aviso": "nao consigo criar a pasta %s (%s)" % (pasta_sync, erro)}
    problema = _destino_valido(pasta_sync)
    if problema:
        return {"importados": [], "exportados": [], "aviso": problema}
    importados = importar(pasta_sync, pasta_dados)
    exportados = exportar(pasta_dados, pasta_sync)
    return {"importados": importados, "exportados": exportados, "aviso": None}


def carimbo(pasta):
    """Data do arquivo mais novo da pasta, em formato legivel (ou None).

    A tela mostra "última sincronização" com isso; None quer dizer que nada
    foi sincronizado ainda.
    """
    pasta = Path(pasta)
    mais_novo = 0.0
    for nome in arquivos_de_dados(pasta):
        try:
            t = (pasta / nome).stat().st_mtime
            if t > mais_novo:
                mais_novo = t
        except OSError:
            continue
    if not mais_novo:
        return None
    return time.strftime("%d/%m/%Y %H:%M", time.localtime(mais_novo))


def estado(pasta_dados, pasta_sync):
    """Resumo para a aba de sincronizacao: pasta, se existe, carimbo, aviso."""
    pasta_sync = _pasta_real(pasta_sync)
    if not pasta_sync.is_dir():
        try:
            pasta_sync.mkdir(parents=True, exist_ok=True)
        except OSError:
            pass
    aviso = None if pasta_sync.is_dir() else "a pasta %s nao existe" % pasta_sync
    grava = aviso is None
    if grava:
        grava = _destino_valido(pasta_sync) is None
        if not grava:
            aviso = "nao consigo gravar em %s" % pasta_sync
    return {
        "pasta": str(pasta_sync),
        "existe": pasta_sync.is_dir(),
        "gravavel": grava,
        "carimbo": carimbo(pasta_dados) if Path(pasta_dados).is_dir() else None,
        "aviso": aviso,
    }
