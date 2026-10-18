# -*- coding: utf-8 -*-
"""Contador de uso: quantas perguntas foram para a IA hoje.

Por que um arquivo separado do config.json: o config.json guarda as CHAVES
de API. Reescrever esse arquivo a cada pergunta seria arriscado demais para
o ganho. Aqui a contagem vive em `contagem.json`, na mesma pasta de dados,
e nunca encosta no config.

O que conta: so o que REALMENTE vai para a IA. Lembretes, plugins e a
busca de imagens sao locais e gratuitos, e nao entram na conta.

A contagem zera sozinha: a chave do dicionario e' a data (YYYY-MM-DD), entao
virou o dia, o contador comeca de novo. Guardamos so os ultimos 30 dias
para o arquivo nao crescer para sempre.

Nada aqui pode derrubar o programa: se o arquivo falhar, a tela apenas nao
mostra numero nenhum.
"""

import json
import os
import time
from pathlib import Path

# Mesma conta do eye_of_thundera (%LOCALAPPDATA%\Eye of Thundera).
PASTA_DADOS_ANTIGA = Path(
    os.environ.get("LOCALAPPDATA", Path.home())) / "PesquisaIA"
PASTA_DADOS = Path(
    os.environ.get("LOCALAPPDATA", Path.home())) / "Eye of Thundera"
ARQUIVO = PASTA_DADOS / "contagem.json"

DIAS_GUARDADOS = 30      # nao vale a pena guardar mais que isso


def _hoje(agora=None):
    """Data de hoje em texto (YYYY-MM-DD)."""
    return time.strftime("%Y-%m-%d", time.localtime(agora))


def _data_valida(dia):
    """True quando `dia` parece mesmo uma data YYYY-MM-DD de verdade."""
    if not isinstance(dia, str) or len(dia) != 10:
        return False
    if dia[4] != "-" or dia[7] != "-":
        return False
    ano, mes, resto = dia[:4], dia[5:7], dia[8:10]
    return ano.isdigit() and mes.isdigit() and resto.isdigit()


def _ler(arquivo=None):
    """Le o arquivo de contagem. Devolve {} quando nao ha nada de util."""
    caminho = Path(arquivo or ARQUIVO)
    if not caminho.is_file():
        return {}
    try:
        dados = json.loads(caminho.read_text(encoding="utf-8"))
    except Exception:
        return {}
    if not isinstance(dados, dict):
        return {}
    # So pares (data YYYY-MM-DD, numero inteiro positivo) valem. Chave torta
    # (por exemplo "xyz") e valor errado sao lixo de arquivo corrompido.
    limpo = {}
    for dia, valor in dados.items():
        if not _data_valida(dia):
            continue
        try:
            numero = int(valor)
        except Exception:
            continue
        if numero > 0:
            limpo[dia] = numero
    return limpo


def _gravar(dados, arquivo=None):
    """Grava com substituicao atomica (mesmo cuidado do config.json)."""
    import tempfile
    caminho = Path(arquivo or ARQUIVO)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    temporario = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=str(caminho.parent),
            prefix=".contagem-", suffix=".tmp", delete=False,
        ) as arquivo_tmp:
            json.dump(dados, arquivo_tmp, ensure_ascii=False, indent=2)
            temporario = Path(arquivo_tmp.name)
        os.replace(str(temporario), str(caminho))
        temporario = None
    finally:
        if temporario is not None:
            try:
                temporario.unlink()
            except Exception:
                pass


def hoje(arquivo=None, agora=None):
    """Quantas perguntas foram hoje. Devolve 0 se der qualquer problema."""
    try:
        dados = _ler(arquivo)
        return int(dados.get(_hoje(agora), 0))
    except Exception:
        return 0


def somar(quantidade=1, arquivo=None, agora=None):
    """Soma `quantidade` ao dia de hoje e devolve o total do dia.

    Devolve 0 (sem gravar) se o arquivo nao puder ser escrito: perder uma
    contagem e' melhor do que derrubar a conversa.
    """
    try:
        if quantidade <= 0:
            return hoje(arquivo, agora)
        caminho = Path(arquivo or ARQUIVO)
        dados = _ler(caminho)
        dia = _hoje(agora)
        dados[dia] = int(dados.get(dia, 0)) + int(quantidade)
        _guardar_so_necessario(dados, dia)
        _gravar(dados, caminho)
        return int(dados[dia])
    except Exception:
        return hoje(arquivo, agora)


def _guardar_so_necessario(dados, dia):
    """Mantem so os ultimos DIAS_GUARDADOS dias, sempre com o dia de hoje."""
    chaves = [k for k in dados if _data_valida(k)]
    if len(chaves) <= DIAS_GUARDADOS:
        return
    # O dia de hoje nunca sai; os mais antigos saem primeiro.
    outras = sorted(k for k in chaves if k != dia)
    sobrando = outras[-(DIAS_GUARDADOS - 1):] if DIAS_GUARDADOS > 1 else []
    for chave in chaves:
        if chave not in sobrando and chave != dia:
            dados.pop(chave, None)


def zerar(arquivo=None):
    """Apaga a contagem. Devolve True se limpou."""
    try:
        caminho = Path(arquivo or ARQUIVO)
        if caminho.is_file():
            caminho.unlink()
        return True
    except Exception:
        return False


def resumo(arquivo=None, agora=None):
    """O que a tela mostra: o total de hoje e se o arquivo esta acessivel."""
    try:
        caminho = Path(arquivo or ARQUIVO)
        return {"hoje": hoje(caminho, agora), "disponivel": True,
                "caminho": str(caminho)}
    except Exception:
        return {"hoje": 0, "disponivel": False, "caminho": ""}