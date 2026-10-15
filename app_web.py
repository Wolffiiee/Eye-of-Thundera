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
      programa antigo (so LEITURA);
    - abre as quatro abas de Configuracoes (tambem so leitura);
    - o botao de salvar a resposta em .txt ja funciona de verdade.

O QUE AINDA NAO FUNCIONA (e avisa na tela, sem quebrar)
    - enviar pergunta: a IA ainda nao esta ligada nesta tela (passo 3);
    - microfone (passo 4);
    - mudar qualquer coisa nas Configuracoes ou na Memoria (passo 5);
    - excluir conversa (passo 2).
    Tudo que for isso devolve um aviso honesto. NUNCA grava, apaga ou
    muda nada do Wolf.

REGRA DE OURO
    O `pesquisa_ia.py` NAO foi tocado e o atalho da Area de Trabalho
    continua apontando para ele. A tela nova nasce ao lado da antiga; so
    trocamos quando ela estiver igual ou melhor. Assim nunca sobra o Wolf
    sem programa funcionando.

Como rodar (esta e' a forma normal, o que o Wolf vai usar):
    .venv\\Scripts\\python.exe app_web.py
"""

import sys
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

PASSO = {
    "enviar": "3",
    "microfone": "4",
    "config": "5",
    "excluir": "2",
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
    """A lista da barra esquerda. Ordena da mais nova para a mais antiga."""
    if DEMO:
        return list(CONVERSAS_DEMO)
    lista = p.carregar_conversas()
    return sorted(
        lista,
        key=lambda c: str(c.get("quando", "")),
        reverse=True,
    )


def _mensagens_de(conversa):
    return list(conversa.get("mensagens", [])) if conversa else []


# --- a ponte: o que o JavaScript chama -------------------------------------

class Ponte:
    """Tudo que a tela nova pode pedir ao Python.

    REGRA DESTE PASSO: so as funcoes de LEITURA fazem o que pedem. As
    outras devolvem um aviso dizendo em qual passo serao feitas. Assim
    nenhum teste pode mexer nas conversas, na memoria ou nas chaves do
    Wolf.
    """

    def __init__(self, janela=None):
        self.janela = janela

    # --- 1. o que a tela precisa para comecar ---

    def iniciar(self):
        """Primeira coisa que a tela chama: devolve o estado inicial."""
        conversas = _conversas_para_a_tela()
        atual = conversas[0] if conversas else None
        if DEMO:
            cfg = {}
        else:
            cfg = p._ler_json(p.ARQUIVO_CONFIG, {})
        return {
            "cfg": {
                "modo_pesquisa": cfg.get("modo_pesquisa", "auto"),
                "corretor": bool(cfg.get("corretor", True)),
            },
            "conversas": conversas,
            "mensagens": _mensagens_de(atual),
            "atual": (atual or {}).get("id"),
            "tem_chave": bool(cfg.get("api_key")),
        }

    def abrir_conversa(self, identificador):
        """Clique numa conversa da barra esquerda."""
        for c in _conversas_para_a_tela():
            if str(c.get("id")) == str(identificador):
                return {
                    "mensagens": _mensagens_de(c),
                    "atual": c.get("id"),
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

    # --- 2. o que ja dá para usar de verdade ---

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

    # --- 3. o que ainda falta (avisa, sem quebrar) ---

    def enviar(self, texto):
        if DEMO:
            return {}
        return aviso_honesto("enviar")

    def nova_conversa(self):
        return aviso_honesto("enviar")

    def excluir_conversa(self, identificador):
        return aviso_honesto("excluir")

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

    print("Abrindo a tela nova (passo 1, so leitura).")
    print("Janela no segundo monitor: x=%d y=%d  (%dx%d)"
          % (X_PADRAO, Y_PADRAO, LARGURA, ALTURA))
    if DEMO:
        print("MODO DEMO: as conversas mostradas sao de EXEMPLO.")
    print("Suas conversas, memoria e chaves NAO vao ser alteradas.")
    try:
        webview.start(ao_abrir, janela, gui="edgechromium")
    except Exception as erro:
        sys.exit("A janela nao abriu: %r" % (erro,))
    print("Tela nova fechada.")


if __name__ == "__main__":
    principal()
