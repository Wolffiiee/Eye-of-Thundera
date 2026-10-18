# -*- coding: utf-8 -*-
"""
Verificação automática do Eye of Thundera.

Rode SEMPRE depois de qualquer alteração no programa (duplo clique em
"verificar.bat"). Se aparecer alguma linha [FALHA], a alteração NÃO está
pronta: corrija e rode de novo até terminar com "TUDO CERTO".

O que ele confere:
  1. se o eye_of_thundera.py não tem erro de escrita (sintaxe);
  2. se as bibliotecas do requirements.txt estão instaladas;
  3. análise do código (pyflakes): nomes que não existem = FALHA;
  4. regras do projeto (ex.: proibido unbind_all de clique);
  5. teste com a janela de verdade: seleção de texto, menus que fecham ao
     clicar fora, janela de Configurações e erros escondidos nos botões.

Para criar um teste novo: copie um dos "caso(...)" ou "ok(...)" abaixo.
"""

import importlib.util
import io
import json
import py_compile
import re
import shutil
import subprocess
import sys
import threading
import time
import tkinter as tk
import traceback
import types
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

PASTA = Path(__file__).resolve().parent
ARQUIVO = PASTA / "eye_of_thundera.py"

# Onde a janela de teste aparece. O segundo monitor do Wolf comeca em
# X=1920; usar +2000+100 joga a janela para la e deixa a tela principal
# dele livre. Se um dia o monitor mudar, e so mexer aqui.
POSICAO_TESTE = "+2000+100"

falhas = []
avisos = []


def ok(msg):
    print("[OK]     " + msg)


def falha(msg):
    print("[FALHA]  " + msg)
    falhas.append(msg)


def aviso(msg):
    print("[AVISO]  " + msg)
    avisos.append(msg)

# --- 5c. memoria sem repeticao ----------------------------------------------


def testes_memoria():
    import memoria
    import eye_of_thundera as p

    problemas = memoria.autoteste()
    for problema in problemas:
        falha("memoria: %s" % problema)
    if not problemas:
        ok("memoria: sem repeticao (casos do memoria.autoteste)")
    # a ligacao com o programa: apelido repetido de outro jeito = 1 fato
    guardado = ["Prefere ser chamado de Wolf"]
    originais = (p.carregar_memoria, p.salvar_memoria)
    p.carregar_memoria = lambda: list(guardado)
    p.salvar_memoria = lambda lista: (
        guardado.__setitem__(slice(None), list(lista)) or list(lista))
    try:
        p._mesclar_memoria(["O apelido do usuario e Wolf"])
        p._mesclar_memoria(["Gosta de ser chamado de Wolf"])
        if len(guardado) == 1:
            ok("memoria: o programa nao guarda o apelido varias vezes")
        else:
            falha("memoria: apelido repetido ficou %r" % (guardado,))
    finally:
        p.carregar_memoria, p.salvar_memoria = originais


if not falhas:
    try:
        testes_memoria()
    except Exception as erro:
        falha("os testes da memoria quebraram: %r" % (erro,))

# --- 5d. tela nova (HTML): a ponte e as conversas ----------------------------


