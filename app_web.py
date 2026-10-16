# -*- coding: utf-8 -*-
"""
Tela nova do Pesquisa IA, feita em HTML (PASSO 1: so a tela, sem a IA).

POR QUE EXISTE
    O programa de sempre e' feito com o Tk (tkinter), que e' antigo: ele
    so desenha emoji de UMA cor, deixa o texto selectionsseo estranha e
    obriga a desenhar cada icone na mao. A tela nova e' uma pagina de
    navegador dentro de uma janela do Windows (o pywebview), que resolve
    isso de graca. O teste em `web\\spike_webview.py` ja provou que
    funciona nesta maquina (inclusive com emoji COLORIDO).

O QUE ESTE PASSO FAZ
    - abre a janela da tela nova no SEGUNDO MONITOR (regra do Wolf);
    - mostra as conversas que ele ja tem, lendo os MESMOS arquivos do
      programa antigo;
    - abrir, criar e excluir conversa;
    - ENVIAR PERGUNTA: a IA de verdade responde, e o que ela esta
      fazendo aparece na tela enquanto trabalha (passo 3);
    - abre as quatro abas de Configuracoes (so leitura);
    - o botao de salvar a resposta em .txt ja funciona de verdade.

O QUE AINDA NAO FUNCIONA (e avisa na tela, sem quebrar)
    - microfone (passo 4);
    - mudar qualquer coisa nas Configuracoes ou na Memoria (passo 5).
    Tudo que for isso devolve um aviso honesto. No modo exemplo
    (`--demo`) nada e gravado nunca.

REGRA DE OURO
    O `pesquisa_ia.py` NAO foi tocado e o atalho da Area de Trabalho
    continua apontando para ele. A tela nova nasce ao lado da antiga; so
    trocamos quando ela estiver igual ou melhor. Assim nunca sobra o Wolf
    sem programa funcionando.

Como rodar (esta e' a forma normal, o que o Wolf vai usar):
    .venv\\Scripts\\python.exe app_web.py
"""

import json
import sys
import threading
import time
import webbrowser
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
sys.path.insert(0, str(RAIZ))
sys.stdout.reconfigure(encoding="utf-8")

# O pywebview e' a unica coisa que esta tela usa de fora. Se faltar, o
# erro diz o que fazer em vez de dar uma excecao gigante.
try:
    import webview
except ImportError:
    sys.exit(
        "Falta a biblioteca pywebview.\n"
        "Rode isto na pasta do projeto:\n"
        "    .venv\\Scripts\\python.exe -m pip install pywebview\n"
    )

# O mesmo modulo do programa antigo: os dados (conversas, memoria,
# chaves) ficam nos mesmos arquivos, entao a tela nova ve o que o Wolf
# ja tem. Importar o modulo NAO abre janela nenhuma.
import pesquisa_ia as p

WEB = RAIZ / "web"
INDEX = WEB / "index.html"
ESTILO = WEB / "estilo.css"
SCRIPT = WEB / "app.js"

# Janela de PREVIA: nasce no segundo monitor, nunca no principal, para
# nunca cobrir a tela que o Wolf esta usando.
PREVIA = "--previa" in sys.argv
# Modo DEMO: conversas de exemplo (com emoji COLORIDO) para o Wolf ver a
# tela cheia e poder decidir. NAO le nem grava nada do Wolf: e' so olhar.
DEMO = "--demo" in sys.argv or PREVIA
X_PADRAO, Y_PADRAO = (2000, 100) if PREVIA else (120, 90)
LARGURA, ALTURA = (1100, 760) if PREVIA else (1180, 820)

