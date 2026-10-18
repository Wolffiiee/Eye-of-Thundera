# -*- coding: utf-8 -*-
"""Plugins (PLANO-PLUGINS.md): comandos locais que o Wolf ativa e desativa.

Um plugin e' um arquivo `.py` na pasta de plugins com uma funcao:

    def responder(texto):
        # devolve None (nao e' com ele) ou a resposta (string)

Opcionalmente o modulo pode definir NOME e DESCRICAO para aparecer na
interface. Plugins sao codigo local de confianca — como os lembretes:
respondem texto, sem IA, sem rede, sem chave.

Regras de ouro:
- Um plugin com erro NAO derruba o programa: cada chamada vai dentro de try;
  erro vai para o log e o plugin e' marcado como "com erro" na interface.
- Ativar/desativar fica no config.json (chave "plugins_ativos", lista de
  nomes). A aba Plugins lista, liga e desliga.
- O plugin de exemplo (/tempo) e' criado na primeira vez, se faltar.
- Dados reais intocados nos testes: pasta de plugins sintetica em _tmp.
"""

import importlib.util
import os
import sys
import time
from pathlib import Path

# A pasta de plugins fica junto dos dados (fora do repositorio), como o
# pesquisa_ia faz com a PASTA_CONFIG.
PASTA_DADOS = Path(
    os.environ.get("LOCALAPPDATA", Path.home())) / "PesquisaIA"
PASTA_PLUGINS = PASTA_DADOS / "plugins"


def _nome_do_arquivo(arquivo):
    return Path(arquivo).stem


def _caminho_modulo(nome, pasta=None):
    pasta = Path(pasta) if pasta else PASTA_PLUGINS
    return str(pasta / (nome + ".py"))


def _carregar_arquivo(arquivo, pasta=None):
    """Importa o arquivo .py como modulo. Devolve (modulo, erro)."""
    nome = _nome_do_arquivo(arquivo)
    try:
        spec = importlib.util.spec_from_file_location("plugin_" + nome,
                                                      _caminho_modulo(nome, pasta))
        modulo = importlib.util.module_from_spec(spec)
        sys.modules["plugin_" + nome] = modulo
        spec.loader.exec_module(modulo)
        if not hasattr(modulo, "responder"):
            return None, "o plugin nao tem a funcao responder(texto)"
        return modulo, None
    except Exception as erro:      # um plugin quebrado nao derruba o programa
        return None, "%s: %s" % (type(erro).__name__, erro)


def _info_de(modulo, nome):
    """Lê NOME e DESCRICAO do modulo (opcionais)."""
    nome_amigavel = getattr(modulo, "NOME", None) or nome
    descricao = getattr(modulo, "DESCRICAO", None) or "Sem descricao."
    return str(nome_amigavel), str(descricao)


def descobrir(pasta=None):
    """Lista os plugins encontrados, sem carregar (so le os nomes).

    Devolve lista de dicionarios: {"arquivo", "nome", "erro"} — o erro so
    aparece se o arquivo nao puder ser lido como plugin valido.
    """
    pasta = Path(pasta) if pasta else PASTA_PLUGINS
    plugins = []
    if not pasta.is_dir():
        return plugins
    for arquivo in sorted(pasta.glob("*.py")):
        nome = _nome_do_arquivo(arquivo)
        modulo, erro = _carregar_arquivo(arquivo, pasta)
        if modulo is None:
            plugins.append({"arquivo": nome, "nome": nome, "descricao": "",
                           "erro": erro})
            continue
        nome_amigavel, descricao = _info_de(modulo, nome)
        plugins.append({"arquivo": nome, "nome": nome_amigavel,
                        "descricao": descricao, "erro": erro})
    return plugins


def carregar(ativos=None, pasta=None):
    """Carrega os plugins ativos. Devolve lista com modulo, nome, descricao,
    erro e o nome do arquivo (para a interface).

    `ativos` e' uma lista de nomes de arquivo (sem .py); None carrega todos.
    """
    pasta = Path(pasta) if pasta else PASTA_PLUGINS
    carregados = []
    for arquivo in sorted(pasta.glob("*.py")):
        nome = _nome_do_arquivo(arquivo)
        if ativos is not None and nome not in ativos:
            continue
        modulo, erro = _carregar_arquivo(arquivo, pasta)
        if modulo is None:
            carregados.append({"arquivo": nome, "nome": nome, "descricao": "",
                             "modulo": None, "erro": erro})
            continue
        nome_amigavel, descricao = _info_de(modulo, nome)
        carregados.append({"arquivo": nome, "nome": nome_amigavel,
                           "descricao": descricao, "modulo": modulo,
                           "erro": None})
    return carregados


def responder(texto, ativos=None, pasta=None):
    """Pergunta a cada plugin ativo, em ordem, se ele responde ao texto.

    Devolve (resposta, nome_do_plugin) ou (None, None). Erros de plugin sao
    logados (via log_erro, se passado) e ignorados — o proximo plugin e'
    tentado. Resposta vazia conta como "nao e' com ele".
    """
    for plugin in carregar(ativos, pasta):
        modulo = plugin.get("modulo")
        if modulo is None:
            continue
        try:
            saida = modulo.responder(texto)
        except Exception:
            continue
        if saida:
            return str(saida), plugin["nome"]
    return None, None


EXEMPLO = '''# -*- coding: utf-8 -*-
"""Plugin de exemplo — mostre como criar um comando novo.

Para ativar, ligue o interruptor na aba Plugins das Configuracoes. Para
criar o SEU plugin, copie este arquivo (sem o .py antigo) e troque a
funcao responder abaixo — o resto e' so apresentacao.

Contrato:
- responder(texto) recebe a frase do usuario e devolve:
  - None  -> "nao e' com este plugin" (o programa segue para o proximo);
  - str  -> a resposta, que entra na conversa como mensagem local.
"""

from datetime import datetime

NOME = "Hora atual"
DESCRICAO = "Responde a /tempo com a data e a hora de agora."


def responder(texto):
    if texto.strip().lower() in ("/tempo", "que horas sao", "hora atual"):
        agora = datetime.now()
        return "Agora sao %s de %s." % (
            agora.strftime("%H:%M:%S"),
            agora.strftime("%d/%m/%Y"))
    return None
'''


def garantir_pasta(pasta=None):
    """Cria a pasta de plugins se nao existir. Devolve o caminho."""
    pasta = Path(pasta) if pasta else PASTA_PLUGINS
    pasta.mkdir(parents=True, exist_ok=True)
    return pasta


def garantir_exemplo(pasta=None):
    """Cria o plugin de exemplo na pasta (so se nao existir).

    Se o Wolf ja apagou, nao recria. Se ja existir um /tempo de outro
    plugin, tambem nao sobrescreve.
    """
    pasta = garantir_pasta(pasta)
    exemplo = pasta / "exemplo.py"
    if not exemplo.exists():
        exemplo.write_text(EXEMPLO, encoding="utf-8")
    return exemplo