def testes_tela_nova(p):
    """Confere a ponte da tela nova (app_web.py) SEM tocar nos dados do
    Wolf: os arquivos de historico e memoria sao apontados para uma pasta
    de teste e restaurados no fim.
    """
    import shutil
    import app_web

    pasta = Path(PASTA) / "_tmp" / "teste-tela-nova"
    shutil.rmtree(pasta, ignore_errors=True)
    pasta.mkdir(parents=True, exist_ok=True)
    historico_original = p.ARQUIVO_HISTORICO
    memoria_original = p.ARQUIVO_MEMORIA
    demo_original = app_web.DEMO
    try:
        # ---- os dados do Wolf sao "escondidos" durante o teste ----
        p.ARQUIVO_HISTORICO = pasta / "historico.json"
        p.ARQUIVO_MEMORIA = pasta / "memoria.json"
        app_web.DEMO = False

        # 1. comeca vazio, sem quebrar
        ponte = app_web.Ponte()
        inicio = ponte.iniciar()
        if inicio["conversas"] == [] and inicio["mensagens"] == []:
            ok("tela nova: começa sem conversa nenhuma, sem erro")
        else:
            falha("tela nova: começou com %r" % (inicio["conversas"],))

        # 2. a conversa so e gravada quando tem mensagem de verdade
        ponte.nova_conversa()
        ponte._gravar_conversa()
        if p.carregar_conversas() == []:
            ok("tela nova: conversa vazia NÃO é gravada (nada a salvar)")
        else:
            falha("tela nova: gravou uma conversa sem mensagem")

        # 3. conversa com pergunta e resposta e gravada e aparece na lista
        ponte.mensagens = [
            {"role": "user", "text": "Oi, tudo bem?"},
            {"role": "model", "text": "Tudo ótimo! Como vai?"},
        ]
        ponte._gravar_conversa()
        salvas = p.carregar_conversas()
        if len(salvas) == 1 and len(salvas[0]["mensagens"]) == 2:
            ok("tela nova: conversa gravada e com as 2 mensagens")
        else:
            falha("tela nova: gravação ficou %r" % (salvas,))
        if salvas and salvas[0].get("titulo") == "Oi, tudo bem?":
            ok("tela nova: o título da conversa é a primeira pergunta")
        else:
            falha("tela nova: título ficou %r" % (salvas[0].get("titulo"),))

        # 4. a lista que a tela recebe vem da mais nova para a mais antiga
        ponte2 = app_web.Ponte()
        ponte2.iniciar()
        ponte2.mensagens = [
            {"role": "user", "text": "Segunda conversa"},
            {"role": "model", "text": "Oi de novo"},
        ]
        ponte2.id_atual = None
        ponte2._gravar_conversa()
        lista = ponte2.iniciar()["conversas"]
        if [c["titulo"] for c in lista] == ["Segunda conversa", "Oi, tudo bem?"]:
            ok("tela nova: a lista vem da mais nova para a mais antiga")
        else:
            falha("tela nova: ordem da lista ficou %r"
                  % [c["titulo"] for c in lista])

        # 5. abrir uma conversa traz as mensagens de volta
        alvo = [c for c in lista if c["titulo"] == "Oi, tudo bem?"][0]
        ponte2.id_atual = None
        ponte2.mensagens = []
        aberta = ponte2.abrir_conversa(alvo["id"])
        if len(aberta["mensagens"]) == 2 and aberta["atual"] == alvo["id"]:
            ok("tela nova: abrir a conversa traz as 2 mensagens")
        else:
            falha("tela nova: abrir a conversa devolveu %r" % (aberta,))
        if ponte2.abrir_conversa("conversa-que-nao-existe").get("erro"):
            ok("tela nova: conversa inexistente avisa em vez de quebrar")
        else:
            falha("tela nova: conversa inexistente devolveu algo")

        # 6. NOVA CONVERSA limpa a conversa aberta e nao apaga nada do arquivo
        antes = len(p.carregar_conversas())
        nova = ponte2.nova_conversa()
        if nova.get("atual") is None and ponte2.mensagens == []:
            ok("tela nova: 'Nova conversa' limpa a conversa aberta")
        else:
            falha("tela nova: 'Nova conversa' devolveu %r" % (nova,))
        if len(p.carregar_conversas()) == antes:
            ok("tela nova: 'Nova conversa' não apaga as conversas guardadas")
        else:
            falha("tela nova: 'Nova conversa' mexeu no arquivo")

        # 7. EXCLUIR apaga so a escolhida e devolve a lista nova
        alvo2 = [c for c in p.carregar_conversas()
                 if c.get("titulo") == "Oi, tudo bem?"][0]
        r = ponte2.excluir_conversa(alvo2["id"])
        restantes = [c.get("titulo") for c in p.carregar_conversas()]
        if restantes == ["Segunda conversa"]:
            ok("tela nova: excluir apaga só a conversa escolhida")
        else:
            falha("tela nova: depois de excluir sobrou %r" % (restantes,))
        if [c["titulo"] for c in r.get("conversas", [])] == ["Segunda conversa"]:
            ok("tela nova: excluir devolve a lista já atualizada")
        else:
            falha("tela nova: excluir devolveu lista %r" % (r.get("conversas"),))

        # 8. excluir a conversa que estava aberta limpa a tela
        alvo3 = p.carregar_conversas()[0]
        ponte2.abrir_conversa(alvo3["id"])
        r2 = ponte2.excluir_conversa(alvo3["id"])
        if r2.get("era_atual") and r2.get("atual") is None and not ponte2.mensagens:
            ok("tela nova: excluir a conversa aberta limpa a tela")
        else:
            falha("tela nova: excluir a aberta devolveu %r" % (r2,))
        if ponte2.excluir_conversa("nao-existe").get("erro"):
            ok("tela nova: excluir o que não existe avisa em vez de quebrar")
        else:
            falha("tela nova: excluir o que não existe devolveu algo")

        # 9. PROCURAR dentro das conversas (o Wolf digita sem acento e sem
        # se preocupar com maiuscula)
        p.salvar_conversas([
            {"id": "busca-1", "titulo": "Receita de bolo",
             "quando": "16/10 10:00",
             "mensagens": [
                 {"role": "user", "text": "Me da uma receita de bolo de cenoura"},
                 {"role": "model", "text": "Leve 3 cenouras grandes a ..."}]},
            {"id": "busca-2", "titulo": "Japão", "quando": "16/10 09:00",
             "mensagens": [
                 {"role": "user", "text": "Qual a capital?"},
                 {"role": "model", "text": "Tóquio, no Japão."}]},
        ])
        achados = ponte2.conversas_buscar("japao").get("achados", [])
        if [a["id"] for a in achados] == ["busca-2"]:
            ok("tela nova: procurar acha o texto mesmo digitado sem acento")
        else:
            falha("tela nova: procurar por 'japao' deu %r"
                  % ([a["id"] for a in achados],))
        if achados and "Japão" in achados[0]["trecho"]:
            ok("tela nova: a busca mostra o trecho onde achou (com o acento)")
        else:
            falha("tela nova: o trecho da busca ficou %r"
                  % (achados[0]["trecho"] if achados else None,))
        if [a["id"] for a in ponte2.conversas_buscar("CENOURA").get("achados", [])] \
                == ["busca-1"]:
            ok("tela nova: a busca não liga para maiúscula")
        else:
            falha("tela nova: procurar em maiúscula não achou")
        if [a["id"] for a in ponte2.conversas_buscar("bolo").get("achados", [])] \
                == ["busca-1"]:
            ok("tela nova: a busca olha o título da conversa também")
        else:
            falha("tela nova: procurar só no título não achou")
        if ponte2.conversas_buscar("bolo").get("achados", [])[0]["indice"] == 0:
            ok("tela nova: a busca diz em qual mensagem achou")
        else:
            falha("tela nova: o índice da mensagem ficou %r"
                  % (ponte2.conversas_buscar("bolo").get("achados", []),))
        if ponte2.conversas_buscar("z").get("vazio") and \
                not ponte2.conversas_buscar("z").get("achados"):
            ok("tela nova: uma letra sozinha não procura (acha demais)")
        else:
            falha("tela nova: uma letra sozinha dispara a busca")
        if ponte2.conversas_buscar("   ").get("achados") == [] and \
                ponte2.conversas_buscar("xablau").get("achados") == []:
            ok("tela nova: busca em branco e busca sem nada dão lista vazia")
        else:
            falha("tela nova: a busca respondeu coisa para busca vazia")
        if ponte2.conversas_buscar("Tokio").get("achados") == []:
            ok("tela nova: procurar por 'Tokio' NÃO acha 'Tóquio' "
               "(o Unicode trata os dois como coisas diferentes)")
        else:
            falha("tela nova: a busca devolveu coisa para 'Tokio'")
        if len(p.carregar_conversas()) == 2:
            ok("tela nova: procurar não apaga nem muda conversa nenhuma")
        else:
            falha("tela nova: procurar mexeu nas conversas")
        # as conversas de mentira da busca ficam no arquivo de TESTE; o
        # check do fim da secao exige arquivo vazio, entao limpar aqui
        p.salvar_conversas([])

        # 8b. FIXAR NO TOPO: a conversa vai para o comeco e volta quando solta
        p.salvar_conversas([
            {"id": "p1", "titulo": "Antiga", "quando": "10/10 10:00",
             "mensagens": [{"role": "user", "text": "pergunta antiga"}]},
            {"id": "p2", "titulo": "Do meio", "quando": "11/10 10:00",
             "mensagens": [{"role": "user", "text": "oi"}]},
            {"id": "p3", "titulo": "Recente", "quando": "12/10 10:00",
             "mensagens": [{"role": "user", "text": "e a ultima"}]},
        ])
        if [c["id"] for c in app_web._conversas_para_a_tela()] == \
                ["p3", "p2", "p1"]:
            ok("tela nova: a lista começa pela conversa mais nova")
        else:
            falha("tela nova: a lista ficou %r"
                  % ([c["id"] for c in app_web._conversas_para_a_tela()],))
        ponte_f = app_web.Ponte()
        r = ponte_f.fixar_conversa("p1")
        if [c["id"] for c in r.get("conversas", [])] == ["p1", "p3", "p2"]:
            ok("tela nova: fixar traz a conversa para o topo da lista")
        else:
            falha("tela nova: depois de fixar a lista ficou %r"
                  % ([c["id"] for c in r.get("conversas", [])],))
        salvas = [c for c in p.carregar_conversas()
                  if c.get("id") == "p1"]
        if salvas and salvas[0].get("fixada") is True:
            ok("tela nova: a conversa fica marcada como fixada no arquivo")
        else:
            falha("tela nova: a marca de fixada nao foi gravada (%r)"
                  % (salvas[0] if salvas else None,))
        if salvas and len(salvas[0].get("mensagens") or []) == 1:
            ok("tela nova: fixar não perde as mensagens da conversa")
        else:
            falha("tela nova: as mensagens sumiram ao fixar")
        r = ponte_f.fixar_conversa("p1")
        if r.get("fixada") is False and \
                [c["id"] for c in r.get("conversas", [])] == ["p3", "p2", "p1"]:
            ok("tela nova: soltar devolve a conversa para o fim da lista")
        else:
            falha("tela nova: depois de soltar ficou %r"
                  % (r.get("conversas"),))
        if ponte_f.fixar_conversa("nao-existe").get("erro"):
            ok("tela nova: fixar o que não existe avisa em vez de inventar")
        else:
            falha("tela nova: fixar o que não existe devolveu algo")
        # o programa antigo (tkinter) ignora o campo 'fixada': a conversa
        # continua aparecendo la, sem a fixacao, e nao some do arquivo
        if "fixada" not in [k for c in p.carregar_conversas()
                            for k in c if k != "fixada"]:
            ok("tela nova: o campo novo não atrapalha a leitura das conversas")
        if len(p.carregar_conversas()) == 3:
            ok("tela nova: fixar não apaga nem cria conversa")
        else:
            falha("tela nova: sobrou ou faltou conversa ao fixar (%d)"
                  % len(p.carregar_conversas()))
        # as 3 conversas de mentira ficam no arquivo de TESTE; o check do
        # fim da secao exige ele vazio, entao limpar aqui
        p.salvar_conversas([])

        # 8c. CONVERSA PRIVADA: nada e' salvo e nada entra na memoria
        p.salvar_conversas([])
        p.salvar_memoria([])
        ponte_p = app_web.Ponte(None)
        ponte_p.iniciar()
        antes_hist = len(p.carregar_conversas())
        r = ponte_p.definir_privada(True)
        if r.get("privada") is True and r.get("atual") is None \
                and not ponte_p.mensagens:
            ok("tela nova: ligar a conversa privada começa uma conversa limpa")
        else:
            falha("tela nova: ligar a conversa privada devolveu %r" % (r,))
        ponte_p.mensagens = [{"role": "user", "text": "segredo do Wolf"},
                             {"role": "model", "text": "ok"}]
        ponte_p._gravar_conversa()
        if p.carregar_conversas() == []:
            ok("tela nova: a conversa privada NÃO é gravada no arquivo")
        else:
            falha("tela nova: a conversa privada foi gravada (%r)"
                  % (p.carregar_conversas(),))
        p._mesclar_memoria(["fato que o Wolf mandou não guardar"])
        ponte_p._aprender("pergunta", "resposta", {"aprender": True}, "AIza-x")
        if p.carregar_memoria() == ["fato que o Wolf mandou não guardar"]:
            ok("tela nova: a conversa privada não faz a IA aprender")
        else:
            falha("tela nova: a memória mudou na conversa privada (%r)"
                  % (p.carregar_memoria(),))
        # O VAZAMENTO IMPORTANTE: desligar o modo com a conversa privada
        # na tela nao pode deixar a conversa ser gravada depois. Por isso
        # `definir_privada` comeca uma conversa nova nos dois sentidos.
        ponte_p.definir_privada(False)
        ponte_p.mensagens.append({"role": "user", "text": "agora pode salvar"})
        ponte_p._gravar_conversa()
        salvas = p.carregar_conversas()
        textos = [m.get("text") for c in salvas for m in (c.get("mensagens") or [])]
        if textos == ["agora pode salvar"]:
            ok("tela nova: desligar o modo privado não vaza o que foi dito antes")
        else:
            falha("tela nova: VAZOU conversa privada: %r" % (textos,))
        if len(p.carregar_conversas()) == antes_hist + 1:
            ok("tela nova: desligar o modo privado volta a salvar normalmente")
        else:
            falha("tela nova: depois de desligar o privado, %d conversa(s)"
                  % len(p.carregar_conversas()))
        p.salvar_conversas([])
        p.salvar_memoria([])

        # 10. a memoria que a tela mostra vem do arquivo, sem mudar nada
        p.salvar_memoria(["Gosta de RPG", "Mora em Santa Maria"])
        antes_mem = p.carregar_memoria()
        if app_web.Ponte().memoria_listar()["fatos"] == antes_mem:
            ok("tela nova: a aba Memória mostra o que está guardado")
        else:
            falha("tela nova: a aba Memória devolveu coisa diferente")
        if p.carregar_memoria() == antes_mem:
            ok("tela nova: só ler a Memória não muda nada")
        else:
            falha("tela nova: ler a Memória alterou o arquivo")

        # 10. no modo DEMO nada é lido do Wolf e nada é gravado
        app_web.DEMO = True
        demo = app_web.Ponte()
        inicial = demo.iniciar()
        if len(inicial["conversas"]) == 3 and inicial["mensagens"]:
            ok("tela nova: o modo exemplo mostra 3 conversas de exemplo")
        else:
            falha("tela nova: o modo exemplo mostrou %d conversa(s)"
                  % len(inicial["conversas"]))
        # "Nova conversa" pode funcionar no exemplo (ela nao grava nada),
        # mas EXCLUIR tem que continuar barrado: as conversas mostradas
        # ali sao de mentira e o arquivo de verdade e' do Wolf.
        nova = demo.nova_conversa()
        if nova.get("atual") is None and not demo.mensagens:
            ok("tela nova: no modo exemplo, 'Nova conversa' limpa a tela")
        else:
            falha("tela nova: no modo exemplo, 'Nova conversa' devolveu %r"
                  % (nova,))
        if demo.excluir_conversa("demo-1").get("erro"):
            ok("tela nova: no modo exemplo, excluir conversa avisa e não faz")
        else:
            falha("tela nova: no modo exemplo respondeu que excluiu conversa")
        if p.carregar_conversas() == []:
            ok("tela nova: o teste todo não deixou conversa nenhuma no disco")
        else:
            falha("tela nova: sobrou conversa no arquivo: %r"
                  % (p.carregar_conversas(),))
    finally:
        p.ARQUIVO_HISTORICO = historico_original
        p.ARQUIVO_MEMORIA = memoria_original
        app_web.DEMO = demo_original
        shutil.rmtree(pasta, ignore_errors=True)



