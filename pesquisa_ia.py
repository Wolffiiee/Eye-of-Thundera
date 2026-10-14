# -*- coding: utf-8 -*-
"""
Pesquisa IA - assistente pessoal que pesquisa na web.

Como funciona: você digita uma pergunta, este programa procura na web por
você (busca gratuita) e manda os trechos encontrados para o Google Gemini
(a "inteligência"), que junta tudo numa resposta escrita em português.

Para usar, você só precisa de uma chave de API gratuita do Google
(Gemini). Clique em "Configurações" aqui dentro do programa.
"""

import io
import json
import math
import os
import queue
import re
import difflib
import sys
import threading
import time
import traceback
import webbrowser
from concurrent.futures import ThreadPoolExecutor
from html import unescape
from pathlib import Path

import tkinter as tk
import tkinter.ttk as ttk
from tkinter import filedialog, messagebox

# Pillow é usado para mostrar as imagens na conversa. Se ele não estiver
# instalado, o programa funciona normalmente (só não mostra imagens).
try:
    from PIL import Image, ImageColor, ImageDraw, ImageTk

    TEM_PIL = True
except Exception:
    Image = None
    ImageColor = None
    ImageDraw = None
    ImageTk = None
    TEM_PIL = False

# ----------------------------------------------------------------------------
# Configurações gerais
# ----------------------------------------------------------------------------

MODELO_PADRAO = "gemini-3.8-flash"
URL_CHAVE = "https://aistudio.google.com/apikey"

# Se um modelo estiver sobrecarregado ou fora do ar, o programa tenta o proximo.
# A ordem prioriza os modelos mais rapidos e estaveis no plano gratuito.
MODELOS_RESERVA = [
    "gemini-3.8-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.7-flash",
]

# Modelos antigos que o Google aposentou (davam erro). Sao trocados pelo padrao.
MODELOS_APOSENTADOS = {
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-2.5-pro",
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
}

# ----------------------------------------------------------------------------
# Plano B: outros serviços de IA, usados só se o Gemini não responder.
# Todos falam o mesmo "idioma" (o padrão da OpenAI), então basta trocar o
# endereço, a chave e o nome do modelo. São grátis e não pedem cartão.
# ----------------------------------------------------------------------------

# O Groq e o OpenRouter ficam atrás do Cloudflare, que recusa ("403
# Forbidden", erro 1010) qualquer pedido que não diga quem é. Sem este
# cabeçalho, a chave certa seria recusada mesmo estando certa.
USER_AGENT_PADRAO = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)

SERVICOS_RESERVA = [
    {
        "nome": "Groq",
        "endereco": "https://api.groq.com/openai/v1/chat/completions",
        "modelo": "openai/gpt-oss-120b",
        "campo_chave": "chave_groq",
        "campo_modelo": "modelo_groq",
        "pagina": "https://console.groq.com/keys",
        "resumo": "grátis, sem cartão (cerca de 1.000 pedidos por dia)",
        "passos": (
            "Como conseguir: 1) clique em \"Como conseguir a chave\"; "
            "2) entre com Google ou GitHub; 3) clique em \"Create API Key\"; "
            "4) copie o código (começa com gsk_) e cole aqui."
        ),
    },
    {
        "nome": "OpenRouter",
        "endereco": "https://openrouter.ai/api/v1/chat/completions",
        "modelo": "openrouter/free",
        "campo_chave": "chave_openrouter",
        "campo_modelo": "modelo_openrouter",
        "pagina": "https://openrouter.ai/keys",
        "resumo": "grátis, sem cartão (cerca de 50 pedidos por dia)",
        "passos": (
            "Como conseguir: 1) clique em \"Como conseguir a chave\"; "
            "2) entre com Google ou GitHub; 3) clique em \"Create API Key\"; "
            "4) copie o código (começa com sk-or-) e cole aqui."
        ),
    },
]

PASTA_CONFIG = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "PesquisaIA"
ARQUIVO_CONFIG = PASTA_CONFIG / "config.json"
# Quando o programa roda como executável, grava o log junto das configurações
# (a pasta do .exe pode ser só leitura, como a Área de Trabalho).
if getattr(sys, "frozen", False):
    ARQUIVO_ERRO = PASTA_CONFIG / "erro.log"
else:
    ARQUIVO_ERRO = Path(__file__).resolve().parent / "erro.log"

INSTRUCOES = (
    "Você é um assistente de pesquisa pessoal, escrito para uma pessoa comum "
    "no Brasil.\n"
    "\n"
    "Você recebe a pergunta do usuário e um material achado agora mesmo na "
    "web: resumos de sites, notícias recentes (com data e fonte) e o texto de "
    "algumas páginas. Escreva UMA única resposta em português do Brasil, "
    "usando esse material como base.\n"
    "\n"
    "Regras:\n"
    "- Responda em português do Brasil, sempre.\n"
    "- Use o material como fonte principal. Traduza o que estiver em outro "
    "idioma (inglês, espanhol etc.).\n"
    "- Quando houver itens 'NOTÍCIA' com data, use-os para perguntas sobre "
    "hoje, últimas notícias ou novidades, dando preferência ao mais recente.\n"
    "- Junte tudo em UMA resposta organizada e natural, sem listar os sites e "
    "sem colocar links.\n"
    "- Quando a informação muda com o tempo (notícias, preços, datas, "
    "resultados, índices), deixe claro a que período ou data ela se refere.\n"
    "- Se os trechos não tiverem a informação exata, diga isso com honestidade "
    "e, se souber de algo confiável, complemente deixando claro que não veio "
    "dos trechos.\n"
    "- Nunca invente números, datas ou fatos.\n"
    "- Escreva de forma clara e direta, com tópicos curtos quando ajudar a "
    "leitura.\n"
    "- Escreva em texto simples: NÃO use asteriscos (*), cerquilhas (#) nem "
    "outras marcações. Para fazer uma lista, comece a linha com '•'."
)

# ----------------------------------------------------------------------------
# Paleta (tema escuro moderno)
# ----------------------------------------------------------------------------

FONTE = "Segoe UI"

# Respiro de dentro das bolhas (o texto nao encosta na borda).
BALHA_RESPIRO = 12

COR_FUNDO = "#0f0f14"
COR_PAINEL = "#15151c"
COR_BARRA = "#1a1a22"
COR_BARRA_MAIS = "#26262f"     # um tom acima, para o mouse passar por cima
COR_BORDA = "#2a2a36"
COR_TEXTO = "#ececf1"
COR_TEXTO_2 = "#9a9aa8"
COR_TEXTO_3 = "#6f6f7c"
COR_ACCENT = "#4f7cff"
COR_ACCENT_CLARO = "#6b93ff"
COR_USUARIO = "#2b5cff"
COR_USUARIO_TX = "#ffffff"
COR_IA = "#1c1c25"
COR_IA_TX = "#ececf1"
COR_ERRO_BG = "#2a1a1e"
COR_ERRO_TX = "#ff9a9a"
COR_OK = "#4ade80"
# Botao de enviar: usa a mesma paleta da lupa (pastilha cinza + traco preto)
COR_ENVIAR = (134, 134, 141)       # bolha (mesma cor da pastilha da lupa)
COR_ENVIAR_HOVER = (156, 156, 162) # um tom acima quando o mouse passa
COR_ENVIAR_TRACO = (16, 16, 20)    # o aviao, na cor do traco da lupa
AVIAO_XY = (10, 11, 26, 18, 10, 25, 15.5, 18)


# ----------------------------------------------------------------------------
# Configuracao (chave da API salva no computador)
# ----------------------------------------------------------------------------


def carregar_config():
    """Le a configuracao salva. Se nao existir, usa o padrao."""
    cfg = {}
    if ARQUIVO_CONFIG.exists():
        try:
            cfg = json.loads(ARQUIVO_CONFIG.read_text(encoding="utf-8"))
        except Exception:
            cfg = {}

    # Permite tambem usar a variavel de ambiente GEMINI_API_KEY.
    if not cfg.get("api_key") and os.environ.get("GEMINI_API_KEY"):
        cfg["api_key"] = os.environ["GEMINI_API_KEY"]

    cfg.setdefault("api_key", "")
    cfg.setdefault("modelo", MODELO_PADRAO)
    cfg.setdefault("usar_contexto", True)
    cfg.setdefault("usar_plano_b", True)
    for _servico in SERVICOS_RESERVA:
        cfg.setdefault(_servico["campo_chave"], "")

    # Se o modelo salvo foi aposentado pelo Google, volta para o padrao novo.
    if cfg.get("modelo") in MODELOS_APOSENTADOS:
        cfg["modelo"] = MODELO_PADRAO

    return cfg


def salvar_config(cfg):
    """Grava a configuracao no computador (somente do seu usuario)."""
    PASTA_CONFIG.mkdir(parents=True, exist_ok=True)
    ARQUIVO_CONFIG.write_text(
        json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8"
    )


# ----------------------------------------------------------------------------
# Memoria e conversas guardadas
# ----------------------------------------------------------------------------
# Sao duas coisas separadas:
#   - a MEMORIA e o que a IA aprendeu sobre o usuario (gostos, jeitos, o que
#     ele pediu para lembrar). A IA usa isso sozinha, sem perguntar nada e
#     sem nunca comentar que guardou.
#   - as CONVERSAS sao o historico do que foi perguntado.
# Excluir uma conversa NAO apaga a memoria.

ARQUIVO_HISTORICO = PASTA_CONFIG / "historico.json"
ARQUIVO_MEMORIA = PASTA_CONFIG / "memoria.json"

MAX_MEMORIAS = 80
MAX_CARACTERES_CONTEXTO = 5000
MODELO_MEMORIA = "gemini-3.5-flash-lite"
ESPACO_ENTRE_APRENDIZADOS = 90  # segundos

_memoria_cache = None
_ultimo_aprendizado = 0.0


def _ler_json(caminho, padrao):
    """Le um arquivo de dados do programa. Se estiver quebrado, devolve o padrao."""
    try:
        if caminho.exists():
            dados = json.loads(caminho.read_text(encoding="utf-8"))
            if isinstance(dados, type(padrao)):
                return dados
    except Exception:
        pass
    return padrao


def _gravar_json(caminho, dados):
    try:
        PASTA_CONFIG.mkdir(parents=True, exist_ok=True)
        caminho.write_text(
            json.dumps(dados, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        return True
    except Exception:
        return False


def _sem_acento(texto):
    try:
        import unicodedata

        return "".join(
            letra
            for letra in unicodedata.normalize("NFKD", str(texto).lower())
            if not unicodedata.combining(letra)
        )
    except Exception:
        return str(texto).lower()


def carregar_memoria():
    """Fatos que a IA aprendeu sobre o usuario."""
    global _memoria_cache
    if _memoria_cache is None:
        vistos = []
        for item in _ler_json(ARQUIVO_MEMORIA, []):
            texto = str(item).strip()
            if texto and texto not in vistos:
                vistos.append(texto)
        _memoria_cache = vistos
    return list(_memoria_cache)


def salvar_memoria(fatos):
    global _memoria_cache
    _memoria_cache = [
        str(f).strip() for f in fatos if str(f).strip()
    ][:MAX_MEMORIAS]
    _gravar_json(ARQUIVO_MEMORIA, _memoria_cache)
    return list(_memoria_cache)


def esquecer_memoria(fragmento=None):
    """Apaga um fato da memoria (ou todos, se nao passar nada)."""
    if fragmento is None:
        return salvar_memoria([])
    alvo = _sem_acento(fragmento)
    return salvar_memoria(
        [f for f in carregar_memoria() if _sem_acento(f) != alvo]
    )


def _mesclar_memoria(novos):
    """Junta fatos novos, sem repetir os que ja estavam guardados."""
    atuais = carregar_memoria()
    chaves = {_sem_acento(f) for f in atuais}
    mudou = False
    for fato in novos:
        chave = _sem_acento(fato)
        if not chave or chave in chaves:
            continue
        if any(chave in dentro or dentro in chave for dentro in chaves):
            continue
        atuais.append(fato)
        chaves.add(chave)
        mudou = True
    if mudou:
        salvar_memoria(atuais)
    return atuais


def carregar_conversas():
    """Conversas guardadas, da mais antiga para a mais nova."""
    return _ler_json(ARQUIVO_HISTORICO, [])


def salvar_conversas(lista):
    """Grava as conversas. Nao apaga nada sozinho: cada uma fica guardada
    ate o usuario escolher excluir."""
    _gravar_json(ARQUIVO_HISTORICO, list(lista))


def _titulo_da_conversa(mensagens):
    for msg in mensagens:
        if msg.get("role") == "user":
            texto = (msg.get("text") or "").strip().replace("\n", " ")
            if texto:
                return texto[:44] + "..." if len(texto) > 44 else texto
    return "Conversa"


def guardar_conversa(identificador, mensagens):
    """Salva (ou atualiza) a conversa atual. A memoria fica intacta."""
    limpa = []
    for msg in mensagens or []:
        papel = msg.get("role")
        if papel not in ("user", "model"):
            continue
        texto = (msg.get("text") or "").strip()
        if texto:
            limpa.append({"role": papel, "text": texto})
    if not limpa:
        return None
    conversa = {
        "id": str(identificador),
        "titulo": _titulo_da_conversa(limpa),
        "quando": time.strftime("%d/%m/%Y as %H:%M"),
        "mensagens": limpa,
    }
    lista = [
        c for c in carregar_conversas() if c.get("id") != conversa["id"]
    ]
    lista.append(conversa)
    salvar_conversas(lista)
    return conversa


def contexto_das_conversas(limite=MAX_CARACTERES_CONTEXTO, ignorar=None):
    """Assuntos de conversas anteriores, so para a IA ter contexto."""
    lista = carregar_conversas()
    if ignorar is not None:
        lista = [c for c in lista if str(c.get("id")) != str(ignorar)]
    if not lista:
        return ""
    blocos = []
    total = 0
    for conversa in reversed(lista):
        perguntas = []
        for msg in conversa.get("mensagens", []):
            if msg.get("role") != "user":
                continue
            texto = (msg.get("text") or "").strip().replace("\n", " ")
            if len(texto) < 3:
                continue
            perguntas.append(texto[:200])
            if len(perguntas) >= 3:
                break
        if not perguntas:
            continue
        bloco = "%s (%s): %s" % (
            conversa.get("titulo", "conversa"),
            conversa.get("quando", ""),
            " | ".join(perguntas),
        )
        blocos.append(bloco)
        total += len(bloco)
        if total > limite:
            break
    if not blocos:
        return ""
    return (
        "\n\nAssuntos que esta pessoa ja perguntou antes (use so como "
        "contexto; nunca comente sobre isso nem diga que lembrou):\n"
        + "\n".join("- " + bloco for bloco in blocos)
    )


def instrucoes_da_ia():
    """Instrucoes do programa + a memoria sobre o usuario."""
    fatos = carregar_memoria()
    if not fatos:
        return INSTRUCOES
    lista = "\n".join("- " + fato for fato in fatos[:40])
    return (
        INSTRUCOES
        + "\n\nO QUE VOCE SABE SOBRE ESTA PESSOA (use essas informacoes de "
        "forma natural, sem nunca dizer que voce sabe, sem falar de "
        "memoria e sem perguntar como voce sabe):\n" + lista
    )


INSTRUCOES_APRENDER = (
    "Voce vai montar o perfil de uma pessoa a partir de uma conversa.\n"
    "Responda APENAS com ate 3 fatos curtos e duradouros sobre ela, um por "
    "linha, cada linha comecando com '- '. Escreva em portugues do Brasil.\n"
    "Servem: nome e como quer ser chamada, profissao, empresa, cidade onde "
    "mora, rotina, gostos, hobbies, series, jogos, estilo de resposta "
    "preferido, reclamacao que se repete.\n"
    "Nao servem: o assunto da pesquisa do dia, opiniao passageira, nem "
    "dados sensiveis (endereco, telefone, documentos, senha, saude, "
    "financas).\n"
    "Se nao houver nada duradouro, responda exatamente: NADA"
)


def _extrair_fatos(texto):
    fatos = []
    for linha in (texto or "").splitlines():
        linha = linha.strip()
        if not linha or linha.upper().startswith("NADA"):
            continue
        linha = linha.lstrip("-* ").strip()
        if len(linha) < 4 or len(linha) > 160:
            continue
        if linha not in fatos:
            fatos.append(linha)
    return fatos[:3]


def aprender_com_o_usuario(api_key, pergunta, resposta):
    """Pede a IA os fatos que ela aprendeu e guarda. Roda em segundo plano.

    Nao mostra nada para o usuario: nem pergunta, nem avisa, nem aparece
    na conversa.
    """
    global _memoria_cache, _ultimo_aprendizado
    api_key = (api_key or "").strip()
    if not api_key or len((resposta or "")) < 120:
        return None
    if time.time() - _ultimo_aprendizado < ESPACO_ENTRE_APRENDIZADOS:
        return None
    _ultimo_aprendizado = time.time()
    try:
        from google import genai

        cliente = genai.Client(api_key=api_key)
        resultado = cliente.models.generate_content(
            model=MODELO_MEMORIA,
            contents=(
                "Conversa:\nPESSOA: %s\nASSISTENTE: %s\n\n%s"
                % (
                    (pergunta or "")[:1500],
                    (resposta or "")[:2500],
                    INSTRUCOES_APRENDER,
                )
            ),
        )
        texto = (getattr(resultado, "text", "") or "").strip()
    except Exception:
        return None
    return _mesclar_memoria(_extrair_fatos(texto))



# ----------------------------------------------------------------------------
# Conversa com a IA
# ----------------------------------------------------------------------------


def _buscar_texto(consulta, quantidade=8):
    """Pesquisa páginas na web de graça e devolve uma lista de resultados.

    Usa o DuckDuckGo por baixo dos panos. Tenta provedores diferentes porque
    às vezes um deles falha. Cada item tem 'title', 'href' e 'body'.
    """
    try:
        from ddgs import DDGS
    except Exception:
        return []

    for provedor in ("auto", "bing", "yahoo"):
        for _tentativa in range(2):
            try:
                resultados = list(
                    DDGS().text(consulta, max_results=quantidade, backend=provedor)
                )
            except Exception:
                resultados = []
            if resultados:
                return resultados
            time.sleep(0.4)
    return []


def _buscar_noticias(consulta, quantidade=6):
    """Busca notícias recentes (traz manchetes e datas de verdade)."""
    try:
        from ddgs import DDGS
    except Exception:
        return []

    for provedor in ("auto", "bing"):
        for _tentativa in range(2):
            try:
                resultados = list(
                    DDGS().news(consulta, max_results=quantidade, backend=provedor)
                )
            except Exception:
                resultados = []
            if resultados:
                return resultados
            time.sleep(0.4)
    return []


# Palavras que indicam que a pessoa quer algo do momento (aí vale buscar notícias).
PALAVRAS_DO_MOMENTO = (
    "hoje", "agora", "notícia", "noticia", "notícias", "noticias", "últim",
    "ultim", "atual", "nesta semana", "este ano", "esse ano", "resultado",
    "placar", "cotação", "cotacao", "preço", "preco", "eleição", "eleicao",
    "governo", "economia", "bolsa", "dólar", "dolar", "euro", "clima",
    "previsão", "previsao", "aconteceu", "estreia", "lançamento", "lancamento",
)


def _quer_pesquisa(pergunta):
    """Heurística: pesquisa só quando a pergunta for relevante/externa.

    A IA deve ser, em boa parte, um amigo: cumprimentos, papo sobre a memória
    e perguntas sobre a si própria não exigem busca web. Qualquer coisa com
    indício de fato atual, dado numérico, clima, preços ou interrogativo
    concreto dispara pesquisa normal.
    """
    baixo = (pergunta or "").lower()
    palavras = set(re.findall(r"[\wÀ-ÿ]+", baixo))
    if _quer_noticias(pergunta) or _quer_imagens(pergunta):
        return True
    indicadores_pesquisa = {
        "qual", "quem", "quando", "onde", "quantos", "quantas", "quanto",
        "porque", "por que", "como", "weather", "clima", "preço", "preco", "tempo",
        "cotação", "cotacao", "noticia", "notícia", "resultado", "placar",
        "hoje", "agora", "último", "ultimo", "atual", "dolar", "dólar",
        "euro", "bolsa", "governo", "imdb", "score", "lançamento", "lancamento",
        "quantidade", "taxa", "população", "populacao",
    }
    if palavras & indicadores_pesquisa:
        return True
    # termos de converse com o amigo pessoa
    termos_conversa = {
        "oi", "olá", "ola", "bom", "boa", "tarde", "noite", "dia", "tudo",
        "bem", "obrigado", "obrigada", "valeu", "memória", "memoria",
        "lembrou", "lembrar", "sobre mim", "saber", "conversar", "papo",
        "como você", "vc", "você", "voce", "amigo", "amiga",
    }
    if palavras & termos_conversa and len(palavras) <= 12:
        return False
    # interrogativos são pesquisa, frases sem pergunta direta são papo
    if baixo.strip().endswith("?"):
        # pergunta curta e genérica sobre feeling/estado é conversa
        if any(p in baixo for p in (
                "melhor", "feel", "sentindo", "como vai", "como está",
                "como esta", "animado", "triste", "feliz")):
            return False
        return True
    if len(palavras) <= 7:
        return False
    return True

def _quer_noticias(pergunta):
    """Diz se a pergunta parece ser sobre algo atual (notícia)."""
    baixo = pergunta.lower()
    return any(palavra in baixo for palavra in PALAVRAS_DO_MOMENTO)


def _limpar_html(html, limite=3500):
    """Tira as tags e deixa só o texto legível de uma página."""
    try:
        html = re.sub(
            r"(?is)<(script|style|noscript|svg|head|nav|footer).*?</\1>", " ", html
        )
        texto = re.sub(r"(?s)<[^>]+>", " ", html)
        texto = unescape(texto)
        texto = re.sub(r"[ \t\r\f\v]+", " ", texto)
        texto = re.sub(r"\n\s*\n+", "\n", texto).strip()
        return texto[:limite]
    except Exception:
        return ""


def _baixar_pagina(url, limite=3500):
    """Abre uma página e devolve o texto dela (ou vazio se falhar)."""
    try:
        import httpx
    except Exception:
        return ""
    try:
        resposta = httpx.get(
            url,
            timeout=8.0,
            follow_redirects=True,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0 Safari/537.36"
                )
            },
        )
        if resposta.status_code != 200:
            return ""
        return _limpar_html(resposta.text, limite)
    except Exception:
        return ""