CONVERSAS_DEMO = [
    {
        "id": "demo-1",
        "titulo": "Me conta uma curiosidade legal",
        "quando": "15/10/2026 às 19:40",
        "mensagens": [
            {"role": "user",
             "text": "Me conta uma curiosidade legal sobre o espaço"},
            {"role": "model", "text":
                "Claro! 🚀 Uma das coisas mais esquisitas do universo é que "
                "você está flutuando no espaço agora mesmo.\n\n"
                "A gravidade te puxa para o centro da Terra com tanta força "
                "que, se ela parasse de repente, você sairia correndo a uns "
                "465 km/h — mais rápido que um avião de linha! 😱\n\n"
                "E tem mais: a Lua se afasta da Terra uns 3,8 cm por ano. "
                "Daqui a bilhões de anos ela vira um planeta duplo. 🌕✨"},
        ],
    },
    {
        "id": "demo-2",
        "titulo": "Pesquisa as notícias de tecnologia",
        "quando": "15/10/2026 às 18:05",
        "mensagens": [
            {"role": "user",
             "text": "Pesquisa as notícias de tecnologia de hoje"},
            {"role": "model", "text":
                "Aqui vão os destaques de hoje: 📰\n\n"
                "• **Modelos de IA menores** — rodam no seu próprio "
                "computador, sem depender da internet. 🔒\n"
                "• **Tela dobrável** — já virou commonplace e o preço caiu. 📱\n"
                "• **Bateria de sódio** — cerca de 30% mais barata que a de "
                "lítio. 🔋\n\n"
                "Se quiser, eu aprofundo algum desses. 🙂"},
        ],
    },
    {
        "id": "demo-3",
        "titulo": "Dicas para começar um RPG",
        "quando": "14/10/2026 às 21:12",
        "mensagens": [
            {"role": "user",
             "text": "Me dá dicas para começar um jogo de RPG"},
            {"role": "model", "text":
                "Para começar sem se perder: 🗺️\n\n"
                "1. Escolha um jogo com **trilha sonora** — ajuda a entrar no "
                "clima.\n"
                "2. Anote no mapa onde achou cada loja. 🏪\n"
                "3. Não tenha pressa: jogo de RPG é sobre explorar, não "
                "sobre terminar rápido. 🎉\n\n"
                "Você prefere jogar de magio, lutador ou inventor?"},
        ],
    },
]

# O que AINDA nao esta ligado nesta tela. O passo 3 (a IA) ja foi feito,
# por isso "enviar" saiu daqui.
PASSO = {
    "microfone": "4",
    "config": "5",
}


def aviso_honesto(assunto):
    """Resposta para o que ainda nao foi ligado nesta tela."""
    return {
        "erro": "Na tela nova isso ainda nao funciona (passo %s). "
                "Use o programa de sempre, que continua funcionando."
                % PASSO.get(assunto, "?"),
    }


# --- leitura dos dados ------------------------------------------------------

def _tem_chave(valor):
    """A tela so mostra os ultimos caracteres da chave, nunca ela toda."""
    return {
        "definida": bool(valor),
        "final": (str(valor)[-4:] if valor else ""),
    }


def _cfg_tela():
    """O que as abas de Configuracoes precisam mostrar (so leitura)."""
    cfg = p._ler_json(p.ARQUIVO_CONFIG, {})
    servicos = []
    for s in p.SERVICOS_RESERVA:
        chave = cfg.get(s["campo_chave"], "")
        servicos.append({
            "nome": s["nome"],
            "campo": s["campo_chave"],
            "resumo": s.get("resumo", ""),
            "passos": s.get("passos", ""),
            "pagina": s.get("pagina", ""),
            "definida": bool(chave),
            "final": (str(chave)[-4:] if chave else ""),
        })
    return {
        "modo_pesquisa": cfg.get("modo_pesquisa", "auto"),
        "usar_contexto": bool(cfg.get("usar_contexto", True)),
        "aprender": cfg.get("aprender", True) is not False,
        "web_corretor": bool(cfg.get("corretor", True)),
        "voz_enviar": bool(cfg.get("voz_enviar", True)),
        "usar_plano_b": bool(cfg.get("usar_plano_b", True)),
        "gemini": _tem_chave(cfg.get("api_key", "")),
        "gemini_reserva": _tem_chave(cfg.get("api_key_reserva", "")),
        "servicos": servicos,
    }