# --- 5e. tela nova: a IA de verdade (o passo 3) ----------------------------


class _JanelaDeMentira:
    """Janela de mentira: guarda o que o Python tentou falar para a tela."""

    def __init__(self):
        self.eventos = []
        self.scriptos = []

    def evaluate_js(self, script):
        self.scriptos.append(script)
        # chega "window.PIA.evento({...})": o que importa e' o objeto
        dentro = script[script.index("(") + 1:script.rindex(")")]
        self.eventos.append(json.loads(dentro))

    def tipos(self):
        return [e.get("tipo") for e in self.eventos]

    def unico(self, tipo):
        achados = [e for e in self.eventos if e.get("tipo") == tipo]
        return achados[0] if achados else None


class _ThreadNaHora:
    """Thread que roda na hora (o teste nao pode esperar a IA de verdade).

    O app_web chama `Thread(target=..., args=(...), daemon=True)`, entao
    os nomes dos parâmetros precisam bater com os do threading de verdade.
    """

    def __init__(self, target=None, args=(), **_ignorado):
        self._alvo, self._args, self.rodou = target, args, False

    def start(self):
        self.rodou = True
        self._alvo(*self._args)


class _ThreadsNaHora:
    """Finge o `threading` do app_web e anota o que foi criado.

    A tela nova trabalha em thread para a janela nao travar. Aqui tudo roda
    na hora, e `rodadas` fica com o nome de cada thread, para o teste
    conferir que a tarefa de aprender foi chamada (ou nao).
    """

    def __init__(self):
        self.rodadas = []

    def Thread(self, target=None, args=(), **_ignorado):
        self.rodadas.append(getattr(target, "__name__", str(target)))
        return _ThreadNaHora(target=target, args=args)


# Resposta com acento e emoji: é o que pega o ensure_ascii=False quebrado
# (sem ele o ç e o 🚀 chegariam na tela como "\\u00e7" e "\\ud83d\\ude80").
RESPOSTA_TESTE = "Claro! Voce tem razão: çãé, ação e 🚀 (resposta de teste)"