def _conteudo_das_paginas(resultados, quantidade=4):
    """Baixa em paralelo as páginas mais bem colocadas na busca."""
    alvos = []
    for item in resultados[:quantidade]:
        url = (item.get("href") or item.get("url") or "").strip()
        if url.startswith("http"):
            alvos.append((item.get("title") or url, url))
    if not alvos:
        return []

    textos = []
    try:
        with ThreadPoolExecutor(max_workers=min(5, len(alvos))) as pool:
            conteudos = list(pool.map(lambda par: _baixar_pagina(par[1]), alvos))
    except Exception:
        conteudos = ["" for _ in alvos]

    for (titulo, url), texto in zip(alvos, conteudos):
        if texto and len(texto) > 200:
            textos.append("[%s]\n%s" % (titulo, texto))
    return textos


# ----------------------------------------------------------------------------
# Busca de imagens (quando a pessoa pede imagens na conversa)
# ----------------------------------------------------------------------------

# Palavras que indicam que a pessoa quer ver imagens.
PALAVRAS_IMAGEM = re.compile(
    r"(?i)\b(papel\s+de\s+parede|imagem|imagens|foto|fotos|figura|figuras|"
    r"desenho|desenhos|wallpaper|wallpapers|ilustra[çc][ãa]o|"
    r"ilustra[çc][õo]es)\b"
)

# Palavras de comando que costumam vir antes do assunto ("me mostre...",
# "quero ver..."). Servem para descobrir o assunto das imagens.
_COMANDOS_IMAGEM = re.compile(
    r"(?i)^\s*(?:(?:por\s+favor|me|nos|eu|quero(?:\s+ver)?|queria|"
    r"gostaria(?:\s+de)?|preciso(?:\s+de)?|ver|veja|mostre|mostra|mande|"
    r"manda|envie|envia|busque|busca|pesquise|pesquisa|procure|procura|"
    r"encontre|encontra|traga|traz)[\s,:.]+)+"
)

_CONECTORES_IMAGEM = re.compile(
    r"(?i)^\s*(?:(?:de|do|da|dos|das|sobre|com|para|no|na|num|numa|um|uma|"
    r"uns|umas|algum|alguma|alguns|algumas|o|a|os|as)[\s,:.]+)+"
)


def _quer_imagens(pergunta):
    """Diz se a pergunta é um pedido de imagens (ex.: 'imagens de god of war')."""
    return bool(PALAVRAS_IMAGEM.search(pergunta or ""))


def _termo_imagens(pergunta):
    """Descobre o assunto das imagens ('imagens de god of war' -> 'god of war').

    Devolve "" quando a pessoa não disse o assunto (ex.: só "imagens").
    """
    texto = _COMANDOS_IMAGEM.sub("", pergunta or "")
    texto = PALAVRAS_IMAGEM.sub(" ", texto)
    texto = _CONECTORES_IMAGEM.sub("", texto)
    texto = re.sub(r"\s+", " ", texto).strip(" ?.!,\u2026-")
    return texto


def _baixar_bytes(url, tempo=8.0, limite=4_000_000):
    """Baixa o conteúdo de uma imagem (bytes). Devolve None se não der."""
    if not url or not str(url).lower().startswith("http"):
        return None
    try:
        import httpx

        resposta = httpx.get(
            url,
            timeout=tempo,
            follow_redirects=True,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0 Safari/537.36"
                )
            },
        )
        if resposta.status_code != 200:
            return None
        dados = resposta.content
        if not dados or len(dados) > limite:
            return None
        return dados
    except Exception:
        return None


def _buscar_imagens(consulta, quantidade=9):
    """Busca imagens na web de graça e já baixa as miniaturas.

    Devolve uma lista de dicionários com 'titulo', 'pagina', 'imagem' e
    'thumb' (os bytes da miniatura, prontos para mostrar na tela).
    """
    try:
        from ddgs import DDGS
    except Exception:
        return []

    resultados = []
    for _tentativa in range(2):
        try:
            resultados = list(DDGS().images(consulta, max_results=quantidade))
        except Exception:
            resultados = []
        if resultados:
            break

    itens = []
    for bruto in resultados:
        if len(itens) >= quantidade:
            break
        imagem = (bruto.get("image") or "").strip()
        miniatura = (bruto.get("thumbnail") or imagem).strip()
        if not imagem and not miniatura:
            continue
        itens.append({
            "titulo": (bruto.get("title") or "").strip(),
            "pagina": (bruto.get("url") or "").strip(),
            "imagem": imagem,
            "thumb_url": miniatura,
            "thumb": None,
        })

    if not itens:
        return []

    def baixar(item):
        item["thumb"] = (
            _baixar_bytes(item["thumb_url"]) or _baixar_bytes(item["imagem"])
        )
        return item

    try:
        with ThreadPoolExecutor(max_workers=min(6, len(itens))) as pool:
            itens = list(pool.map(baixar, itens))
    except Exception:
        pass

    return [item for item in itens if item.get("thumb")]


def _reduzir(imagem, lado_max=1400):
    """Deixa a imagem em um tamanho razoável (economiza memória)."""
    if imagem is None:
        return None
    try:
        imagem = imagem.convert("RGB")
    except Exception:
        return imagem
    largura, altura = imagem.size
    maior = max(largura, altura)
    if maior <= 0 or maior <= lado_max:
        return imagem
    escala = lado_max / maior
    nova = (
        max(1, int(largura * escala + 0.5)),
        max(1, int(altura * escala + 0.5)),
    )
    try:
        return imagem.resize(nova, Image.LANCZOS)
    except Exception:
        return imagem


def _imagem_de_bytes(dados, lado_max=1400):
    """Transforma os bytes de uma imagem em uma imagem do Pillow (reduzida)."""
    if not dados or Image is None:
        return None
    try:
        imagem = Image.open(io.BytesIO(dados))
        imagem.load()
    except Exception:
        return None
    return _reduzir(imagem, lado_max)


def _precarregar_imagens(itens):
    """Baixa em segundo plano as imagens grandes de uma busca.

    Guarda a imagem já reduzida em item['_grande'], para que clicar em cima
    dela seja instantâneo (sem esperar o download). Roda em uma thread.
    """
    if Image is None:
        return
    alvos = [item for item in itens if item.get("_grande") is None]
    if not alvos:
        return

    def baixar(item):
        dados = _baixar_bytes(
            item.get("imagem") or item.get("thumb_url"),
            tempo=15.0, limite=8_000_000,
        )
        imagem = _imagem_de_bytes(dados)
        if imagem is not None:
            item["_grande"] = imagem

    try:
        with ThreadPoolExecutor(max_workers=min(4, len(alvos))) as pool:
            list(pool.map(baixar, alvos))
    except Exception:
        pass