def _cfg_tela_demo():
    """Configurações de exemplo (usado no modo DEMO, para a tela ter
    o mesmo aspecto mesmo sem ler nada do Wolf)."""
    return {
        "modo_pesquisa": "auto",
        "usar_contexto": True,
        "aprender": True,
        "web_corretor": True,
        "voz_enviar": True,
        "usar_plano_b": True,
        "gemini": {"definida": True, "final": "a1b2"},
        "gemini_reserva": {"definida": False, "final": ""},
        "servicos": [{
            "nome": s["nome"],
            "campo": s["campo_chave"],
            "resumo": s.get("resumo", ""),
            "passos": s.get("passos", ""),
            "pagina": s.get("pagina", ""),
            "definida": False,
            "final": "",
        } for s in p.SERVICOS_RESERVA],
    }


def _conversas_para_a_tela():
    """A lista da barra esquerda, da mais nova para a mais antiga.

    Mesmo criterio do programa antigo: o arquivo guarda as conversas na
    ordem em que foram salvas (a mais antiga primeiro) e a lista mostra
    ao contrario. Nao ordenar pelo texto do horario de propósito: ele so
    tem minuto de precisao, e duas conversas no mesmo minuto ficariam em
    ordem aleatoria.
    """
    if DEMO:
        return list(CONVERSAS_DEMO)
    return list(reversed(p.carregar_conversas()))


def _mensagens_de(conversa):
    return list(conversa.get("mensagens", [])) if conversa else []


# --- a ponte: o que o JavaScript chama -------------------------------------