def testes_tela_nova_ia(p):
    """O passo 3: enviar pergunta e a resposta voltando por evento.

    NAO chama a IA de verdade (gastaria a cota do Wolf e depends de
    internet): o `conversar`/`perguntar` sao trocados por uma resposta de
    mentira. O arquivo de configuracao tambem aponta para uma pasta de
    teste, entao a chave do Wolf nem chega a ser lida.
    """
    import app_web

    pasta = Path(PASTA) / "_tmp" / "teste-tela-nova-ia"
    shutil.rmtree(pasta, ignore_errors=True)
    pasta.mkdir(parents=True, exist_ok=True)

    chamadas = []
    aprendidas = []

    def ia_de_mentira(api_key, modelo, historico, pergunta, usar_contexto,
                      progresso=None, cfg=None, id_atual=None, consulta=None,
                      profundo=False):
        """Responde na hora, como o `eye_of_thundera.conversar`/`perguntar`."""
        chamadas.append({"api_key": api_key, "pergunta": pergunta,
                         "historico": list(historico), "id_atual": id_atual,
                         "consulta": consulta})
        if progresso:
            progresso("Procurando na web")
            progresso("Consultando a inteligência artificial")
        return RESPOSTA_TESTE, [], [], "Gemini"

    def ia_quebrada(*_args, **_kw):
        raise RuntimeError("API key not valid: 401 UNAUTHENTICATED")

    def ia_sem_internet(*_args, **_kw):
        raise RuntimeError("ConnectionError: a internet caiu")

    def decidir_de_mentira(chave, texto, historico, modo="auto"):
        return {"modo": "amigo", "consulta": texto}

    def aprender_de_mentira(chave, pergunta, resposta):
        aprendidas.append((pergunta, resposta))

    guardados = {
        "ARQUIVO_HISTORICO": p.ARQUIVO_HISTORICO,
        "ARQUIVO_MEMORIA": p.ARQUIVO_MEMORIA,
        "ARQUIVO_CONFIG": p.ARQUIVO_CONFIG,
        "_memoria_cache": p._memoria_cache,
        "conversar": p.conversar,
        "perguntar": p.perguntar,
        "_decidir_modo": p._decidir_modo,
        "aprender_com_o_usuario": p.aprender_com_o_usuario,
        "threading": app_web.threading,
        "DEMO": app_web.DEMO,
    }
    try:
        # ---- os dados do Wolf estao "escondidos" durante o teste ----
        p.ARQUIVO_HISTORICO = pasta / "historico.json"
        p.ARQUIVO_MEMORIA = pasta / "memoria.json"
        p.ARQUIVO_CONFIG = pasta / "config.json"
        # a memoria tem um cache dentro do modulo: sem zerar aqui, o teste
        # de cima ("Gosta de RPG") apareceria como se fosse do Wolf
        p._memoria_cache = None
        p.conversar = ia_de_mentira
        p.perguntar = ia_de_mentira
        p._decidir_modo = decidir_de_mentira
        p.aprender_com_o_usuario = aprender_de_mentira
        app_web.DEMO = False
        threads = _ThreadsNaHora()
        app_web.threading = threads

        def com_chave(aprender=True):
            p._gravar_json(p.ARQUIVO_CONFIG,
                           {"api_key": "AIza-chave-de-teste",
                            "aprender": aprender})

        # 1. SEM CHAVE: a tela e avisada na hora, sem chamar a IA
        com_chave()
        p._gravar_json(p.ARQUIVO_CONFIG, {})
        janela = _JanelaDeMentira()
        ponte = app_web.Ponte(janela)
        chamadas.clear()
        resposta = ponte.enviar("Olá")
        if resposta.get("erro") == "sem_chave":
            ok("tela nova: sem chave, o envio avisa 'sem_chave' na hora")
        else:
            falha("tela nova: sem chave o envio devolveu %r" % (resposta,))
        if not chamadas and not threads.rodadas and not janela.eventos:
            ok("tela nova: sem chave, a IA nem é chamada e nada é desenhado")
        else:
            falha("tela nova: sem chave, mas a IA foi chamada (%r)"
                  % (chamadas,))

        # 2. pergunta vazia e envio com a tela ocupada sao recusados
        if ponte.enviar("   ").get("erro"):
            ok("tela nova: pergunta em branco não é enviada")
        else:
            falha("tela nova: pergunta em branco foi aceita")
        ponte.ocupado = True
        if ponte.enviar("outra coisa").get("erro"):
            ok("tela nova: não aceita segunda pergunta enquanto responde")
        else:
            falha("tela nova: aceitou segunda pergunta enquanto respondia")
        ponte.ocupado = False

        # 3. RESPOSTA COMPLETA: devolve na hora e o texto volta por evento
        com_chave()
        janela = _JanelaDeMentira()
        ponte = app_web.Ponte(janela)
        chamadas.clear()
        resposta = ponte.enviar("Me explica o que é IA")
        tipos = janela.tipos()
        if resposta == {}:
            ok("tela nova: enviar volta na hora (a janela não trava)")
        else:
            falha("tela nova: enviar devolveu %r" % (resposta,))
        if "resposta" in tipos:
            ok("tela nova: a resposta chega como evento 'resposta'")
        else:
            falha("tela nova: os eventos foram %r" % (tipos,))
        if janela.unico("resposta") and \
                janela.unico("resposta").get("texto") == RESPOSTA_TESTE:
            ok("tela nova: o texto da resposta chega inteiro")
        else:
            falha("tela nova: o evento 'resposta' veio %r"
                  % (janela.unico("resposta"),))
        if "etapa" in tipos:
            ok("tela nova: a tela é avisada do que a IA está fazendo (etapa)")
        else:
            falha("tela nova: nenhum evento 'etapa' chegou (%r)" % (tipos,))
        if tipos.index("etapa") < tipos.index("resposta"):
            ok("tela nova: a etapa vem antes da resposta")
        else:
            falha("tela nova: a ordem dos eventos ficou %r" % (tipos,))
        if not ponte.ocupado:
            ok("tela nova: depois da resposta a tela volta a aceitar")
        else:
            falha("tela nova: a tela ficou travada depois da resposta")

        # 4. o texto vai com acento e emoji de verdade (ensure_ascii=False)
        if any("🚀" in s and "ç" in s and "\\u" not in s
               for s in janela.scriptos):
            ok("tela nova: acento e emoji chegam crus, sem \\u escapado")
        else:
            falha("tela nova: o texto para a tela foi escapado: %r"
                  % (janela.scriptos[-1:],))

        # 5. a conversa e gravada e a lista da esquerda e atualizada
        salvas = p.carregar_conversas()
        if len(salvas) == 1 and salvas[0].get("titulo") == \
                "Me explica o que é IA" and \
                [m["role"] for m in salvas[0]["mensagens"]] == \
                ["user", "model"]:
            ok("tela nova: a pergunta e a resposta foram gravadas juntas")
        else:
            falha("tela nova: a gravação ficou %r" % (salvas,))
        lista = janela.unico("conversas")
        if lista and [c.get("titulo") for c in lista.get("conversas", [])] \
                == ["Me explica o que é IA"] and \
                lista.get("atual") == salvas[0]["id"]:
            ok("tela nova: a lista da esquerda é atualizada com a conversa")
        else:
            falha("tela nova: o evento 'conversas' veio %r" % (lista,))

        # 6. a segunda pergunta continua a MESMA conversa e leva o historico
        chamadas.clear()
        ponte.enviar("E como ela aprende?")
        if len(p.carregar_conversas()) == 1:
            ok("tela nova: a segunda pergunta continua a mesma conversa")
        else:
            falha("tela nova: a segunda pergunta abriu outra conversa (%d)"
                  % len(p.carregar_conversas()))
        historico = chamadas[0]["historico"] if chamadas else []
        if [m["role"] for m in historico] == ["user", "model"] and \
                historico[0]["text"] == "Me explica o que é IA":
            ok("tela nova: a IA recebe a conversa anterior como histórico")
        else:
            falha("tela nova: o histórico da IA ficou %r" % (historico,))
        if chamadas and chamadas[0].get("id_atual") == salvas[0]["id"]:
            ok("tela nova: a conversa aberta não entra duas vezes no contexto")
        else:
            falha("tela nova: id_atual ficou %r"
                  % (chamadas[0].get("id_atual") if chamadas else None,))

        # 7. ERRO DE CHAVE: vem em portugues e a tela abre as Configuracoes
        p.conversar = ia_quebrada
        p.perguntar = ia_quebrada
        janela = _JanelaDeMentira()
        ponte = app_web.Ponte(janela)
        ponte.enviar("Oi")
        erro = janela.unico("erro")
        if erro and "chave" in erro.get("texto", "").lower() \
                and "401" not in erro.get("texto", ""):
            ok("tela nova: erro de chave vira frase em português")
        else:
            falha("tela nova: o evento de erro veio %r" % (erro,))
        if erro and erro.get("chave") is True:
            ok("tela nova: erro de chave avisa a tela para abrir as Config.")
        else:
            falha("tela nova: o evento de erro nao marcou 'chave': %r"
                  % (erro,))
        if ponte.mensagens and ponte.mensagens[-1].get("role") == "erro":
            ok("tela nova: o erro também fica na conversa da tela")
        else:
            falha("tela nova: o erro não entrou na conversa: %r"
                  % (ponte.mensagens,))

        # 8. erro que NAO e de chave nao manda a tela para as Configuracoes
        p.conversar = ia_sem_internet
        p.perguntar = ia_sem_internet
        janela = _JanelaDeMentira()
        ponte = app_web.Ponte(janela)
        ponte.enviar("Oi")
        erro = janela.unico("erro")
        if erro and erro.get("chave") is False:
            ok("tela nova: erro de internet não mexe nas Configurações")
        else:
            falha("tela nova: erro de internet veio %r" % (erro,))

        # 9. a IA DECIDE o modo: pesquisa quando o roteador manda pesquisar
        p.conversar = ia_de_mentira
        p.perguntar = ia_de_mentira
        p._decidir_modo = lambda c, t, h, modo="auto": {
            "modo": "pesquisa", "consulta": "IA generativa"}
        chamadas.clear()
        janela = _JanelaDeMentira()
        ponte = app_web.Ponte(janela)
        ponte.enviar("O que é IA generativa?")   # nao e' pedido de noticia
        if chamadas and chamadas[0].get("consulta") == "IA generativa":
            ok("tela nova: em modo pesquisa, a busca usa o assunto do "
               "roteador")
        else:
            falha("tela nova: a consulta da busca ficou %r"
                  % (chamadas[0].get("consulta") if chamadas else None,))
        # PEDIDO DE NOTÍCIA é tratado à parte, igual ao programa antigo: a
        # busca sai com a pergunta inteira, não com o assunto abreviado.
        chamadas.clear()
        ponte.enviar("Pesquisa as notícias de tecnologia de hoje")
        if chamadas and chamadas[0].get("consulta") == \
                "Pesquisa as notícias de tecnologia de hoje":
            ok("tela nova: pedido de notícia busca a pergunta inteira")
        else:
            falha("tela nova: a consulta de notícia ficou %r"
                  % (chamadas[0].get("consulta") if chamadas else None,))
        p._decidir_modo = decidir_de_mentira

        # 10. a IA pode aprender sobre o Wolf, em segundo plano e calado
        aprendidas.clear()
        com_chave(aprender=True)
        janela = _JanelaDeMentira()
        ponte = app_web.Ponte(janela)
        ponte.enviar("Gosto de jogar RPG")
        if len(aprendidas) == 1 and aprendidas[0][0] == "Gosto de jogar RPG":
            ok("tela nova: a IA é mandada aprender depois de responder")
        else:
            falha("tela nova: a tarefa de aprender rodou %d vez(es)"
                  % len(aprendidas))
        if any(r == "tarefa" for r in threads.rodadas):
            ok("tela nova: aprender roda fora da tela (em segundo plano)")
        else:
            falha("tela nova: nenhuma thread de aprender foi criada (%r)"
                  % (threads.rodadas,))

        # 11. com 'aprender' desligado, nada e aprendido
        aprendidas.clear()
        com_chave(aprender=False)
        ponte = app_web.Ponte(_JanelaDeMentira())
        ponte.enviar("Moro em Porto Alegre")
        if not aprendidas:
            ok("tela nova: com 'aprender' desligado, a IA não aprende nada")
        else:
            falha("tela nova: aprendeu %r com a opção desligada"
                  % (aprendidas,))

        # 12. MODO EXEMPLO: a IA responde, mas NADA é gravado
        app_web.DEMO = True
        aprendidas.clear()
        janela = _JanelaDeMentira()
        ponte = app_web.Ponte(janela)
        ponte.iniciar()
        chamadas.clear()
        ponte.enviar("Me conta uma curiosidade")
        if janela.unico("resposta"):
            ok("tela nova: no modo exemplo a IA de verdade também responde")
        else:
            falha("tela nova: no modo exemplo a IA não respondeu (%r)"
                  % (janela.tipos(),))
        if not aprendidas:
            ok("tela nova: no modo exemplo a IA não aprende nada")
        else:
            falha("tela nova: no modo exemplo aprendeu %r" % (aprendidas,))
        app_web.DEMO = False
        if ponte.mensagens[-1].get("role") == "model":
            ok("tela nova: no modo exemplo a resposta entra na conversa da tela")
        else:
            falha("tela nova: a conversa do exemplo ficou %r"
                  % (ponte.mensagens[-1],))

        # 13. a memoria do Wolf nao foi mexida e o teste rodou isolado
        if p.ARQUIVO_HISTORICO == pasta / "historico.json" and \
                p.ARQUIVO_CONFIG == pasta / "config.json":
            ok("tela nova: o teste da IA rodou com os arquivos do Wolf "
               "escondidos")
        else:
            falha("tela nova: o teste da IA usou o arquivo de verdade (%r)"
                  % (p.ARQUIVO_HISTORICO,))
        if p.carregar_memoria() == []:
            ok("tela nova: a IA da tela nova não escreveu nada na Memória")
        else:
            falha("tela nova: sobrou memória na pasta de teste: %r"
                  % (p.carregar_memoria(),))
    finally:
        for nome, valor in guardados.items():
            if nome == "DEMO":
                app_web.DEMO = valor
            elif nome == "threading":
                app_web.threading = valor
            else:
                setattr(p, nome, valor)
        shutil.rmtree(pasta, ignore_errors=True)


if not falhas:
    try:
        testes_tela_nova(importlib.import_module("eye_of_thundera"))
    except Exception as erro:
        falha("os testes da tela nova quebraram: %r" % (erro,))

if not falhas:
    try:
        testes_tela_nova_ia(importlib.import_module("eye_of_thundera"))
    except Exception as erro:
        falha("os testes da IA da tela nova quebraram: %r" % (erro,))