def _com_setas(imagem, alpha=70):
    """Desenha setas pequenas e discretas nas laterais da imagem.

    São só uma dica visual, sem fundo: clicando na lateral esquerda aparece a
    imagem anterior e clicando na lateral direita aparece a próxima.
    """
    if imagem is None or ImageDraw is None:
        return imagem
    try:
        base = imagem.convert("RGBA")
    except Exception:
        return imagem

    largura, altura = base.size
    if largura < 160 or altura < 100:
        return imagem

    camada = Image.new("RGBA", base.size, (0, 0, 0, 0))
    pincel = ImageDraw.Draw(camada)

    tamanho = max(16, int(min(largura, altura) * 0.09))
    folga = max(8, int(largura * 0.03))
    meio = altura // 2
    traco = max(2, tamanho // 9)
    claro = (255, 255, 255, alpha)

    def desenhar(centro, para_direita):
        metade = tamanho // 2
        if para_direita:
            pontos = [
                (centro - metade // 2, meio - metade),
                (centro + metade // 2, meio),
                (centro - metade // 2, meio + metade),
            ]
        else:
            pontos = [
                (centro + metade // 2, meio - metade),
                (centro - metade // 2, meio),
                (centro + metade // 2, meio + metade),
            ]
        pincel.line(pontos, fill=claro, width=traco, joint="curve")

    desenhar(folga + tamanho // 2, False)
    desenhar(largura - folga - tamanho // 2, True)

    try:
        return Image.alpha_composite(base, camada).convert("RGB")
    except Exception:
        return imagem


def _criar_cliente(api_key):
    """Cria o cliente do Gemini já configurado para falhar rápido.

    Quando um modelo está sobrecarregado (erro 503/429), o próprio SDK fica
    tentando sozinho por muito tempo. Aqui ele desiste rápido e o programa
    passa para o próximo modelo — assim a resposta sai bem mais depressa.
    """
    from google import genai
    from google.genai import types

    http = types.HttpOptions(
        timeout=120000,
        retry_options=types.HttpRetryOptions(
            attempts=1,
            initial_delay=0.3,
            max_delay=2.0,
            http_status_codes=[408, 429, 500, 502, 503, 504],
        ),
    )
    return genai.Client(api_key=api_key, http_options=http)


def _montar_servico(cfg, servico):
    """Junta os dados de um serviço de reserva com a chave e o modelo salvos."""
    item = dict(servico)
    item["chave"] = (cfg.get(servico["campo_chave"]) or "").strip()
    item["modelo"] = (
        cfg.get(servico["campo_modelo"]) or servico["modelo"]
    ).strip() or servico["modelo"]
    return item


def _servicos_prontos(cfg):
    """Devolve só os serviços de reserva que estão ligados e com chave."""
    if not cfg or not cfg.get("usar_plano_b", True):
        return []
    prontos = []
    for servico in SERVICOS_RESERVA:
        item = _montar_servico(cfg, servico)
        if item["chave"]:
            prontos.append(item)
    return prontos


def _erro_do_servico(servico, erro):
    """Transforma o erro bruto do Groq/OpenRouter em algo que dá pra resolver.

    Sem isso o Windows mostra só "HTTP Error 403: Forbidden", que não diz
    nada. Aqui cada caso vira uma explicação em português.
    """
    nome = servico.get("nome", "serviço")
    codigo = getattr(erro, "code", None)
    detalhe = ""
    try:
        bruto = erro.read().decode("utf-8", "replace")
        try:
            detalhe = json.loads(bruto)["error"]["message"]
        except Exception:
            detalhe = bruto.strip()
    except Exception:
        detalhe = str(erro)
    detalhe = (detalhe or "").strip()[:220]

    if codigo == 401:
        return (
            "A chave do %s não foi aceita.\n\n"
            "Confira se colou a chave inteira (começa com '%s') e sem espaço "
            "no fim dela. O botão Testar já usa o que está escrito no campo."
            % (nome, "gsk_" if nome == "Groq" else "sk-or-")
        )
    if codigo == 403:
        if "1010" in detalhe:
            return (
                "O %s bloqueou o pedido antes de olhar a chave.\n\n"
                "Isto é uma trava do servidor contra programas que não se "
                "identificam; já está corrigido nesta versão. Atualize o "
                "programa e teste de novo." % nome
            )
        return (
            "O %s recusou a chave (403).\n\n"
            "Isso costuma ser chave sem permissão ou conta ainda não "
            "ativada. Entre em console.groq.com e confira se a chave está "
            "ativa.\n\nDetalhe: %s" % (nome, detalhe)
        )
    if codigo == 404:
        return (
            "O %s não achou o modelo '%s'.\n\n"
            "Atualize o programa (o modelo pode ter mudado de nome)."
            % (nome, servico.get("modelo", "?"))
        )
    if codigo == 429:
        return (
            "Você usou o %s demais por agora (limite do plano grátis).\n\n"
            "Espere alguns minutos e tente de novo." % nome
        )
    return "O %s deu erro: %s" % (nome, detalhe or erro)


def _chamar_servico(servico, prompt, historico):
    """Chama um serviço de reserva (Groq, OpenRouter...) e devolve o texto.

    Usa a biblioteca que já vem com o Python, então não é preciso instalar
    mais nada no computador.
    """
    import urllib.error
    import urllib.request

    mensagens = [{"role": "system", "content": instrucoes_da_ia()}]
    for turno in (historico or [])[-6:]:
        texto = (turno.get("text") or "").strip()
        if not texto:
            continue
        papel = "assistant" if turno.get("role") == "model" else "user"
        mensagens.append({"role": papel, "content": texto})
    mensagens.append({"role": "user", "content": prompt})

    corpo = json.dumps(
        {
            "model": servico["modelo"],
            "messages": mensagens,
            "temperature": 0.3,
        }
    ).encode("utf-8")

    pedido = urllib.request.Request(
        servico["endereco"],
        data=corpo,
        method="POST",
        # O User-Agent é obrigatório: sem ele o Cloudflare (que fica na
        # frente do Groq e do OpenRouter) barra o pedido com "403 Forbidden"
        # antes mesmo de olhar a chave (erro 1010).
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": "Bearer %s" % servico["chave"],
            "User-Agent": USER_AGENT_PADRAO,
        },
    )
    try:
        with urllib.request.urlopen(pedido, timeout=120) as resposta:
            dados = json.loads(resposta.read().decode("utf-8"))
    except urllib.error.HTTPError as erro:
        raise RuntimeError(_erro_do_servico(servico, erro))
    except urllib.error.URLError as erro:
        raise RuntimeError(
            "Não consegui falar com o %s. Confira a internet e tente de novo."
            % servico.get("nome", "serviço")
        )

    try:
        return (dados["choices"][0]["message"]["content"] or "").strip()
    except Exception:
        raise RuntimeError("o %s devolveu uma resposta estranha" % servico["nome"])


def testar_servico(cfg, campo_chave):
    """Testa um serviço de reserva com uma pergunta de uma palavra só."""
    for servico in SERVICOS_RESERVA:
        if servico["campo_chave"] != campo_chave:
            continue
        item = _montar_servico(cfg, servico)
        if not item["chave"]:
            raise RuntimeError("cole a chave antes de testar")
        return _chamar_servico(item, "Responda apenas: OK", [])
    raise RuntimeError("serviço desconhecido")


def _gerar_texto(api_key, modelo, prompt, historico, cfg=None,
                 com_plano_b=True):
    """Chama o Gemini (grátis) para escrever a resposta final.

    Tenta o modelo principal e, se ele estiver fora do ar, passa rapidamente
    para os modelos de reserva. Se o Gemini não responder de jeito nenhum,
    tenta os serviços de plano B (Groq, OpenRouter) que estiverem com chave.

    Devolve (texto, origem), sendo a origem o nome de quem escreveu a resposta.
    """
    from google.genai import types

    cliente = _criar_cliente(api_key)
    ordem = [modelo] + [m for m in MODELOS_RESERVA if m != modelo]
    ultimo_erro = None

    conteudo = []
    for turno in (historico or [])[-6:]:
        conteudo.append(
            types.Content(
                role=turno["role"],
                parts=[types.Part(text=turno["text"])],
            )
        )
    conteudo.append(types.Content(role="user", parts=[types.Part(text=prompt)]))

    for _rodada in range(2):
        for nome in ordem:
            try:
                config = types.GenerateContentConfig(
                    temperature=0.3,
                    system_instruction=instrucoes_da_ia(),
                )
                resposta = cliente.models.generate_content(
                    model=nome, contents=conteudo, config=config
                )
                texto = (getattr(resposta, "text", "") or "").strip()
                if not texto:
                    texto = _juntar_partes(resposta)
                if texto:
                    return texto, "Gemini"
                ultimo_erro = RuntimeError("a IA não devolveu texto")
            except Exception as erro:
                ultimo_erro = erro
                continue
        time.sleep(1.5)

    # O Gemini não respondeu: entra o plano B (se estiver configurado).
    # Na corrida entre as IAs quem chama este ponto já cuida do plano B em
    # outra thread, então ele é pulado para não repetir a mesma chamada.
    if com_plano_b:
        servicos = _servicos_prontos(cfg)
        if servicos:
            erros = []
            for servico in servicos:
                try:
                    texto = _chamar_servico(servico, prompt, historico)
                    if texto:
                        return texto, servico["nome"]
                    erros.append("%s: não devolveu texto" % servico["nome"])
                except Exception as erro:
                    erros.append("%s: %s" % (servico["nome"], erro))
            raise RuntimeError(
                "O Gemini não respondeu e o plano B também falhou (%s)."
                % " | ".join(erros)
            )

    raise ultimo_erro or RuntimeError("não foi possível falar com a IA")


def _juntar_partes(resposta):
    """Remonta o texto quando o campo .text não vem preenchido."""
    pedacos = []
    try:
        for candidato in (resposta.candidates or []):
            partes = getattr(getattr(candidato, "content", None), "parts", None)
            for parte in (partes or []):
                if getattr(parte, "text", None):
                    pedacos.append(parte.text)
    except Exception:
        pass
    return "\n".join(pedacos).strip()


def _sem_markdown(texto):
    """Deixa o texto bonito na tela, sem marcas como ** e ###."""
    if not texto:
        return texto
    t = texto
    t = re.sub(r"\[([^\]]+)\]\((?:[^)]*)\)", r"\1", t)      # [texto](link) -> texto
    t = re.sub(r"(?m)^\s{0,3}#{1,6}\s*", "", t)              # titulos com #
    t = t.replace("**", "").replace("__", "")               # negrito
    t = re.sub(r"(?<!\w)\*(?!\s)([^*\n]+?)(?<!\s)\*(?!\w)", r"\1", t)  # italico
    t = re.sub(r"(?m)^\s*[-*+]\s+", "• ", t)                 # listas -> •
    t = t.replace("`", "")                                  # crases
    t = re.sub(r"\n{3,}", "\n\n", t)                        # linhas extras
    return t.strip()


def _espacar_blocos(texto):
    """Coloca uma linha em branco entre os tópicos/blocos, para o texto não
    ficar amontoado na tela (ex.: um parágrafo por assunto)."""
    if not texto:
        return texto
    saida = []
    for linha in texto.split("\n"):
        # Linhas indentadas são continuação do bloco anterior: não separa.
        continuacao = linha[:1] in (" ", "\t")
        if linha.strip() and not continuacao and saida and saida[-1].strip():
            saida.append("")
        saida.append(linha)
    return "\n".join(saida)


# ----------------------------------------------------------------------------
# Resposta mais rapida: a corrida entre o Gemini e o plano B
# ----------------------------------------------------------------------------
# O Gemini e o plano B sao chamados AO MESMO TEMPO e o programa fica com a
# primeira resposta que chegar. O Gemini ganha alguns segundos de vantagem
# porque e o modelo escolhido pelo usuario; se ele estiver lento (como
# acontece quando o Google esta sobrecarregado) ou fora do ar, o plano B
# responde antes e a espera acaba.
#
# Se o usuario nao colocar nenhuma chave de plano B, nada muda: so o
# Gemini responde, como antes.

ANTENACAO_PADRAO = 3.0  # segundos de vantagem do Gemini


def _gerar_texto_rapido(
    api_key, modelo, prompt, historico, cfg=None, antecipacao=ANTENACAO_PADRAO
):
    """Pede a resposta para varias IAs ao mesmo tempo e fica com a primeira.

    Devolve (texto, origem) igual ao _gerar_texto, mas sem esperar a mais
    lenta: quem responder primeiro vence.
    """
    servicos = _servicos_prontos(cfg) if cfg else []
    if not servicos:
        # sem plano B nao ha corrida: e so o Gemini mesmo
        return _gerar_texto(api_key, modelo, prompt, historico, cfg)

    resultados = queue.Queue()
    erros = []
    andamento = {"gemini": True, "plano_b": True}

    def avisar_fim(chave, texto="", origem="", erro=None):
        """Guarda a resposta ou o erro e diz se acabou a corrida."""
        if texto:
            resultados.put(("resposta", texto, origem))
        else:
            erros.append(erro or RuntimeError("a IA não respondeu"))
        andamento[chave] = False
        if not any(andamento.values()):
            resultados.put(("fim", "", ""))

    def correr_gemini():
        try:
            # com_plano_b=False: aqui quem cuida do plano B e a outra thread
            texto, origem = _gerar_texto(
                api_key, modelo, prompt, historico, cfg, com_plano_b=False
            )
            avisar_fim("gemini", texto, origem)
        except Exception as erro:
            avisar_fim("gemini", erro=erro)

    def correr_plano_b():
        ultimo_erro = None
        for servico in servicos:
            try:
                texto = _chamar_servico(servico, prompt, historico)
            except Exception as erro:
                ultimo_erro = erro
                continue
            if texto:
                avisar_fim("plano_b", texto, servico["nome"])
                return
        avisar_fim("plano_b", erro=ultimo_erro)

    def ligar_plano_b():
        try:
            threading.Thread(target=correr_plano_b, daemon=True).start()
        except Exception as erro:
            avisar_fim("plano_b", erro=erro)

    threading.Thread(target=correr_gemini, daemon=True).start()
    relogio = threading.Timer(max(0.0, antecipacao), ligar_plano_b)
    relogio.daemon = True
    relogio.start()

    while True:
        tipo, texto, origem = resultados.get()
        if tipo == "resposta":
            relogio.cancel()
            return texto, origem
        # todas as IAs falharam: devolve o erro mais recente para a tela
        raise erros[-1] if erros else RuntimeError("nenhuma IA respondeu")


def perguntar(
    api_key, modelo, historico, pergunta, usar_contexto, progresso=None, cfg=None,
    id_atual=None,
):
    """Pesquisa na web e pede para a IA juntar tudo em uma resposta.

    Devolve (texto, fontes, buscas, origem) para manter o mesmo formato de
    antes, mas sem links (as fontes vêm vazias de propósito). A "origem" diz
    qual serviço escreveu a resposta (Gemini ou um dos serviços de plano B).

    A função "progresso" (opcional) é chamada a cada etapa, para a tela
    mostrar ao usuário o que está acontecendo.

    O "id_atual" é a conversa que está aberta na tela: ela não entra de novo
    no contexto das conversas antigas.
    """
    def avisar(mensagem):
        if progresso is not None:
            try:
                progresso(mensagem)
            except Exception:
                pass

    avisar("Procurando na web")
    resultados = _buscar_texto(pergunta)
    noticias = _buscar_noticias(pergunta) if _quer_noticias(pergunta) else []

    blocos = []
    for indice, item in enumerate(resultados, 1):
        titulo = (item.get("title") or "").strip()
        resumo = (item.get("body") or "").strip()
        if not resumo and not titulo:
            continue
        blocos.append("RESUMO %d: %s\n%s" % (indice, titulo, resumo))

    urls_vistas = {(item.get("href") or item.get("url") or "").strip()
                   for item in resultados}
    for indice, item in enumerate(noticias, 1):
        titulo = (item.get("title") or "").strip()
        resumo = (item.get("body") or "").strip()
        url = (item.get("url") or item.get("href") or "").strip()
        if url and url in urls_vistas:
            continue
        if not resumo and not titulo:
            continue
        data = (item.get("date") or "")[:10]
        fonte = (item.get("source") or "").strip()
        detalhes = ", ".join(parte for parte in (data, fonte) if parte)
        cabecalho = "NOTÍCIA %d" % indice
        if detalhes:
            cabecalho += " (%s)" % detalhes
        blocos.append("%s: %s\n%s" % (cabecalho, titulo, resumo))
        if url:
            urls_vistas.add(url)

    # Tenta pegar o texto completo das páginas mais relevantes (melhora muito
    # a qualidade, principalmente em notícias).
    avisar("Lendo as páginas encontradas")
    conteudos = _conteudo_das_paginas(resultados, quantidade=4)
    blocos.extend("PÁGINA COMPLETA:\n%s" % texto for texto in conteudos)

    if blocos:
        contexto = "\n\n".join(blocos)
    else:
        contexto = (
            "(A busca na web não retornou nada desta vez. Responda com o que "
            "você sabe e avise que a informação pode não estar atualizada.)"
        )

    aviso_data = time.strftime("%d/%m/%Y")
    prompt = (
        "Data de hoje: %s\n\n"
        "Pergunta do usuário: %s\n\n"
        "Material encontrado agora na web:\n%s\n\n"
        "Escreva a resposta final em português do Brasil, usando esse "
        "material." % (aviso_data, pergunta, contexto)
    ) + contexto_das_conversas(ignorar=id_atual)

    historico_para_ia = historico if usar_contexto else []
    avisar("Consultando a inteligência artificial")
    # Varias IAs respondem ao mesmo tempo e vale a primeira que chegar.
    texto, origem = _gerar_texto_rapido(
        api_key, modelo, prompt, historico_para_ia, cfg
    )
    return _espacar_blocos(_sem_markdown(texto)), [], [], origem

def conversar(
    api_key, modelo, historico, pergunta, usar_contexto, progresso=None, cfg=None,
    id_atual=None,
):
    """Responde como um amigo, sem pesquisar na web."""
    def avisar(mensagem):
        if progresso is not None:
            try:
                progresso(mensagem)
            except Exception:
                pass
    avisar("Conversando com você")
    memoria = []
    try:
        memoria = carregar_memoria()
    except Exception:
        memoria = []
    historico_para_ia = historico if usar_contexto else []
    hoJe = __import__("time").strftime("%d/%m/%Y")
    bloco_memoria = (
        "Memória que a IA tem sobre o usuário:\n" + "\n".join(memoria)
        if memoria else "Não há memória guardada ainda sobre o usuário."
    )
    prompt = (
        "Data de hoje: %s\n\n"
        "Você não deve procurar nada na web agora. Responda apenas como um "
        "amigo atencioso que está conversando com o usuário, usando a memória "
        "abaixo. Seja natural, sem diagnóstico, sem instrução robótica, sem "
        "citações de fontes, sem markdown complexo. Pode responder curto. Se a "
        "resposta precisar de informação factual recente e você não tem,"
        " avise honestamente que pode não estar atualizado.\n\n"
        "%s\n\nConversas anteriores relevantes (memória e contexto).\n"
        "Pergunta do usuário: %s" % (hoJe, bloco_memoria, pergunta)
    ) + contexto_das_conversas(ignorar=id_atual)
    texto, origem = _gerar_texto_rapido(
        api_key, modelo, prompt, historico_para_ia, cfg
    )
    origem = "Gemini (sem pesquisa)" if not origem else origem
    return _espacar_blocos(_sem_markdown(texto)), [], [], origem


def testar_chave(api_key, modelo):
    """Faz uma chamada bem curta apenas para conferir se a chave funciona."""
    cliente = _criar_cliente(api_key)
    ordem = [modelo] + [m for m in MODELOS_RESERVA if m != modelo]
    ultimo_erro = None
    for nome in ordem:
        try:
            resposta = cliente.models.generate_content(
                model=nome, contents="Responda apenas: OK"
            )
            texto = (getattr(resposta, "text", "") or "").strip()
            return texto or "OK"
        except Exception as erro:
            ultimo_erro = erro
            continue
    raise ultimo_erro or RuntimeError("não foi possível testar a chave")


# ----------------------------------------------------------------------------
# Pequenos componentes de tela
# ----------------------------------------------------------------------------


def _pontos_arredondados(x1, y1, x2, y2, r=16):
    r = min(r, (x2 - x1) / 2, (y2 - y1) / 2)
    return [
        x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r,
        x2, y2 - r, x2, y2, x2 - r, y2, x1 + r, y2,
        x1, y2, x1, y2 - r, x1, y1 + r, x1, y1,
    ]


def arredondado(tela, x1, y1, x2, y2, r=16, **kw):
    """Desenha um retangulo de cantos arredondados dentro de um Canvas."""
    return tela.create_polygon(
        _pontos_arredondados(x1, y1, x2, y2, r), smooth=True, **kw
    )


# ----------------------------------------------------------------------------
# A marca do programa: uma lupa com um brilho de IA dentro da lente.
# O mesmo desenho vira o icone do .exe e o "rosto" da IA na conversa.
# ----------------------------------------------------------------------------

MARCA_TOPO = (0x6C, 0x95, 0xFF)      # azul claro (canto de cima)
MARCA_BASE = (0x2B, 0x4B, 0xE0)      # azul fundo (canto de baixo)
MARCA_VIDRO = (10, 16, 46, 92)       # vidro da lente (escuro, translucido)
MARCA_BRANCO = (255, 255, 255, 255)  # cor do traco

# A mesma lupa em cores diferentes. "topo"/"base" sao as pontas do degrade da
# pastilha, "traco" e a cor da lupa, "vidro" o dentro da lente e "brilho" o
# quanto de reflexo entra no alto da pastilha.
PALETA_AZUL = {
    "topo": MARCA_TOPO,
    "base": MARCA_BASE,
    "traco": MARCA_BRANCO,
    "vidro": MARCA_VIDRO,
    "brilho": 58,
}

# Cinza medio escuro, como escolheu o usuario: a lupa preta se destaca bem
# tanto na tela escura do programa quanto na area de trabalho.
PALETA_CINZA = {
    "topo": (156, 156, 162),
    "base": (134, 134, 141),
    "traco": (16, 16, 20, 255),
    "vidro": (0, 0, 0, 30),
    "brilho": 0,
}

PALETA_PRETA = {
    "topo": (255, 255, 255),
    "base": (223, 223, 229),
    "traco": (12, 12, 14, 255),
    "vidro": (0, 0, 0, 26),
    "brilho": 0,
}

PALETA_AZUL_COM_LUPA_PRETA = {
    "topo": MARCA_TOPO,
    "base": MARCA_BASE,
    "traco": (12, 16, 34, 255),
    "vidro": (255, 255, 255, 46),
    "brilho": 58,
}

# A marca que o programa usa de verdade: lupa preta na pastilha cinza clara.
MARCA_DO_PROGRAMA = PALETA_CINZA

# Quanto o desenho e ampliado antes de reduzir (deixa a borda suave).
_MARCA_AMPLIACAO = 4


def desenhar_icone(tamanho, com_fundo=True, paleta=None, com_brilho=True):
    """Desenha a marca do programa em qualquer tamanho.

    Devolve uma imagem do Pillow (RGBA) ou None se o Pillow nao estiver
    instalado. E a mesmissima arte usada no icone do .exe e no avatar da IA.

    "com_brilho" liga/desliga a estrelinha de IA que fica dentro da lente.
    """
    if not TEM_PIL:
        return None
    cores = paleta or MARCA_DO_PROGRAMA
    n = max(8, int(tamanho))
    ss = n * _MARCA_AMPLIACAO
    if ss > 2048:
        ss = 2048
    if ss < n:
        ss = n

    def px(fracao):
        return fracao * ss

    if com_fundo:
        # -- fundo: quadrado de cantos bem arredondados com degrade --
        mascara = Image.new("L", (ss, ss), 0)
        ImageDraw.Draw(mascara).rounded_rectangle(
            [px(0.030), px(0.030), ss - px(0.030), ss - px(0.030)],
            radius=px(0.225), fill=255,
        )
        pequeno = Image.new("RGB", (48, 48), cores["topo"])
        pp = pequeno.load()
        topo = cores["topo"]
        base = cores["base"]
        for y in range(48):
            for x in range(48):
                t = (x + y) / 94.0
                pp[x, y] = (
                    int(topo[0] + (base[0] - topo[0]) * t),
                    int(topo[1] + (base[1] - topo[1]) * t),
                    int(topo[2] + (base[2] - topo[2]) * t),
                )
        pintado = pequeno.resize((ss, ss), Image.BICUBIC)
        # brilho suave na parte de cima (efeito de vidro)
        brilho = Image.new("L", (1, ss), 0)
        bp = brilho.load()
        for y in range(ss):
            t = y / float(ss)
            bp[0, y] = int(
                cores["brilho"] * max(0.0, 1.0 - t / 0.40) ** 1.6
            )
        brilho = brilho.resize((ss, ss))
        pintado = Image.composite(
            Image.new("RGB", (ss, ss), (255, 255, 255)), pintado, brilho
        )
        fundo = Image.new("RGBA", (ss, ss), (0, 0, 0, 0))
        fundo.paste(pintado, (0, 0), mascara)
    else:
        fundo = Image.new("RGBA", (ss, ss), (0, 0, 0, 0))

    # -- a lupa --
    camada = Image.new("RGBA", (ss, ss), (0, 0, 0, 0))
    d = ImageDraw.Draw(camada)
    cx, cy = px(0.455), px(0.415)
    raio = px(0.205)
    traco = max(2, int(px(0.058)))

    d.ellipse(
        [cx - raio, cy - raio, cx + raio, cy + raio], fill=cores["vidro"]
    )
    # cabo na diagonal, com as pontas arredondadas
    desloc = raio / math.sqrt(2.0)
    inicio = (cx + desloc, cy + desloc)
    fim = (px(0.772), px(0.742))
    d.line([inicio, fim], fill=cores["traco"], width=traco)
    for ponto in (inicio, fim):
        d.ellipse(
            [ponto[0] - traco / 2.0, ponto[1] - traco / 2.0,
             ponto[0] + traco / 2.0, ponto[1] + traco / 2.0],
            fill=cores["traco"],
        )
    d.ellipse(
        [cx - raio, cy - raio, cx + raio, cy + raio],
        outline=cores["traco"], width=traco,
    )

    # brilho de IA (estrela de 4 pontas) no meio da lente
    if com_brilho:
        pontos = []
        brilho_raio = px(0.098)
        for grau in range(0, 360, 3):
            angulo = math.radians(grau)
            cosseno = abs(math.cos(2 * angulo))
            r = brilho_raio * (0.16 + 0.84 * cosseno ** 0.8)
            pontos.append(
                (cx + r * math.cos(angulo), cy + r * math.sin(angulo))
            )
        d.polygon(pontos, fill=cores["traco"])

    fundo = Image.alpha_composite(fundo, camada)
    if ss != n:
        fundo = fundo.resize((n, n), Image.LANCZOS)
    return fundo


def _arquivo_recurso(nome):
    """Acha um arquivo do programa (na pasta dele ou dentro do .exe)."""
    pastas = []
    try:
        pastas.append(Path(__file__).resolve().parent)
    except Exception:
        pass
    dentro_do_exe = getattr(sys, "_MEIPASS", None)
    if dentro_do_exe:
        pastas.append(Path(dentro_do_exe))
    try:
        pastas.append(Path.cwd())
    except Exception:
        pass
    for pasta in pastas:
        try:
            alvo = pasta / nome
            if alvo.is_file():
                return alvo
        except Exception:
            pass
    return None


def _arquivo_icone():
    """Acha o arquivo "icone.ico" (na pasta do programa ou dentro do .exe)."""
    return _arquivo_recurso("icone.ico")


# Os avatares da IA ficam guardados aqui para não serem redesenhados
# a cada mensagem (nem apagados pelo "coletor de lixo" do Python).
_FOTOS_IA = {}
_FOTOS_ENVIO = {}


def anda(widget):
    """Todos os widgets abaixo de um widget (ele mesmo incluido)."""
    achados = [widget]
    for filho in widget.winfo_children():
        achados.extend(anda(filho))
    return achados


def _foto_enviar(cor_bolao, tamanho=36):
    """Imagem do botao de enviar (bolha + aviao), com as bordas suavizadas.

    O Canvas do Tk desenha as diagonais em degraus e o aviao ficava
    serrilhado. Aqui a arte e feita pelo Pillow, que suaviza as bordas.
    """
    if not TEM_PIL or ImageTk is None:
        return None
    chave = (tuple(cor_bolao), int(tamanho))
    if chave in _FOTOS_ENVIO:
        return _FOTOS_ENVIO[chave]
    try:
        n = int(tamanho)
        ss = n * 4                      # desenha grande e reduz
        imagem = Image.new("RGBA", (ss, ss), (0, 0, 0, 0))
        desenho = ImageDraw.Draw(imagem)
        fator = ss / 36.0
        desenho.ellipse(
            [2 * fator, 2 * fator, 34 * fator, 34 * fator],
            fill=tuple(cor_bolao) + (255,),
        )
        desenho.polygon(
            [
                (AVIAO_XY[i] * fator, AVIAO_XY[i + 1] * fator)
                for i in range(0, len(AVIAO_XY), 2)
            ],
            fill=tuple(COR_ENVIAR_TRACO) + (255,),
        )
        foto = ImageTk.PhotoImage(imagem.resize((n, n), Image.LANCZOS))
    except Exception:
        return None
    _FOTOS_ENVIO[chave] = foto
    return foto


def _foto_ia(tamanho):
    if not TEM_PIL or ImageTk is None:
        return None
    chave = int(tamanho)
    if chave in _FOTOS_IA:
        return _FOTOS_IA[chave]
    try:
        imagem = desenhar_icone(chave)
        if imagem is None:
            return None
        foto = ImageTk.PhotoImage(imagem)
    except Exception:
        return None
    _FOTOS_IA[chave] = foto
    return foto


# ---------------------------------------------------------------------------
# Avatar do usuario (a imagem que o usuario escolheu, no lugar do "Voce")
# ---------------------------------------------------------------------------

_FOTOS_USUARIO = {}

# O avatar do usuario aparece sem pastilha: só o desenho, na cor do texto,
# direto no fundo escuro (do jeito que o usuario escolheu).
FUNDO_AVATAR_USUARIO = None
COR_AVATAR_USUARIO = (236, 236, 241, 255)

NOMES_AVATAR = (
    "avatar_usuario.png",
    "avatar_usuario.jpg",
    "avatar_usuario.jpeg",
    "avatar_usuario.webp",
)


def _arquivo_avatar_usuario():
    """Acha a imagem do usuario (png, jpg ou webp) que o usuario escolheu."""
    for nome in NOMES_AVATAR:
        achado = _arquivo_recurso(nome)
        if achado is not None:
            return achado
    return None


def _foto_usuario(tamanho):
    """Carrega a imagem do usuario pronta para mostrar na tela (ou None)."""
    if not TEM_PIL or ImageTk is None:
        return None
    chave = int(tamanho)
    if chave in _FOTOS_USUARIO:
        return _FOTOS_USUARIO[chave]
    arquivo = _arquivo_avatar_usuario()
    if arquivo is None:
        return None
    try:
        with Image.open(arquivo) as original:
            imagem = preparar_avatar(
                original, chave, fundo=FUNDO_AVATAR_USUARIO,
                so_desenho=True, cor=COR_AVATAR_USUARIO,
            )
        foto = ImageTk.PhotoImage(imagem)
    except Exception:
        return None
    _FOTOS_USUARIO[chave] = foto
    return foto


def preparar_avatar(original, tamanho, margem=0.06, fundo=None,
                   so_desenho=False, cor=None):
    """Ajusta a imagem do usuario num quadrado do tamanho pedido.

    Corta as bordas vazias, centraliza e coloca sobre o fundo escolhido.
    Com "so_desenho", o fundo preto da foto vira transparencia e sobra
    apenas o desenho, na cor "cor".
    """
    if so_desenho:
        brilho = original.convert("L")
        alfa = brilho.point(
            lambda v: 0 if v < 55 else min(255, int((v - 55) * 255 / 140))
        )
        caixa = alfa.point(lambda v: 255 if v > 24 else 0).getbbox()
        if caixa:
            alfa = alfa.crop(caixa)
            original = original.crop(caixa)
        imagem = Image.new("RGBA", original.size, cor or (255, 255, 255, 255))
        imagem.putalpha(alfa)
    else:
        imagem = original.convert("RGBA")

    caixa = imagem.getbbox()
    if caixa:
        imagem = imagem.crop(caixa)
    alvo = max(1, int(tamanho * (1.0 - margem)))
    escala = min(alvo / imagem.width, alvo / imagem.height)
    novo = (max(1, int(imagem.width * escala)), max(1, int(imagem.height * escala)))
    imagem = imagem.resize(novo, Image.LANCZOS)
    quadrado = Image.new("RGBA", (tamanho, tamanho), fundo or (0, 0, 0, 0))
    quadrado.alpha_composite(
        imagem, ((tamanho - novo[0]) // 2, (tamanho - novo[1]) // 2)
    )
    return quadrado



# ----------------------------------------------------------------------------
# Barra de rolagem escura
# ----------------------------------------------------------------------------

ESTILO_BARRA = "Pesquisa.Vertical.TScrollbar"
_ESTILO_BARRA_PRONTO = False


class Dica:
    """Texto de ajuda que aparece quando o mouse fica parado em cima.

    Fica quieto na tela (sem borda) e some assim que o mouse sai.
    """

    def __init__(self, alvo, texto, espera=500):
        self.alvo = alvo
        self.texto = texto
        self.espera = espera
        self.janela = None
        self._agendado = None
        alvo.bind("<Enter>", self._entrou, add="+")
        alvo.bind("<Leave>", self._saiu, add="+")
        alvo.bind("<Button-1>", self._saiu, add="+")

    def _entrou(self, _evento=None):
        self._agendado = self.alvo.after(self.espera, self._mostrar)

    def _saiu(self, _evento=None):
        if self._agendado is not None:
            try:
                self.alvo.after_cancel(self._agendado)
            except Exception:
                pass
            self._agendado = None
        self._esconder()

    def _mostrar(self):
        self._agendado = None
        if self.janela is not None or not self.alvo.winfo_exists():
            return
        try:
            topo = tk.Toplevel(self.alvo)
            topo.overrideredirect(True)
            topo.configure(bg=COR_BORDA)
            tk.Label(
                topo, text=self.texto, bg=COR_BARRA, fg=COR_TEXTO,
                font=(FONTE, 8), padx=9, pady=5, bd=0,
            ).pack()
            topo.update_idletasks()
            x = self.alvo.winfo_rootx() + self.alvo.winfo_width() // 2
            y = self.alvo.winfo_rooty() + self.alvo.winfo_height() + 7
            x -= topo.winfo_width() // 2
            topo.geometry("+%d+%d" % (x, y))
            self.janela = topo
        except Exception:
            self.janela = None

    def _esconder(self):
        if self.janela is not None:
            try:
                self.janela.destroy()
            except Exception:
                pass
            self.janela = None


def _desenhar_copiar(pincel, s, cor, fundo_dentro, espessura=1):
    """Duas folhas sobrepostas (o icone de copiar resposta)."""
    dentro = fundo_dentro or (0, 0, 0, 0)
    pincel.rectangle(
        [5.5 * s, 3.5 * s, 16.5 * s, 14.5 * s], outline=cor,
        width=espessura,
    )
    pincel.rectangle(
        [9.5 * s, 7.5 * s, 20 * s, 18.5 * s], fill=dentro, outline=cor,
        width=espessura,
    )


def _icone_copiar(pai, comando, tamanho=19, cor=COR_TEXTO_3,
                  cor_vivo=COR_TEXTO, fundo_ativo=COR_BARRA):
    """Ícone discreto de 'copiar' (duas folhas) usado nas respostas.

    Passa a ser um botão de verdade: quando o mouse entra, aparece um
    quadradinho de fundo e o desenho fica mais claro; quando sai, volta
    ao normal (sem fundo), bem discretinho.
    """
    n = int(tamanho)
    desenho = tk.Canvas(
        pai, width=n, height=n, bg=COR_FUNDO, highlightthickness=0, bd=0,
        cursor="hand2",
    )
    repouso = _foto_de_simbolo(
        "copiar", n, cor, _desenhar_copiar, fundo_dentro=COR_FUNDO,
    )
    ativo = _foto_de_simbolo(
        "copiar", n, cor_vivo, _desenhar_copiar, fundo=fundo_ativo,
        cantos=6, fundo_dentro=fundo_ativo,
    )

    if repouso is None or ativo is None:
        # sem Pillow: desenho antigo no Canvas (fica serrilhado, mas funciona)
        def pintar(mouse_por_cima):
            desenho.delete("tudo")
            cor_atual = cor_vivo if mouse_por_cima else cor
            if mouse_por_cima:
                arredondado(
                    desenho, 0, 0, n, n, 6, fill=fundo_ativo, outline=""
                )
            s = n / 22.0
            desenho.create_rectangle(
                5.5 * s, 3.5 * s, 16.5 * s, 14.5 * s, outline=cor_atual, width=1
            )
            desenho.create_rectangle(
                9.5 * s, 7.5 * s, 20 * s, 18.5 * s, fill=COR_FUNDO,
                outline=cor_atual, width=1,
            )
    else:
        item = desenho.create_image(
            n / 2.0, n / 2.0, image=repouso, anchor="center",
        )

        def pintar(mouse_por_cima):
            desenho.itemconfigure(
                item, image=ativo if mouse_por_cima else repouso
            )

    def entrou(_evento=None):
        pintar(True)

    def saiu(_evento=None):
        pintar(False)

    def apertou(_evento=None):
        pintar(False)
        comando()

    pintar(False)
    desenho.bind("<Enter>", entrou)
    desenho.bind("<Leave>", saiu)
    desenho.bind("<Button-1>", apertou)
    return desenho


def _desenhar_engrenagem(pincel, s, cor, fundo_dentro, espessura=1):
    """Engrenagem de linha fina: dentes ligados num corpo só, com o furo."""
    import math

    centro = 11.0 * s
    dentes = 8
    passo = 2 * math.pi / dentes
    ponta = 22.0 * 0.46 * s
    raiz = 22.0 * 0.33 * s
    furo = 22.0 * 0.13 * s
    pontos = []
    for i in range(dentes):
        base = i * passo
        for fracao, raio in (
            (0.00, raiz), (0.16, raiz), (0.26, ponta), (0.74, ponta),
            (0.84, raiz), (1.00, raiz),
        ):
            ang = base + passo * fracao
            pontos.append(centro + math.cos(ang) * raio)
            pontos.append(centro + math.sin(ang) * raio)
    # fecha o desenho repeating o primeiro ponto (a linha fica fechada)
    pincel.line(pontos + [pontos[0], pontos[1]], fill=cor, width=espessura,
                joint="curve")
    pincel.ellipse(
        [centro - furo, centro - furo, centro + furo, centro + furo],
        outline=cor, width=espessura,
    )


def _engrenagem(pai, tamanho=18, cor=COR_TEXTO_2, cor_vivo=COR_TEXTO):
    """Ícone de Configurações: engrenagem desenhada com Pillow (bem lisa)."""
    n = int(tamanho)
    desenho = tk.Canvas(
        pai, width=n, height=n, bg=COR_PAINEL, highlightthickness=0, bd=0,
    )
    repouso = _foto_de_simbolo("engrenagem", n, cor, _desenhar_engrenagem)
    ativo = _foto_de_simbolo("engrenagem", n, cor_vivo, _desenhar_engrenagem)
    if repouso is None or ativo is None:
        # sem Pillow: mantem o desenho antigo no Canvas
        import math

        def pintar(mouse_por_cima):
            cor_atual = cor_vivo if mouse_por_cima else cor
            desenho.delete("tudo")
            cx = cy = n / 2.0
            dentes = 8
            passo = 2 * math.pi / dentes
            pont = n * 0.46
            raz = n * 0.33
            furo = n * 0.13
            pontos = []
            for i in range(dentes):
                base = i * passo
                for fracao, raio in (
                    (0.00, raz), (0.16, raz), (0.26, pont), (0.74, pont),
                    (0.84, raz), (1.00, raz),
                ):
                    ang = base + passo * fracao
                    pontos.extend(
                        (cx + math.cos(ang) * raio, cy + math.sin(ang) * raio)
                    )
            desenho.create_polygon(
                pontos, outline=cor_atual, width=1, fill="", smooth=False
            )
            desenho.create_oval(
                cx - furo, cy - furo, cx + furo, cy + furo,
                outline=cor_atual, width=1,
            )
    else:
        item = desenho.create_image(
            n / 2.0, n / 2.0, image=repouso, anchor="center",
        )

        def pintar(mouse_por_cima):
            desenho.itemconfigure(
                item, image=ativo if mouse_por_cima else repouso
            )

    pintar(False)
    desenho.bind("<Enter>", lambda _e: pintar(True))
    desenho.bind("<Leave>", lambda _e: pintar(False))
    return desenho


_FOTOS_PONTOS = {}
_FOTOS_SIMBOLOS = {}

# Tamanho dos tres pontinhos de "pensando". Pequenos e lisinhos.
TAMANHO_PONTO = 6

# Todos os icones do programa sao desenhados com o Pillow (e nao com o
# Canvas do Tk), porque o Tk nao suaviza as bordas e os desenhos ficavam
# serrilhados. Aqui cada icone e desenhado 4x maior e depois reduzido com
# LANCZOS, o que deixa tudo com borda lisa.


def _rgba(cor, alpha=255):
    """As cores do programa sao textos como '#6f6f7c'; o Pillow quer RGB."""
    if cor is None:
        return (255, 255, 255, alpha)
    if isinstance(cor, str):
        try:
            vermelho, verde, azul = ImageColor.getrgb(cor)
            return (vermelho, verde, azul, alpha)
        except Exception:
            return (255, 255, 255, alpha)
    partes = tuple(cor)
    if len(partes) >= 4:
        return partes
    return (partes[0], partes[1], partes[2], alpha)


def _foto_de_simbolo(nome, tamanho, cor, desenhar, fundo=None, cantos=0,
                     fundo_dentro=None):
    """Desenha um icone com o Pillow e devolve a foto pronta (ou None)."""
    chave = (nome, int(tamanho), cor, fundo, cantos, fundo_dentro)
    if chave in _FOTOS_SIMBOLOS:
        return _FOTOS_SIMBOLOS[chave]
    if not TEM_PIL or ImageTk is None:
        return None
    try:
        n = int(tamanho)
        ss = n * 4
        imagem = Image.new("RGBA", (ss, ss), (0, 0, 0, 0))
        pincel = ImageDraw.Draw(imagem)
        escala = ss / 22.0            # os desenhos usam uma grade de 22
        # O trace e desenhado no tamanho grande e reduzido depois: 1 pixel
        # no desenho 4x daria menos de meio pixel na tela (ficava apagado).
        espessura = max(1, int(round(escala * 1.15)))
        if fundo is not None and cantos > 0:
            pincel.rounded_rectangle(
                [0, 0, ss - 1, ss - 1], radius=cantos * escala,
                fill=_rgba(fundo),
            )
        desenhar(pincel, escala, _rgba(cor), _rgba(fundo_dentro), espessura)
        foto = ImageTk.PhotoImage(imagem.resize((n, n), Image.LANCZOS))
    except Exception:
        return None
    _FOTOS_SIMBOLOS[chave] = foto
    return foto


def _foto_ponto(tamanho, cor, forte):
    """Um pontinho redondo e liso (o Canvas do Tk deixa serrilhado)."""
    chave = (int(tamanho), cor, bool(forte))
    if chave in _FOTOS_PONTOS:
        return _FOTOS_PONTOS[chave]
    if not TEM_PIL or ImageTk is None:
        return None
    try:
        n = int(tamanho)
        ss = n * 4                      # desenha grande e reduz: fica liso
        imagem = Image.new("RGBA", (ss, ss), (0, 0, 0, 0))
        ImageDraw.Draw(imagem).ellipse([0, 0, ss - 1, ss - 1], fill=_rgba(cor))
        foto = ImageTk.PhotoImage(imagem.resize((n, n), Image.LANCZOS))
    except Exception:
        return None
    _FOTOS_PONTOS[chave] = foto
    return foto



def _preparar_scrollbar_escuro(raiz):
    """Deixa a barra de rolagem com a cor escura do programa.

    O Windows desenha a barra de rolagem sempre clara (tema do sistema) e
    ignora as cores do tkinter. Aqui a gente troca para um estilo próprio,
    sem as setinhas, igual aos aplicativos escuros modernos.
    """
    global _ESTILO_BARRA_PRONTO
    if _ESTILO_BARRA_PRONTO:
        return
    _ESTILO_BARRA_PRONTO = True
    try:
        estilo = ttk.Style(raiz)
        estilo.theme_use("clam")
        # Tira as setinhas de cima e de baixo: sobra só a barrinha fina.
        estilo.layout(
            ESTILO_BARRA,
            [(
                "Vertical.Scrollbar.trough",
                {
                    "sticky": "ns",
                    "children": [(
                        "Vertical.Scrollbar.thumb",
                        {"expand": "1", "sticky": "nswe"},
                    )],
                },
            )],
        )
        estilo.configure(
            ESTILO_BARRA,
            background=COR_BORDA,      # a parte que se arrasta
            troughcolor=COR_FUNDO,     # o fundo da canaleta
            bordercolor=COR_FUNDO,
            arrowcolor=COR_FUNDO,
            darkcolor=COR_BORDA,
            lightcolor=COR_BORDA,
        )
        estilo.map(
            ESTILO_BARRA,
            background=[("pressed", COR_TEXTO_3), ("active", COR_TEXTO_3)],
        )
    except Exception:
        pass


def ativar_barra_escura(janela):
    """Deixa a barra de título do Windows escura (modo escuro de verdade).

    Funciona no Windows 10 (1809+) e no Windows 11. Se não der certo, o
    programa segue normalmente com a barra clara.
    """
    try:
        import ctypes

        janela.update_idletasks()
        hwnd = ctypes.windll.user32.GetParent(janela.winfo_id())
        if not hwnd:
            hwnd = janela.winfo_id()
        ligado = ctypes.c_int(1)
        # 20 = Windows 11 / 10 novo; 19 = Windows 10 1809.
        for atributo in (20, 19):
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, atributo, ctypes.byref(ligado), ctypes.sizeof(ligado)
            )
    except Exception:
        pass


class Avatar(tk.Canvas):
    """Bolinha com iniciais, ao lado de cada mensagem."""

    def __init__(self, pai, texto, cor, tamanho=30):
        super().__init__(
            pai, width=tamanho, height=tamanho, bg=COR_FUNDO,
            highlightthickness=0, bd=0,
        )
        fonte = (FONTE, 9 if len(texto) <= 2 else 7, "bold")
        self.create_oval(1, 1, tamanho - 1, tamanho - 1, fill=cor, outline="")
        self.create_text(
            tamanho / 2, tamanho / 2 + 1, text=texto, fill="#ffffff",
            font=fonte,
        )


def avatar_ia(pai, tamanho=30):
    """Devolve o "rosto" da IA: o icone do programa (ou a bolinha, se falhar)."""
    foto = _foto_ia(tamanho)
    if foto is None:
        return Avatar(pai, "IA", COR_ACCENT, tamanho)
    rotulo = tk.Label(pai, image=foto, bg=COR_FUNDO, bd=0, highlightthickness=0)
    rotulo.imagem = foto
    return rotulo


def avatar_usuario(pai, tamanho=30):
    """Devolve a imagem do usuario (ou a bolinha azul, se ela nao existir)."""
    foto = _foto_usuario(tamanho)
    if foto is None:
        return Avatar(pai, "Você", COR_USUARIO, tamanho)
    rotulo = tk.Label(pai, image=foto, bg=COR_FUNDO, bd=0, highlightthickness=0)
    rotulo.imagem = foto
    return rotulo


class Botao(tk.Label):
    """Botao "fantasma" (sem borda) usado no topo."""

    def __init__(self, pai, texto, comando, destaque=False):
        cor = COR_ACCENT if destaque else COR_BARRA
        super().__init__(
            pai, text=texto, font=(FONTE, 10),
            fg="#ffffff" if destaque else COR_TEXTO_2,
            bg=cor, padx=13, pady=7, cursor="hand2",
        )
        self._normal = cor
        self._hover = COR_ACCENT_CLARO if destaque else COR_BORDA
        self._cor_fg = "#ffffff" if destaque else COR_TEXTO
        self.bind("<Enter>", self._entrar)
        self.bind("<Leave>", self._sair)
        self.bind("<Button-1>", lambda _e: comando())

    def _entrar(self, _e=None):
        self.configure(bg=self._hover, fg=self._cor_fg)

    def _sair(self, _e=None):
        self.configure(bg=self._normal)


class BotaoLateral(tk.Frame):
    """Botão da barra lateral (fino, alinhado à esquerda, realça ao passar o mouse)."""

    def __init__(self, pai, texto, comando, icone=""):
        super().__init__(pai, bg=COR_PAINEL, cursor="hand2")
        self._comando = comando
        self._filhos = []
        if callable(icone):
            # ícone desenhado pelo próprio programa (linhas finas)
            self._icone = icone(self)
            self._icone.pack(side="left", padx=(13, 0), pady=9)
        elif icone:
            self._icone = tk.Label(
                self, text=icone, bg=COR_PAINEL, fg=COR_TEXTO_3, font=(FONTE, 12)
            )
            self._icone.pack(side="left", padx=(14, 0), pady=9)
            self._filhos.append(self._icone)
        else:
            self._icone = None
        self._rotulo = tk.Label(
            self, text=texto, bg=COR_PAINEL, fg=COR_TEXTO_2, font=(FONTE, 10),
            anchor="w",
        )
        self._rotulo.pack(
            side="left", fill="x", expand=True,
            padx=((10 if icone else 14), 10), pady=9,
        )
        self._filhos.append(self._rotulo)
        for widget in [self] + self._filhos:
            widget.bind("<Enter>", self._entrar)
            widget.bind("<Leave>", self._sair)
            widget.bind("<Button-1>", self._clicar)

    def _entrar(self, _e=None):
        self.configure(bg=COR_BARRA)
        for widget in self._filhos:
            widget.configure(bg=COR_BARRA, fg=COR_TEXTO)
        # o icone so pode ser pintado se for um Label (desenhos em Canvas
        # nao aceitam a opcao fg)
        if self._icone is not None and self._icone.winfo_class() == "Label":
            self._icone.configure(fg=COR_TEXTO)

    def _sair(self, _e=None):
        self.configure(bg=COR_PAINEL)
        for widget in self._filhos:
            widget.configure(bg=COR_PAINEL, fg=COR_TEXTO_2)
        # o icone so pode ser pintado se for um Label (desenhos em Canvas
        # nao aceitam a opcao fg)
        if self._icone is not None and self._icone.winfo_class() == "Label":
            self._icone.configure(fg=COR_TEXTO_3)

    def _clicar(self, _e=None):
        self._comando()


class Chip(tk.Canvas):
    """Sugestão clicável mostrada na tela de boas-vindas."""

    def __init__(self, pai, rotulo, pergunta, comando, largura_max=520):
        super().__init__(pai, bg=COR_FUNDO, highlightthickness=0, bd=0)
        item = self.create_text(
            0, 0, text=rotulo, font=(FONTE, 10), fill=COR_TEXTO_2,
            width=largura_max, anchor="nw", justify="left",
        )
        x0, y0, x1, y1 = self.bbox(item)
        self.move(item, 18 - x0, 11 - y0)
        largura, altura = (x1 - x0) + 36, (y1 - y0) + 22
        self.configure(width=largura, height=altura)
        fundo = arredondado(
            self, 0, 0, largura, altura, 14, fill=COR_BARRA, outline=COR_BORDA
        )
        self.tag_lower(fundo)
        self.configure(cursor="hand2")
        self.bind("<Enter>", lambda e: (
            self.itemconfigure(fundo, fill=COR_BORDA),
            self.itemconfigure(item, fill=COR_TEXTO),
        ))
        self.bind("<Leave>", lambda e: (
            self.itemconfigure(fundo, fill=COR_BARRA),
            self.itemconfigure(item, fill=COR_TEXTO_2),
        ))
        self.bind("<Button-1>", lambda e: comando(pergunta))


# ----------------------------------------------------------------------------
# Janela do programa
# ----------------------------------------------------------------------------

SUGESTOES = [
    ("Quais são as principais notícias de hoje?",
     "Quais são as principais notícias de hoje no Brasil e no mundo?"),
    ("Qual foi o resultado do último jogo do Brasil?",
     "Qual foi o resultado do último jogo da seleção brasileira de futebol?"),
    ("Quanto está o dólar hoje?",
     "Quanto está a cotação do dólar hoje em relação ao real?"),
    ("Me mostre imagens de God of War",
     "imagens de god of war"),
    ("Me explique o que é inteligência artificial de forma simples",
     "Me explique o que é inteligência artificial de forma simples, para "
     "quem não entende de tecnologia."),
]


class Aplicativo:
    def __init__(self, raiz):
        self.raiz = raiz
        self.cfg = carregar_config()
        self.historico = []
        self.mensagens = []
        self.fila = queue.Queue()
        self.ocupado = False
        self.animacao_id = None
        self.animacao_passo = 0
        self._pontos_digitando = []
        self._canvas_digitando = None
        self._redim_id = None
        self._janela_config = None
        self._janela_conversas = None
        self._aba_config = "chave"
        self._popup_conversa = None
        # Identificador da conversa aberta (para atualizar o historico).
        self._id_conversa = None
        # Qual serviço escreveu a última resposta (Gemini ou plano B).
        self._origem_resposta = ""
        # Animação de escrita (efeito de digitar a resposta letra a letra).
        self._anim = None
        self._anim_id = None
        self._bolha_anim = None
        # Corretor ortográfico (carregado só quando usado).
        self._corretor = None
        self._corretor_en = None
        self._checagem_id = None
        self._menu_ortografia_atual = None

        raiz.title("Pesquisa IA")
        self._definir_icone(raiz)
        raiz.geometry("1000x740")
        raiz.minsize(760, 560)
        raiz.configure(bg=COR_FUNDO)

        self._montar_tela()
        self._renderizar()
        self._atualizar_status_chave()
        self.raiz.after(100, self._processar_fila)
        # Deixa a barra de título do Windows escura (modo escuro de verdade).
        self.raiz.after(150, lambda: ativar_barra_escura(self.raiz))

    # -- montagem -----------------------------------------------------------

    def _definir_icone(self, raiz):
        """Coloca o icone do programa na janela (barra de tarefas)."""
        caminho = _arquivo_icone()
        if caminho is None:
            return
        try:
            raiz.iconbitmap(default=str(caminho))
        except Exception:
            pass

    def _montar_tela(self):
        self._montar_lateral()
        self.principal = tk.Frame(self.raiz, bg=COR_FUNDO)
        self.principal.pack(side="left", fill="both", expand=True)
        self._montar_barra_superior()
        self._montar_chat()
        self._montar_rodape()
        # A lateral ja começa aberta, entao a barra do "Menu" comeca escondida.
        self._atualizar_menu()

    def _montar_barra_superior(self):
        # Essa barra existe so para o botao de abrir a lateral. Quando a
        # lateral esta aberta, ela some de vez (quem fecha e o botao "«").
        barra = tk.Frame(self.principal, bg=COR_FUNDO)
        barra.pack(fill="x", padx=12, pady=(8, 0))
        self.barra_menu = barra
        self.botao_lateral = tk.Label(
            barra, text="☰   Menu", bg=COR_FUNDO, fg=COR_TEXTO_2,
            font=(FONTE, 10), cursor="hand2", padx=6, pady=3,
        )
        self.botao_lateral.pack(side="left")
        self.botao_lateral.bind("<Button-1>", lambda _e: self._alternar_lateral())
        self.botao_lateral.bind(
            "<Enter>", lambda _e: self.botao_lateral.configure(fg=COR_TEXTO)
        )
        self.botao_lateral.bind(
            "<Leave>", lambda _e: self.botao_lateral.configure(fg=COR_TEXTO_2)
        )

    def _atualizar_menu(self):
        """Esconde a barra de cima enquanto a lateral estiver aberta."""
        if getattr(self, "barra_menu", None) is None:
            return
        if getattr(self, "lateral_visivel", True):
            self.barra_menu.pack_forget()
            return
        area = getattr(self, "area_chat", None)
        if area is not None:
            self.barra_menu.pack(
                before=area, fill="x", padx=12, pady=(8, 0)
            )
        else:
            self.barra_menu.pack(fill="x", padx=12, pady=(8, 0))

    def _alternar_lateral(self):
        if getattr(self, "lateral_visivel", True):
            self.lateral.pack_forget()
            self.lateral_visivel = False
        else:
            self.lateral.pack(side="left", fill="y", before=self.principal)
            self.lateral_visivel = True
        self._atualizar_menu()

    def _montar_lateral(self):
        self.lateral_visivel = True
        self.lateral = tk.Frame(self.raiz, bg=COR_PAINEL, width=232)
        self.lateral.pack(side="left", fill="y")
        self.lateral.pack_propagate(False)
        self._largura_lateral = 232

        marca = tk.Frame(self.lateral, bg=COR_PAINEL)
        marca.pack(fill="x", padx=18, pady=(20, 16))
        foto_logo = _foto_ia(34)
        if foto_logo is not None:
            tk.Label(
                marca, image=foto_logo, bg=COR_PAINEL, bd=0, highlightthickness=0
            ).pack(side="left")
        else:
            logo = tk.Canvas(
                marca, width=34, height=34, bg=COR_PAINEL, highlightthickness=0
            )
            logo.pack(side="left")
            logo.create_oval(2, 2, 32, 32, fill=COR_ACCENT, outline="")
            logo.create_text(17, 18, text="IA", fill="#ffffff", font=(FONTE, 10, "bold"))
        textos = tk.Frame(marca, bg=COR_PAINEL)
        textos.pack(side="left", padx=(10, 0))
        tk.Label(
            textos, text="Pesquisa IA", bg=COR_PAINEL, fg=COR_TEXTO,
            font=(FONTE, 12, "bold"),
        ).pack(anchor="w")

        fechar = tk.Label(
            marca, text="«", bg=COR_PAINEL, fg=COR_TEXTO_3,
            font=(FONTE, 14), cursor="hand2",
        )
        fechar.pack(side="right")
        fechar.bind("<Button-1>", lambda _e: self._alternar_lateral())
        fechar.bind("<Enter>", lambda _e: fechar.configure(fg=COR_TEXTO))
        fechar.bind("<Leave>", lambda _e: fechar.configure(fg=COR_TEXTO_3))

        tk.Frame(self.lateral, bg=COR_BORDA, height=1).pack(fill="x", padx=14)

        menu = tk.Frame(self.lateral, bg=COR_PAINEL)
        menu.pack(fill="x", pady=(10, 0))
        BotaoLateral(menu, "Nova conversa", self._nova_conversa, "＋").pack(
            fill="x", padx=8, pady=2
        )
        BotaoLateral(menu, "Conversas", self._alternar_lista_conversas, "☰").pack(
            fill="x", padx=8, pady=2
        )
        # A lista de conversas abre em cascata logo abaixo deste botao.
        self.lista_conversas = tk.Frame(menu, bg=COR_PAINEL)
        self._botao_config = BotaoLateral(
            menu, "Configurações", self._abrir_config,
            lambda pai: _engrenagem(pai),
        )
        self._botao_config.pack(fill="x", padx=8, pady=2)

        # A borda direita da lateral é arrastável: puxa para alargar ou
        # afinar, e os titulos das conversas se ajustam na hora.
        alca = tk.Frame(self.lateral, bg=COR_BORDA, cursor="sb_h_double_arrow")
        alca.pack(side="right", fill="y")
        alca.bind("<Button-1>", lambda _e: setattr(self, "_arrastando", True))
        alca.bind("<B1-Motion>", self._arrastar_lateral)
        alca.bind("<ButtonRelease-1>",
                  lambda _e: setattr(self, "_arrastando", False))

    def _arrastar_lateral(self, evento):
        """Alarga ou afina a lateral arrastando a borda direita dela."""
        x = evento.x_root - self.raiz.winfo_rootx()
        nova = max(170, min(430, x))
        if nova == self._largura_lateral:
            return
        self._largura_lateral = nova
        self.lateral.configure(width=nova)
        self._reajustar_titulos_conversas()

    def _reajustar_titulos_conversas(self):
        """Reajusta a quebra de linha dos titulos conforme a largura."""
        if not self.lista_conversas.winfo_ismapped():
            return
        # espaco ocupado pelo item: paddings + os tres pontinhos + folga
        largura_texto = max(60, self._largura_lateral - 78)
        for item in self.lista_conversas.winfo_children():
            for filho in self._todos(item):
                if getattr(filho, "_titulo", False):
                    try:
                        filho.configure(wraplength=largura_texto)
                    except Exception:
                        pass

    def _todos(self, widget):
        """Todos os widgets abaixo de um widget (atalho para anda)."""
        return anda(widget)

    def _montar_chat(self):
        area = tk.Frame(self.principal, bg=COR_FUNDO)
        area.pack(fill="both", expand=True)
        self.area_chat = area

        self.canvas = tk.Canvas(area, bg=COR_FUNDO, highlightthickness=0, bd=0)
        self.canvas.pack(side="left", fill="both", expand=True)

        _preparar_scrollbar_escuro(self.raiz)
        self.barra = ttk.Scrollbar(
            area, orient="vertical", command=self.canvas.yview,
            style=ESTILO_BARRA,
        )
        self.barra.pack(side="right", fill="y")
        self.canvas.configure(yscrollcommand=self.barra.set)

        self.interno = tk.Frame(self.canvas, bg=COR_FUNDO)
        self._janela = self.canvas.create_window(
            (0, 0), window=self.interno, anchor="nw"
        )
        self.interno.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )
        self.canvas.bind(
            "<Configure>",
            lambda e: (
                self.canvas.itemconfigure(self._janela, width=e.width),
                self._agendar_redesenho(),
                self._teto_do_chat(),
            ),
        )

        self.raiz.bind_all("<MouseWheel>", self._rolar)
        self.raiz.bind("<F5>", lambda _e: self._nova_conversa())
        self.raiz.bind("<Control-b>", lambda _e: self._alternar_lateral())

    def _montar_rodape(self):
        rodape = tk.Frame(self.principal, bg=COR_FUNDO)
        rodape.pack(fill="x", padx=16, pady=(8, 6))

        caixa = tk.Frame(
            rodape, bg=COR_BARRA, highlightthickness=1,
            highlightbackground=COR_BORDA, highlightcolor=COR_BORDA,
        )
        caixa.pack(fill="x")

        self.entrada = tk.Text(
            caixa, height=1, wrap="word", font=(FONTE, 11),
            bg=COR_BARRA, fg=COR_TEXTO, insertbackground=COR_ACCENT,
            relief="flat", borderwidth=0, padx=14, pady=11,
        )
        self.botao_enviar = tk.Canvas(
            caixa, width=36, height=36, bg=COR_BARRA,
            highlightthickness=0, bd=0, cursor="hand2",
        )
        self._desenhar_enviar(COR_ENVIAR)
        # pacote botao ANTES da entrada, assim o Tk reserva espaço para ele
        # e não o encolhe quando a janela encurta ao mínimo
        self.botao_enviar.pack(side="right", padx=8, pady=7)
        self.entrada.pack(side="left", fill="both", expand=True)

        self.entrada.bind("<Return>", self._ao_enter)
        self.entrada.bind("<KeyRelease>", self._ao_digitar)
        self.entrada.bind("<Button-3>", self._menu_ortografia)
        # Palavra errada fica com a cor normal e ganha SO um sublinhado
        # vermelho (sem deixar o texto vermelho, que atrapalha a leitura).
        try:
            self.entrada.tag_configure(
                "ortografia", underline=True, underlinefg=COR_ERRO_TX,
            )
        except tk.TclError:
            # Versao antiga do Tk: nao sabe pintar o sublinhado, entao
            # sublinha sem cor (o texto continua na cor normal).
            self.entrada.tag_configure("ortografia", underline=True)

        self.botao_enviar.bind("<Enter>", lambda e: self._desenhar_enviar(COR_ENVIAR_HOVER))
        self.botao_enviar.bind("<Leave>", lambda e: self._desenhar_enviar(COR_ENVIAR))
        self.botao_enviar.bind("<Button-1>", lambda e: self._enviar())
        # Ao redimensionar a janela, o Tk chega a limpar o Canvas do botao;
        # por isso o desenho e refeito sempre que o tamanho muda.
        self.botao_enviar.bind(
            "<Configure>",
            lambda e: self._desenhar_enviar(COR_ENVIAR),
        )

        # A linha de avisos fica escondida quando nao ha nada a dizer (so
        # aparece sozinha em mensagens como "Imagem salva em ...").
        linha_status = tk.Frame(self.principal, bg=COR_FUNDO)
        self.linha_status = linha_status
        self.var_status = tk.StringVar(value="")
        self.rotulo_status = tk.Label(
            linha_status, textvariable=self.var_status, bg=COR_FUNDO,
            fg=COR_TEXTO_3, font=(FONTE, 9),
        )
        self._status_visivel = False

        self.entrada.focus_set()

    def _desenhar_enviar(self, cor):
        """Desenha o botao de enviar.

        O aviao e uma imagem feita com Pillow (o Canvas do Tk deixa a borda
        em degraus, o que fica serrilhado). Sem Pillow, cai no desenho antigo.
        """
        if (getattr(self, "_cor_enviar_atual", None) == cor
                and self.botao_enviar.find_all()):
            return
        self._cor_enviar_atual = cor

        foto = _foto_enviar(cor)
        if foto is not None:
            self._foto_enviar_atual = foto
            item = getattr(self, "_item_enviar", None)
            if item is not None:
                try:
                    self.botao_enviar.itemconfigure(item, image=foto)
                    return
                except tk.TclError:
                    pass
            self.botao_enviar.delete("all")
            self._item_enviar = self.botao_enviar.create_image(18, 18, image=foto)
            return

        self.botao_enviar.delete("all")
        self._item_enviar = None
        cor_bolha = "#%02x%02x%02x" % cor
        cor_aviao = "#%02x%02x%02x" % COR_ENVIAR_TRACO
        self.botao_enviar.create_oval(2, 2, 34, 34, fill=cor_bolha, outline="")
        self.botao_enviar.create_polygon(
            AVIAO_XY, fill=cor_aviao, outline="",
        )

    # -- utilidades ---------------------------------------------------------

    def _descende_de(self, widget, ancestral):
        while widget is not None:
            if widget is ancestral:
                return True
            widget = getattr(widget, "master", None)
        return False

    def _rolar(self, evento):
        if not self.mensagens:
            return "break"
        try:
            alvo = self.raiz.winfo_containing(evento.x_root, evento.y_root)
        except Exception:
            alvo = None
        if self._descende_de(alvo, self.canvas):
            # teto: se o conteudo nao preenche a tela, nao ha por onde
            # rolar -- manter o topo evita o espaco em branco.
            try:
                if self.interno.winfo_height() <= self.canvas.winfo_height():
                    self.canvas.yview_moveto(0.0)
                    return "break"
            except Exception:
                pass
            self.canvas.yview_scroll(int(-evento.delta / 120), "units")
            self._teto_do_chat()

    def _teto_do_chat(self):
        """Evita espaco em branco desnecessario acima da primeira mensagem."""
        try:
            if self.interno.winfo_height() <= self.canvas.winfo_height():
                self.canvas.yview_moveto(0.0)
        except Exception:
            pass

    def _agendar_redesenho(self):
        if self._redim_id is not None:
            try:
                self.raiz.after_cancel(self._redim_id)
            except Exception:
                pass
        self._redim_id = self.raiz.after(150, self._renderizar)

    def _largura_bolha(self):
        largura = self.canvas.winfo_width()
        if largura <= 1:
            largura = 900
        return max(240, min(680, largura - 150))

    def _rolar_fim(self):
        try:
            self.canvas.update_idletasks()
            # teto: se o conteudo cabe inteiro na tela, nao rola
            if self.interno.winfo_height() <= self.canvas.winfo_height():
                self.canvas.yview_moveto(0.0)
            else:
                self.canvas.yview_moveto(1.0)
        except Exception:
            pass

    def _definir_status(self, texto, cor=None):
        """Mostra um aviso embaixo da barra de pergunta (so quando ha algo)."""
        self.var_status.set(texto)
        self.rotulo_status.configure(fg=cor or COR_TEXTO_3)
        visivel = bool(texto)
        if visivel == self._status_visivel:
            return
        self._status_visivel = visivel
        if visivel:
            self.rotulo_status.pack(side="left")
            self.linha_status.pack(fill="x", padx=18, pady=(0, 10))
        else:
            self.linha_status.pack_forget()

    def _ajustar_altura(self, _e=None):
        texto = self.entrada.get("1.0", "end-1c")
        if not texto.strip():
            self.entrada.configure(height=1)
            return
        try:
            d = self.entrada.count("1.0", "end-1c", "displaylines")
            linhas = d[0] if isinstance(d, (tuple, list)) else int(d)
        except Exception:
            linhas = texto.count("\n") + 1
        self.entrada.configure(height=max(1, min(8, linhas or 1)))

    def _ao_digitar(self, evento=None):
        self._ajustar_altura()
        self._agendar_correcao()

    # -- corretor ortografico ----------------------------------------------

    def _corretor_ativo(self):
        return bool(self.cfg.get("corretor", True))

    def _obter_corretor(self):
        if self._corretor is None:
            try:
                from spellchecker import SpellChecker
                self._corretor = SpellChecker(language="pt")
            except Exception:
                self._corretor = False
        return self._corretor

    def _obter_corretor_en(self):
        if self._corretor_en is None:
            try:
                from spellchecker import SpellChecker
                self._corretor_en = SpellChecker(language="en")
            except Exception:
                self._corretor_en = False
        return self._corretor_en

    def _agendar_correcao(self):
        if self._checagem_id is not None:
            try:
                self.raiz.after_cancel(self._checagem_id)
            except Exception:
                pass
        self._checagem_id = self.raiz.after(350, self._checar_ortografia)

    def _checar_ortografia(self):
        self._checagem_id = None
        entrada = self.entrada
        entrada.tag_remove("ortografia", "1.0", "end")
        if not self._corretor_ativo():
            return
        corretor = self._obter_corretor()
        if not corretor:
            return
        conteudo = entrada.get("1.0", "end-1c")
        if not conteudo.strip():
            return
        # Junta as palavras em uma lista so, para consultar o dicionario
        # de uma vez (bem mais rapido do que palavra por palavra).
        palavras = []
        for achado in re.finditer(r"[^\W\d_]{2,}", conteudo, re.UNICODE):
            palavras.append((achado.group(0), achado.start(), achado.end()))
        if not palavras:
            return
        unicas = {p[0].lower() for p in palavras}
        erradas = corretor.unknown(unicas)
        # Termos em inglês válidos não devem ser marcados.
        corretor_en = self._obter_corretor_en()
        if corretor_en:
            erradas = {
                w for w in erradas
                if corretor_en.unknown({w})
            }
        if not erradas:
            return
        for original, inicio, fim in palavras:
            if original.lower() in erradas:
                entrada.tag_add(
                    "ortografia",
                    "1.0 + %dc" % inicio,
                    "1.0 + %dc" % fim,
                )

    def _menu_ortografia(self, evento):
        if not self._corretor_ativo():
            return
        corretor = self._obter_corretor()
        if not corretor:
            return
        try:
            indice = self.entrada.index("@%d,%d" % (evento.x, evento.y))
            inicio = self.entrada.index("%s wordstart" % indice)
            fim = self.entrada.index("%s wordend" % indice)
        except Exception:
            return
        palavra = self.entrada.get(inicio, fim).strip()
        if not palavra or not re.fullmatch(r"[^\W\d_]{2,}", palavra, re.UNICODE):
            return
        if palavra.lower() not in corretor.unknown({palavra.lower()}):
            return
        corretor_en = self._obter_corretor_en()
        # termo válido em inglês não sugere nada
        if corretor_en and not corretor_en.unknown({palavra.lower()}):
            return
        cands_pt = list(corretor.candidates(palavra.lower()) or [])
        cands_en = []
        if (corretor_en and corretor_en is not False
                and corretor_en.unknown({palavra.lower()})):
            cands_en = list(corretor_en.candidates(palavra.lower()) or [])
        def melhor(cands):
            if not cands:
                return 0.0
            return max(
                difflib.SequenceMatcher(None, palavra.lower(), c).ratio()
                for c in cands)
        # a língua primária é o português: só usa inglês se for
        # claramente mais parecido (palavra se assemelhar mais ao inglês)
        if cands_pt and cands_en:
            if melhor(cands_en) > melhor(cands_pt) + 0.10:
                sugestoes = cands_en
            else:
                sugestoes = cands_pt
        else:
            sugestoes = cands_en or cands_pt
        if not sugestoes:
            return
        sugestoes = sorted(sugestoes)[:6]

        if self._menu_ortografia_atual is not None:
            try:
                self._menu_ortografia_atual.destroy()
            except Exception:
                pass
        if self._menu_ortografia_atual is not None:
            try:
                self._menu_ortografia_atual.destroy()
            except Exception:
                pass
            self._menu_ortografia_atual = None

        pop = tk.Toplevel(self.raiz)
        pop.overrideredirect(True)
        pop.configure(bg=COR_PAINEL)
        pop._itens = []
        caixa = tk.Frame(pop, bg=COR_BARRA, highlightthickness=1,
                         highlightbackground=COR_BORDA)
        caixa.pack(padx=2, pady=2)

        def item(rotulo, comando=None, negrito=False):
            etiqueta = tk.Label(
                caixa, text=rotulo, bg=COR_BARRA, fg=COR_TEXTO,
                font=(FONTE, 9, "bold" if negrito else "normal"), cursor="hand2",
                anchor="w", padx=16, pady=6,
            )
            etiqueta.pack(fill="x")
            etiqueta.bind("<Enter>", lambda _e: etiqueta.configure(
                bg=COR_BARRA_MAIS))
            etiqueta.bind("<Leave>", lambda _e: etiqueta.configure(
                bg=COR_BARRA, fg=COR_TEXTO))
            etiqueta.bind("<Button-1>", lambda _e: comando())
            pop._itens.append(etiqueta)
            return etiqueta

        for sugestao in sugestoes:
            item(
                "   " + sugestao,
                lambda s=sugestao: (
                    self._trocar_palavra(inicio, fim, s),
                    self._fechar_menu_ortografia(),
                ),
            )
        # separador
        tk.Frame(caixa, bg=COR_BORDA, height=1).pack(fill="x", padx=8, pady=2)
        item("   Ignorar", lambda: self._fechar_menu_ortografia())

        self._menu_ortografia_atual = pop
        pop.update_idletasks()
        largura = pop.winfo_reqwidth()
        altura = pop.winfo_reqheight()
        x = evento.x_root
        y = evento.y_root + 4
        # evita cair fora da tela
        if x + largura > self.raiz.winfo_screenwidth():
            x = self.raiz.winfo_screenwidth() - largura - 8
        if y + altura > self.raiz.winfo_screenheight():
            y = evento.y_root - altura - 4
        pop.geometry("+%d+%d" % (x, y))

        def fora(_e=None):
            if self._menu_ortografia_atual is not pop:
                return
            try:
                alvo = _e.widget if _e is not None else None
                atual = alvo
                while atual is not None:
                    if atual is pop:
                        return
                    atual = getattr(atual, "master", None)
            except Exception:
                pass
            self._fechar_menu_ortografia()

        pop._fora = fora
        pop.bind("<Escape>", lambda _e: self._fechar_menu_ortografia())
        self.raiz.bind_all("<Button-1>", fora, add="+")
        pop.after(6000, self._fechar_menu_ortografia)

    def _fechar_menu_ortografia(self):
        pop = getattr(self, "_menu_ortografia_atual", None)
        try:
            self.raiz.unbind_all("<Button-1>")
        except Exception:
            pass
        if pop is not None and isinstance(pop, tk.Toplevel):
            try:
                pop.destroy()
            except Exception:
                pass
        self._menu_ortografia_atual = None

    def _trocar_palavra(self, inicio, fim, nova):
        self.entrada.delete(inicio, fim)
        self.entrada.insert(inicio, nova)
        self._checar_ortografia()

    def _ao_enter(self, evento):
        if evento.state & 0x0001:  # Shift pressionado -> quebra de linha
            return None
        self._enviar()
        return "break"

    def _copiar_texto(self, texto):
        try:
            self.raiz.clipboard_clear()
            self.raiz.clipboard_append(texto)
            self._definir_status("Copiado para a área de transferência.", COR_OK)
        except Exception as erro:
            self._definir_status("Não consegui copiar: %s" % erro, COR_ERRO_TX)

    def _copiar_ultima(self):
        """Copia a última resposta (usado pelo atalho de teclado)."""
        for msg in reversed(self.mensagens):
            if msg["role"] == "model":
                self._copiar_texto(msg["text"])
                return
        self._definir_status("Ainda não tem resposta para copiar.")

    # -- desenho das mensagens ---------------------------------------------

    def _renderizar(self):
        self._redim_id = None
        for filho in self.interno.winfo_children():
            filho.destroy()
        self._pontos_digitando = []
        self._canvas_digitando = None
        self._bolha_anim = None

        if not self.mensagens:
            self._montar_boas_vindas()
        else:
            for indice, msg in enumerate(self.mensagens):
                if msg["role"] == "digitando":
                    self._criar_digitando()
                    continue
                if msg["role"] == "imagens":
                    self._criar_galeria(msg)
                    continue
                animando = self._anim is not None and self._anim["indice"] == indice
                if animando:
                    texto = msg["text"][: self._anim["mostrado"]]
                else:
                    texto = msg["text"]
                ref = self._criar_bolha(
                    texto, msg["role"], texto_completo=msg["text"]
                )
                if animando:
                    self._bolha_anim = ref
        try:
            if not self.mensagens:
                self.barra.state(["disabled"])
                self.canvas.yview_moveto(0.0)
            else:
                self.barra.state(["!disabled"])
        except Exception:
            pass
        self.raiz.after_idle(self._rolar_fim)

    def _montar_boas_vindas(self):
        bloco = tk.Frame(self.interno, bg=COR_FUNDO)
        bloco.pack(fill="x", pady=(46, 24), padx=24)

        tk.Label(
            bloco, text="Olá! 👋", bg=COR_FUNDO, fg=COR_TEXTO,
            font=(FONTE, 24, "bold"),
        ).pack()
        tk.Label(
            bloco, text="Faça uma pergunta e eu pesquiso na web para você.",
            bg=COR_FUNDO, fg=COR_TEXTO_2, font=(FONTE, 11),
        ).pack(pady=(8, 0))

        if not self.cfg.get("api_key", "").strip():
            aviso = tk.Frame(bloco, bg=COR_ERRO_BG)
            aviso.pack(pady=(20, 0))
            tk.Label(
                aviso,
                text="Falta colar a sua chave de API do Google para começar.",
                bg=COR_ERRO_BG, fg=COR_ERRO_TX, font=(FONTE, 10),
                padx=16, pady=10,
            ).pack(side="left")
            Botao(aviso, "Configurar agora", self._abrir_config, destaque=True).pack(
                side="left", padx=8, pady=6
            )

        tk.Label(
            bloco, text="Sugestões", bg=COR_FUNDO, fg=COR_TEXTO_3,
            font=(FONTE, 9, "bold"),
        ).pack(pady=(30, 10))

        for rotulo, pergunta in self._sugestoes_dinamicas():
            chip = Chip(self.interno, rotulo, pergunta, self._sugestao_clicada)
            chip.pack(pady=4)

    def _sugestoes_dinamicas(self):
        """Sugestoes para a tela inicial, baseadas na memoria e nas perguntas
        que ja foram feitas."""
        resultado = []
        visto = set()

        def adicionar(rotulo, pergunta):
            chave = (rotulo or "").strip().lower()
            if not chave or chave in visto:
                return
            visto.add(chave)
            resultado.append((rotulo.strip(), (pergunta or rotulo).strip()))

        # Conversas ja aconteceram -> continuar assuntos.
        try:
            for c in reversed(carregar_conversas()):
                titulo = (c.get("titulo") or "").strip()
                if titulo:
                    adicionar("Continuar: " + titulo[:40], titulo)
                if len(resultado) >= 5:
                    break
        except Exception:
            pass

        # Memoria -> perguntar sobre o que a IA ja sabe.
        try:
            for fato in carregar_memoria():
                adicionar("Sobre: " + fato[:32],
                         "Quero falar sobre %s. Me explique melhor." % fato)
                if len(resultado) >= 5:
                    break
        except Exception:
            pass

        # Completa com sugestoes de base quando ainda ha pouco historico.
        if len(resultado) < 5:
            for rotulo, pergunta in SUGESTOES:
                if len(resultado) >= 5:
                    break
                adicionar(rotulo, pergunta)

        if not resultado:
            for rotulo, pergunta in SUGESTOES:
                adicionar(rotulo, pergunta)

        return resultado[:5]

    def _sugestao_clicada(self, pergunta):
        self.entrada.delete("1.0", "end")
        self.entrada.insert("1.0", pergunta)
        self._ajustar_altura()
        self._enviar()

    def _criar_bolha(self, texto, autor, texto_completo=None):
        usuario = autor == "user"
        if autor == "erro":
            cor_fundo, cor_txt = COR_ERRO_BG, COR_ERRO_TX
        elif usuario:
            cor_fundo, cor_txt = COR_USUARIO, COR_USUARIO_TX
        else:
            cor_fundo, cor_txt = COR_IA, COR_IA_TX
        if texto_completo is None:
            texto_completo = texto

        linha = tk.Frame(self.interno, bg=COR_FUNDO)
        linha.pack(fill="x", padx=16, pady=6)

        coluna = tk.Frame(linha, bg=COR_FUNDO)
        largura = self._largura_bolha()
        tela = tk.Canvas(coluna, bg=COR_FUNDO, highlightthickness=0, bd=0)
        item = tela.create_text(
            0, 0, text=texto, font=(FONTE, 11), fill=cor_txt,
            width=largura, anchor="nw", justify="left",
        )
        x0, y0, x1, y1 = tela.bbox(item) or (0, 0, 1, 1)
        larg, alt = x1 - x0, y1 - y0
        px, py = 16, BALHA_RESPIRO
        tela.move(item, px - x0, py - y0)
        tela.configure(width=larg + 2 * px, height=alt + 2 * py)
        fundo = arredondado(
            tela, 0, 0, larg + 2 * px, alt + 2 * py, 16,
            fill=cor_fundo, outline="",
        )
        tela.tag_lower(fundo)
        tela.pack(anchor="e" if usuario else "w")

        if not usuario and autor != "erro":
            # Iconezinho de copiar logo abaixo da resposta, no canto de fora
            # do balao (do lado do balão), bem discreto. Passando o mouse em
            # cima dele, depois de um tempinho, aparece a explicação.
            canto = tk.Frame(coluna, bg=COR_FUNDO)
            canto.pack(anchor="w", pady=(2, 0))
            icone = _icone_copiar(
                canto, lambda: self._copiar_texto(texto_completo)
            )
            icone.pack(side="left", padx=(2, 0))
            Dica(icone, "Copiar resposta")

        if usuario:
            avatar_usuario(linha).pack(
                side="right", padx=(10, 0), anchor="n"
            )
            coluna.pack(side="right", anchor="n")
        else:
            avatar_ia(linha).pack(
                side="left", padx=(0, 10), anchor="n"
            )
            coluna.pack(side="left", anchor="n")

        return {
            "tela": tela, "item": item, "fundo": fundo,
            "largura": largura, "cor": cor_fundo,
        }

    def _atualizar_bolha(self, ref, texto):
        """Redesenha uma bolha já existente (usado na animação de escrita)."""
        tela, item = ref["tela"], ref["item"]
        px, py = 16, 12
        tela.itemconfigure(item, text=texto, width=ref["largura"])
        tela.coords(item, 0, 0)
        x0, y0, x1, y1 = tela.bbox(item) or (0, 0, 1, 1)
        larg, alt = x1 - x0, y1 - y0
        tela.move(item, px - x0, py - y0)
        largura_total, altura_total = larg + 2 * px, alt + 2 * py
        tela.configure(width=largura_total, height=altura_total)
        tela.coords(
            ref["fundo"],
            *_pontos_arredondados(0, 0, largura_total, altura_total, 16)
        )

    def _criar_digitando(self):
        linha = tk.Frame(self.interno, bg=COR_FUNDO)
        linha.pack(fill="x", padx=16, pady=6)
        avatar_ia(linha).pack(side="left", padx=(0, 10), anchor="n")

        tela = tk.Canvas(linha, width=76, height=44, bg=COR_FUNDO, highlightthickness=0, bd=0)
        tela.pack(side="left", anchor="n")
        arredondado(tela, 0, 0, 76, 44, 16, fill=COR_IA, outline="")
        self._pontos_digitando = []
        for x in (26, 39, 52):
            foto = _foto_ponto(TAMANHO_PONTO, COR_TEXTO_3, False)
            if foto is None:
                # sem Pillow: volta para o oval (um pouco mais grosso)
                self._pontos_digitando.append(
                    tela.create_oval(
                        x - 3, 19, x + 3, 25, fill=COR_TEXTO_3, outline=""
                    )
                )
            else:
                self._pontos_digitando.append(
                    tela.create_image(x, 22, image=foto, anchor="center")
                )
        self._canvas_digitando = tela

    # -- galeria de imagens -------------------------------------------------

    def _criar_galeria(self, msg):
        """Desenha a grade de miniaturas das imagens pedidas na conversa."""
        linha = tk.Frame(self.interno, bg=COR_FUNDO)
        linha.pack(fill="x", padx=16, pady=6)
        avatar_ia(linha).pack(side="left", padx=(0, 10), anchor="n")

        coluna = tk.Frame(linha, bg=COR_FUNDO)
        coluna.pack(side="left", anchor="n")

        termo = (msg.get("termo") or "").strip()
        titulo = "Imagens de \u201c%s\u201d" % termo if termo else "Imagens"
        tk.Label(
            coluna, text=titulo, bg=COR_FUNDO, fg=COR_TEXTO_2, font=(FONTE, 10),
        ).pack(anchor="w", pady=(2, 8))

        largura_tela = self.canvas.winfo_width()
        if largura_tela <= 60:
            largura_tela = self._largura_bolha() + 90
        disponivel = max(250, largura_tela - 120)
        colunas = max(2, min(4, disponivel // 180))
        margem = 6
        lado = max(90, (disponivel - (colunas - 1) * margem) // colunas)
        altura = int(lado * 0.72)

        grade = tk.Frame(coluna, bg=COR_FUNDO)
        grade.pack(anchor="w")

        # Área onde a imagem clicada é ampliada aqui mesmo, no chat.
        ampliado = tk.Frame(coluna, bg=COR_FUNDO)

        posicao = 0
        for indice, item in enumerate(msg.get("itens") or []):
            foto = self._miniatura(item, lado, altura)
            if foto is None:
                continue
            celula = tk.Label(
                grade, image=foto, bd=0, bg=COR_BORDA, cursor="hand2",
            )
            celula.grid(
                row=posicao // colunas, column=posicao % colunas,
                padx=margem // 2, pady=margem // 2,
            )
            celula.bind(
                "<Button-1>",
                lambda _evento, i=indice, area=ampliado: self._ampliar_no_chat(
                    msg, i, area
                ),
            )
            posicao += 1

        ampliado.pack(anchor="w", pady=(8, 0))

    def _miniatura(self, item, largura, altura):
        """Prepara a miniatura de uma imagem para mostrar na tela."""
        if not TEM_PIL:
            return None
        base = item.get("_pil")
        if base is None:
            dados = item.get("thumb")
            if not dados:
                return None
            try:
                base = Image.open(io.BytesIO(dados))
                base.load()
            except Exception:
                return None
            item["_pil"] = base
        try:
            foto = ImageTk.PhotoImage(
                self._cobrir(base, largura, altura), master=self.raiz
            )
        except Exception:
            return None
        item["_foto"] = foto  # mantém a referência viva para o Tk mostrar
        return foto

    @staticmethod
    def _cobrir(imagem, largura, altura):
        """Recorta a imagem para preencher exatamente largura x altura."""
        larg_im, alt_im = imagem.size
        if larg_im <= 0 or alt_im <= 0:
            return imagem
        escala = max(largura / larg_im, altura / alt_im)
        nova = (
            max(1, int(larg_im * escala + 0.5)),
            max(1, int(alt_im * escala + 0.5)),
        )
        imagem = imagem.convert("RGB").resize(nova, Image.LANCZOS)
        esquerda = (nova[0] - largura) // 2
        topo = (nova[1] - altura) // 2
        return imagem.crop((esquerda, topo, esquerda + largura, topo + altura))

    def _ampliar_no_chat(self, msg, indice, area):
        """Amplia a imagem clicada na própria conversa (sem abrir janela)."""
        if not TEM_PIL or not self._janela_viva(area):
            return
        itens = msg.get("itens") or []
        if not 0 <= indice < len(itens):
            return
        area._msg = msg
        area._indice = indice
        self._mostrar_ampliada(area)

    def _navegar_imagem(self, area, passo):
        """Mostra a imagem anterior ou a próxima, aqui mesmo na conversa."""
        msg = getattr(area, "_msg", None)
        itens = (msg or {}).get("itens") or []
        if len(itens) < 2 or not self._janela_viva(area):
            return
        area._indice = (getattr(area, "_indice", 0) + passo) % len(itens)
        self._mostrar_ampliada(area)

    def _mostrar_ampliada(self, area):
        """Desenha, na área da conversa, a imagem que está selecionada."""
        if not TEM_PIL or not self._janela_viva(area):
            return
        msg = getattr(area, "_msg", None)
        itens = (msg or {}).get("itens") or []
        indice = getattr(area, "_indice", 0)
        if not 0 <= indice < len(itens):
            return
        item = itens[indice]
        area._item_atual = item

        self._remover_espaco(area)
        for filho in area.winfo_children():
            filho.destroy()

        if item.get("_grande") is None:
            tk.Label(
                area, text="Carregando a imagem em tamanho maior...",
                bg=COR_FUNDO, fg=COR_TEXTO_2, font=(FONTE, 10),
            ).pack(anchor="w")
            if not item.get("_baixando"):
                item["_baixando"] = True
                self._baixar_grande(item, area)
            return

        self._desenhar_ampliado(area, item, indice, len(itens))

    def _baixar_grande(self, item, area):
        def tarefa():
            dados = _baixar_bytes(
                item.get("imagem") or item.get("thumb_url"),
                tempo=12.0, limite=12_000_000,
            )
            imagem = _imagem_de_bytes(dados)
            if imagem is None:
                self.fila.put(("imagem_chat_erro", area, item))
                return
            self.fila.put(("imagem_chat_ok", area, item, imagem))

        threading.Thread(target=tarefa, daemon=True).start()

    @staticmethod
    def _janela_viva(area):
        try:
            return bool(area.winfo_exists())
        except Exception:
            return False

    @staticmethod
    def _nome_arquivo(item):
        url = (item.get("imagem") or "").split("?")[0]
        nome = url.rsplit("/", 1)[-1] or "imagem"
        if "." not in nome:
            nome += ".jpg"
        return nome

    def _limpar_area(self, area):
        if not self._janela_viva(area):
            return False
        for filho in area.winfo_children():
            filho.destroy()
        return True

    def _remover_espaco(self, area):
        """Tira o espaço extra que deixa a imagem no meio da tela."""
        espaco = getattr(area, "_espaco", None)
        if espaco is not None:
            try:
                espaco.destroy()
            except Exception:
                pass
            area._espaco = None

    def _ajustar_espaco(self, area):
        """Cria um espaço no fim da conversa para a imagem caber no meio.

        Sem esse espaço, quando a imagem é a última coisa da conversa, ela
        ficaria colada embaixo, sem como descer mais.
        """
        self._remover_espaco(area)
        try:
            self.interno.update_idletasks()
            visivel = self.canvas.winfo_height()
            sobra = (visivel - area.winfo_height()) / 2.0
            if sobra < 4:
                return
            espaco = tk.Frame(self.interno, bg=COR_FUNDO, height=int(sobra))
            espaco.pack(fill="x")
            area._espaco = espaco
            self.interno.update_idletasks()
        except Exception:
            pass

    def _posicao_no_interno(self, widget):
        """Descobre a posição vertical do widget dentro da conversa."""
        y = 0
        atual = widget
        while atual is not None and atual is not self.interno:
            try:
                y += atual.winfo_y()
            except Exception:
                return y
            atual = getattr(atual, "master", None)
        return y

    def _centralizar(self, widget):
        """Rola a conversa para deixar o widget no meio da parte visível."""
        try:
            self.interno.update_idletasks()
            visivel = self.canvas.winfo_height()
            total = max(1, self.interno.winfo_height())
            topo = self._posicao_no_interno(widget)
            altura = widget.winfo_height()
            alvo = topo + altura / 2.0 - visivel / 2.0
            self.canvas.yview_moveto(max(0.0, min(1.0, alvo / total)))
        except Exception:
            pass

    def _desenhar_ampliado(self, area, item, indice=0, total=1):
        grande = item.get("_grande")
        if not self._janela_viva(area) or grande is None:
            return
        for filho in area.winfo_children():
            filho.destroy()

        visivel = self.canvas.winfo_height()
        if visivel <= 60:
            visivel = 600
        largura_max = self.canvas.winfo_width()
        if largura_max <= 60:
            largura_tela = self._largura_bolha() + 90
            largura_max = largura_tela
        largura_max = max(260, largura_max - 130)
        # Deixa a imagem caber na parte visível, sem precisar rolar.
        altura_max = max(160, min(int(largura_max * 0.9), int(visivel * 0.70)))

        copia = grande.convert("RGB")
        copia.thumbnail((largura_max, altura_max), Image.LANCZOS)
        if total > 1:
            copia = _com_setas(copia)

        foto = ImageTk.PhotoImage(copia, master=area)
        item["_foto_grande"] = foto  # referência viva
        tela = tk.Label(area, image=foto, bg=COR_FUNDO, bd=0, cursor="hand2")
        tela.pack(anchor="w")
        if total > 1:
            tela.bind(
                "<Button-1>",
                lambda evento: self._clique_na_ampliada(area, evento),
            )

        rodape = tk.Frame(area, bg=COR_FUNDO)
        rodape.pack(anchor="w", pady=(6, 0))
        Botao(
            rodape, "Salvar como...",
            lambda: self._salvar_imagem(item), destaque=True,
        ).pack(side="left")
        if total > 1:
            tk.Label(
                rodape, text="%d de %d" % (indice + 1, total),
                bg=COR_FUNDO, fg=COR_TEXTO_3, font=(FONTE, 9),
            ).pack(side="left", padx=10)
        Botao(rodape, "Fechar", lambda: self._recolher(area)).pack(
            side="left", padx=8
        )
        self._ajustar_espaco(area)
        self._centralizar(area)

    def _clique_na_ampliada(self, area, evento):
        """Clique na lateral esquerda volta; na direita mostra a próxima."""
        try:
            tela = evento.widget
            largura = max(tela.winfo_width(), tela.winfo_reqwidth())
        except Exception:
            return
        if largura <= 1:
            return
        if evento.x < largura * 0.34:
            self._navegar_imagem(area, -1)
        elif evento.x > largura * 0.66:
            self._navegar_imagem(area, 1)
    def _salvar_imagem(self, item):
        grande = item.get("_grande")
        if grande is None:
            return
        caminho = filedialog.asksaveasfilename(
            parent=self.raiz,
            title="Salvar imagem como...",
            initialfile=self._nome_arquivo(item),
            filetypes=[
                ("Imagem", "*.jpg *.jpeg *.png"),
                ("Todos os arquivos", "*.*"),
            ],
        )
        if not caminho:
            return
        try:
            grande.convert("RGB").save(caminho)
            self._definir_status("Imagem salva em: %s" % caminho, COR_OK)
        except Exception as erro:
            messagebox.showerror(
                "Erro", "Não consegui salvar a imagem: %s" % erro
            )

    def _recolher(self, area):
        if not self._janela_viva(area):
            return
        self._remover_espaco(area)
        for filho in area.winfo_children():
            filho.destroy()

    def _mostrar_erro_no_chat(self, area, item):
        if not self._janela_viva(area):
            return
        for filho in area.winfo_children():
            filho.destroy()
        msg = getattr(area, "_msg", None)
        itens = (msg or {}).get("itens") or []
        aviso = "Esta imagem não abriu agora."
        if len(itens) > 1:
            aviso += " Veja outra:"
        tk.Label(
            area, text=aviso, bg=COR_FUNDO, fg=COR_ERRO_TX, font=(FONTE, 10),
            wraplength=380, justify="left",
        ).pack(anchor="w", pady=(0, 6))

        rodape = tk.Frame(area, bg=COR_FUNDO)
        rodape.pack(anchor="w")
        if len(itens) > 1:
            Botao(
                rodape, "\u25c0 Anterior",
                lambda: self._navegar_imagem(area, -1),
            ).pack(side="left")
            Botao(
                rodape, "Próxima \u25b6",
                lambda: self._navegar_imagem(area, 1),
            ).pack(side="left", padx=8)
        Botao(rodape, "Fechar", lambda: self._recolher(area)).pack(
            side="left", padx=8
        )

    def _iniciar_digitando(self):
        self.mensagens.append({"role": "digitando", "text": ""})
        self._renderizar()
        self.animacao_passo = 0
        self._passo_animacao()

    def _parar_digitando(self):
        self.mensagens = [m for m in self.mensagens if m["role"] != "digitando"]
        if self.animacao_id is not None:
            try:
                self.raiz.after_cancel(self.animacao_id)
            except Exception:
                pass
            self.animacao_id = None

    def _passo_animacao(self):
        self.animacao_passo = (self.animacao_passo + 1) % 3
        forte = _foto_ponto(TAMANHO_PONTO, COR_TEXTO, True)
        fraco = _foto_ponto(TAMANHO_PONTO, COR_TEXTO_3, False)
        for indice, ponto in enumerate(self._pontos_digitando or []):
            if self._canvas_digitando is not None:
                if forte is not None and fraco is not None:
                    # desenho liso: so troca a imagem do pontinho
                    self._canvas_digitando.itemconfigure(
                        ponto,
                        image=forte if indice == self.animacao_passo else fraco,
                    )
                else:
                    self._canvas_digitando.itemconfigure(
                        ponto,
                        fill=COR_TEXTO if indice == self.animacao_passo
                        else COR_TEXTO_3,
                    )
        self.animacao_id = self.raiz.after(320, self._passo_animacao)

    def _iniciar_digitacao(self, indice):
        """Comeca a escrever a resposta no balao, como nos chats modernos."""
        total = len(self.mensagens[indice]["text"])
        self._anim = {"indice": indice, "total": total, "mostrado": 0, "passos": 0}
        self._bolha_anim = None
        self._renderizar()
        self._definir_status("Escrevendo a resposta...")
        self._passo_digitacao()

    def _rolar_fim_suave(self):
        try:
            if self.interno.winfo_height() <= self.canvas.winfo_height():
                self.canvas.yview_moveto(0.0)
            else:
                self.canvas.yview_moveto(1.0)
        except Exception:
            pass

    def _passo_digitacao(self):
        anim = self._anim
        if anim is None or self._bolha_anim is None:
            self._anim_id = None
            return
        # Revela o texto em passos, mirando uns 2,5 segundos no total.
        passo = max(1, (anim["total"] + 149) // 150)
        anim["mostrado"] = min(anim["total"], anim["mostrado"] + passo)
        completo = anim["mostrado"] >= anim["total"]
        texto = self.mensagens[anim["indice"]]["text"][: anim["mostrado"]]
        # Cursor piscando no fim, enquanto a resposta esta sendo escrita.
        if not completo and (anim["passos"] // 5) % 2 == 0:
            texto += "▌"
        try:
            self._atualizar_bolha(self._bolha_anim, texto)
        except Exception:
            pass
        anim["passos"] += 1
        if completo:
            self._rolar_fim()
            self._anim = None
            self._bolha_anim = None
            self._anim_id = None
            self._definir_ocupado(False)
            # Se a resposta veio do plano B, a linha de baixo avisa qual foi.
            origem = getattr(self, "_origem_resposta", "")
            if origem and origem != "Gemini":
                self._definir_status(
                    "Resposta gerada pelo plano B: %s." % origem,
                    COR_TEXTO_2,
                )
            else:
                self._definir_status("")
            return
        if anim["passos"] % 3 == 0:
            self._rolar_fim_suave()
        self._anim_id = self.raiz.after(10, self._passo_digitacao)

    def _cancelar_digitacao(self):
        if self._anim_id is not None:
            try:
                self.raiz.after_cancel(self._anim_id)
            except Exception:
                pass
        self._anim_id = None
        self._anim = None
        self._bolha_anim = None

    # -- acoes --------------------------------------------------------------

    def _atualizar_status_chave(self):
        tem_chave = bool(self.cfg.get("api_key", "").strip())
        if not tem_chave:
            self._definir_status(
                "Falta configurar a chave de API. Clique em Configurações.",
                COR_ERRO_TX,
            )

    def _definir_ocupado(self, ocupado):
        self.ocupado = ocupado
        estado = "disabled" if ocupado else "normal"
        self.entrada.configure(state=estado)
        self.botao_enviar.configure(cursor="arrow" if ocupado else "hand2")
        if not ocupado:
            self.entrada.focus_set()

    def _enviar(self):
        if self.ocupado:
            return
        pergunta = self.entrada.get("1.0", "end-1c").strip()
        if not pergunta:
            return

        ver_imagens = TEM_PIL and _quer_imagens(pergunta)

        chave = self.cfg.get("api_key", "").strip()
        if not chave and not ver_imagens:
            self._definir_status("Cole a sua chave de API antes de pesquisar.", COR_ERRO_TX)
            self._abrir_config()
            return

        self.entrada.delete("1.0", "end")
        self._ajustar_altura()
        self.entrada.tag_remove("ortografia", "1.0", "end")
        self.mensagens.append({"role": "user", "text": pergunta})

        self._definir_ocupado(True)

        # Se a pessoa pediu imagens, busca algumas e mostra na conversa.
        if ver_imagens:
            termo = _termo_imagens(pergunta)
            if not termo:
                self.mensagens.append({
                    "role": "erro",
                    "text": (
                        "Escreva o que você quer ver, por exemplo: "
                        "imagens de lobos."
                    ),
                })
                self._renderizar()
                self._definir_ocupado(False)
                return
            self._iniciar_digitando()
            self._definir_status("Buscando imagens...")

            def tarefa_imagens():
                try:
                    itens = _buscar_imagens(termo)
                    self.fila.put(("imagens", pergunta, termo, itens))
                    # Já baixa as imagens grandes em segundo plano.
                    _precarregar_imagens(itens)
                except Exception as erro:
                    self.fila.put(("erro", pergunta, self._traduzir_erro(erro)))

            threading.Thread(target=tarefa_imagens, daemon=True).start()
            return

        amigo = (not ver_imagens) and (not _quer_pesquisa(pergunta))

        self._iniciar_digitando()
        if amigo:
            self._definir_status("Conversando com você...")
        else:
            self._definir_status("Pesquisando na web...")

        usar_contexto = bool(self.cfg.get("usar_contexto", True))
        modelo = self.cfg.get("modelo", MODELO_PADRAO)
        historico = list(self.historico)

        def avisar_progresso(mensagem):
            self.fila.put(("etapa", mensagem))

        def tarefa():
            try:
                if amigo:
                    texto, fontes, buscas, origem = conversar(
                        chave, modelo, historico, pergunta, usar_contexto,
                        progresso=avisar_progresso, cfg=self.cfg,
                        id_atual=self._id_conversa,
                    )
                else:
                    texto, fontes, buscas, origem = perguntar(
                        chave, modelo, historico, pergunta, usar_contexto,
                        progresso=avisar_progresso, cfg=self.cfg,
                        id_atual=self._id_conversa,
                    )
                self.fila.put(("ok", pergunta, texto, fontes, buscas, origem))
            except Exception as erro:
                self.fila.put(("erro", pergunta, self._traduzir_erro(erro)))

        threading.Thread(target=tarefa, daemon=True).start()

    def _traduzir_erro(self, erro):
        mensagem = str(erro)
        baixo = mensagem.lower()
        if (
            "api key" in baixo or "api_key" in baixo
            or "unauthenticated" in baixo or "no auth credentials" in baixo
            or "invalid authentication" in baixo or "401" in baixo
        ):
            return (
                "Uma das chaves de API parece inválida. Abra Configurações e "
                "confira se copiou a chave completa (a do Google começa com "
                "AIza ou AQ., a do Groq com gsk_ e a do OpenRouter com "
                "sk-or-)."
            )
        if "quota" in baixo or "rate limit" in baixo or "resource_exhausted" in baixo:
            return (
                "Você atingiu o limite gratuito por agora. "
                "Isso se renova sozinho — espere alguns minutos (ou volte "
                "amanhã) e tente de novo."
            )
        if "plano b" in baixo:
            return (
                "O Gemini não respondeu e o plano B também falhou.\n\n"
                "Detalhe: %s\n\n"
                "Tente de novo em alguns minutos." % mensagem
            )
        if "internet" in baixo or "connect" in baixo or "timeout" in baixo or "ssl" in baixo:
            return "Parece que a internet caiu. Confira a conexão e tente de novo."
        if "ddgs" in baixo or "duckduckgo" in baixo:
            return (
                "Não consegui pesquisar na web agora. Verifique a internet e "
                "tente de novo em alguns segundos."
            )
        return "Aconteceu um erro: %s" % mensagem

    # -- janela de configuracoes (com abas) ---------------------------------

    ABAS_CONFIG = (("memoria", "Memória"), ("chave", "Chave"), ("ajuda", "Ajuda"))

    def _abrir_config(self, aba="memoria"):
        if self._janela_config is not None and self._janela_config.winfo_exists():
            self._janela_config.lift()
            self._janela_config.focus_force()
            if aba != getattr(self, "_aba_config", "memoria"):
                self._mostrar_aba_config(aba)
            return

        jan = tk.Toplevel(self.raiz)
        self._janela_config = jan
        self._aba_config = "memoria"
        jan.title("Configurações")
        jan.configure(bg=COR_FUNDO)
        jan.geometry("700x780")
        jan.minsize(580, 620)
        jan.transient(self.raiz)
        jan.after(150, lambda: ativar_barra_escura(jan))

        # ---- barra de abas no topo ----
        barra_abas = tk.Frame(jan, bg=COR_FUNDO)
        barra_abas.pack(fill="x", padx=18, pady=(14, 0))
        conteudo = tk.Frame(jan, bg=COR_FUNDO)
        conteudo.pack(fill="both", expand=True)
        botoes_abas = {}
        quadros = {}
        for nome_aba, titulo_aba in self.ABAS_CONFIG:
            quadros[nome_aba] = tk.Frame(conteudo, bg=COR_FUNDO)
            rotulo = tk.Label(
                barra_abas, text=titulo_aba, bg=COR_FUNDO, fg=COR_TEXTO_3,
                font=(FONTE, 10), cursor="hand2", padx=18, pady=9,
            )
            rotulo.pack(side="left", padx=(0, 4))
            rotulo.bind(
                "<Button-1>",
                lambda _e, alvo=nome_aba: self._mostrar_aba_config(alvo),
            )
            rotulo.bind(
                "<Enter>",
                lambda _e, r=rotulo, t=titulo_aba: r.configure(
                    bg=COR_BARRA, fg=COR_TEXTO,
                ),
            )
            rotulo.bind("<Leave>", lambda _e, r=rotulo, t=titulo_aba: r.configure(
                bg=COR_BARRA if self._aba_config == t else COR_FUNDO,
                fg=COR_TEXTO if self._aba_config == t else COR_TEXTO_3,
            ))
            botoes_abas[titulo_aba] = rotulo

        def mostrar_aba(nome_aba):
            self._aba_config = nome_aba
            for chave_aba, _titulo in self.ABAS_CONFIG:
                if chave_aba == nome_aba:
                    quadros[chave_aba].pack(fill="both", expand=True)
                else:
                    quadros[chave_aba].pack_forget()
            for titulo_aba, rotulo in botoes_abas.items():
                ativo = titulo_aba == self._aba_config
                rotulo.configure(
                    bg=COR_BARRA if ativo else COR_FUNDO,
                    fg=COR_TEXTO if ativo else COR_TEXTO_3,
                )

        self._mostrar_aba_config = mostrar_aba
        aba_chave = quadros["chave"]

        # ---- rodapé com o botão de fechar (vale para todas as abas) ----
        rodape = tk.Frame(jan, bg=COR_FUNDO)
        rodape.pack(fill="x", padx=18, pady=(0, 14))
        Botao(rodape, "Fechar", jan.destroy).pack(side="right")

        # A configuração ficou grande, então a área do meio tem rolagem.
        tela = tk.Canvas(aba_chave, bg=COR_FUNDO, highlightthickness=0, bd=0)
        _preparar_scrollbar_escuro(aba_chave)
        barra = ttk.Scrollbar(
            aba_chave, orient="vertical", command=tela.yview, style=ESTILO_BARRA,
        )
        # A barra de rolagem e empacotada PRIMEIRO de propósito: o Tk encolhe
        # quem vem por ultimo quando a janela aperta, e assim a barra some.
        barra.pack(side="right", fill="y")
        tela.pack(side="left", fill="both", expand=True)
        tela.configure(yscrollcommand=barra.set)
        corpo = tk.Frame(tela, bg=COR_FUNDO)
        corpo.bind("<Configure>", lambda _e: tela.configure(
            scrollregion=tela.bbox("all")
        ))
        corpo_id = tela.create_window((0, 0), window=corpo, anchor="nw")

        def _acertar_largura(_evento=None):
            tela.itemconfigure(corpo_id, width=tela.winfo_width())

        tela.bind("<Configure>", _acertar_largura)

        def _rolar(evento):
            tela.yview_scroll(int(-evento.delta / 120), "units")
            return "break"

        # A roda do mouse so funciona em cima do widget onde ela foi ligada;
        # os botoes e caixas de texto "engolem" o evento. Por isso a rolagem
        # e ligada em TODOS os pedacos da aba, um por um. Isso so pode ser
        # feito no FINAL, quando todo o conteudo ja existe.
        def _ligar_todos(widget):
            widget.bind("<MouseWheel>", _rolar)
            for filho in widget.winfo_children():
                _ligar_todos(filho)

        def _rolar_ajuda(evento):
            tela_ajuda.yview_scroll(int(-evento.delta / 120), "units")
            return "break"

        tk.Label(
            corpo, text="Chave da API do Google (Gemini)", bg=COR_FUNDO,
            fg=COR_TEXTO, font=(FONTE, 14, "bold"),
        ).pack(anchor="w", pady=(22, 0))

        tk.Label(
            corpo,
            text=(
                "Cole aqui a chave gratuita do Google. É ela que permite "
                "pesquisar e escrever as respostas."
            ),
            bg=COR_FUNDO, fg=COR_TEXTO_3, font=(FONTE, 9), justify="left",
            wraplength=560,
        ).pack(anchor="w", pady=(4, 0))

        tk.Label(
            corpo, text="Chave da API do Google (Gemini)", bg=COR_FUNDO,
            fg=COR_TEXTO_2, font=(FONTE, 10, "bold"),
        ).pack(anchor="w", pady=(20, 6))

        moldura = tk.Frame(
            corpo, bg=COR_BARRA, highlightthickness=1,
            highlightbackground=COR_BORDA,
        )
        moldura.pack(fill="x")
        var_chave = tk.StringVar(value=self.cfg.get("api_key", ""))
        entrada = tk.Entry(
            moldura, textvariable=var_chave, show="•", font=(FONTE, 11),
            bg=COR_BARRA, fg=COR_TEXTO, insertbackground=COR_ACCENT,
            relief="flat", borderwidth=0,
        )
        entrada.pack(side="left", fill="x", expand=True, padx=12, pady=10)

        var_mostrar = tk.BooleanVar(value=False)

        def alternar():
            entrada.configure(show="" if var_mostrar.get() else "•")

        tk.Checkbutton(
            corpo, text="mostrar a chave", variable=var_mostrar, command=alternar,
            bg=COR_FUNDO, fg=COR_TEXTO_2, selectcolor=COR_BARRA,
            activebackground=COR_FUNDO, activeforeground=COR_TEXTO,
            font=(FONTE, 9), highlightthickness=0, bd=0,
        ).pack(anchor="w", pady=(6, 0))

        botoes = tk.Frame(corpo, bg=COR_FUNDO)
        botoes.pack(fill="x", pady=(14, 0))

        def salvar():
            self.cfg["api_key"] = var_chave.get().strip()
            self.cfg["usar_contexto"] = bool(self.var_contexto.get())
            self.cfg["corretor"] = bool(self.var_corretor.get())
            self.cfg["usar_plano_b"] = bool(self.var_plano_b.get())
            for campo, variavel in vars_reserva.items():
                self.cfg[campo] = variavel.get().strip()
            try:
                salvar_config(self.cfg)
                self._atualizar_status_chave()
                self._checar_ortografia()
                messagebox.showinfo(
                    "Salvo", "As chaves foram salvas no seu computador.", parent=jan
                )
            except Exception as erro:
                messagebox.showerror(
                    "Erro", "Não consegui salvar: %s" % erro, parent=jan
                )

        def testar():
            chave = var_chave.get().strip()
            if not chave:
                messagebox.showwarning(
                    "Falta a chave", "Cole a chave antes de testar.", parent=jan
                )
                return

            def terminou(sucesso, msg=""):
                if sucesso:
                    self.cfg["api_key"] = chave
                    self.cfg["usar_contexto"] = bool(self.var_contexto.get())
                    self.cfg["usar_plano_b"] = bool(self.var_plano_b.get())
                    for campo, variavel in vars_reserva.items():
                        self.cfg[campo] = variavel.get().strip()
                    try:
                        salvar_config(self.cfg)
                    except Exception:
                        pass
                    self._atualizar_status_chave()
                    messagebox.showinfo(
                        "Tudo certo",
                        "A chave está funcionando! Já pode pesquisar.",
                        parent=jan,
                    )
                else:
                    self._atualizar_status_chave()
                    messagebox.showerror("Problema com a chave", msg, parent=jan)

            self._testar_com_retorno(var_chave.get().strip(), terminou)

        Botao(botoes, "Salvar", salvar, destaque=True).pack(side="left")
        Botao(botoes, "Testar chave", testar).pack(side="left", padx=(8, 0))

        self.var_contexto = tk.BooleanVar(value=bool(self.cfg.get("usar_contexto", True)))
        tk.Checkbutton(
            corpo,
            text="Lembrar o assunto da conversa (permite perguntas de acompanhamento)",
            variable=self.var_contexto, bg=COR_FUNDO, fg=COR_TEXTO_2,
            selectcolor=COR_BARRA, activebackground=COR_FUNDO,
            activeforeground=COR_TEXTO, font=(FONTE, 9),
            highlightthickness=0, bd=0, wraplength=540, justify="left",
        ).pack(anchor="w", pady=(18, 0))

        self.var_corretor = tk.BooleanVar(value=bool(self.cfg.get("corretor", True)))
        tk.Checkbutton(
            corpo,
            text="Corretor ortográfico do português (sublinha palavras erradas)",
            variable=self.var_corretor, bg=COR_FUNDO, fg=COR_TEXTO_2,
            selectcolor=COR_BARRA, activebackground=COR_FUNDO,
            activeforeground=COR_TEXTO, font=(FONTE, 9),
            highlightthickness=0, bd=0, wraplength=540, justify="left",
        ).pack(anchor="w", pady=(10, 0))

        # ---- plano B: serviços de reserva (opcionais) ----
        tk.Label(
            corpo, text="Plano B (opcional)", bg=COR_FUNDO, fg=COR_TEXTO_2,
            font=(FONTE, 10, "bold"),
        ).pack(anchor="w", pady=(24, 6))

        tk.Label(
            corpo,
            text=(
                "Se o Gemini não responder (limite do dia, manutenção...), o "
                "programa tenta estes serviços de reserva e a resposta sai "
                "igual. Os dois são grátis e não pedem cartão de crédito.\n"
                "Se você não preencher nada aqui, o programa continua "
                "funcionando exatamente como antes."
            ),
            bg=COR_FUNDO, fg=COR_TEXTO_3, font=(FONTE, 9), justify="left",
            wraplength=560,
        ).pack(anchor="w")

        self.var_plano_b = tk.BooleanVar(
            value=bool(self.cfg.get("usar_plano_b", True))
        )
        tk.Checkbutton(
            corpo,
            text="Usar o plano B quando o Gemini não responder",
            variable=self.var_plano_b, bg=COR_FUNDO, fg=COR_TEXTO_2,
            selectcolor=COR_BARRA, activebackground=COR_FUNDO,
            activeforeground=COR_TEXTO, font=(FONTE, 9),
            highlightthickness=0, bd=0, wraplength=560, justify="left",
        ).pack(anchor="w", pady=(10, 0))

        vars_reserva = {}
        for servico in SERVICOS_RESERVA:
            tk.Label(
                corpo,
                text="%s — %s" % (servico["nome"], servico["resumo"]),
                bg=COR_FUNDO, fg=COR_TEXTO_2, font=(FONTE, 9, "bold"),
            ).pack(anchor="w", pady=(16, 5))

            moldura_servico = tk.Frame(
                corpo, bg=COR_BARRA, highlightthickness=1,
                highlightbackground=COR_BORDA,
            )
            moldura_servico.pack(fill="x")
            var_chave_servico = tk.StringVar(
                value=self.cfg.get(servico["campo_chave"], "")
            )
            vars_reserva[servico["campo_chave"]] = var_chave_servico
            tk.Entry(
                moldura_servico, textvariable=var_chave_servico, show="•",
                font=(FONTE, 11), bg=COR_BARRA, fg=COR_TEXTO,
                insertbackground=COR_ACCENT, relief="flat", borderwidth=0,
            ).pack(side="left", fill="x", expand=True, padx=12, pady=9)

            linha_servico = tk.Frame(corpo, bg=COR_FUNDO)
            linha_servico.pack(fill="x", pady=(6, 0))

            def testar_da_vez(
                campo=servico["campo_chave"], nome=servico["nome"]
            ):
                if not vars_reserva[campo].get().strip():
                    messagebox.showwarning(
                        "Falta a chave",
                        "Cole a chave do %s antes de testar." % nome,
                        parent=jan,
                    )
                    return
                if self.ocupado:
                    return

                cfg_teste = dict(self.cfg)
                cfg_teste["usar_plano_b"] = True
                for campo_cfg, variavel in vars_reserva.items():
                    cfg_teste[campo_cfg] = variavel.get().strip()

                def tarefa():
                    try:
                        texto = testar_servico(cfg_teste, campo)
                        self.fila.put(("teste_reserva_ok", nome, texto))
                    except Exception as erro:
                        self.fila.put(
                            ("teste_reserva_erro", nome,
                             self._traduzir_erro(erro))
                        )

                self._definir_ocupado(True)
                self._definir_status("Testando o %s..." % nome)
                threading.Thread(target=tarefa, daemon=True).start()

            def abrir_pagina(pagina=servico["pagina"], nome=servico["nome"]):
                webbrowser.open(pagina)
                self._definir_status("Página do %s aberta no navegador." % nome)

            Botao(linha_servico, "Testar", testar_da_vez).pack(side="left")
            Botao(
                linha_servico, "Como conseguir a chave", abrir_pagina,
            ).pack(side="left", padx=(8, 0))
            tk.Label(
                corpo,
                text=servico["passos"],
                bg=COR_FUNDO, fg=COR_TEXTO_3, font=(FONTE, 8),
                justify="left", wraplength=560,
            ).pack(anchor="w", pady=(6, 0))

        ajuda = tk.Frame(corpo, bg=COR_BARRA)
        ajuda.pack(fill="x", pady=(18, 0))
        tk.Label(
            ajuda,
            text=(
                "Não tem uma chave ainda? É grátis e leva 2 minutos:\n"
                "1) Clique no botão azul abaixo.\n"
                "2) Entre com a sua conta Google.\n"
                "3) Clique em 'Create API key' (criar chave).\n"
                "4) Copie o código (começa com AIza ou AQ.) e cole no campo "
                "acima.\n\n"
                "A chave do Google tem um plano gratuito generoso, e a busca "
                "na web que o programa usa também é gratuita. Não precisa de "
                "cartão de crédito."
            ),
            bg=COR_BARRA, fg=COR_TEXTO_2, font=(FONTE, 9), justify="left",
            wraplength=540,
        ).pack(anchor="w", padx=14, pady=(12, 8))
        Botao(
            ajuda, "Abrir página para criar a chave",
            lambda: webbrowser.open(URL_CHAVE), destaque=True,
        ).pack(anchor="w", padx=14, pady=(0, 14))

        # ================= aba MEMÓRIA =================
        # O que a IA aprendeu sobre o usuário. Não é preciso preencher nada:
        # a IA guarda sozinha, em segundo plano, sem avisar na conversa.
        self._preencher_aba_memoria(quadros["memoria"], jan)

        # ================= aba AJUDA =================
        self._preencher_aba_ajuda(quadros["ajuda"], _rolar_ajuda)

        # agora que o conteudo inteiro existe, liga a rolagem em tudo
        _ligar_todos(aba_chave)

        mostrar_aba("memoria")
        jan.bind("<Escape>", lambda _e: jan.destroy())
        entrada.focus_set()

    # -- conteúdo das abas de Configurações ---------------------------------

    def _preencher_aba_memoria(self, pai, janela):
        """Monta a aba 'Memória': o que a IA aprendeu sobre o usuário."""
        env = {"tempo": None}

        tk.Label(
            pai, text="O que a IA sabe sobre você", bg=COR_FUNDO,
            fg=COR_TEXTO, font=(FONTE, 16, "bold"),
        ).pack(anchor="w", padx=24, pady=(22, 0))
        tk.Label(
            pai,
            text=(
                "Você não precisa preencher nada: a IA guarda sozinha os "
                "gostos e hábitos que aparecem nas conversas, e usa isso para "
                "responder melhor. Ela nunca comenta que guardou. Se quiser "
                "apagar algum item (ou todos), é só usar o X."
            ),
            bg=COR_FUNDO, fg=COR_TEXTO_3, font=(FONTE, 9), justify="left",
            wraplength=600,
        ).pack(anchor="w", padx=24, pady=(6, 0))

        moldura = tk.Frame(pai, bg=COR_FUNDO)
        moldura.pack(fill="both", expand=True, padx=24, pady=16)
        _preparar_scrollbar_escuro(moldura)

        # a lista pode ficar longa, então rola igual às outras abas
        tela = tk.Canvas(moldura, bg=COR_FUNDO, highlightthickness=0, bd=0)
        barra = ttk.Scrollbar(
            moldura, orient="vertical", command=tela.yview, style=ESTILO_BARRA,
        )
        barra.pack(side="right", fill="y")
        tela.pack(side="left", fill="both", expand=True)
        tela.configure(yscrollcommand=barra.set)
        lista = tk.Frame(tela, bg=COR_FUNDO)
        lista_id = tela.create_window((0, 0), window=lista, anchor="nw")
        lista.bind(
            "<Configure>",
            lambda _e: tela.configure(scrollregion=tela.bbox("all")),
        )
        tela.bind(
            "<Configure>",
            lambda _e: (
                tela.itemconfigure(lista_id, width=tela.winfo_width()),
                tela.coords("empty", tela.winfo_width() // 2, tela.winfo_height() // 2),
            ),
        )
        def _ajustar_barra_memoria(_evento=None):
            try:
                lista.update_idletasks()
                if lista.winfo_reqheight() <= tela.winfo_height():
                    barra.state(["disabled"])
                    tela.yview_moveto(0.0)
                else:
                    barra.state(["!disabled"])
            except Exception:
                pass
        def _rolar_memoria(_e):
            try:
                if (not carregar_memoria() or
                        lista.winfo_reqheight() <= tela.winfo_height()):
                    tela.yview_moveto(0.0)
                    barra.state(['disabled'])
                    return 'break'
                barra.state(['!disabled'])
                tela.yview_scroll(int(-_e.delta / 120), 'units')
            except Exception:
                pass
            return 'break'

        def _centralizar_vazio_memoria(_e=None):
            _ajustar_barra_memoria()
            try:
                tela.coords('empty', tela.winfo_width() // 2,
                            tela.winfo_height() // 2)
            except Exception:
                pass
        lista.bind('<Configure>', _centralizar_vazio_memoria)
        moldura.bind(
            "<MouseWheel>",
            _rolar_memoria,
        )

        def desenhar():
            tela.delete("empty")
            for filho in lista.winfo_children():
                filho.destroy()
            fatos = carregar_memoria()
            env["mostrado"] = list(fatos)
            if not fatos:
                tela.delete("empty")
                x = max(1, tela.winfo_width()) // 2
                y = max(1, tela.winfo_height()) // 2
                tela.create_text(
                    x, y,
                    text=(
                        "Nada guardado ainda.\n\n"
                        "Conforme você conversa, a IA vai guardando o que "
                        "acha importante sobre você."
                    ),
                    fill=COR_TEXTO_3, font=(FONTE, 10), justify="center",
                    tags=("empty",), anchor="center",
                )
                barra.state(["disabled"])
                tela.yview_moveto(0.0)
                return
            for fato in fatos:
                linha = tk.Frame(lista, bg=COR_BARRA)
                linha.pack(fill="x", pady=3)
                tk.Label(
                    linha, text=fato, bg=COR_BARRA, fg=COR_TEXTO,
                    font=(FONTE, 10), anchor="w", justify="left",
                    wraplength=490,
                ).pack(side="left", fill="x", expand=True, padx=12, pady=9)

                def apagar(texto=fato):
                    esquecer_memoria(texto)
                    desenhar()

                Botao(linha, "X", apagar).pack(side="right", padx=(0, 10))

        def conferir():
            """A IA aprende em segundo plano: a lista se atualiza sozinha."""
            if not janela.winfo_exists():
                return
            if carregar_memoria() != env.get("mostrado"):
                desenhar()
            env["tempo"] = janela.after(3000, conferir)

        def limpar():
            if not messagebox.askyesno(
                "Apagar a memória",
                "Apagar tudo o que a IA aprendeu sobre você?",
                parent=janela,
            ):
                return
            esquecer_memoria()
            desenhar()

        botoes = tk.Frame(pai, bg=COR_FUNDO)
        botoes.pack(fill="x", padx=24, pady=(0, 10))
        Botao(botoes, "Apagar tudo", limpar).pack(side="left")

        desenhar()
        def _ligar_memoria(w):
            try:
                w.bind("<MouseWheel>", _rolar_memoria)
            except Exception:
                pass
            for c in w.winfo_children():
                _ligar_memoria(c)
        try:
            moldura.bind("<MouseWheel>", _rolar_memoria)
            _ligar_memoria(moldura)
        except Exception:
            pass
        env["tempo"] = janela.after(3000, conferir)

    def _preencher_aba_ajuda(self, pai, ao_rolar):
        """Monta a aba 'Ajuda': como usar o programa."""
        tela = tk.Canvas(pai, bg=COR_FUNDO, highlightthickness=0, bd=0)
        _preparar_scrollbar_escuro(pai)
        barra = ttk.Scrollbar(
            pai, orient="vertical", command=tela.yview, style=ESTILO_BARRA,
        )
        barra.pack(side="right", fill="y")
        tela.pack(side="left", fill="both", expand=True)
        tela.configure(yscrollcommand=barra.set)

        corpo = tk.Frame(tela, bg=COR_FUNDO)
        corpo.bind(
            "<Configure>", lambda _e: tela.configure(scrollregion=tela.bbox("all"))
        )
        corpo_id = tela.create_window((0, 0), window=corpo, anchor="nw")

        def acertar_largura(_evento=None):
            tela.itemconfigure(corpo_id, width=tela.winfo_width())

        tela.bind("<Configure>", acertar_largura)


        margem = tk.Frame(corpo, bg=COR_FUNDO)
        margem.pack(fill="both", expand=True, padx=24, pady=22)

        tk.Label(
            margem, text="Como usar o Pesquisa IA", bg=COR_FUNDO,
            fg=COR_TEXTO, font=(FONTE, 16, "bold"),
        ).pack(anchor="w")

        def bloco(titulo, texto):
            tk.Label(
                margem, text=titulo, bg=COR_FUNDO, fg=COR_TEXTO_2,
                font=(FONTE, 10, "bold"),
            ).pack(anchor="w", pady=(18, 4))
            tk.Label(
                margem, text=texto, bg=COR_FUNDO, fg=COR_TEXTO_3,
                font=(FONTE, 9), justify="left", wraplength=600,
            ).pack(anchor="w")

        bloco(
            "Começando",
            "1) Na aba Chave, cole sua chave gratuita do Google e clique em "
            "Salvar.\n"
            "2) Clique em Testar chave para confirmar que ela funciona.\n"
            "3) Escreva a pergunta aqui na conversa e aperte Enter.\n\n"
            "Sem chave? Clique no botão azul lá embaixo para abrir a página "
            "do Google e criar a sua (é grátis e leva 2 minutos).",
        )
        bloco(
            "O que o programa faz",
            "Ele procura na web por você e o Google Gemini junta tudo em uma "
            "resposta só, em português, com informação atualizada. Se o Gemini "
            "demorar ou ficar fora do ar, outro serviço de IA (Groq ou "
            "OpenRouter) responde antes — por isso a resposta chega rápido.",
        )
        bloco(
            "Imagens",
            "Escreva algo como 'imagens de god of war' ou 'fotos de lobos'. "
            "O programa mostra várias imagens na conversa; clique numa para "
            "ela ampliar aqui mesmo, sem abrir outra janela, com opção de "
            "salvar.",
        )
        bloco(
            "Conversas",
            "Tudo o que você pergunta fica guardado. Na barra da esquerda, "
            "'Nova conversa' limpa a tela e 'Conversas' mostra as anteriores "
            "para reabrir. Ao excluir uma conversa, o que a IA aprendeu sobre "
            "você continua guardado (veja a aba Memória).",
        )
        bloco(
            "Atalhos",
            "Enter envia a pergunta.\n"
            "Shift+Enter quebra a linha sem enviar.\n"
            "F5 começa uma conversa nova.\n"
            "Ctrl+B mostra ou esconde a barra da esquerda.",
        )
        bloco(
            "Tudo é gratuito",
            "A busca na web que o programa usa não precisa de chave nem de "
            "cartão, e a chave do Google tem plano grátis. Se um dia o Google "
            "não responder, o plano B (aba Chave) assume com outros serviços "
            "também gratuitos.",
        )

        Botao(
            margem, "Abrir página para criar a chave",
            lambda: webbrowser.open(URL_CHAVE), destaque=True,
        ).pack(anchor="w", pady=(22, 0))

        def _rolar_ajuda(_e):
            try:
                tela.yview_scroll(int(-_e.delta / 120), "units")
            except Exception:
                pass
            return "break"

        for _parte in anda(pai):
            try:
                _parte.bind("<MouseWheel>", _rolar_ajuda)
            except Exception:
                pass

    def _testar_com_retorno(self, chave, ao_terminar):
        if self.ocupado:
            return
        self._definir_ocupado(True)
        self._definir_status("Testando a chave...")
        modelo = self.cfg.get("modelo", MODELO_PADRAO)

        def tarefa():
            try:
                testar_chave(chave, modelo)
                self.fila.put(("teste_ok_form", ao_terminar))
            except Exception as erro:
                self.fila.put(("teste_erro_form", self._traduzir_erro(erro), ao_terminar))

        threading.Thread(target=tarefa, daemon=True).start()

    # -- conversas guardadas -------------------------------------------------

    # -- conversas guardadas (lista em cascata na lateral) -------------------

    def _alternar_lista_conversas(self):
        """Abre ou recolhe a lista de conversas, em cascata na lateral."""
        if self.lista_conversas.winfo_ismapped():
            self._recolher_lista_conversas()
            return
        self._preencher_lista_conversas()
        # "before" deixa a lista sempre logo abaixo do botao Conversas
        self.lista_conversas.pack(
            fill="x", padx=8, pady=(0, 4), before=self._botao_config,
        )

    def _recolher_lista_conversas(self):
        self._fechar_popup_conversa()
        try:
            self.lista_conversas.pack_forget()
        except Exception:
            pass

    def _preencher_lista_conversas(self):
        """Desenha as conversas salvas, da mais nova para a mais antiga."""
        for filho in self.lista_conversas.winfo_children():
            filho.destroy()
        conversas = list(reversed(carregar_conversas()))
        if not conversas:
            vazio = tk.Label(
                self.lista_conversas,
                text="Nenhuma conversa ainda.\nFaça uma pergunta e ela\n"
                     "aparece aqui.",
                bg=COR_PAINEL, fg=COR_TEXTO_3, font=(FONTE, 8),
                justify="center", pady=10,
            )
            vazio._titulo = True
            vazio.pack(fill="x")
            return

        for conversa in conversas:
            item = tk.Frame(
                self.lista_conversas, bg=COR_BARRA, cursor="hand2",
            )
            item.pack(fill="x", pady=2)

            textos = tk.Frame(item, bg=COR_BARRA)
            textos.pack(side="left", fill="x", expand=True, padx=8, pady=6)
            titulo = tk.Label(
                textos,
                text=(conversa.get("titulo") or "Conversa")[:40],
                bg=COR_BARRA, fg=COR_TEXTO, font=(FONTE, 9),
                anchor="w", justify="left", wraplength=120,
            )
            titulo._titulo = True
            titulo.pack(anchor="w")
            tk.Label(
                textos, text=conversa.get("quando", ""), bg=COR_BARRA,
                fg=COR_TEXTO_3, font=(FONTE, 7), anchor="w",
            ).pack(anchor="w")

            # Os tres pontinhos: abrem o menu da conversa (excluir, abrir)
            mais = tk.Label(
                item, text="\u22ef", bg=COR_BARRA, fg=COR_TEXTO_3,
                font=(FONTE, 12), cursor="hand2",
            )
            mais.pack(side="right", padx=(0, 5), pady=2)

            def abrir(_e=None, c=conversa):
                self._carregar_conversa(c)

            def pontos(_e=None, c=conversa, botao=mais):
                self._menu_da_conversa(c, botao)

            # o cursor de "maozinha" mostra que o titulo abre a conversa
            for botao in (item, textos, titulo):
                botao.configure(cursor="hand2")
                botao.bind("<Button-1>", abrir)
            mais.configure(cursor="hand2")
            mais.bind("<Button-1>", pontos)
            # sem destaque colorido: o titulo abre, e pronto

    def _menu_da_conversa(self, conversa, ancora):
        """Caixinha 'Excluir' que abre do lado dos tres pontinhos clicados.

        O menu do Windows vinha com uma borda branca e era dificil de
        alinhar; aqui e uma janelinha propria, sem borda, com a mesma cara
        do programa. A conversa abre clicando no titulo.
        """
        self._fechar_popup_conversa()
        pop = tk.Toplevel(self.raiz)
        pop.overrideredirect(True)          # sem borda de janela
        pop.configure(bg=COR_PAINEL)        # a "borda" e da propria caixa
        item = tk.Label(
            pop, text="Excluir", bg=COR_BARRA, fg=COR_TEXTO,
            font=(FONTE, 9), cursor="hand2", padx=16, pady=7,
        )
        item.pack(fill="x", padx=2, pady=2)
        self._popup_conversa = pop

        def fechar(_e=None):
            self._fechar_popup_conversa()

        def excluir(_e=None):
            fechar()
            self._excluir_conversa_da_lista(conversa)

        item.bind("<Button-1>", excluir)
        item.bind(
            "<Enter>",
            lambda _e: item.configure(bg=COR_BARRA_MAIS, fg=COR_TEXTO),
        )
        item.bind(
            "<Leave>", lambda _e: item.configure(bg=COR_BARRA, fg=COR_TEXTO)
        )
        pop.bind("<Escape>", fechar)
        # clicar fora da caixinha fecha ela
        def fora(_e=None):
            if self._popup_conversa is None:
                return
            alvo = _e.widget if _e is not None else None
            if alvo is not None:
                atual = alvo
                while atual is not None:
                    if atual is pop:
                        return          # o clique foi dentro: deixa
                    atual = getattr(atual, "master", None)
            self._fechar_popup_conversa()

        self.raiz.bind_all("<Button-1>", fora, add="+")
        self._fechar_popup = fechar
        pop.update_idletasks()
        largura = pop.winfo_reqwidth()
        # a borda direita da caixa alinha com os tres pontinhos
        x = ancora.winfo_rootx() + ancora.winfo_width() - largura
        y = ancora.winfo_rooty() + ancora.winfo_height() + 2
        if x < 4:
            x = 4
        pop.geometry("+%d+%d" % (x, y))
        # seguranca: se o usuario esquecer a caixa, ela some sozinha
        pop.after(6000, fechar)
        return pop

    def _fechar_popup_conversa(self):
        self.raiz.unbind_all("<Button-1>")
        pop = getattr(self, "_popup_conversa", None)
        if pop is not None:
            try:
                pop.destroy()
            except Exception:
                pass
            self._popup_conversa = None

    def _confirmar(self, titulo, texto):
        """Diálogo de confirmação no tema escuro (sem branco do Windows)."""
        resultado = {"ok": False}
        pop = tk.Toplevel(self.raiz)
        pop.overrideredirect(True)
        pop.configure(bg=COR_PAINEL)
        janela = tk.Frame(pop, bg=COR_PAINEL)
        janela.pack(padx=1, pady=1)
        caixa = tk.Frame(janela, bg=COR_BARRA, highlightthickness=1,
                        highlightbackground=COR_BORDA)
        caixa.pack(fill="both")

        # Cabecalho arrastavel (permite mover a janelinha)
        topo = tk.Frame(caixa, bg=COR_BARRA)
        topo.pack(fill="x", padx=16, pady=(14, 4))
        rotulo_titulo = tk.Label(
            topo, text=titulo, bg=COR_BARRA, fg=COR_TEXTO,
            font=(FONTE, 11, "bold"), anchor="w",
        )
        rotulo_titulo.pack(fill="x")

        def _arrastar_inicio(_e):
            pop._drag = (_e.x_root, _e.y_root,
                          pop.winfo_x(), pop.winfo_y())

        def _arrastar_mover(_e):
            d = getattr(pop, "_drag", None)
            if not d:
                return
            start_xr, start_yr, start_xw, start_yw = d
            pop.geometry("+%d+%d" % (
                start_xw + (_e.x_root - start_xr),
                start_yw + (_e.y_root - start_yr),
            ))

        def _arrastar_fim(_e):
            pop._drag = None

        for widget in (topo, rotulo_titulo):
            widget.bind("<Button-1>", _arrastar_inicio)
            widget.bind("<B1-Motion>", _arrastar_mover)
            widget.bind("<ButtonRelease-1>", _arrastar_fim)

        tk.Label(
            caixa, text=texto, bg=COR_BARRA, fg=COR_TEXTO_2,
            font=(FONTE, 9), wraplength=300, justify="left",
        ).pack(fill="x", padx=16, pady=(0, 12), anchor="w")

        botoes = tk.Frame(caixa, bg=COR_BARRA)
        botoes.pack(fill="x", padx=16, pady=(0, 12))
        def sim():
            resultado["ok"] = True
            pop.destroy()
        def cancelar():
            resultado["ok"] = False
            pop.destroy()
        Botao(botoes, "Excluir", sim, destaque=True).pack(side="left")
        Botao(botoes, "Cancelar", cancelar).pack(side="left", padx=(8, 0))
        pop.bind("<Escape>", lambda _e: cancelar())
        pop.update_idletasks()
        largura = pop.winfo_width()
        altura = pop.winfo_height()
        centro_x = self.raiz.winfo_rootx() + (self.raiz.winfo_width() - largura) // 2
        centro_y = self.raiz.winfo_rooty() + (self.raiz.winfo_height() - altura) // 2
        pop.geometry("+%d+%d" % (centro_x, centro_y))

        pop.grab_set()
        self.raiz.wait_window(pop)
        return resultado["ok"]

    def _abrir_conversa_da_lista(self, conversa):
        """Abre a conversa escolhida (quando se clica no titulo)."""
        self._carregar_conversa(conversa)
        self._recolher_lista_conversas()

    def _excluir_conversa_da_lista(self, conversa):
        """Apaga a conversa. O que a IA aprendeu continua guardado."""
        titulo = (conversa.get("titulo") or "Conversa")[:44]
        confirmar = self._confirmar(
            "Excluir conversa",
            'Excluir a conversa "%s"?\n\n'
            "O que a IA aprendeu sobre você continua guardado "
            "(só a conversa é apagada)." % titulo,
        )
        if not confirmar:
            return
        salvar_conversas(
            [x for x in carregar_conversas()
             if str(x.get("id")) != str(conversa.get("id"))]
        )
        # se era a conversa aberta, a proxima resposta comeca outra
        # (senao ela voltaria sozinha na lista)
        if str(self._id_conversa) == str(conversa.get("id")):
             self._id_conversa = None
        if self.lista_conversas.winfo_ismapped():
            self._preencher_lista_conversas()
            # Se nao sobrou conversa alguma, volta para a tela inicial
            # (conversa nova), para nao deixar a tela 'presa'.
            if not carregar_conversas():
                self._id_conversa = None
                self._nova_conversa()
        self._definir_status("Conversa excluída. A memória continua guardada.")
    def _carregar_conversa(self, conversa):
        """Abre uma conversa antiga na tela (sem mexer na memoria)."""
        mensagens = [
            {"role": m.get("role"), "text": m.get("text", "")}
            for m in conversa.get("mensagens", [])
            if m.get("role") in ("user", "model")
        ]
        if not mensagens:
            return
        self._cancelar_digitacao()
        self._parar_digitando()
        self.mensagens = list(mensagens)
        self.historico = list(mensagens)
        self._id_conversa = conversa.get("id")
        self._definir_ocupado(False)
        self._renderizar()
        self._rolar_fim()

    # -- memoria sobre o usuario ---------------------------------------------

    def _nova_conversa(self):
        self._cancelar_digitacao()
        self.historico = []
        self.mensagens = []
        self._id_conversa = None
        self._parar_digitando()
        self._definir_ocupado(False)
        self._renderizar()
        self._atualizar_status_chave()
        self.entrada.focus_set()

    def _guardar_e_aprender(self, pergunta, texto):
        """Salva a conversa e deixa a IA aprender sobre o usuario.

        Roda em segundo plano, sem mostrar nada na tela: o usuario nao
        precisa preencher nada e a IA nunca conta que guardou.
        """
        try:
            if getattr(self, "_id_conversa", None) is None:
                self._id_conversa = str(time.time())
            guardar_conversa(self._id_conversa, self.mensagens)
        except Exception:
            pass
        chave = (self.cfg.get("api_key") or "").strip()
        if not chave:
            return

        def tarefa():
            try:
                aprender_com_o_usuario(chave, pergunta, texto)
            except Exception:
                pass

        threading.Thread(target=tarefa, daemon=True).start()

    # -- comunicacao com a thread de trabalho -------------------------------

    def _processar_fila(self):
        try:
            while True:
                item = self.fila.get_nowait()
                self._tratar_item(item)
        except queue.Empty:
            pass
        self.raiz.after(100, self._processar_fila)

    def _pai_aviso(self):
        """Devolve a janela de configurações, se ela ainda estiver aberta."""
        jan = getattr(self, "_janela_config", None)
        try:
            if jan is not None and jan.winfo_exists():
                return jan
        except Exception:
            pass
        return None

    def _tratar_item(self, item):
        tipo = item[0]

        if tipo == "teste_ok_form":
            self._definir_ocupado(False)
            item[1](True)
            return

        if tipo == "teste_erro_form":
            self._definir_ocupado(False)
            item[2](False, item[1])
            return

        if tipo == "teste_ok":
            self._definir_ocupado(False)
            self._atualizar_status_chave()
            messagebox.showinfo(
                "Tudo certo", "A chave da API está funcionando. Pode pesquisar!"
            )
            return

        if tipo == "teste_erro":
            self._definir_ocupado(False)
            messagebox.showerror("Problema com a chave", item[1])
            return

        if tipo == "teste_reserva_ok":
            _, nome, texto = item
            self._definir_ocupado(False)
            self._definir_status("%s está funcionando." % nome, COR_OK)
            messagebox.showinfo(
                "Tudo certo",
                "O %s respondeu: %s\n\nO plano B já pode ser usado."
                % (nome, (texto or "OK")[:120]),
                parent=self._pai_aviso(),
            )
            return

        if tipo == "teste_reserva_erro":
            _, nome, msg = item
            self._definir_ocupado(False)
            self._definir_status("")
            messagebox.showerror(
                "Problema com o %s" % nome, msg, parent=self._pai_aviso()
            )
            return

        if tipo == "imagem_chat_ok":
            _, area, item_imagem, imagem = item
            item_imagem["_baixando"] = False
            item_imagem["_grande"] = imagem
            if self._janela_viva(area) and getattr(
                area, "_item_atual", None
            ) is item_imagem:
                self._mostrar_ampliada(area)
            return

        if tipo == "imagem_chat_erro":
            _, area, item_imagem = item
            item_imagem["_baixando"] = False
            if self._janela_viva(area) and getattr(
                area, "_item_atual", None
            ) is item_imagem:
                self._mostrar_erro_no_chat(area, item_imagem)
            return

        if tipo == "etapa":
            self._definir_status(item[1] + "...")
            return

        self._parar_digitando()

        if tipo == "imagens":
            _, _pergunta, termo, itens = item
            if not itens:
                self.mensagens.append({
                    "role": "erro",
                    "text": (
                        "Não encontrei imagens para \u201c%s\u201d. "
                        "Tente escrever de outro jeito." % termo
                    ),
                })
                self._definir_status("Não encontrei imagens.", COR_ERRO_TX)
            else:
                self.mensagens.append({
                    "role": "imagens", "text": "", "termo": termo, "itens": itens,
                })
                self._definir_status("")
            self._renderizar()
            self._definir_ocupado(False)
            return

        if tipo == "ok":
            _, pergunta, texto, _fontes, _buscas, _origem = item
            self._origem_resposta = _origem or "Gemini"
            texto = texto or "(sem resposta)"
            if self.cfg.get("usar_contexto", True):
                self.historico.append({"role": "user", "text": pergunta})
                self.historico.append({"role": "model", "text": texto})
            self.mensagens.append({"role": "model", "text": texto})
            # Escreve a resposta no balao letra a letra (como chats modernos).
            self._iniciar_digitacao(len(self.mensagens) - 1)
            # Guarda a conversa e deixa a IA aprender sobre o usuario,
            # tudo em segundo plano e sem avisar ninguem.
            self._guardar_e_aprender(pergunta, texto)
            return

        _, _pergunta, mensagem = item
        self.mensagens.append({"role": "erro", "text": mensagem})
        self._renderizar()
        self._definir_status("Deu erro. Veja a mensagem em vermelho.", COR_ERRO_TX)
        self._definir_ocupado(False)


# ----------------------------------------------------------------------------
# Inicio
# ----------------------------------------------------------------------------


def main():
    try:
        from ctypes import windll

        windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

    raiz = tk.Tk()

    # No programa compilado (sem janela preta) qualquer erro ficaria
    # escondido. Aqui tudo que der errado e guardado no erro.log, para
    # poder ser lido e mandado para quem ajuda.
    def registrar_erro(onde, erro):
        try:
            ARQUIVO_ERRO.parent.mkdir(parents=True, exist_ok=True)
            with ARQUIVO_ERRO.open("a", encoding="utf-8") as arquivo:
                arquivo.write(
                    "\n===== %s | %s =====\n%s\n"
                    % (time.strftime("%d/%m/%Y %H:%M:%S"), onde, erro)
                )
        except Exception:
            pass

    def ao_falhar(tipo, valor, tb):
        registrar_erro("erro na tela", "".join(
            traceback.format_exception(tipo, valor, tb)))

    raiz.report_callback_exception = ao_falhar

    def excecao_nao_tratada(tipo, valor, tb):
        try:
            ao_falhar(tipo, valor, tb)
        finally:
            try:
                sys.__excepthook__(tipo, valor, tb)
            except Exception:
                pass

    def excecao_em_thread(args):
        ao_falhar(
            "erro em outra tarefa",
            "".join(traceback.format_exception(args.exc_type,
                                                args.exc_value,
                                                args.exc_traceback)),
        )

    sys.excepthook = excecao_nao_tratada
    threading.excepthook = excecao_em_thread

    Aplicativo(raiz)
    raiz.mainloop()


if __name__ == "__main__":
    try:
        main()
    except Exception:
        detalhes = traceback.format_exc()
        try:
            ARQUIVO_ERRO.write_text(detalhes, encoding="utf-8")
        except Exception:
            pass
        try:
            raiz_erro = tk.Tk()
            raiz_erro.withdraw()
            messagebox.showerror(
                "Pesquisa IA - erro ao abrir",
                "O programa não conseguiu abrir.\n\n"
                "Detalhes foram salvos em:\n%s\n\n"
                "Últimas linhas:\n%s" % (ARQUIVO_ERRO, detalhes[-600:]),
            )
            raiz_erro.destroy()
        except Exception:
            print(detalhes)
        sys.exit(1)