class Ponte:
    """Tudo que a tela nova pode pedir ao Python.

    A conversa aberta mora AQUI (em `self.mensagens` e `self.id_atual`),
    igual ao programa antigo, que tambem guarda a conversa aberta dentro
    dele e so grava no arquivo quando ha mensagem nova.

    O `self.ocupado` e o "trava" do envio: enquanto a IA responde, a tela
    nao aceita outra pergunta (e o botao fica apagado, la no JavaScript).
    """

    def __init__(self, janela=None):
        self.janela = janela
        self.id_atual = None        # conversa aberta (igual ao app antigo)
        self.mensagens = []
        self.ocupado = False

    # --- 1. o que a tela precisa para comecar ---

    def iniciar(self):
        """Primeira coisa que a tela chama: devolve o estado inicial."""
        conversas = _conversas_para_a_tela()
        atual = conversas[0] if conversas else None
        cfg = p._ler_json(p.ARQUIVO_CONFIG, {})
        self.id_atual = (atual or {}).get("id")
        self.mensagens = _mensagens_de(atual)
        return {
            "cfg": {
                "modo_pesquisa": cfg.get("modo_pesquisa", "auto"),
                "corretor": bool(cfg.get("corretor", True)),
            },
            "conversas": conversas,
            "mensagens": list(self.mensagens),
            "atual": self.id_atual,
            # No modo exemplo a chave e' lida (so ler nao mexe em nada) para
            # o aviso ser honesto: sem chave, a IA realmente nao responde.
            "tem_chave": bool(cfg.get("api_key")),
        }

    def abrir_conversa(self, identificador):
        """Clique numa conversa da barra esquerda."""
        for c in _conversas_para_a_tela():
            if str(c.get("id")) == str(identificador):
                self.id_atual = c.get("id")
                self.mensagens = _mensagens_de(c)
                return {
                    "mensagens": list(self.mensagens),
                    "atual": self.id_atual,
                }
        return {"erro": "Não achei essa conversa."}

    def config_ler(self):
        """Abre as Configurações (so leitura neste passo)."""
        if DEMO:
            return _cfg_tela_demo()
        return _cfg_tela()

    def memoria_listar(self):
        """Aba Memória (so leitura neste passo)."""
        if DEMO:
            return {"fatos": [
                "Nome: Igor (pode ser chamado de Wolf)",
                "Natural de Santa Maria, Rio Grande do Sul",
                "Gosta muito de jogar videogames",
            ]}
        return {"fatos": p.carregar_memoria()}

    # --- 2. as conversas de verdade (este passo) ---

    def nova_conversa(self):
        """Botão 'Nova conversa' (também F5 no programa antigo).

        NAO grava nada: conversa sem pergunta nao tem o que salvar. O
        arquivo só é escrito quando houver mensagem nova (passo 3).
        Funciona tambem no modo exemplo (lá nada e gravado mesmo).
        """
        self.id_atual = None
        self.mensagens = []
        return {"atual": None, "conversas": _conversas_para_a_tela()}

    def excluir_conversa(self, identificador):
        """Apaga uma conversa da lista.

        Faz exatamente o que o programa antigo faz: tira a conversa do
        arquivo e, se era a que estava aberta, abre a tela inicial. O
        que a IA aprendeu sobre o Wolf continua guardado de proposito
        (apagar a conversa nao e apagar o que ele ensinou).

        No modo exemplo NÃO apaga: as conversas mostradas ali são de
        mentira, e o arquivo de verdade é do Wolf.
        """
        if DEMO:
            return {"erro": "No modo exemplo nada é apagado (as conversas "
                            "aí são de mentira). Use o programa de sempre "
                            "para excluir de verdade."}
        alvo = str(identificador)
        restantes = [c for c in p.carregar_conversas()
                     if str(c.get("id")) != alvo]
        apagada = len(restantes) != len(p.carregar_conversas())
        if not apagada:
            return {"erro": "Não achei essa conversa."}
        p.salvar_conversas(restantes)
        era_atual = str(self.id_atual) == alvo
        if era_atual:
            self.id_atual = None
            self.mensagens = []
        return {
            "conversas": _conversas_para_a_tela(),
            "era_atual": era_atual,
            "atual": self.id_atual,
        }

    # --- o que já dá para usar de verdade (desde o passo 1) ---

    def _gravar_conversa(self):
        """Guarda a conversa aberta no arquivo (usado no passo 3).

        Mesma regra do programa antigo: a conversa só ganha id (e só vai
        para o arquivo) quando tem mensagem de verdade.
        """
        if DEMO:
            return None
        if not self.mensagens:
            return None
        if self.id_atual is None:
            self.id_atual = str(time.time())
        return p.guardar_conversa(self.id_atual, self.mensagens)

    def salvar_texto(self, texto):
        """Salvar a resposta num .txt. Este funciona mesmo."""
        if not texto or not str(texto).strip():
            return {"erro": "Não tem resposta para salvar."}
        nome = p._nome_de_resposta(texto)
        from tkinter import filedialog
        import tkinter as tk
        dono = tk.Tk()
        dono.withdraw()
        dono.attributes("-topmost", True)
        try:
            p._deixar_dialogo_do_sistema_escuro(dono)
            caminho = filedialog.asksaveasfilename(
                parent=dono,
                title="Salvar resposta como...",
                initialfile=nome,
                defaultextension=".txt",
                filetypes=[("Arquivo de texto", "*.txt"),
                           ("Todos os arquivos", "*.*")],
            )
        finally:
            try:
                dono.destroy()
            except Exception:
                pass
        if not caminho:
            return {}                      # cancelou: nao e erro
        try:
            with open(caminho, "w", encoding="utf-8-sig") as arquivo:
                arquivo.write(str(texto).rstrip() + "\n")
        except Exception as erro:
            return {"erro": "Não consegui salvar: %s" % erro}
        return {"caminho": caminho}

    def abrir_link(self, url):
        """Clique num link da resposta (vai abrir o navegador de sempre)."""
        try:
            if url and str(url).startswith(("http://", "https://")):
                webbrowser.open(str(url))
        except Exception:
            pass
        return {}

    # --- 3. a IA de verdade (este passo) ---

    def _evento(self, dados):
        """Fala com a tela: `window.PIA.evento({...})` (ver web/app.js).

        O `json.dumps` com `ensure_ascii=False` e' obrigatorio: sem ele o
        acento e o emoji viram "\\u00e7" na tela.

        Aqui nunca estoura nada: se o Wolf fechou a janela no meio da
        resposta, o erro e' engolido (a thread morre em silencio).
        """
        if self.janela is None:
            return                    # teste sem janela: nao ha para quem falar
        try:
            self.janela.evaluate_js(
                "window.PIA.evento("
                + json.dumps(dados, ensure_ascii=False) + ")"
            )
        except Exception:
            pass

    def enviar(self, texto):
        """O Wolf aperta Enter (ou o botao): a IA responde.

        DEVOLVE NA HORA. Quem trabalha e' a thread `_responder`; o que ela
        descobre volta para a tela por `_evento` ("etapa" enquanto pesquisa,
        "resposta" no fim, "erro" se deu ruim). Fazer o trabalho aqui
        mesmo travaria a janela por varios segundos.

        Os dois unicos erros que saem daqui sao os que a tela precisa saber
        AGORA, antes de mostrar a pergunta: pergunta vazia e falta de
        chave ("sem_chave", que o app.js reconhece e abre as Configuracoes).
        """
        texto = str(texto or "").strip()
        if not texto:
            return {"erro": "Escreva a pergunta antes de enviar."}
        if self.ocupado:
            return {"erro": "Aguarde a resposta terminar."}

        cfg = p._ler_json(p.ARQUIVO_CONFIG, {})
        chave = (cfg.get("api_key") or "").strip()
        if not chave:
            return {"erro": "sem_chave"}

        # A pergunta entra no espelho da conversa antes da thread comecar,
        # para ela ja fazer parte do historico que a IA vai ler.
        self.ocupado = True
        self.mensagens.append({"role": "user", "text": texto})
        threading.Thread(
            target=self._responder, args=(texto, cfg, chave), daemon=True
        ).start()
        return {}

    def _responder(self, texto, cfg, chave):
        """A thread que trabalha enquanto a janela continua viva.

        Reaproveita o caminho do programa antigo: `pesquisa_ia.perguntar`
        (com busca na web) ou `pesquisa_ia.conversar` (papo normal),
        escolhidos pelo mesmo roteador, com a mesma chave reserva e o
        mesmo tradutor de erro. Nenhum disso foi reescrito aqui.
        """
        def avisar(mensagem):
            """`progresso` das funcoes acima: o que a IA esta fazendo."""
            self._evento({"tipo": "etapa", "texto": str(mensagem or "")})

        try:
            modelo = cfg.get("modelo", p.MODELO_PADRAO)
            usar_contexto = bool(cfg.get("usar_contexto", True))
            modo_cfg = cfg.get("modo_pesquisa", "auto")
            if modo_cfg not in ("auto", "sempre", "nunca"):
                modo_cfg = "auto"

            # Historico que a IA entende: so "user" e "model" (o erro de
            # uma tentativa anterior nao entra, e o Gemini nao aceita).
            historico = [{"role": m["role"], "text": m["text"]}
                         for m in self.mensagens[:-1]
                         if m.get("role") in ("user", "model")
                         and str(m.get("text") or "").strip()]

            # "lembra que ...": guarda direto, sem gastar chamada de IA
            # (igual ao programa antigo). No modo exemplo nao guarda nada.
            if not DEMO:
                try:
                    fato = p.roteador.fato_pedido(texto)
                    if fato:
                        p._mesclar_memoria([fato])
                except Exception:
                    pass

            decisao = p._decidir_modo(chave, texto, historico, modo_cfg)
            modo = decisao.get("modo", "amigo")
            consulta = decisao.get("consulta") or texto
            # Noticia explicita continua pesquisando, como antes.
            if p._quer_noticias(texto):
                modo = "pesquisa"
                consulta = texto

            def chamar_a_ia(qual_chave):
                if modo == "amigo":
                    return p.conversar(
                        qual_chave, modelo, historico, texto, usar_contexto,
                        progresso=avisar, cfg=cfg, id_atual=self.id_atual,
                    )
                return p.perguntar(
                    qual_chave, modelo, historico, texto, usar_contexto,
                    progresso=avisar, cfg=cfg, id_atual=self.id_atual,
                    consulta=consulta,
                )

            # Mesma troca automatica de chave do programa antigo.
            resposta, _fontes, _buscas, _origem = p.tentar_com_reserva(
                chamar_a_ia, cfg, {})
            resposta = (resposta or "").strip() or "(sem resposta)"

            self.mensagens.append({"role": "model", "text": resposta})
            if not DEMO:
                self._gravar_conversa()
            self._evento({"tipo": "resposta", "texto": resposta})
            if not DEMO:
                # A lista da esquerda mostra a conversa nova.
                self._evento({"tipo": "conversas",
                              "conversas": _conversas_para_a_tela(),
                              "atual": self.id_atual})
                self._aprender(texto, resposta, cfg, chave)
        except Exception as erro:
            self.mensagens.append({"role": "erro", "text": p.traduzir_erro(erro)})
            # `chave`: a tela abre as Configuracoes sozinha (como o programa
            # antigo faz quando a chave morre).
            self._evento({"tipo": "erro",
                          "texto": p.traduzir_erro(erro),
                          "chave": bool(p._falha_de_chave(erro))})
        finally:
            self.ocupado = False

    def _aprender(self, pergunta, resposta, cfg, chave):
        """Deixa a IA aprender sobre o Wolf, em segundo plano e calada.

        Igual ao programa antigo: nada aparece na tela, nada e' perguntado,
        e o proprio `aprender_com_o_usuario` se limita para nao chamar a IA
        a cada mensagem.
        """
        if DEMO or not cfg.get("aprender", True) or not chave:
            return

        def tarefa():
            try:
                p.aprender_com_o_usuario(chave, pergunta, resposta)
            except Exception:
                pass

        threading.Thread(target=tarefa, daemon=True).start()

    # --- o que ainda falta (avisa, sem quebrar) ---

    def definir_modo(self, modo):
        return aviso_honesto("config")

    def config_salvar(self, dados):
        return aviso_honesto("config")

    def testar_chave(self, campo, valor):
        return aviso_honesto("config")

    def memoria_adicionar(self, texto):
        return aviso_honesto("config")

    def memoria_apagar(self, fato):
        return aviso_honesto("config")

    def memoria_apagar_tudo(self):
        return aviso_honesto("config")

    def memoria_organizar(self):
        return aviso_honesto("config")