def testes_tela_nova_microfone(p):
    """Passo 4: o microfone da tela nova.

    NAO grava audio de verdade e NAO chama a IA de verdade (o microfone do
    Wolf ficaria aberto e a cota dele seria gasta). O `voz` inteiro e
    trocado por um de mentira, e o arquivo de configuracao aponta para
    uma pasta de teste, entao nem a chave nem as conversas do Wolf sao
    tocadas.
    """
    import app_web

    pasta = Path(PASTA) / "_tmp" / "teste-tela-nova-mic"
    shutil.rmtree(pasta, ignore_errors=True)
    pasta.mkdir(parents=True, exist_ok=True)

    gravados = []      # o que o microfone de mentira "ouviu"
    pedidos = []       # cada transcricao pedida (modelos, wav)

    class GravadorDeMentira:
        """Finge o `voz.Gravador`: nada de som, so marca o que foi feito."""

        def __init__(self):
            self.parado = False

        def iniciar(self):
            gravados.append("iniciou")

        def parar(self):
            self.parado = True
            gravados.append("parou")
            return b"onda-de-som-de-mentira"

    def microfone_de_mentira(**muda):
        """Monta um `voz` falso. `muda` troca o que o teste quiser."""
        falso = types.SimpleNamespace()
        falso.TEM_SOM = True
        falso.Gravador = GravadorDeMentira
        falso.microfone_disponivel = lambda: True
        falso.wav_tem_som = lambda wav: True
        falso.transcrever = (lambda cliente, modelos, wav:
                             pedidos.append({"modelos": list(modelos),
                                             "wav": wav}) or
                             "O que foi falado: çãé 🚀")
        falso.microfone_erro = (lambda erro: " microfone: %s" % (erro,))
        for nome, valor in muda.items():
            setattr(falso, nome, valor)
        return falso

    def com_chave(voz_enviar=False):
        p._gravar_json(p.ARQUIVO_CONFIG,
                       {"api_key": "AIza-chave-de-teste",
                        "voz_enviar": voz_enviar})

    def ponte_limpa():
        gravados.clear()
        pedidos.clear()
        janela = _JanelaDeMentira()
        return app_web.Ponte(janela), janela

    def ja_gravando(falso):
        """Coloca o microfone falso, liga a gravacao e devolve a ponte."""
        p.voz = falso
        ponte, _janela = ponte_limpa()
        ponte.mic_alternar()
        return ponte

    guardados = {"ARQUIVO_CONFIG": p.ARQUIVO_CONFIG,
                 "ARQUIVO_HISTORICO": p.ARQUIVO_HISTORICO,
                 "voz": p.voz,
                 "_criar_cliente": p._criar_cliente,
                 "threading": app_web.threading,
                 "DEMO": app_web.DEMO,
                 "VOZ_REAL": app_web.VOZ_REAL,
                 "VOZ_FALSA": app_web.VOZ_FALSA}
    try:
        p.ARQUIVO_CONFIG = pasta / "config.json"
        p.ARQUIVO_HISTORICO = pasta / "historico.json"
        p._criar_cliente = lambda api_key: "cliente-de-teste"
        app_web.threading = _ThreadsNaHora()
        app_web.DEMO = False

        # 1. SEM SOM: fala em portugues e nao finge que gravou
        p.voz = microfone_de_mentira(TEM_SOM=False)
        com_chave()
        ponte, janela = ponte_limpa()
        resposta = ponte.mic_alternar()
        if "sem a biblioteca de som" in str(resposta.get("erro", "")):
            ok("microfone: avisando que o programa foi montado sem som")
        else:
            falha("microfone: sem som devolveu %r" % (resposta,))
        if not janela.unico("gravando") and not ponte.gravando:
            ok("microfone: sem som ele não finge que está gravando")
        else:
            falha("microfone: sem som ele disse que estava gravando")

        # 2. SEM MICROFONE LIGADO
        p.voz = microfone_de_mentira(microfone_disponivel=lambda: False)
        ponte, _janela = ponte_limpa()
        resposta = ponte.mic_alternar()
        if "microfone ligado" in str(resposta.get("erro", "")):
            ok("microfone: avisando que não achou microfone ligado")
        else:
            falha("microfone: sem microfone devolveu %r" % (resposta,))

        # 3. SEM CHAVE: avisa para a tela abrir as Configuracoes
        p.voz = microfone_de_mentira()
        p._gravar_json(p.ARQUIVO_CONFIG, {})
        ponte, _janela = ponte_limpa()
        resposta = ponte.mic_alternar()
        if resposta.get("erro") == "sem_chave_voz" and not ponte.gravando:
            ok("microfone: sem chave pede a chave e não grava")
        else:
            falha("microfone: sem chave devolveu %r" % (resposta,))

        # 4. GRAVAR: o primeiro clique liga, e a tela e avisada na hora
        com_chave()
        ponte, janela = ponte_limpa()
        resposta = ponte.mic_alternar()
        ligado = janela.unico("gravando")
        if resposta.get("gravando") and ponte.gravando and gravados == ["iniciou"]:
            ok("microfone: o primeiro clique começa a gravar")
        else:
            falha("microfone: o primeiro clique devolveu %r (gravou %r)"
                  % (resposta, gravados))
        if ligado and ligado.get("ligado") is True:
            ok("microfone: a tela é avisada que começou a gravar")
        else:
            falha("microfone: nenhum aviso de 'começou a gravar' (%r)"
                  % (ligado,))

        # 5. PARAR: o segundo clique para e o texto falado entra na caixa
        janela.eventos.clear()
        resposta = ponte.mic_alternar()
        voz = janela.unico("voz")
        desligado = [e for e in janela.eventos
                     if e.get("tipo") == "gravando"
                     and e.get("ligado") is False]
        if resposta.get("transcrevendo") and "parou" in gravados:
            ok("microfone: o segundo clique para de gravar")
        else:
            falha("microfone: o segundo clique devolveu %r (gravados %r)"
                  % (resposta, gravados))
        if desligado:
            ok("microfone: a tela é avisada que parou de gravar")
        else:
            falha("microfone: nenhum aviso de 'parou'")
        if voz and voz.get("texto") == "O que foi falado: çãé 🚀":
            ok("microfone: o que foi falado chega na caixa, com acento e emoji")
        else:
            falha("microfone: o texto falado veio %r" % (voz,))
        if ponte.ocupado is False:
            ok("microfone: depois de transcrever, o programa volta a aceitar")
        else:
            falha("microfone: ficou travado depois de transcrever")

        # 6. o texto falado NAO e' enviado sozinho
        if voz and voz.get("enviar") is False:
            ok("microfone: o texto falado NÃO é enviado sozinho (Wolf confere)")
        else:
            falha("microfone: o texto falado foi marcado para enviar (%r)"
                  % (voz,))

        # 7. a lista de modelos e' a mesma do programa antigo (com reservas).
        #    Repare que MODELOS_RESERVA ja comeca pelo modelo bom: a regra
        #    e' "o modelo escolhido primeiro, e os outros uma vez cada".
        escolhido = p.MODELO_PADRAO
        esperado = [escolhido] + [m for m in p.MODELOS_RESERVA
                                  if m != escolhido]
        if pedidos and pedidos[0]["modelos"] == esperado:
            ok("microfone: tenta o modelo bom e os de reserva, como antes")
        else:
            falha("microfone: os modelos pedidos foram %r (esperado %r)"
                  % (pedidos[0]["modelos"] if pedidos else None, esperado))

        # 8. SILENCIO: "não ouvi nada" e nenhum texto na caixa
        ponte = ja_gravando(microfone_de_mentira(wav_tem_som=lambda wav: False))
        janela = ponte._janela
        janela.eventos.clear()
        resposta = ponte.mic_alternar()
        if "Não ouvi nada" in str(resposta.get("erro", "")) and \
                not janela.unico("voz"):
            ok("microfone: quando não ouve nada, avisa e não inventa texto")
        else:
            falha("microfone: no silêncio devolveu %r" % (resposta,))

        # 9. TRANSCRICAO QUE FALHA: vira frase em portugues na tela
        def transcrever_quebrado(cliente, modelos, wav):
            raise RuntimeError("API key not valid: 401 UNAUTHENTICATED")

        ponte = ja_gravando(microfone_de_mentira(transcrever=transcrever_quebrado))
        janela = ponte._janela
        janela.eventos.clear()
        ponte.mic_alternar()
        erro = janela.unico("voz_erro")
        if erro and "chave" in str(erro.get("texto", "")).lower():
            ok("microfone: chave recusada vira frase em português na tela")
        else:
            falha("microfone: o erro de chave veio %r" % (erro,))
        if erro and erro.get("chave") is True:
            ok("microfone: erro de chave avisa a tela para abrir as Config.")
        else:
            falha("microfone: o erro não avisou das Configurações (%r)"
                  % (erro,))

        # 10. FALHA DO MICROFONE AO LIGAR: vira frase, sem travar
        class GravadorQuebrado:
            def iniciar(self):
                raise RuntimeError("dispositivo ocupado")

        p.voz = microfone_de_mentira(Gravador=GravadorQuebrado)
        ponte, _janela = ponte_limpa()
        resposta = ponte.mic_alternar()
        if "dispositivo ocupado" in str(resposta.get("erro", "")) and \
                not ponte.gravando:
            ok("microfone: microfone ocupado avisa e não trava o programa")
        else:
            falha("microfone: microfone ocupado devolveu %r" % (resposta,))

        # 11. clicou no microfone com uma conversa rodando: espera
        p.voz = microfone_de_mentira()
        ponte, _janela = ponte_limpa()
        ponte.ocupado = True
        resposta = ponte.mic_alternar()
        ponte.ocupado = False
        if "Aguarde" in str(resposta.get("erro", "")):
            ok("microfone: não grava por cima de uma resposta em andamento")
        else:
            falha("microfone: com a tela ocupada devolveu %r" % (resposta,))

        # 12. MODO EXEMPLO: o microfone e' de mentira, sem chave nenhuma
        app_web.DEMO = True
        app_web.VOZ_REAL = False
        app_web.VOZ_FALSA = True
        app_web.threading = threading
        ponte, janela = ponte_limpa()
        ponte.mic_alternar()
        janela.eventos.clear()
        ponte.mic_alternar()
        if janela.unico("voz"):
            ok("microfone: no modo exemplo ele finge que ouviu algo")
        else:
            falha("microfone: no modo exemplo não respondeu (%r)"
                  % (janela.tipos(),))
        if not gravados:
            ok("microfone: no modo exemplo NENHUM som de verdade e' gravado")
        else:
            falha("microfone: no modo exemplo gravou %r" % (gravados,))

        # 12b. com --voz, o microfone de verdade e' usado, mas ainda sem
        #      gravar nada. E' assim que o Wolf testa falando de verdade.
        app_web.DEMO = True
        app_web.VOZ_REAL = True
        app_web.VOZ_FALSA = False
        p.voz = microfone_de_mentira()
        ponte, janela = ponte_limpa()
        ponte.mic_alternar()
        janela.eventos.clear()
        ponte.mic_alternar()
        if janela.unico("voz") and gravados == ["iniciou", "parou"]:
            ok("microfone: com --voz ele grava de verdade (e transcreve)")
        else:
            falha("microfone: com --voz ficou %r (gravados %r)"
                  % (janela.tipos(), gravados))
        app_web.DEMO = False

        # 13. NADA foi gravado: nem conversa, nem arquivo do Wolf
        if p.ARQUIVO_CONFIG == pasta / "config.json" and \
                p.ARQUIVO_HISTORICO == pasta / "historico.json":
            ok("microfone: o teste rodou com os arquivos do Wolf escondidos")
        else:
            falha("microfone: o teste usou o arquivo de verdade (%r)"
                  % (p.ARQUIVO_CONFIG,))
        if not (pasta / "historico.json").exists():
            ok("microfone: falar não cria conversa nenhuma no disco")
        else:
            falha("microfone: sobrou conversa do microfone no disco")
    finally:
        for nome, valor in guardados.items():
            if nome == "threading":
                app_web.threading = valor
            elif nome in ("DEMO", "VOZ_REAL", "VOZ_FALSA"):
                setattr(app_web, nome, valor)
            else:
                setattr(p, nome, valor)
        shutil.rmtree(pasta, ignore_errors=True)


if not falhas:
    try:
        testes_tela_nova_microfone(importlib.import_module("eye_of_thundera"))
    except Exception as erro:
        falha("os testes do microfone quebraram: %r" % (erro,))


def testes_tela_nova_config(p):
    """Passo 5: Configuracoes e Memoria da tela nova gravam de verdade
    (numa pasta de teste, nunca nos arquivos do Wolf)."""
    import app_web

    pasta = Path(PASTA) / "_tmp" / "teste-tela-nova-config"
    shutil.rmtree(pasta, ignore_errors=True)
    pasta.mkdir(parents=True, exist_ok=True)
    guardados = {"ARQUIVO_MEMORIA": p.ARQUIVO_MEMORIA,
                 "ARQUIVO_CONFIG": p.ARQUIVO_CONFIG,
                 "_memoria_cache": p._memoria_cache,
                 "testar_chave": p.testar_chave}
    demo = app_web.DEMO
    try:
        p.ARQUIVO_MEMORIA = pasta / "memoria.json"
        p.ARQUIVO_CONFIG = pasta / "config.json"
        p._memoria_cache = None
        app_web.DEMO = False
        ponte = app_web.Ponte(None)

        r = ponte.definir_modo("sempre")
        if r.get("cfg", {}).get("modo_pesquisa") == "sempre" and \
                p._ler_json(p.ARQUIVO_CONFIG, {}).get("modo_pesquisa") == "sempre":
            ok("tela nova: definir_modo grava o modo da web")
        else:
            falha("tela nova: definir_modo devolveu %r" % (r,))
        if "erro" in ponte.definir_modo("xyz"):
            ok("tela nova: modo invalido e recusado")
        else:
            falha("tela nova: modo invalido foi aceito")

        ponte.config_salvar({"aprender": False, "web_corretor": False,
                             "chaves": {"api_key": "AIzaCHAVE1234",
                                        "campo_falso": "x"}})
        cfg = p._ler_json(p.ARQUIVO_CONFIG, {})
        if cfg.get("aprender") is False and cfg.get("corretor") is False \
                and cfg.get("api_key") == "AIzaCHAVE1234" \
                and "campo_falso" not in cfg:
            ok("tela nova: config_salvar grava opcoes e chave, ignora campo falso")
        else:
            falha("tela nova: config_salvar gravou %r" % (cfg,))
        ponte.config_salvar({"chaves": {"api_key": ""}})
        if p._ler_json(p.ARQUIVO_CONFIG, {}).get("api_key") == "AIzaCHAVE1234":
            ok("tela nova: chave vazia nao apaga a chave salva")
        else:
            falha("tela nova: chave vazia apagou a chave salva")

        p.testar_chave = lambda chave, modelo: "OK"
        if ponte.testar_chave("api_key", "").get("ok") is True:
            ok("tela nova: testar_chave usa a chave ja salva quando o campo vem vazio")
        else:
            falha("tela nova: testar_chave com chave salva falhou")
        def quebra(chave, modelo):
            raise RuntimeError("401 UNAUTHENTICATED")
        p.testar_chave = quebra
        r = ponte.testar_chave("api_key", "AIzaRUIM")
        if r.get("ok") is False and r.get("texto"):
            ok("tela nova: testar_chave com chave ruim explica em portugues")
        else:
            falha("tela nova: testar_chave ruim devolveu %r" % (r,))

        r = ponte.memoria_adicionar("Gosta de RPG")
        r = ponte.memoria_adicionar("Gosta de RPG")
        if r.get("fatos") == ["Gosta de RPG"]:
            ok("tela nova: memoria_adicionar nao repete fato")
        else:
            falha("tela nova: memoria ficou %r" % (r,))
        ponte.memoria_adicionar("Mora em Santa Maria")
        r = ponte.memoria_apagar("Gosta de RPG")
        if r.get("fatos") == ["Mora em Santa Maria"]:
            ok("tela nova: memoria_apagar tira so o item escolhido")
        else:
            falha("tela nova: memoria_apagar deixou %r" % (r,))
        if "mudou" in ponte.memoria_organizar():
            ok("tela nova: memoria_organizar responde")
        else:
            falha("tela nova: memoria_organizar nao respondeu")
        if ponte.memoria_apagar_tudo().get("fatos") == []:
            ok("tela nova: memoria_apagar_tudo esvazia")
        else:
            falha("tela nova: memoria_apagar_tudo nao esvaziou")

        # 7. EDITAR um item: e' o que o Wolf faz clicando no texto
        ponte.memoria_adicionar("Moro em Santa Maria")
        ponte.memoria_adicionar("Gosta de RPG")
        antes_editar = p.carregar_memoria()
        r = ponte.memoria_editar("Gosta de RPG", "Gosta de RPG de mesa")
        depois = r.get("fatos") or []
        if "Gosta de RPG de mesa" in depois and "Gosta de RPG" not in depois:
            ok("tela nova: editar a memória troca o texto do item")
        else:
            falha("tela nova: editar deixou %r" % (depois,))
        if [f for f in antes_editar if f != "Gosta de RPG"] == \
                [f for f in depois if f != "Gosta de RPG de mesa"]:
            ok("tela nova: editar não mexe nos outros itens da memória")
        else:
            falha("tela nova: editar mudou os outros itens (%r -> %r)"
                  % (antes_editar, depois))
        if ponte.memoria_editar("item que nao existe", "x").get("erro"):
            ok("tela nova: editar o que não existe avisa em vez de inventar")
        else:
            falha("tela nova: editar o que não.exists devolveu algo")
        if ponte.memoria_editar("Gosta de RPG de mesa", "  ").get("erro"):
            ok("tela nova: editar para texto vazio é recusado")
        else:
            falha("tela nova: deixou um item vazio na memória")
        if ponte.memoria_editar("Gosta de RPG de mesa",
                                "x" * (p.memoria.TAMANHO_MAXIMO + 1)).get("erro"):
            ok("tela nova: item maior que o limite é recusado com aviso")
        else:
            falha("tela nova: aceitou item maior que o limite")
        if "Gosta de RPG de mesa" in p.carregar_memoria():
            ok("tela nova: as edições recusadas não estragaram o item")
        else:
            falha("tela nova: o item se perdeu numa edição recusada")

        # 8. EXPORTAR a memória: o texto vem pronto para o .txt
        exportados = []
        ponte.salvar_texto = lambda texto: exportados.append(texto) or {}
        r = ponte.memoria_exportar()
        corpo = exportados[0] if exportados else ""
        if not r.get("erro") and corpo:
            ok("tela nova: exportar a memória monta o texto e não abre janela")
        else:
            falha("tela nova: exportar devolveu %r (texto %r)"
                  % (r, corpo[:80]))
        # Compara o que foi SALVO com o que a memoria tem de verdade, item
        # por item. Antes este teste procurava um texto solto dentro do
        # .txt inteiro, e foi assim que uma falha ficou sem explicacao: o
        # arquivo tinha o item dentro e o teste dizia que nao. Comparar a
        # lista inteira nao deixa passar item trocado, item a menos nem
        # item a mais -- e nao depende de formatacao nenhuma.
        esperado = p.carregar_memoria()
        linhas_txt = corpo.splitlines()
        itens_txt = [l[2:] for l in linhas_txt if l.startswith("- ")]
        if sorted(itens_txt) == sorted(esperado):
            ok("tela nova: o .txt da memoria traz exatamente os itens que ela tem")
        else:
            falha("tela nova: o .txt ficou %r mas a memoria tem %r"
                  % (itens_txt, esperado))
        if len(linhas_txt) > 2 and \
                "%d item(ns)" % len(esperado) in linhas_txt[2]:
            ok("tela nova: o .txt da memoria diz quantos itens sao")
        else:
            falha("tela nova: o .txt nao diz quantos itens sao")

        ponte.memoria_apagar_tudo()
        if ponte.memoria_exportar().get("erro"):
            ok("tela nova: exportar memória vazia avisa e não abre janela")
        else:
            falha("tela nova: exportar memória vazia tentou salvar assim mesmo")

        app_web.DEMO = True
        antes = p.ARQUIVO_CONFIG.read_text(encoding="utf-8")
        ponte.config_salvar({"aprender": True})
        ponte.memoria_adicionar("nao pode gravar")
        if p.ARQUIVO_CONFIG.read_text(encoding="utf-8") == antes \
                and p.carregar_memoria() == []:
            ok("tela nova: no modo exemplo configuracoes e memoria nao gravam")
        else:
            falha("tela nova: o modo exemplo gravou algo")
    finally:
        app_web.DEMO = demo
        for nome, valor in guardados.items():
            setattr(p, nome, valor)
        shutil.rmtree(pasta, ignore_errors=True)