# --- montando a janela ------------------------------------------------------

def _endereco_de(arquivo):
    """webview.create_window nao aceita caminho com acento: usa file://."""
    return arquivo.resolve().as_uri()


def principal():
    faltando = [a for a in (INDEX, ESTILO, SCRIPT) if not a.exists()]
    if faltando:
        sys.exit("Faltam arquivos da tela nova:\n  "
                 + "\n  ".join(str(a) for a in faltando))

    ponte = Ponte()
    janela = webview.create_window(
        "Pesquisa IA (tela nova - em construção)",
        url=_endereco_de(INDEX),
        js_api=ponte,
        x=X_PADRAO, y=Y_PADRAO,
        width=LARGURA, height=ALTURA,
        min_size=(900, 620),
        background_color="#0e0e13",      # a barra some no fundo escuro
        frameless=False,
        easy_drag=False,
    )
    ponte.janela = janela

    def ao_abrir(instancia):
        # A barra de titulo do Windows e' branca por padrao e destoa de
        # um programa escuro. Esta e' a mesma funcao que o programa antigo
        # usa, entao as duas janelas ficam iguais.
        try:
            p.ativar_barra_escura(instancia)
        except Exception:
            pass

    print("Abrindo a tela nova (passo 3: a IA ja esta ligada).")
    print("Janela no segundo monitor: x=%d y=%d  (%dx%d)"
          % (X_PADRAO, Y_PADRAO, LARGURA, ALTURA))
    if DEMO:
        print("MODO DEMO: as conversas mostradas sao de EXEMPLO.")
        print("A IA de verdade responde, mas NADA e gravado (nem conversa,")
        print("nem memoria) enquanto a janela estiver no modo exemplo.")
    else:
        print("Suas conversas e memoria podem ser atualizadas ao conversar.")
    try:
        webview.start(ao_abrir, janela, gui="edgechromium")
    except Exception as erro:
        sys.exit("A janela nao abriu: %r" % (erro,))
    print("Tela nova fechada.")


if __name__ == "__main__":
    principal()