if not falhas:
    try:
        testes_tela_nova_config(importlib.import_module("eye_of_thundera"))
    except Exception as erro:
        falha("os testes de config da tela nova quebraram: %r" % (erro,))


# --- 5f. aba Memoria: a rolagem do mouse continua depois de apagar ------


# --- 6. roteador: papo ou pesquisa (sem internet) --------------------------
try:
    sys.path.insert(0, str(PASTA))
    import roteador
    import eye_of_thundera as _pia

    def confere(condicao, nome):
        if condicao:
            ok(nome)
        else:
            falha(nome)

    r = roteador.regra_local

    # O PRAZO DO ROTEADOR: o Google exige 10 s ou mais. Com menos, ele
    # recusa com 400 INVALID_ARGUMENT e o roteador cai na regra das
    # palavras SEM AVISAR NINGUEM - foi assim que "pesquisar ou papo"
    # ficou desligado sem ninguem perceber (achado em 16/10/2026).
    _fonte = io.open(ARQUIVO, encoding="utf-8").read()
    _achado = re.search(r"timeout=(\d+),", _fonte)
    if _achado and int(_achado.group(1)) >= 10000:
        ok("o prazo do roteador é de %d ms (o Google exige 10 s ou mais)"
           % int(_achado.group(1)))
    else:
        falha("o prazo do roteador é %s ms: o Google recusa com menos de "
              "10 s e o roteador decide errado SEM AVISAR"
              % (_achado.group(1) if _achado else "desconhecido"))
    confere(r("oi") == "amigo", "roteador: 'oi' é papo")
    confere(r("valeu!") == "amigo", "roteador: 'valeu!' é papo")
    confere(r("/web preço do dólar") == "pesquisa",
            "roteador: '/web ...' é pesquisa")
    confere(r("sem pesquisar, o que acha de RPG?") == "amigo",
            "roteador: 'sem pesquisar' é papo")
    confere(r("oi", modo="sempre") == "pesquisa",
            "roteador: modo 'sempre' pesquisa tudo")
    confere(r("quanto custa?", modo="nunca") == "amigo",
            "roteador: modo 'nunca' nunca pesquisa")

    def quebrou(_prompt):
        raise RuntimeError("sem internet")

    d = roteador.decidir("oi", [], quebrou)
    confere(d == {"modo": "amigo", "consulta": "oi", "origem": "regra"},
            "roteador: 'oi' decide papo pela regra")
    d = roteador.decidir("/web preço do dólar", [], quebrou)
    confere(d["modo"] == "pesquisa" and d["consulta"] == "preço do dólar"
            and d["origem"] == "regra",
            "roteador: '/web ...' tira o prefixo da consulta")
    d = roteador.decidir(
        "q?", [], lambda p: '{"pesquisar": true, "consulta": "x", "motivo": "y"}')
    confere(d["modo"] == "pesquisa" and d["origem"] == "modelo",
            "roteador: entende JSON limpo do modelo")
    d = roteador.decidir(
        "q?", [],
        lambda p: 'texto ```json {"pesquisar": false, "consulta": "", '
                   '"motivo": "papo"} ``` fim')
    confere(d["modo"] == "amigo" and d["origem"] == "modelo",
            "roteador: entende JSON dentro de cerca")
    d = roteador.decidir("q?", [], lambda p: "não entendi nada")
    confere(d["origem"] == "padrao",
            "roteador: texto solto cai na heurística")
    d = roteador.decidir("q?", [], quebrou)
    confere(d["origem"] == "padrao",
            "roteador: erro do modelo cai na heurística")

    def modelo_amigo(_p):
        return '{"pesquisar": false, "consulta": "", "motivo": "papo"}'

    d = roteador.decidir("como você está hoje?", [], modelo_amigo)
    confere(d["modo"] == "amigo", "roteador: 'como você está hoje?' é papo")
    d = roteador.decidir("quanto está o dólar hoje?", [], quebrou)
    confere(d["modo"] == "pesquisa",
            "roteador: 'quanto está o dólar hoje?' é pesquisa")
    d = roteador.decidir("me explica o que é uma API", [], modelo_amigo)
    confere(d["modo"] == "amigo",
            "roteador: 'me explica o que é uma API' é papo")
    d = roteador.decidir("qual a última versão do Windows 11?", [], quebrou)
    confere(d["modo"] == "pesquisa",
            "roteador: 'última versão' é pesquisa pela heurística")

    confere(roteador.fato_pedido("lembra que eu gosto de RPG")
            == "gosto de RPG",
            "roteador: 'lembra que...' vira fato guardado")
    confere(roteador.fato_pedido("que dia é hoje?") is None,
            "roteador: pergunta normal não é pedido para lembrar")

    # instrucoes_da_ia com memória falsa (nunca lê a memória de verdade)
    _memoria_real = _pia.carregar_memoria
    _pia.carregar_memoria = lambda: []
    try:
        texto_amigo = _pia.instrucoes_da_ia("amigo")
        texto_pesquisa = _pia.instrucoes_da_ia("pesquisa")
    finally:
        _pia.carregar_memoria = _memoria_real
    confere("material achado" not in texto_amigo,
            "roteador: prompt do amigo não fala de material da web")
    confere("material achado" in texto_pesquisa,
            "roteador: prompt de pesquisa continua com o material da web")
except Exception as erro:
    falha("os testes do roteador quebraram: %r" % (erro,))
    print(traceback.format_exc()[-900:])

# --- 7. voz: gravador e transcricao (sem internet e sem microfone) ---------
try:
    import array
    import wave as _wave
    import voz

    def confere_voz(condicao, nome):
        if condicao:
            ok(nome)
        else:
            falha(nome)

    confere_voz(isinstance(voz.microfone_disponivel(), bool),
                "voz: microfone_disponivel() responde sem quebrar")
    confere_voz("microfone" in voz.microfone_erro(
        PermissionError("Access is denied")).lower(),
        "voz: erro de permissao vira frase em portugues")
    confere_voz("microfone" in voz.microfone_erro(
        RuntimeError("PortAudioError: no default device")).lower(),
        "voz: erro sem microfone vira frase em portugues")

    # --- Gravador com um fluxo de audio falso (nao mexe no microfone) ------
    class _FluxoFalso(object):
        def __init__(self):
            self.iniciado = False
            self.fechado = False

        def start(self):
            self.iniciado = True

        def stop(self):
            pass

        def close(self):
            self.fechado = True

    class _GravadorFalso(voz.Gravador):
        def _criar_fluxo(self, callback):
            self.callback = callback
            self.falso = _FluxoFalso()
            return self.falso

    silencio = array.array("h", [0] * 800)
    alto = array.array("h", [8000 if i % 2 else -8000 for i in range(800)])

    g = _GravadorFalso()
    g.iniciar()
    confere_voz(g.gravando and g.falso.iniciado,
                "voz: Gravador.iniciar() abre o fluxo e marca gravando")
    g.callback(silencio, 800, 0, None)
    confere_voz(g.nivel() == 0.0,
                "voz: silencio da nivel 0")
    g.callback(alto, 800, 0, None)
    confere_voz(g.nivel() > 1000,
                "voz: audio alto da nivel alto")
    confere_voz(not g.limite(),
                "voz: gravacao curta ainda nao chegou no limite")
    confere_voz(g.segundos > 0, "voz: conta os segundos gravados")

    g.tempo_maximo = 0.001
    confere_voz(g.limite(),
                "voz: avisando quando passou do tempo maximo")
    g.tempo_maximo = 120

    wav = g.parar()
    confere_voz(not g.gravando and g.falso.fechado,
                "voz: Gravador.parar() fecha o fluxo e para de gravar")

    # o WAV tem que sair com o cabecalho certo, senao o Gemini recusa
    try:
        with _wave.open(io.BytesIO(wav), "rb") as arquivo:
            canais = arquivo.getnchannels()
            largura = arquivo.getsampwidth()
            taxa = arquivo.getframerate()
            quadros = arquivo.getnframes()
        cabecalho_ok = (canais == 1 and largura == 2 and taxa == 16000
                        and quadros > 0)
    except Exception as erro:
        cabecalho_ok = False
        falha("voz: o WAV montado nao abre: %r" % (erro,))
    confere_voz(cabecalho_ok,
                "voz: WAV montado com 1 canal, 16 bits e 16 kHz")
    confere_voz(voz.segundos_do_wav(wav) > 0,
                "voz: segundos_do_wav() le a duracao")
    confere_voz(voz.wav_tem_som(wav),
                "voz: wav_tem_som() reconhece audio com voz")
    confere_voz(not voz.wav_tem_som(b""),
                "voz: wav_tem_som() diz que nao ha nada em audio vazio")
    confere_voz(not voz.wav_tem_som(
        voz._para_wav(silencio.tobytes())),
        "voz: wav_tem_som() diz que nao ha nada em silencio")

    # --- transcrever com um cliente falso (nao chama a internet) -----------
    class _ParteFalsa(object):
        def __init__(self, texto=None):
            self.text = texto

    class _RespostaFalsa(object):
        def __init__(self, texto):
            self.text = texto
            self.candidates = []

    class _ModelsFalsos(object):
        def __init__(self, respostas):
            self.respostas = dict(respostas)
            self.chamados = []

        def generate_content(self, model, contents, config=None):
            self.chamados.append(model)
            if model not in self.respostas:
                raise RuntimeError("modelo %s fora do ar" % model)
            return _RespostaFalsa(self.respostas[model])

    class _ClienteFalso(object):
        """Mesma forma do cliente do Gemini: cliente.models.generate_content."""

        def __init__(self, respostas):
            self.models = _ModelsFalsos(respostas)

    cliente_1 = _ClienteFalso({"m1": "qual o seu nome?"})
    confere_voz(voz.transcrever(cliente_1, ["m1"], wav) == "qual o seu nome?",
                "voz: transcrever() devolve o texto falado")

    cliente_2 = _ClienteFalso({"m2": "tudo bem"})
    confere_voz(voz.transcrever(cliente_2, ["m1", "m2"], wav) == "tudo bem",
                "voz: transcrever() tenta o proximo modelo quando um falha")
    confere_voz(cliente_2.models.chamados == ["m1", "m2"],
                "voz: transcrever() guarda a ordem dos modelos")

    try:
        voz.transcrever(_ClienteFalso({}), ["m1"], wav)
        confere_voz(False, "voz: transcrever() avisa quando nenhum modelo responde")
    except RuntimeError:
        ok("voz: transcrever() avisa quando nenhum modelo responde")

    try:
        voz.transcrever(_ClienteFalso({"m1": "x"}), ["m1"], b"")
        confere_voz(False, "voz: transcrever() recusa audio vazio")
    except RuntimeError:
        ok("voz: transcrever() recusa audio vazio")

    # O teste de "tem voz?" tem que aceitar voz fraca (pessoa longe do
    # microfone) e recusar so o ruido de fundo. Montamos os dois casos.
    def _wav_de(trechos):
        partes = []
        for nivel, amostras in trechos:
            partes.append(array.array(
                "h", [int(nivel if i % 2 else -nivel)
                      for i in range(amostras)]).tobytes())
        return voz._para_wav(b"".join(partes))

    # Niveis tirados da medicao real: microfone parado fica em ~5-20 e a
    # voz passando por ele passa de 400.
    voz_fraca = _wav_de([(450, 8000), (18, 8000), (420, 8000)])
    so_ruido = _wav_de([(12, 8000), (14, 8000), (11, 8000)])
    confere_voz(voz.wav_tem_som(voz_fraca),
                "voz: wav_tem_som() aceita voz fraca entre pausas")
    confere_voz(not voz.wav_tem_som(so_ruido),
                "voz: wav_tem_som() recusa so ruido de fundo")

    # quando o campo .text vem vazio, tem que remontar pelas partes
    class _RespostaEmPartes(object):
        text = ""
        candidates = []

    class _Conteudo(object):
        parts = [_ParteFalsa("bom dia")]

    class _Candidato(object):
        content = _Conteudo()

    _RespostaEmPartes.candidates = [_Candidato()]

    class _ModelsEmPartes(object):
        def generate_content(self, model, contents, config=None):
            return _RespostaEmPartes()

    class _ClienteEmPartes(object):
        models = _ModelsEmPartes()

    confere_voz(
        voz.transcrever(_ClienteEmPartes(), ["m1"], wav) == "bom dia",
        "voz: transcrever() remonta o texto quando .text vem vazio")
except Exception as erro:
    falha("os testes de voz quebraram: %r" % (erro,))
    print(traceback.format_exc()[-900:])

# --- 8. cantos arredondados da caixa (a conta da curva, sem tela) ----------
try:
    sys.path.insert(0, str(PASTA))
    import eye_of_thundera as _p2

    def confere_canto(condicao, nome):
        if condicao:
            ok(nome)
        else:
            falha(nome)

    # A curva de cada canto tem que ter o centro no canto OPOSTO: o canto
    # verdadeiro fica FORA (é o que a tampinha pinta de fundo) e o miolo da
    # caixa fica DENTRO (é o que fica transparente). Se inverter, a
    # tampinha come o botão de enviar em vez de arredondar o canto.
    LADO = 12
    ultimo = LADO - 1
    for canto, fora, dentro in (
        ("nw", (0, 0), (ultimo, ultimo)),
        ("ne", (ultimo, 0), (0, ultimo)),
        ("sw", (0, ultimo), (ultimo, 0)),
        ("se", (ultimo, ultimo), (0, 0)),
    ):
        d = _p2._dentro_do_canto
        confere_canto(not d(*fora, LADO, canto),
                      "canto %s: o bico do canto fica FORA da caixa" % canto)
        confere_canto(d(*dentro, LADO, canto),
                      "canto %s: o miolo da caixa fica DENTRO" % canto)

    # A caixa inteira (4 quadrantes de LADO) tem que perder só as pontas:
    # sobra a curvatura, uns 80% da área. Se ficar muito abaixo, os cantos
    # estão comendo a caixa; se ficar acima, não estão arredondando nada.
    dentro = total = 0
    for y in range(2 * LADO):
        for x in range(2 * LADO):
            if y < LADO:
                canto, px, py = ("nw" if x < LADO else "ne"), x % LADO, y
            else:
                canto = "sw" if x < LADO else "se"
                px, py = x % LADO, y - LADO
            total += 1
            if _p2._dentro_do_canto(px, py, LADO, canto):
                dentro += 1
    proporcao = 100.0 * dentro / total
    if 75.0 <= proporcao <= 90.0:
        ok("os quatro cantos cortam só a curvatura (%.1f%% do miolo)"
           % proporcao)
    else:
        falha("os cantos cortaram a medida errada: %.1f%% do miolo "
              "(esperado entre 75%% e 90%%)" % proporcao)

    # A imagem do canto tem que vir PINTAADA (dentro = cor da caixa, fora =
    # cor de fundo) e sem buraco transparente: o tkinter nao tem widget
    # transparente, e o fundo de um Label cobre o quadrado todo — com
    # buraco, o canto saia como um QUADRADO preto em vez de uma curva.
    _p2._FOTOS_CANTO.clear()
    imagem = _p2._imagem_canto(_p2.RAIO_CANTO, _p2.COR_BARRA,
                               _p2.COR_FUNDO, "nw")
    if imagem is None:
        falha("não consegui desenhar a imagem do canto arredondado")
    else:
        da_caixa = de_fundo = transparentes = outros = 0
        for y in range(imagem.height):
            for x in range(imagem.width):
                cor = imagem.getpixel((x, y))
                if cor[3] < 128:
                    transparentes += 1
                elif cor[:3] == _p2._rgba(_p2.COR_BARRA)[:3]:
                    da_caixa += 1
                elif cor[:3] == _p2._rgba(_p2.COR_FUNDO)[:3]:
                    de_fundo += 1
                else:
                    outros += 1
        if transparentes == 0:
            ok("imagem do canto sem buraco transparente (ela pinta as "
               "duas cores)")
        else:
            falha("a imagem do canto tem %d pixel(is) transparente(s): "
                  "o fundo do Label vai aparecer e o canto vira "
                  "quadrado" % transparentes)
        if da_caixa and de_fundo and outros < (da_caixa + de_fundo):
            ok("imagem do canto tem as duas cores (%d da caixa, %d de "
               "fundo, %d de borda/antialising)" % (da_caixa, de_fundo,
                                                     outros))
        else:
            falha("a imagem do canto ficou errada (%d caixa / %d fundo / "
                  "%d borda)" % (da_caixa, de_fundo, outros))
except Exception as erro:
    falha("os testes dos cantos quebraram: %r" % (erro,))

print()
if falhas:
    print("RESULTADO: %d FALHA(S). Corrija antes de entregar." % len(falhas))
    sys.exit(1)
print("TUDO CERTO" + (" (com %d aviso(s))" % len(avisos) if avisos else ""))
