# -*- coding: utf-8 -*-
"""
Eye of Thundera - assistente pessoal que pesquisa na web.

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
import tempfile
import threading
import time
import traceback
import webbrowser
from concurrent.futures import ThreadPoolExecutor
from html import unescape
from pathlib import Path

import tkinter as tk
import tkinter.ttk as ttk
from tkinter import filedialog

import memoria
import roteador
import voz

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
CACHE_EMOJI_COLORIDO = {}
REFERENCIAS_IMG_EMOJI = []

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
        "nome": "ChatGPT (OpenAI)",
        "endereco": "https://api.openai.com/v1/chat/completions",
        "modelo": "gpt-4o-mini",
        "campo_chave": "chave_openai",
        "campo_modelo": "modelo_openai",
        "pagina": "https://platform.openai.com/api-keys",
        "prefixo": "sk-",
        "resumo": "OpenAI (ChatGPT), pago por uso, chave comeca com sk-",
        "passos": (
            "Como conseguir: 1) clique em \"Como conseguir a chave\"; "
            "2) entre com sua conta OpenAI; 3) clique em Create new secret key; "
            "4) copie o codigo (comeca com sk-) e cole aqui."
        ),
    },
    {
        "nome": "Groq",
        "endereco": "https://api.groq.com/openai/v1/chat/completions",
        "modelo": "openai/gpt-oss-120b",
        "campo_chave": "chave_groq",
        "campo_modelo": "modelo_groq",
        "pagina": "https://console.groq.com/keys",
        "prefixo": "gsk_",
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
        "prefixo": "sk-or-",
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

# Portuguese do Brasil, e nao de Portugal. (16/10/2026: o Wolf leu
# respostas com sotaque de Portugal e riu. A causa e' simples: o modelo
# tem duas variantes de portugues e, sem dizer qual, ele escolhe a que
# acha mais "neutra" — que e' a de Portugal. Dizer so "portugues" nao
# resolve; tem que dizer BRASIL e mostrar exemplos do que NAO fazer.)
#
# Os exemplos nao sao enfeite: cada um e' uma palavra que o modelo usa
# quando escorrega. Sem a lista, ele volta para elas na resposta seguinte.
IDIOMA_BR = (
    "IDIOMA: escreva em português do BRASIL, nunca em português de "
    "Portugal.\n"
    "Nada destas palavras de Portugal (e o que se usa aqui):\n"
    "- 'de certeza' → no Brasil se diz 'com certeza'\n"
    "- 'a nível de' → aqui se diz 'no sentido de'\n"
    "- 'equipa' → aqui se diz 'equipe'\n"
    "- 'ecrã' → aqui se diz 'tela'\n"
    "- 'rato' → aqui se diz 'mouse'\n"
    "- 'ficheiro' → aqui se diz 'arquivo'\n"
    "- 'desculpa lá' → aqui se diz só 'desculpa'\n"
    "- 'a seguir está' → aqui se diz 'segue'\n"
    "E o mais importante: em Portugal se gerundiza ('estou a fazer'); "
    "aqui se faz assim: 'estou fazendo', 'vou fazer', 'preciso falar'.\n"
    "Escreva como se falasse com alguém no Sul do Brasil."
)

INSTRUCOES = (
    "Você é um amigo bem informado, que pesquisa na web para uma pessoa comum "
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
    "- Responda exatamente sobre o que foi perguntado. Se a pergunta citar "
    "um time, uma pessoa ou um produto pelo nome, fale DELE, não de outro "
    "parecido. Pode usar o apelido se for o mesmo (Grêmio, por exemplo, "
    "também é chamado de Imortal e Tricolor).\n"
    "- Nunca invente palavras de outros idiomas e não pergunte ao usuário se "
    "elas significam algo. Escreva a frase normalmente em português.\n"
    "- Não termine fazendo perguntas de volta para quem perguntou: "
    "responda e pare.\n"
    "- Escreva de forma clara e direta, com tópicos curtos quando ajudar a "
    "leitura.\n"
    "- Escreva em texto simples: NÃO use asteriscos (*), cerquilhas (#) nem "
    "outras marcações. Para fazer uma lista, comece a linha com '•'.\n"
    "\n"
    + IDIOMA_BR
)

INSTRUCOES_AMIGO = (
    "Você conversa como um amigo de confiança: natural, caloroso, direto, "
    "com humor quando combinar. Sem formalidade.\n"
    "\n"
    "Curto quando o papo é leve; mais fundo quando a pessoa pedir.\n"
    "Aqui você NÃO tem resultados da web. Se a resposta depender de algo "
    "atual e você não tiver certeza, diga isso em uma frase e ofereça "
    "pesquisar. Nunca invente número, data ou fato.\n"
    "Use o que sabe da pessoa só quando ajudar, de forma natural; nunca diga "
    "que 'lembrou' ou 'guardou', nem liste o que sabe dela. Exceção: se ela "
    "pedir para lembrar de algo, confirme curto ('Anotado!').\n"
    "Dê opinião quando pedirem e discorde com jeito quando precisar.\n"
    "Nada de frases de robô ('Como posso ajudar?' em toda resposta) nem "
    "repetir a pergunta.\n"
    "Escreva em texto simples: NÃO use asteriscos (*) nem emojis. Para fazer "
    "uma lista, comece a linha com '•'.\n"
    "\n"
    + IDIOMA_BR
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

# Botao do microfone: mesma bolha cinza do enviar, so que parada e vermelha
# enquanto esta gravando.
COR_MIC = (134, 134, 141)
COR_MIC_HOVER = (156, 156, 162)
COR_MIC_GRAVANDO = (214, 69, 69)
COR_MIC_GRAVANDO_HOVER = (231, 93, 93)
COR_MIC_TRACO = (16, 16, 20)

# Canto arredondado da caixa de digitar. O mesmo tamanho que o respiro
# entre o botao de enviar e a borda da caixa (e o texto comecar em 14),
# senao a tampinha do canto cai por cima do botao.
RAIO_CANTO = 12


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
    cfg.setdefault("usar_gemini", True)
    cfg.setdefault("modo_pesquisa", "auto")
    cfg.setdefault("aprender", True)
    cfg.setdefault("voz_enviar", False)
    cfg.setdefault("api_key_reserva", "")
    cfg.setdefault("tema", "dark")
    cfg.setdefault("temaIdx", 0)
    for _servico in SERVICOS_RESERVA:
        cfg.setdefault(_servico["campo_chave"], "")

    # Se o modelo salvo foi aposentado pelo Google, volta para o padrao novo.
    if cfg.get("modelo") in MODELOS_APOSENTADOS:
        cfg["modelo"] = MODELO_PADRAO

    return cfg


def salvar_config(cfg):
    """Grava a configuracao com substituicao atomica, preservando a versao anterior se falhar."""
    PASTA_CONFIG.mkdir(parents=True, exist_ok=True)
    temporario = None
    try:
        # O arquivo temporario fica na mesma pasta/volume para que os.replace
        # substitua o config.json de uma vez, sem deixa-lo pela metade.
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=str(PASTA_CONFIG),
            prefix=".config-",
            suffix=".tmp",
            delete=False,
        ) as arquivo:
            temporario = Path(arquivo.name)
            json.dump(cfg, arquivo, indent=2, ensure_ascii=False)
            arquivo.write("\n")
            arquivo.flush()
            os.fsync(arquivo.fileno())
        os.replace(temporario, ARQUIVO_CONFIG)
        temporario = None
    finally:
        # Se a escrita ou a troca falhar, limpa apenas o temporario criado.
        # O config.json anterior permanece intacto.
        if temporario is not None:
            try:
                temporario.unlink(missing_ok=True)
            except OSError:
                pass


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


def _arquivo_memoria_data():
    """Onde ficam as datas dos fatos.

    deriving do `ARQUIVO_MEMORIA` (e nao de uma pasta solta) porque os
    testes apontam o arquivo da memoria para uma pasta de teste: assim a
    data vai junto e **nada nunca e' escrito na pasta do Wolf** durante
    um teste.
    """
    return Path(ARQUIVO_MEMORIA).parent / "memoria_datas.json"


def carregar_memoria_datas():
    """Quando cada fato da memoria foi aprendido: {fato: 'dd/mm/aaaa'}.

    Vive num arquivo SEPARADO de proposito: o `memoria.json` e' lido
    pelos dois programas e tem regra de ouro (nunca perder uma palavra),
    entao nao se mexe nele. Factos antigos, que ja estavam guardados
    antes desta data existir, ficam sem data — e a tela mostra isso.
    """
    dados = _ler_json(_arquivo_memoria_data(), {})
    if not isinstance(dados, dict):
        return {}
    return {str(k): str(v) for k, v in dados.items() if str(v).strip()}


def _anotar_datas(fatos):
    """Marca a data de hoje nos fatos novos e esquece os que sairam.

    Nunca levanta erro: a data e' um extra bonito, e perder esse extra
    nao pode derrubar o programa.
    """
    try:
        arquivo = _arquivo_memoria_data()
        dados = carregar_memoria_datas()
        antes = set(carregar_memoria())
        hoje = time.strftime("%d/%m/%Y")
        atual = {}
        for fato in fatos:
            # um fato que ja existia continua com a data antiga
            atual[fato] = dados.get(fato) or (hoje if fato not in antes else hoje)
        _gravar_json(arquivo, atual)
    except Exception:
        pass


def salvar_memoria(fatos):
    global _memoria_cache
    _memoria_cache = [
        str(f).strip() for f in fatos if str(f).strip()
    ][-MAX_MEMORIAS:]
    _anotar_datas(_memoria_cache)
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
    """Junta fatos novos sem repetir (regras no arquivo memoria.py)."""
    atuais = carregar_memoria()
    nova, mudou = memoria.mesclar(atuais, novos)
    if mudou:
        salvar_memoria(nova)
    return nova


def carregar_memoria_gavetas():
    """Memoria agrupada por gaveta (read-only)."""
    return memoria.gavetas_de(carregar_memoria())


def carregar_memoria_por_assunto():
    """Memoria agrupada por assunto (read-only)."""
    return memoria.gavetas_por_assunto(carregar_memoria())


def organizar_memoria():
    """Tira os fatos repetidos da memoria que ja existe.

    Antes da primeira limpeza guarda uma copia de seguranca
    (memoria_antes_de_organizar.json). Devolve True se algo mudou."""
    atuais = carregar_memoria()
    nova, mudou = memoria.consolidar(atuais)
    if not mudou:
        return False
    copia = ARQUIVO_MEMORIA.with_name("memoria_antes_de_organizar.json")
    if not copia.exists():
        _gravar_json(copia, atuais)
    salvar_memoria(nova)
    return True


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


def instrucoes_da_ia(modo="pesquisa"):
    """Instrucoes do programa + a memoria sobre o usuario."""
    base = INSTRUCOES_AMIGO if modo == "amigo" else INSTRUCOES
    fatos = carregar_memoria()
    if not fatos:
        return base
    lista = "\n".join("- " + fato for fato in fatos[:40])
    return (
        base
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
    global _ultimo_aprendizado
    api_key = (api_key or "").strip()
    if not api_key or (len((resposta or "")) < 120
                       and len((pergunta or "")) < 12):
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
                "Conversa:\nPESSOA: %s\nASSISTENTE: %s\n\n"
                "JA GUARDADO (nao repita nem reescreva de outro jeito; "
                "devolva so o que for NOVO ou uma CORRECAO; se nao houver, "
                "responda NADA):\n%s\n\n%s"
                % (
                    (pergunta or "")[:1500],
                    (resposta or "")[:2500],
                    "\n".join("- " + f[:120] for f in carregar_memoria()[-60:])
                    or "(nada ainda)",
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


def _decidir_modo(api_key, texto, historico, modo="auto"):
    """Pergunta ao roteador se precisa pesquisar. Nunca trava a conversa.

    Usa o modelo rápido com tempo curto; se falhar, o roteador decide
    sozinho pela heurística de reserva.
    """
    def chamar_modelo(prompt):
        from google import genai
        from google.genai import types

        # O PRAZO PRECISA SER DE 10 SEGUNDOS OU MAIS. Com 8 o Google
        # recusa com "400 INVALID_ARGUMENT: Manually set deadline 8s is
        # too short. Minimum allowed deadline is 10s" - e o roteador
        # caia na regra das palavras, SEM AVISAR NINGUEM. Isso zerava
        # "pesquisar ou papo" para sempre (achado em 16/10/2026, quando o
        # Wolf perguntou do proximo jogo do Gremio e a IA respondeu que
        # nao tinha internet, sendo que o programa tem).
        http = types.HttpOptions(
            timeout=20000,
            retry_options=types.HttpRetryOptions(
                attempts=1,
                initial_delay=0.2,
                max_delay=1.0,
                http_status_codes=[408, 429, 500, 502, 503, 504],
            ),
        )
        cliente = genai.Client(api_key=api_key, http_options=http)
        resposta = cliente.models.generate_content(
            model=MODELO_MEMORIA,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0,
                response_mime_type="application/json",
            ),
        )
        return (getattr(resposta, "text", "") or "").strip()

    return roteador.decidir(texto, historico, chamar_modelo, modo)


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


# Trechos de erro que significam "esta chave foi recusada" (e não, por
# exemplo, "acabou a cota do dia", que se resolve sozinha).
CHAVE_RECUSADA = (
    "api key not valid",
    "api key invalid",
    "invalid authentication",
    "unauthenticated",
    "no auth credentials",
    "permission_denied",
    "401",
)


def _falha_de_chave(erro):
    """True quando o erro é "a chave foi recusada" (e dá para trocar)."""
    texto = ("%s %s" % (type(erro).__name__, erro)).lower()
    return any(trecho in texto for trecho in CHAVE_RECUSADA)


_CORRETORES = {}


def _obter_corretor(lingua):
    """Carrega (uma vez) o dicionário do corretor. Devolve False se não
    houver biblioteca (o programa continua funcionando sem correção)."""
    if lingua not in _CORRETORES:
        try:
            from spellchecker import SpellChecker
            _CORRETORES[lingua] = SpellChecker(language=lingua)
        except Exception:
            _CORRETORES[lingua] = False
    return _CORRETORES[lingua]


def sugerir_correcao(palavra, maximo=6):
    """Sugestões de correção para UMA palavra. Devolve [] se não houver.

    Vive aqui no motor (e não dentro do tkinter) porque **os dois
    programas** precisam dela: o antigo pelo botão direito, o novo pelo
    menu que a própria tela monta. Duas cópias dessa lógica iam divergir
    com o tempo — foi o que aconteceu com `registrar_erro`.

    Português é a língua primária; o dicionário de inglês só entra quando
    a palavra se assemelha **mais** a ele (jogo, game, chat...).
    """
    palavra = (palavra or "").strip()
    if not re.fullmatch(r"[^\W\d_]{2,}", palavra, re.UNICODE):
        return []
    baixo = palavra.lower()
    pt = _obter_corretor("pt")
    if not pt:
        return []
    if baixo not in pt.unknown({baixo}):
        return []                      # a palavra está certa
    en = _obter_corretor("en")
    # termo válido em inglês não sugere nada (evita "casa" -> "case")
    if en and baixo not in en.unknown({baixo}):
        return []
    cands_pt = list(pt.candidates(baixo) or [])
    cands_en = list(en.candidates(baixo) or []) if en else []

    def melhor(cands):
        if not cands:
            return 0.0
        return max(difflib.SequenceMatcher(None, baixo, c).ratio()
                   for c in cands)

    if cands_pt and cands_en:
        cands = cands_en if melhor(cands_en) > melhor(cands_pt) + 0.10 \
            else cands_pt
    else:
        cands = cands_en or cands_pt
    return sorted(cands)[:maximo]


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
            % (nome, "sk-" if nome.startswith("ChatGPT") else (
                "gsk_" if nome == "Groq" else "sk-or-"))
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


def _chamar_servico(servico, prompt, historico, modo="pesquisa"):
    """Chama um serviço de reserva (Groq, OpenRouter...) e devolve o texto.

    Usa a biblioteca que já vem com o Python, então não é preciso instalar
    mais nada no computador.
    """
    import urllib.error
    import urllib.request

    amigo = (modo == "amigo")
    mensagens = [{"role": "system", "content": instrucoes_da_ia(modo)}]
    for turno in (historico or [])[-12 if amigo else -6:]:
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
            "temperature": 0.7 if amigo else 0.3,
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
    except urllib.error.URLError:
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
                 com_plano_b=True, modo="pesquisa"):
    """Chama o Gemini (grátis) para escrever a resposta final.

    Tenta o modelo principal e, se ele estiver fora do ar, passa rapidamente
    para os modelos de reserva. Se o Gemini não responder de jeito nenhum,
    tenta os serviços de plano B (Groq, OpenRouter) que estiverem com chave.

    Devolve (texto, origem), sendo a origem o nome de quem escreveu a resposta.
    No modo "amigo" usa temperatura 0.7 e as últimas 12 falas; no modo
    "pesquisa" usa 0.3 e as últimas 6.
    """
    from google.genai import types

    amigo = (modo == "amigo")
    usar_gemini = True if not cfg else bool(cfg.get("usar_gemini", True))
    cliente = _criar_cliente(api_key) if usar_gemini else None
    ordem = [modelo] + [m for m in MODELOS_RESERVA if m != modelo]
    ultimo_erro = None

    conteudo = []
    for turno in (historico or [])[-12 if amigo else -6:]:
        conteudo.append(
            types.Content(
                role=turno["role"],
                parts=[types.Part(text=turno["text"])],
            )
        )
    conteudo.append(types.Content(role="user", parts=[types.Part(text=prompt)]))

    if usar_gemini:
        for _rodada in range(2):
            for nome in ordem:
                try:
                    config = types.GenerateContentConfig(
                        temperature=0.7 if amigo else 0.3,
                        system_instruction=instrucoes_da_ia(modo),
                    )
                    resposta = cliente.models.generate_content(
                        model=nome, contents=conteudo, config=config
                    )
                    texto = (getattr(resposta, "text", "") or "").strip()
                    if not texto:
                        texto = _juntar_partes(resposta)
                    if texto:
                        return texto, "Gemini"
                    ultimo_erro = RuntimeError("a IA nao devolveu texto")
                except Exception as erro:
                    ultimo_erro = erro
                    continue
            time.sleep(1.5)

    # O Gemini não respondeu: entra o plano B (se estiver configurado).
    # Na corrida entre as IAs quem chama este ponto já cuida do plano B em
    # outra thread, então ele é pulado para não repetir a mesma chamada.
    if com_plano_b or not usar_gemini:
        servicos = _servicos_prontos(cfg)
        if servicos:
            erros = []
            for servico in servicos:
                try:
                    texto = _chamar_servico(servico, prompt, historico, modo)
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
    api_key, modelo, prompt, historico, cfg=None, antecipacao=ANTENACAO_PADRAO,
    modo="pesquisa",
):
    """Pede a resposta para varias IAs ao mesmo tempo e fica com a primeira.

    Devolve (texto, origem) igual ao _gerar_texto, mas sem esperar a mais
    lenta: quem responder primeiro vence.
    """
    usar_gemini = True if not cfg else bool(cfg.get("usar_gemini", True))
    servicos = _servicos_prontos(cfg) if cfg else []
    if not servicos and not usar_gemini:
        raise RuntimeError("Gemini desligado e nenhum servico de plano B ativo.")
    if not servicos:
        # sem plano B nao ha corrida: e so o Gemini mesmo
        return _gerar_texto(api_key, modelo, prompt, historico, cfg)

    resultados = queue.Queue()
    erros = []
    andamento = {"gemini": usar_gemini, "plano_b": bool(servicos)}

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
                api_key, modelo, prompt, historico, cfg, com_plano_b=False,
                modo=modo,
            )
            avisar_fim("gemini", texto, origem)
        except Exception as erro:
            avisar_fim("gemini", erro=erro)

    def correr_plano_b():
        ultimo_erro = None
        for servico in servicos:
            try:
                texto = _chamar_servico(servico, prompt, historico, modo)
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

    if usar_gemini and api_key:
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
id_atual=None, consulta=None, profundo=False,
):
    """Pesquisa na web e pede para a IA juntar tudo em uma resposta.

    Devolve (texto, fontes, buscas, origem) para manter o mesmo formato de
    antes, mas sem links (as fontes vêm vazias de propósito). A "origem" diz
    qual serviço escreveu a resposta (Gemini ou um dos serviços de plano B).

    A função "progresso" (opcional) é chamada a cada etapa, para a tela
    mostrar ao usuário o que está acontecendo.

    O "id_atual" é a conversa que está aberta na tela: ela não entra de novo
    no contexto das conversas antigas.

    A "consulta" (opcional) é o que vai para a busca na web; o prompt final
    continua com a pergunta original do usuário.
    """
    def avisar(mensagem):
        if progresso is not None:
            try:
                progresso(mensagem)
            except Exception:
                pass

    busca = (consulta or pergunta or "").strip() or pergunta
    avisar("Procurando na web")
    resultados = _buscar_texto(busca)
    noticias = _buscar_noticias(busca) if _quer_noticias(busca) else []
    # Pesquisa profunda: varias queries (sem gastar IA) para cobrir
    # mais fontes. As variacoes sao simples e baratas.
    if profundo:
        _variacoes = (
            (busca or ""),
            (busca or "") + " principais",
            (busca or "") + " atual",
            (busca or "") + " detalhes",
        )
        for _q in _variacoes:
            try:
                _extra = _buscar_texto(_q)
                vistos = {(i.get("href") or i.get("url") or "").strip()
                          for i in (resultados or [])}
                for item in (_extra or []):
                    u = (item.get("href") or item.get("url") or "").strip()
                    if u and u not in vistos:
                        vistos.add(u)
                        (resultados or []).append(item)
            except Exception:
                pass


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
    conteudos = _conteudo_das_paginas(resultados, quantidade=(12 if profundo else 4))
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
    )
    if profundo:
        prompt += (
            "\n\nMODO PESQUISA PROFUNDA: organize a resposta em topicos curtos, "
            "cite site(s) fonte por paragrafo, crie secao 'fontes' final. "
            "Seja mais detalhada (3-5 paragrafos)."
        )
    prompt = prompt + contexto_das_conversas(ignorar=id_atual)


    historico_para_ia = historico if usar_contexto else []
    avisar("Consultando a inteligência artificial")
    # Varias IAs respondem ao mesmo tempo e vale a primeira que chegar.
    texto, origem = _gerar_texto_rapido(
        api_key, modelo, prompt, historico_para_ia, cfg
    )
    return (_espacar_blocos(_sem_markdown(texto)),
            _sites_consultados(resultados, noticias), [], origem)


def _sites_consultados(resultados, noticias, limite=6):
    """Os sites que a busca trouxe, para a tela mostrar embaixo da
    resposta (ideia 1 da IDEIAS.md: e' o que da confianca na resposta).

    Sao os **resultados da busca**, e nao citacoes: o programa nao
    confere se o que o site diz e' verdadeiro, so o que ele entregou.
    Por isso a tela escreve "sites consultados" e nao "fonte da
    verdade", e mostra o link para o Wolf conferir com os proprios olhos.

    Sem link repetido e sem link quebrado, na ordem em que apareceram.
    """
    vistos = set()
    sites = []
    for item in list(resultados or []) + list(noticias or []):
        titulo = (item.get("title") or "").strip()
        url = (item.get("href") or item.get("url") or "").strip()
        if not url or not url.startswith(("http://", "https://")):
            continue
        if url in vistos:
            continue
        vistos.add(url)
        sites.append({"titulo": titulo or url, "url": url})
        if len(sites) >= limite:
            break
    return sites


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
    historico_para_ia = historico if usar_contexto else []
    hoJe = __import__("time").strftime("%d/%m/%Y")
    prompt = (
        "Data de hoje: %s\n\n"
        "Pergunta do usuário: %s" % (hoJe, pergunta)
    ) + contexto_das_conversas(ignorar=id_atual)
    texto, origem = _gerar_texto_rapido(
        api_key, modelo, prompt, historico_para_ia, cfg, modo="amigo",
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
_FOTOS_MIC = {}
_FOTOS_CANTO = {}


def anda(widget):
    """Todos os widgets abaixo de um widget (ele mesmo incluido)."""
    achados = [widget]
    for filho in widget.winfo_children():
        achados.extend(anda(filho))
    return achados


def _acompanhar_largura(janela, margem=76):
    """Faz os textos da janela quebrarem na largura REAL dela.

    Cada texto era criado com um `wraplength` fixo (380, 490, 540, 560,
    600...), tudo diferente. O efeito era o que o Wolf viu: numa janela
    estreita o texto ficava cortado/espremido, e numa larga sobrava um
    vão vazio do lado. Aqui a largura do texto acompanha a da janela e se
    ajusta sozinha quando o Wolf redimensiona.

    Devolve a função de ajuste, para quem precisar chamar na hora.
    """
    def ajustar(_evento=None):
        largura = janela.winfo_width() - margem
        if largura < 200:
            return                      # ainda não desenhou: espera
        for item in anda(janela):
            if not isinstance(item, tk.Label):
                continue
            try:
                if int(item.cget("wraplength")) <= 0:
                    continue           # texto de uma linha só: não mexe
                item.configure(wraplength=largura)
            except Exception:
                pass

    janela.bind("<Configure>", ajustar)
    try:
        janela.after(40, ajustar)       # a janela já tem largura
    except Exception:
        pass
    return ajustar


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


def _dentro_do_canto(x, y, lado, canto):
    """Diz se o ponto (x, y) pertence a uma caixa de cantos arredondados.

    Serve para desenhar as quatro "tampinhas" que deixam a caixa de
    digitar com canto redondo: elas pintam de fundo o que ficou FORA da
    curva. `canto` e "ne", "nw", "se" ou "sw"; o quadrado tem `lado` pixels
    de lado e a curva e um quarto de circulo cujo centro fica no canto
    OPOSTO ao arredondado (é para onde a caixa continua).

    CUIDADO: se o centro sair no canto errado, a tampinha come o miolo da
    caixa (e o botão de enviar) em vez de cortar o canto — já aconteceu.
    """
    ultimo = lado - 1
    if canto in ("nw", "ne"):        # cantos de cima: centro embaixo
        dy = ultimo - y
    else:                             # cantos de baixo: centro em cima
        dy = y
    if canto in ("nw", "sw"):        # cantos da esquerda: centro à direita
        dx = ultimo - x
    else:                             # cantos da direita: centro à esquerda
        dx = x
    return (dx * dx + dy * dy) <= lado * lado


def _imagem_canto(raio, cor_dentro, cor_fora, canto, escala=4):
    """Desenha o cantinho arredondado e devolve a imagem PIL (ou None).

    A imagem é pintada INTEIRA, sem transparência: dentro da curva fica a
    cor da caixa e fora fica a cor de fundo. Isso é de propósito — o
    `tkinter` não tem widget transparente, e o fundo de um `Label` preenche
    o quadrado todo; se a imagem tivesse "buracos", o buraco viraria a cor
    de fundo e o canto sairia como um QUADRADO preto em vez de uma curva.
    """
    if not TEM_PIL or Image is None:
        return None
    try:
        lado = max(2, int(raio)) * escala
        imagem = Image.new("RGBA", (lado, lado), _rgba(cor_dentro))
        pincel = imagem.load()
        fora = _rgba(cor_fora)
        for y in range(lado):
            for x in range(lado):
                if not _dentro_do_canto(x, y, lado, canto):
                    pincel[x, y] = fora
        return imagem.resize((int(raio), int(raio)), Image.LANCZOS)
    except Exception:
        return None


def _foto_canto(raio, cor_dentro, cor_fora, canto, escala=4):
    """A mesma imagem do canto, pronta para um `Label` do tkinter."""
    if not TEM_PIL or ImageTk is None:
        return None
    chave = (int(raio), cor_dentro, cor_fora, canto)
    if chave in _FOTOS_CANTO:
        return _FOTOS_CANTO[chave]
    imagem = _imagem_canto(raio, cor_dentro, cor_fora, canto, escala)
    if imagem is None:
        return None
    try:
        foto = ImageTk.PhotoImage(imagem)
    except Exception:
        return None
    _FOTOS_CANTO[chave] = foto
    return foto


def _foto_mic(cor_bolhao, tamanho=36):
    """Imagem do botao do microfone (bolha + microfone de lapis).

    Mesma técnica do botão de enviar: desenhado com o Pillow e reduzido,
    para a borda não ficar serrilhada. Sem Pillow, devolve None e o botão
    passa a ser desenhado no Canvas (funciona igual, só fica mais "grosseiro").
    """
    if not TEM_PIL or ImageTk is None:
        return None
    chave = (tuple(cor_bolhao), int(tamanho))
    if chave in _FOTOS_MIC:
        return _FOTOS_MIC[chave]
    try:
        n = int(tamanho)
        ss = n * 4
        imagem = Image.new("RGBA", (ss, ss), (0, 0, 0, 0))
        desenho = ImageDraw.Draw(imagem)
        f = ss / 36.0
        desenho.ellipse(
            [2 * f, 2 * f, 34 * f, 34 * f],
            fill=tuple(cor_bolhao) + (255,),
        )
        traco = tuple(COR_MIC_TRACO) + (255,)
        # a "cabeca" do microfone: uma capsula arredondada
        desenho.rounded_rectangle(
            [14.5 * f, 8 * f, 21.5 * f, 20 * f], radius=3.5 * f, fill=traco,
        )
        # o suporte: um arco em U, embaixo da cabeca
        espessura = max(1, int(round(1.6 * f)))
        desenho.arc(
            [10.5 * f, 13 * f, 25.5 * f, 25 * f],
            start=0, end=180, fill=traco, width=espessura,
        )
        # a base: uma haste e o pe
        desenho.line(
            [18 * f, 25 * f, 18 * f, 28 * f], fill=traco, width=espessura,
        )
        desenho.line(
            [14 * f, 28.5 * f, 22 * f, 28.5 * f], fill=traco, width=espessura,
        )
        foto = ImageTk.PhotoImage(imagem.resize((n, n), Image.LANCZOS))
    except Exception:
        return None
    _FOTOS_MIC[chave] = foto
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


def _nome_de_resposta(texto, maximo=48):
    """Sugere um nome de arquivo (.txt) a partir do começo da resposta.

    Pega a primeira linha que tenha conteúdo, tira aenumerateção, troca
    tudo que o Windows proíbe em nome de arquivo e corta em `maximo`
    caracteres (para o nome não ficar enorme na janela de salvar).
    """
    nome = ""
    for linha in str(texto or "").splitlines():
        limpa = linha.strip().lstrip("#*->•·-—").strip()
        # tira a numeração de lista ("1. ", "12) ") para o nome ficar limpo
        limpa = re.sub(r"^\d{1,2}[.)]\s*", "", limpa).strip()
        if limpa:
            nome = limpa
            break
    if not nome:
        return "resposta.txt"
    nome = re.sub(r'[\\/:*?"<>|\r\n\t]', "", nome)      # proibido no Windows
    nome = re.sub(r"\s+", " ", nome).strip()            # espaços repetidos
    nome = nome[:maximo].strip().rstrip(".,;:-— ")
    if not nome:
        return "resposta.txt"
    return nome + ".txt"


def _desenhar_salvar(pincel, s, cor, fundo_dentro, espessura=1):
    """Disquete (o ícone de salvar): quadrado com a fenda de cima e o rótulo."""
    dentro = fundo_dentro or (0, 0, 0, 0)
    # corpo do disquete
    pincel.rectangle(
        [3.5 * s, 3.5 * s, 18.5 * s, 18.5 * s], fill=dentro, outline=cor,
        width=espessura,
    )
    # a parte de cima que gira com o disquete
    pincel.rectangle(
        [8 * s, 3.5 * s, 14 * s, 9 * s], fill=dentro, outline=cor,
        width=espessura,
    )
    # o rótulo de baixo
    pincel.rectangle(
        [7 * s, 12.5 * s, 15 * s, 18.5 * s], outline=cor, width=espessura,
    )


def _desenhar_salvar_no_canvas(desenho, s, cor, fundo, dentro):
    """Versão do disquete direto no Canvas (usada quando não tem Pillow)."""
    desenho.create_rectangle(
        3.5 * s, 3.5 * s, 18.5 * s, 18.5 * s, fill=dentro, outline=cor,
        width=1,
    )
    desenho.create_rectangle(
        8 * s, 3.5 * s, 14 * s, 9 * s, fill=dentro, outline=cor, width=1,
    )
    desenho.create_rectangle(
        7 * s, 12.5 * s, 15 * s, 18.5 * s, outline=cor, width=1,
    )


def _icone_resposta(pai, comando, nome, desenhar, desenhar_no_canvas,
                    tamanho=19, cor=COR_TEXTO_3, cor_vivo=COR_TEXTO,
                    fundo_ativo=COR_BARRA):
    """Ícone discreto das respostas (copiar, salvar...).

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
        nome, n, cor, desenhar, fundo_dentro=COR_FUNDO,
    )
    ativo = _foto_de_simbolo(
        nome, n, cor_vivo, desenhar, fundo=fundo_ativo,
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
            desenhar_no_canvas(desenho, n / 22.0, cor_atual,
                                fundo_ativo if mouse_por_cima else COR_FUNDO,
                                fundo_ativo if mouse_por_cima else COR_FUNDO)
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


def _desenhar_copiar_no_canvas(desenho, s, cor, fundo, dentro):
    """As duas folhas do 'copiar' direto no Canvas (sem Pillow)."""
    desenho.create_rectangle(
        5.5 * s, 3.5 * s, 16.5 * s, 14.5 * s, outline=cor, width=1
    )
    desenho.create_rectangle(
        9.5 * s, 7.5 * s, 20 * s, 18.5 * s, fill=dentro, outline=cor, width=1,
    )


def _icone_copiar(pai, comando, tamanho=19, cor=COR_TEXTO_3,
                  cor_vivo=COR_TEXTO, fundo_ativo=COR_BARRA):
    """Ícone de 'copiar resposta' (duas folhas)."""
    return _icone_resposta(
        pai, comando, "copiar", _desenhar_copiar, _desenhar_copiar_no_canvas,
        tamanho=tamanho, cor=cor, cor_vivo=cor_vivo,
        fundo_ativo=fundo_ativo,
    )


def _icone_salvar(pai, comando, tamanho=19, cor=COR_TEXTO_3,
                  cor_vivo=COR_TEXTO, fundo_ativo=COR_BARRA):
    """Ícone de 'salvar resposta em arquivo' (disquete)."""
    return _icone_resposta(
        pai, comando, "salvar", _desenhar_salvar, _desenhar_salvar_no_canvas,
        tamanho=tamanho, cor=cor, cor_vivo=cor_vivo,
        fundo_ativo=fundo_ativo,
    )


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



def _tela_virtual():
    """Devolve (x, y, largura, altura) da tela toda, com TODOS os monitores.

    `winfo_screenwidth`/`winfo_screenheight` do tkinter devolvem só o
    monitor principal. Com dois monitores, um menu aberto no segundo
    aparecia na tela errada. Aqui usamos os "virtual screen metrics" do
    Windows, que juntam os dois.

    Devolve a tela principal se não conseguir perguntar ao Windows.
    """
    try:
        import ctypes
        # 76 = SM_XVIRTUALSCREEN, 77 = SM_YVIRTUALSCREEN,
        # 78 = SM_CXVIRTUALSCREEN, 79 = SM_CYVIRTUALSCREEN
        x = ctypes.windll.user32.GetSystemMetrics(76)
        y = ctypes.windll.user32.GetSystemMetrics(77)
        largura = ctypes.windll.user32.GetSystemMetrics(78)
        altura = ctypes.windll.user32.GetSystemMetrics(79)
        if largura > 0 and altura > 0:
            return int(x), int(y), int(largura), int(altura)
    except Exception:
        pass
    return 0, 0, 1920, 1080


_MONITORINFO = None


def _tela_do_widget(widget):
    """O monitor em que esta o widget: (x, y, largura, altura).

    Com dois monitores, o "centro da tela" e o centro do monitor onde a
    janela esta — e nao o centro da tela toda, que seria uma posicao
    sem sentido.
    """
    global _MONITORINFO
    try:
        import ctypes
        from ctypes import wintypes

        if _MONITORINFO is None:
            class MONITORINFO(ctypes.Structure):
                _fields_ = [
                    ("cbSize", wintypes.DWORD),
                    ("rcMonitor", wintypes.RECT),
                    ("rcWork", wintypes.RECT),
                    ("dwFlags", wintypes.DWORD),
                ]
            _MONITORINFO = MONITORINFO
        hwnd = ctypes.windll.user32.GetAncestor(widget.winfo_id(), 2)
        monitor = ctypes.windll.user32.MonitorFromWindow(hwnd, 2)
        info = _MONITORINFO()
        info.cbSize = ctypes.sizeof(info)
        ctypes.windll.user32.GetMonitorInfoW(monitor, ctypes.byref(info))
        r = info.rcMonitor
        return int(r.left), int(r.top), int(r.right - r.left), int(r.bottom - r.top)
    except Exception:
        return _tela_virtual()



def _centralizar_sobre(janela, pai):
    """Coloca `janela` no centro de `pai`, no monitor em que `pai` estiver.

    Pedido do Wolf: as janelas do programa tem que abrir JUNTO com ele,
    onde quer que ele esteja. Sem isto o Windows abre onde lhe aprouver
    (num computador com dois monitores, a janela de Configuracoes
    aparecia no monitor principal mesmo com o programa no segundo).

    Tambem impede que a janela saia da tela: se o programa estiver perto
    da borda do monitor, a janelinha e puxada para dentro em vez de
    sumir pela beira.
    """
    try:
        janela.update_idletasks()
        largura, altura = janela.winfo_width(), janela.winfo_height()
        if largura <= 1:
            largura = janela.winfo_reqwidth()
        if altura <= 1:
            altura = janela.winfo_reqheight()
        if largura <= 1 or altura <= 1:
            return False
        x = pai.winfo_rootx() + (pai.winfo_width() - largura) // 2
        y = pai.winfo_rooty() + (pai.winfo_height() - altura) // 2
        mx, my, mw, mh = _tela_do_widget(pai)
        x = max(mx, min(x, mx + mw - largura))
        y = max(my, min(y, my + mh - altura))
        janela.geometry("+%d+%d" % (x, y))
        return True
    except Exception:
        return False


def _deixar_dialogo_do_sistema_escuro(raiz, segundos=10):
    """Tenta deixar escura a janela de escolher arquivo do Windows.

    A janela de "Salvar como..." é do próprio Windows e o tkinter não
    deixa trocar as cores dela. O que dá para fazer é pedir ao Windows que
    a desenhe no modo escuro, setando o tema da janela depois que ela
    abre. Se a sua versão do Windows não aceitar, a janela aparece clara
    mesmo assim (o programa continua funcionando).

    Chame ANTES de abrir a janela de arquivos; ela cuida sozinha.
    """
    try:
        import ctypes
        from ctypes import wintypes
    except Exception:
        return

    try:
        THEMING = ctypes.WinDLL("uxtheme")
    except Exception:
        THEMING = None

    estado = {"fim": time.time() + segundos, "vistas": set()}

    def todas_dialogos():
        achadas = []

        @ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
        def cada(hwnd, _l):
            buffer = ctypes.create_unicode_buffer(64)
            ctypes.windll.user32.GetClassNameW(hwnd, buffer, 64)
            if buffer.value == "#32770":          # classe das janelas do Win
                achadas.append(hwnd)
            return True

        ctypes.windll.user32.EnumWindows(cada, 0)
        return achadas

    def escurecer():
        if time.time() > estado["fim"]:
            return
        try:
            for hwnd in todas_dialogos():
                if hwnd in estado["vistas"]:
                    continue
                estado["vistas"].add(hwnd)
                if THEMING is not None:
                    # "DarkMode_Explorer" e o tema escuro das janelas do
                    # Explorer no Windows 10/11.
                    THEMING.SetWindowTheme(hwnd, "DarkMode_Explorer", None)
        except Exception:
            return
        try:
            raiz.after(250, escurecer)
        except Exception:
            pass

    try:
        raiz.after(150, escurecer)
    except Exception:
        pass


def _dialogo_escuro(pai, titulo, texto, botoes=("Ok",), destaque=0,
                     largura_texto=380, plain=False):
    """Janelinha de aviso no tema do programa (sem nada branco).

    Este é o ÚNICO jeito de mostrar aviso, pergunta ou confirmação. Não use
    `messagebox` nem `simpledialog` do tkinter: o Windows desenha aqueles
    com fundo branco e borda do sistema, e destoa do programa inteiro.

    `botoes` é uma lista de rótulos (o primeiro é o padrão). Devolve o
    rótulo do botão clicado, ou None se a pessoa fechou com Esc.
    `destaque` marca qual botão fica com a cor de destaque.
    """
    escolhido = {"valor": None}
    pop = tk.Toplevel(pai)
    pop.overrideredirect(True)
    pop.configure(bg=COR_PAINEL)
    janela = tk.Frame(pop, bg=COR_PAINEL)
    janela.pack(padx=1, pady=1)
    caixa = tk.Frame(janela, bg=COR_BARRA, highlightthickness=1,
                     highlightbackground=COR_BORDA)
    caixa.pack(fill="both")

    # cabecalho arrastavel
    topo = tk.Frame(caixa, bg=COR_BARRA)
    topo.pack(fill="x", padx=16, pady=(16, 6))
    rotulo = tk.Label(
        topo, text=titulo, bg=COR_BARRA, fg=COR_TEXTO,
        font=(FONTE, 11, "bold"), anchor="w", justify="left",
        wraplength=largura_texto,
    )
    rotulo.pack(fill="x")

    def _arrastar_inicio(_e):
        pop._drag = (_e.x_root, _e.y_root, pop.winfo_x(), pop.winfo_y())

    def _arrastar_mover(_e):
        d = getattr(pop, "_drag", None)
        if not d:
            return
        x0, y0, xa, ya = d
        pop.geometry("+%d+%d" % (xa + (_e.x_root - x0),
                                ya + (_e.y_root - y0)))

    def _arrastar_fim(_e):
        pop._drag = None

    for widget in (topo, rotulo):
        widget.bind("<Button-1>", _arrastar_inicio)
        widget.bind("<B1-Motion>", _arrastar_mover)
        widget.bind("<ButtonRelease-1>", _arrastar_fim)

    if texto:
        tk.Label(
            caixa, text=texto, bg=COR_BARRA, fg=COR_TEXTO_2,
            font=(FONTE, 9), wraplength=largura_texto, justify="left",
            anchor="w",
        ).pack(fill="x", padx=16, pady=(0, 12))

    def fechar(_e=None):
        pop.destroy()

    padrao = None
    if botoes:
        barra = tk.Frame(caixa, bg=COR_BARRA)
        barra.pack(fill="x", padx=16, pady=(0, 16))
        for indice, nome in enumerate(botoes):
            def clicar(qual=nome):
                escolhido["valor"] = qual
                pop.destroy()

            Botao(barra, nome, clicar,
                  destaque=(indice == destaque)).pack(
                      side="left", padx=(0, 8) if indice else 0)
        padrao = botoes[destaque if destaque < len(botoes) else 0]
    else:
        fechar()

    pop.bind("<Escape>", lambda _e: fechar())
    if padrao:
        def enter(_e):
            escolhido["valor"] = padrao
            pop.destroy()

        pop.bind("<Return>", enter)
    pop.update_idletasks()
    largura = pop.winfo_width()
    altura = pop.winfo_height()
    # Pedido do Wolf: a janelinha abre no centro do programa, no monitor
    # em que ele estiver (e nunca pela beira da tela).
    if not _centralizar_sobre(pop, pai):
        try:
            centro_x = pai.winfo_rootx() + (pai.winfo_width() - largura) // 2
            centro_y = pai.winfo_rooty() + (pai.winfo_height() - altura) // 2
            pop.geometry("+%d+%d" % (centro_x, centro_y))
        except Exception:
            pass
    if not plain:
        try:
            pop.grab_set()
            pai.wait_window(pop)
        except Exception:
            pass
    return escolhido["valor"]


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


def escurecer_hwnd(hwnd):
    """Deixa escura a barra de titulo de uma janela do Windows.

    Recebe o NUMERO da janela (o "hwnd"), e nao um widget: assim serve
    tanto para o tkinter quanto para a tela nova em HTML, que nao tem
    `winfo_id`. Devolve True se deu certo. Nunca levanta erro: no
    pior dos casos a barra fica clara e o programa continua funcionando.
    """
    if not hwnd:
        return False
    try:
        import ctypes

        ligado = ctypes.c_int(1)
        # 20 = Windows 11 / 10 novo; 19 = Windows 10 1809.
        for atributo in (20, 19):
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, atributo, ctypes.byref(ligado), ctypes.sizeof(ligado)
            )
        return True
    except Exception:
        return False


def escurecer_janela_por_titulo(titulo, tentativas=40, espera=0.25):
    """Acha a janela pelo titulo e escurece a barra dela.

    Isto existe por causa de um defeito: a tela nova (pywebview) NAO tem
    `update_idletasks` nem `winfo_id` (sao metodos do tkinter), entao
    chamar `ativar_barra_escura` nela levantava erro, o erro era engolido
    e a barra de titulo ficava BRANCA, destoando do resto da tela
    escura. Aqui a janela e' procurada pelo titulo entre todas as do
    Windows.

    A janela pode ainda nao existir no primeiro instante (o Windows cria
    ela demorado), por isso o `tentativas`: se nao achar agora, tenta
    de novo daqui a `espera` segundos, ate ~10 segundos no total.
    """
    alvo = (titulo or "").strip().lower()
    if not alvo:
        return False
    try:
        import ctypes

        usuario = ctypes.windll.user32
    except Exception:
        return False

    @ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
    def visitar(hwnd, _lparam):
        try:
            tamanho = usuario.GetWindowTextLengthW(hwnd)
            if tamanho:
                buffer = ctypes.create_unicode_buffer(tamanho + 1)
                usuario.GetWindowTextW(hwnd, buffer, tamanho + 1)
                if alvo in buffer.value.lower():
                    achadas.append(hwnd)
                    return False            # para de procurar
        except Exception:
            pass
        return True

    for _ in range(max(1, tentativas)):
        achadas = []
        try:
            usuario.EnumWindows(visitar, 0)
        except Exception:
            return False
        for hwnd in achadas:
            if escurecer_hwnd(hwnd):
                return True
        time.sleep(espera)
    return False


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
    """Sugestão clicável mostrada na tela de boas-vindas. Texto completo sempre visível."""

    def __init__(self, pai, rotulo, pergunta, comando, largura_max=520):
        super().__init__(pai, bg=COR_FUNDO, highlightthickness=0, bd=0)
        # Cria texto SEM limite de largura inicial - mostra tudo
        item = self.create_text(
            0, 0, text=rotulo, font=(FONTE, 10), fill=COR_TEXTO_2,
            anchor="nw", justify="left",
        )
        x0, y0, x1, y1 = self.bbox(item)
        self.move(item, 18 - x0, 11 - y0)
        largura, altura = (x1 - x0) + 36, (y1 - y0) + 22
        # Limita largura máxima se necessário
        if largura > largura_max:
            largura = largura_max
            # Recria texto com largura limitada
            self.delete(item)
            item = self.create_text(
                0, 0, text=rotulo, font=(FONTE, 10), fill=COR_TEXTO_2,
                width=largura_max - 36, anchor="nw", justify="left",
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
        # Se pai redimensionar, recalcula
        def _on_pai_resize(_e):
            self.after(10, lambda: self._recalcular_largura(pai, rotulo, largura_max))
        pai.bind("<Configure>", _on_pai_resize, add="+")

    def _recalcular_largura(self, pai, rotulo, largura_max):
        try:
            pw = pai.winfo_width()
            if pw <= 1:
                return
            # Recria com largura baseada no pai
            w_texto = max(200, min(largura_max - 72, pw - 72))
            self.delete("all")
            item = self.create_text(
                0, 0, text=rotulo, font=(FONTE, 10), fill=COR_TEXTO_2,
                width=w_texto, anchor="nw", justify="left",
            )
            x0, y0, x1, y1 = self.bbox(item)
            self.move(item, 18 - x0, 11 - y0)
            largura, altura = (x1 - x0) + 36, (y1 - y0) + 22
            if largura > largura_max:
                largura = largura_max
            self.configure(width=largura, height=altura)
            fundo = arredondado(
                self, 0, 0, largura, altura, 14, fill=COR_BARRA, outline=COR_BORDA
            )
            self.tag_lower(fundo)
        except Exception:
            pass


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


# ----------------------------------------------------------------------------
# Regras que as DUAS telas usam (a do tkinter e a nova, em HTML).
# Estas funcoes nao dependem de nenhuma tela, por isso a tela nova
# (app_web.py) aproveita exatamente a mesma regra em vez de reescrever.

def traduzir_erro(erro):
    """Mete um erro do Google/da web em portugues de gente.

    O mesmo erro acontece em telas diferentes e a pessoa nao pode ver
    "401 UNAUTHENTICATED". Aqui vira uma frase que diz o que fazer.
    """
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


def chave_reserva(cfg):
    """A segunda chave do Google, se o Wolf cadastrou uma."""
    return (cfg.get("api_key_reserva") or "").strip()


def chave_ativa(cfg, falhou_principal):
    """A chave que o programa deve usar agora.

    A troca vale so nesta sessao: se a principal voltar a funcionar, ela
    e usada de novo no proximo dia.
    """
    if falhou_principal and chave_reserva(cfg):
        return chave_reserva(cfg)
    return (cfg.get("api_key") or "").strip()


def tentar_com_reserva(chamar, cfg, estado):
    """Executa `chamar(chave)`. Se o Google recusar a chave principal,
    repete com a chave reserva (uma vez so).

    `estado` e um dicionario com a chave "falhou": se ficar True, o
    programa passa a usar a reserva. E o mesmo dicionario para a
    proxima chamada, para a troca durar a sessao toda.
    """
    for tentativa in range(2):
        chave = chave_ativa(cfg, bool(estado.get("falhou")))
        try:
            return chamar(chave)
        except Exception as erro:
            if tentativa:
                raise
            # so troca quando o erro e de chave mesmo (nao e cota, nem
            # internet) e so se existir uma reserva
            if (estado.get("falhou") or not chave_reserva(cfg)
                    or not _falha_de_chave(erro)):
                raise
            estado["falhou"] = True
    raise RuntimeError("não foi possível falar com a IA")


def fazer_backup_dados(destino=None, quantos=15):
    """Copia as conversas, a memoria e as chaves para um .zip.

    Devolve (caminho_do_zip, [nomes dos arquivos]). Levanta erro se nao
    der — quem chama mostra a frase na tela.

    O `4 - Fazer backup.bat` cuida do CODIGO; este cuida do que nao da
    para refazer. Guarda dentro da pasta "Backup Eye of Thundera" do OneDrive
    e apaga as copias com mais de `quantos`, para o computador nao
    encher.

    So LE e copia: nunca escreve nos arquivos do Wolf.
    """
    import zipfile

    if destino is None:
        destino = Path.home() / "OneDrive" / "Backup Pesquisa IA" / "dados"
    destino = Path(destino)
    destino.mkdir(parents=True, exist_ok=True)
    arquivos = sorted(x for x in PASTA_CONFIG.iterdir() if x.is_file())
    if not arquivos:
        raise RuntimeError(
            "Não achei os seus dados em %s. Nada foi copiado." % PASTA_CONFIG)
    carimbo = time.strftime("%Y-%m-%d_%H%M%S")
    alvo = destino / ("dados_%s.zip" % carimbo)
    with zipfile.ZipFile(alvo, "w", zipfile.ZIP_DEFLATED) as z:
        for arquivo in arquivos:
            z.write(arquivo, arquivo.name)
    velhos = sorted(destino.glob("dados_*.zip"), reverse=True)[quantos:]
    for velho in velhos:
        try:
            velho.unlink()
        except OSError:
            pass
    return alvo, [a.name for a in arquivos]


def registrar_erro(onde, erro):
    """Grava um erro no erro.log, sem nunca levantar erro ela mesma.

    Fica no nivel do modulo (e nao dentro do `main` do tkinter) para que
    a tela nova em HTML tambem possa usar: em 16/10/2026 o Wolf viu a tela
    fechar sem deixar rastro nenhum, porque a tela nova engolia tudo em
    silencio.
    """
    try:
        ARQUIVO_ERRO.parent.mkdir(parents=True, exist_ok=True)
        with ARQUIVO_ERRO.open("a", encoding="utf-8") as arquivo:
            arquivo.write(
                "\n===== %s | %s =====\n%s\n"
                % (time.strftime("%d/%m/%Y %H:%M:%S"), onde, erro)
            )
    except Exception:
        pass


class Aplicativo:
    def __init__(self, raiz):
        self.raiz = raiz
        self.cfg = carregar_config()
        self.historico = []
        self.mensagens = []
        self.fila = queue.Queue()
        self.ocupado = False
        # Microfone: None quando não está gravando.
        self.gravando = False
        self._gravador = None
        self._mic_id = None
        self._margem_rodape = 16
        # A chave principal do Google parou de ser recusada? Vira True e o
        # programa passa a usar a chave reserva (ver _tentar_com_reserva).
        self._falhou_principal = False
        self.animacao_id = None
        self.animacao_passo = 0
        self._pontos_digitando = []
        self._canvas_digitando = None
        self._telas_bolha = []
        # Quem quer saber de "cliques em qualquer lugar" (menus que fecham ao
        # clicar fora). Ver _registrar_clique_global.
        self._ouvintes_clique = []
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

        raiz.title("Eye of Thundera")
        self._definir_icone(raiz)
        raiz.geometry("1000x740")
        raiz.minsize(760, 560)
        raiz.configure(bg=COR_FUNDO)

        self._montar_tela()
        # Clique fora das bolhas desfaz a seleção de texto. Usa bind (e não
        # bind_all) de propósito: há trechos que desligam todos os atalhos
        # "bind_all" de clique e apagariam este sem querer.
        self.raiz.bind("<Button-1>", self._ao_clicar_fora, add="+")
        # Único bind_all de clique do programa. Os menus se cadastram na lista
        # (_registrar_clique_global) em vez de mexer em bind_all/unbind_all.
        self.raiz.bind_all("<Button-1>", self._despachar_clique, add="+")
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
            textos, text="Eye of Thundera", bg=COR_PAINEL, fg=COR_TEXTO,
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
        self.raiz.bind("<Control-m>", lambda _e: self._alternar_mic())
        self.raiz.bind("<Control-s>", lambda _e: self._salvar_ultima())

    def _montar_rodape(self):
        rodape = tk.Frame(self.principal, bg=COR_FUNDO)
        rodape.pack(fill="x", padx=16, pady=(8, 6))

        caixa = tk.Frame(
            rodape, bg=COR_BARRA, highlightthickness=0,
        )
        caixa.pack(fill="x")
        self.caixa_texto = caixa
        self._cantos_ativo = {}
        caixa.bind("<Configure>", lambda _e: self._cantos_da_caixa())
        self.raiz.bind("<Configure>", lambda _e: (
            self._cantos_da_caixa(), self._alinhar_rodape()))

        linha_modo = tk.Frame(rodape, bg=COR_FUNDO)
        linha_modo.pack(fill="x", pady=(6, 0))
        self.linha_modo = linha_modo
        self.rotulo_modo_web = tk.Label(
            linha_modo, text="", bg=COR_FUNDO, fg=COR_TEXTO_3,
            font=(FONTE, 9), cursor="hand2",
        )
        self.rotulo_modo_web.pack(side="left")
        self.rotulo_modo_web.bind(
            "<Button-1>", lambda _e: self._alternar_modo_web())
        tk.Label(
            linha_modo, text="Enter envia, Shift+Enter quebra a linha",
            bg=COR_FUNDO, fg=COR_TEXTO_3, font=(FONTE, 9),
        ).pack(side="right")
        self._atualizar_rotulo_modo_web()

        self.entrada = tk.Text(
            caixa, height=1, wrap="word", font=(FONTE, 11),
            bg=COR_BARRA, fg=COR_TEXTO, insertbackground=COR_ACCENT,
            relief="flat", borderwidth=0, padx=14, pady=11,
            # undo=True liga o historico do Ctrl+Z / Ctrl+Y (o Tk deixa
            # desligado por padrao).
            undo=True, autoseparators=True, maxundo=-1,
        )
        # Texto de apoio dentro da caixa: some assim que a pessoa digita.
        # Ele fica POR CIMA da caixa, então precisa repassar os cliques
        # para ela — senão, com a caixa vazia, o clique do mouse não
        # focava a caixa e o botão direito não abria o menu.
        self.rotulo_apoio = tk.Label(
            caixa, text="Pergunte qualquer coisa...", bg=COR_BARRA,
            fg=COR_TEXTO_3, font=(FONTE, 11),
        )
        self.rotulo_apoio.place(x=15, y=11)
        self.rotulo_apoio.bind("<Button-1>", self._clique_no_apoio)
        self.rotulo_apoio.bind("<Button-3>", self._menu_no_apoio)
        self.entrada.bind("<FocusIn>", lambda _e: self._atualizar_apoio())
        self.entrada.bind("<FocusOut>", lambda _e: self._atualizar_apoio())
        self.botao_enviar = tk.Canvas(
            caixa, width=36, height=36, bg=COR_BARRA,
            highlightthickness=0, bd=0, cursor="hand2",
        )
        self._desenhar_enviar(COR_ENVIAR)
        # pacote botao ANTES da entrada, assim o Tk reserva espaço para ele
        # e não o encolhe quando a janela encurta ao mínimo
        # O padx da direita do enviar é do tamanho do canto arredondado: se
        # for menor, a tampinha do canto passa por cima do botão.
        self.botao_enviar.pack(side="right", padx=(0, RAIO_CANTO), pady=7)
        self.botao_mic = tk.Canvas(
            caixa, width=36, height=36, bg=COR_BARRA,
            highlightthickness=0, bd=0, cursor="hand2",
        )
        self._desenhar_mic(COR_MIC)
        # Mesmo truque do enviar: o pacote ANTES da entrada, para o Tk
        # reservar a largura dele e nao encolher a caixa ao encolher.
        self.botao_mic.pack(side="right", padx=(0, 4), pady=7)
        self.entrada.pack(side="left", fill="both", expand=True)
        self._cantos_da_caixa()
        self._alinhar_rodape()
        self._atualizar_apoio()

        self.botao_mic.bind("<Enter>", lambda e: self._desenhar_mic(
            COR_MIC_GRAVANDO_HOVER if self.gravando else COR_MIC_HOVER))
        self.botao_mic.bind("<Leave>", lambda e: self._desenhar_mic(
            COR_MIC_GRAVANDO if self.gravando else COR_MIC))
        self.botao_mic.bind("<Button-1>", lambda e: self._alternar_mic())
        self.botao_mic.bind("<Configure>", lambda e: self._desenhar_mic(
            COR_MIC_GRAVANDO if self.gravando else COR_MIC))

        self.entrada.bind("<Return>", self._ao_enter)
        self.entrada.bind("<KeyRelease>", self._ao_digitar)
        self.entrada.bind("<Button-3>", self._menu_ortografia)
        # Atalhos de edição que o Windows espera dentro de uma caixa de
        # texto: selecionar tudo, desfazer e refazer.
        self.entrada.bind("<Control-a>", self._selecionar_tudo)
        self.entrada.bind("<Control-A>", self._selecionar_tudo)
        self.entrada.bind("<Control-z>", lambda e: self._desfazer(e, False))
        self.entrada.bind("<Control-Z>", lambda e: self._desfazer(e, False))
        self.entrada.bind("<Control-y>", lambda e: self._desfazer(e, True))
        self.entrada.bind("<Control-Y>", lambda e: self._desfazer(e, True))
        self.entrada.bind("<<Paste>>", self._depois_de_colar)
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

    def _texto_modo_web(self):
        """Texto do botão que escolhe quando pesquisar na web."""
        return {
            "auto": "Web: automática",
            "sempre": "Web: sempre",
            "nunca": "Web: nunca",
        }.get(self.cfg.get("modo_pesquisa", "auto"), "Web: automática")

    def _atualizar_rotulo_modo_web(self):
        try:
            self.rotulo_modo_web.configure(text=self._texto_modo_web())
        except Exception:
            pass

    def _alternar_modo_web(self):
        """Alterna automática -> sempre -> nunca e salva a escolha."""
        ordem = ["auto", "sempre", "nunca"]
        atual = self.cfg.get("modo_pesquisa", "auto")
        proximo = ordem[(ordem.index(atual) + 1) % len(ordem)] \
            if atual in ordem else "auto"
        self.cfg["modo_pesquisa"] = proximo
        try:
            salvar_config(self.cfg)
        except Exception:
            pass
        self._atualizar_rotulo_modo_web()

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

    # -- chave de API: principal, reserva e troca automatica ----------------

    def _chave_reserva(self):
        return chave_reserva(self.cfg)

    def _chave_ativa(self):
        """A chave que o programa deve usar agora."""
        return chave_ativa(self.cfg, self._falhou_principal)

    def _usar_reserva(self, erro):
        """O Google recusou a chave: tem outra para tentar?

        Devolve True quando o programa deve repetir a chamada com a chave
        reserva. A troca vale só nesta sessão (se a principal voltar a
        funcionar, ela é usada de novo no próximo dia).
        """
        if self._falhou_principal:
            return False                    # ja estamos na reserva
        if not self._chave_reserva():
            return False                    # nao ha reserva: avisa o usuario
        if not _falha_de_chave(erro):
            return False                    # e outro erro (cota, internet)
        self._falhou_principal = True
        try:
            self._definir_status(
                "A chave principal do Google parou de valer. Estou usando a "
                "chave reserva.", COR_OK)
        except Exception:
            pass
        return True

    def _tentar_com_reserva(self, chamar):
        """Executa `chamar(chave)`. Se o Google recusar a chave principal,
        repete com a chave reserva (uma vez só). A regra mora em
        `tentar_com_reserva`, compartilhada com a tela nova (app_web.py),
        para as duas telas trocarem de chave do mesmo jeito."""
        estado = {"falhou": self._falhou_principal}
        try:
            return tentar_com_reserva(chamar, self.cfg, estado)
        finally:
            self._falhou_principal = bool(estado["falhou"])

    def _aviso_chave_morta(self, erro):
        """A chave principal morreu e não há reserva: mostra a janelinha
        explicando, com um botão que abre a página do Google."""
        self._definir_ocupado(False)
        try:
            self._definir_status("", COR_TEXTO_3)
        except Exception:
            pass
        self.fila.put(("chave_ruim", self._traduzir_erro(erro)))

    # -- microfone: gravar e transcrever ------------------------------------

    def _desenhar_mic(self, cor):
        """Desenha o botao do microfone (mesma arte do botao de enviar)."""
        if (getattr(self, "_cor_mic_atual", None) == cor
                and self.botao_mic.find_all()):
            return
        self._cor_mic_atual = cor

        foto = _foto_mic(cor)
        if foto is not None:
            self._foto_mic_atual = foto
            item = getattr(self, "_item_mic", None)
            if item is not None:
                try:
                    self.botao_mic.itemconfigure(item, image=foto)
                    return
                except tk.TclError:
                    pass
            self.botao_mic.delete("all")
            self._item_mic = self.botao_mic.create_image(18, 18, image=foto)
            return

        # Sem Pillow: desenha direto no Canvas (fica serrilhado, mas funciona)
        self.botao_mic.delete("all")
        self._item_mic = None
        traco = "#%02x%02x%02x" % COR_MIC_TRACO
        self.botao_mic.create_oval(2, 2, 34, 34, fill="#%02x%02x%02x" % cor,
                                   outline="")
        self.botao_mic.create_line(18, 8, 18, 20, fill=traco, width=3)
        self.botao_mic.create_arc(11, 13, 25, 25, start=0, extent=180,
                                  style="arc", outline=traco, width=2)
        self.botao_mic.create_line(18, 25, 18, 28, fill=traco, width=2)
        self.botao_mic.create_line(14, 28, 22, 28, fill=traco, width=2)

    def _parar_pulsar_mic(self):
        """Cancela a animação de pulsar do botão (usada ao parar de gravar)."""
        if self._mic_id is not None:
            try:
                self.raiz.after_cancel(self._mic_id)
            except Exception:
                pass
            self._mic_id = None

    def _pulsar_mic(self):
        """Faz a bolha do microfone piscar devagar enquanto grava."""
        self._mic_id = None
        if not self.gravando:
            return
        atual = getattr(self, "_cor_mic_atual", None)
        if atual == COR_MIC_GRAVANDO:
            self._desenhar_mic(COR_MIC_GRAVANDO_HOVER)
        else:
            self._desenhar_mic(COR_MIC_GRAVANDO)
        self._mic_id = self.raiz.after(700, self._pulsar_mic)

    def _alternar_mic(self):
        """Um clique começa a gravar; o clique seguinte para e transcreve."""
        if self.ocupado:
            return
        if self.gravando:
            self._parar_gravacao()
        else:
            self._comecar_gravacao()

    def _comecar_gravacao(self):
        """Liga o microfone. Avisa em português qualquer problema."""
        if not voz.TEM_SOM:
            self._definir_status(
                "Este programa foi montado sem a biblioteca de som. Rode "
                "'1 - Instalar.bat' de novo para o microfone funcionar.",
                COR_ERRO_TX,
            )
            return
        if not voz.microfone_disponivel():
            self._definir_status(
                "Não achei nenhum microfone ligado neste computador.",
                COR_ERRO_TX,
            )
            return
        chave = self.cfg.get("api_key", "").strip()
        if not chave:
            self._definir_status(
                "Cole a sua chave de API antes de falar a pergunta.",
                COR_ERRO_TX,
            )
            self._abrir_config()
            return

        gravador = voz.Gravador()
        try:
            gravador.iniciar()
        except Exception as erro:
            self._definir_status(voz.microfone_erro(erro), COR_ERRO_TX)
            return

        self._gravador = gravador
        self.gravando = True
        self._desenhar_mic(COR_MIC_GRAVANDO)
        self.botao_mic.configure(cursor="arrow")
        self._pulsar_mic()
        self._definir_status(
            "Ouvindo... clique de novo no microfone (ou Ctrl+M) para parar.",
            COR_OK,
        )

    def _parar_gravacao(self):
        """Para de gravar e manda o áudio para a IA transcrever."""
        gravador = self._gravador
        self._gravador = None
        self.gravando = False
        self._parar_pulsar_mic()
        self._desenhar_mic(COR_MIC)
        self.botao_mic.configure(cursor="hand2")

        if gravador is None:
            self._definir_status("")
            return

        try:
            wav = gravador.parar()
        except Exception as erro:
            self._definir_status(voz.microfone_erro(erro), COR_ERRO_TX)
            return

        if not voz.wav_tem_som(wav):
            self._definir_status("Não ouvi nada. Tente de novo, mais perto "
                                 "do microfone.", COR_ERRO_TX)
            return

        self._definir_ocupado(True)
        self._definir_status("Ouvindo... transcrevendo o que você falou...")

        modelo = self.cfg.get("modelo", MODELO_PADRAO)
        modelos = [modelo] + [m for m in MODELOS_RESERVA if m != modelo]

        def tarefa():
            try:
                texto = self._tentar_com_reserva(
                    lambda chave: voz.transcrever(
                        _criar_cliente(chave), modelos, wav)
                )
                self.fila.put(("voz", texto))
            except Exception as erro:
                if _falha_de_chave(erro) and not self._chave_reserva():
                    self._definir_ocupado(False)
                    self.fila.put(("chave_ruim", self._traduzir_erro(erro)))
                else:
                    self.fila.put(("voz_erro", self._traduzir_erro(erro)))

        threading.Thread(target=tarefa, daemon=True).start()

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

    # A coluna da conversa fica centralizada e com largura maxima: em janela
    # larga o texto nao corre de ponta a ponta (o olho cansa menos).
    LARGURA_MAX_COLUNA = 820

    def _margem_da_coluna(self):
        """ quanto de branco sobra de cada lado da conversa."""
        try:
            largura = self.canvas.winfo_width()
        except Exception:
            largura = 0
        if largura <= 1:
            return 16
        return max(16, int((largura - self.LARGURA_MAX_COLUNA) / 2) + 16)

    def _alinhar_rodape(self):
        """Deixa a caixa de digitar com a mesma largura da conversa.

        Sem isso, numa janela larga o texto fica no meio mas a caixa de
        digitar continua cruzando a tela toda de ponta a ponta.
        """
        try:
            largura = self.principal.winfo_width()
            if largura <= 1:
                return
            margem = max(16, int((largura - self.LARGURA_MAX_COLUNA) / 2) + 16)
            self._margem_rodape = margem
            self.caixa_texto.pack_configure(padx=margem)
            self.linha_modo.pack_configure(padx=margem)
            if getattr(self, "_status_visivel", False):
                self.linha_status.pack_configure(padx=margem)
        except Exception:
            pass

    def _largura_bolha(self):
        margem = self._margem_da_coluna()
        largura = self.canvas.winfo_width() - 2 * margem
        if largura <= 1:
            largura = 780
        return max(240, min(700, largura - 40))

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
            self.linha_status.pack(fill="x",
                                   padx=getattr(self, "_margem_rodape", 18),
                                   pady=(0, 10))
        else:
            self.linha_status.pack_forget()

    def _evento_da_entrada(self, evento):
        """Repassa um clique feito no texto de apoio como se fosse na caixa.

        O texto de apoio ("Pergunte qualquer coisa...") é um Label por cima
        da caixa; sem esta tradução, o clique pararia nele e a caixa nem
        focaria, nem abriria o menu do botão direito.
        """
        try:
            dx = self.entrada.winfo_rootx() - self.rotulo_apoio.winfo_rootx()
            dy = self.entrada.winfo_rooty() - self.rotulo_apoio.winfo_rooty()
        except Exception:
            dx = dy = 0
        return type("Evento", (object,), {
            "x": evento.x + dx, "y": evento.y + dy,
            "x_root": evento.x_root, "y_root": evento.y_root,
            "state": getattr(evento, "state", 0),
        })()

    def _clique_no_apoio(self, evento):
        """Clicar no texto de apoio = clicar dentro da caixa de digitar."""
        self.entrada.focus_set()
        try:
            self.entrada.mark_set(
                "insert", "@%d,%d" % (evento.x, evento.y))
            self.entrada.see("insert")
        except Exception:
            pass
        return "break"

    def _menu_no_apoio(self, evento):
        """Botão direito no texto de apoio = botão direito na caixa."""
        self.entrada.focus_set()
        self._menu_ortografia(self._evento_da_entrada(evento))
        return "break"

    def _atualizar_apoio(self):
        """Mostra o texto de apoio ("Pergunte qualquer coisa...") só quando a
        caixa está vazia. Se a pessoa já escreveu (ou colou), ele some."""
        try:
            vazio = not self.entrada.get("1.0", "end-1c").strip()
            if vazio and not self.rotulo_apoio.winfo_ismapped():
                self.rotulo_apoio.place(x=15, y=11)
            elif not vazio and self.rotulo_apoio.winfo_ismapped():
                self.rotulo_apoio.place_forget()
        except Exception:
            pass

    def _cantos_da_caixa(self):
        """Desenha as quatro tampinhas que deixam a caixa arredondada.

        O tkinter não sabe arredondar um `tk.Text`, então a gente desenha
        quatro quadradinhos com o fundo do programa por cima dos cantos.
        Eles acompanham o tamanho da caixa quando a janela muda de tamanho.
        """
        try:
            caixa = self.caixa_texto
            largura = caixa.winfo_width()
            altura = caixa.winfo_height()
            if largura <= 1 or altura <= 1:
                return
            raio = RAIO_CANTO
            cantos = self._cantos_ativo
            for chave, canto in (("ne", "ne"), ("nw", "nw"),
                                 ("se", "se"), ("sw", "sw")):
                foto = _foto_canto(raio, COR_BARRA, COR_FUNDO, canto)
                if foto is None:
                    for etiqueta in cantos.values():
                        etiqueta.place_forget()
                    return
                etiqueta = cantos.get(chave)
                if etiqueta is None:
                    etiqueta = tk.Label(
                        caixa, image=foto, bg=COR_FUNDO, bd=0,
                        highlightthickness=0,
                    )
                    cantos[chave] = etiqueta
                else:
                    etiqueta.configure(image=foto)
                etiqueta._foto_canto = foto
                # Com o anchor, a tampinha JA fica com o canto no ponto
                # indicado; somar -raio aqui a empurrava 12 px para dentro
                # da caixa (e ela cobria o botão de enviar).
                if canto == "ne":
                    etiqueta.place(relx=1.0, y=0, anchor="ne")
                elif canto == "nw":
                    etiqueta.place(x=0, y=0, anchor="nw")
                elif canto == "se":
                    etiqueta.place(relx=1.0, rely=1.0, anchor="se")
                else:
                    etiqueta.place(x=0, rely=1.0, anchor="sw")
        except Exception:
            pass

    def _ajustar_altura(self, _e=None):
        self._atualizar_apoio()
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

    # -- edicao basica da caixa de digitar ---------------------------------

    def _selecionar_tudo(self, _evento=None):
        """Ctrl+A: seleciona tudo que esta escrito na caixa."""
        try:
            self.entrada.tag_add("sel", "1.0", "end-1c")
            self.entrada.mark_set("insert", "end-1c")
            self.entrada.see("end-1c")
        except Exception:
            pass
        return "break"

    def _desfazer(self, _evento=None, refazer=False):
        """Ctrl+Z desfaz e Ctrl+Y refaz, como no Windows."""
        try:
            if refazer:
                self.entrada.edit_redo()
            else:
                self.entrada.edit_undo()
        except Exception:
            pass
        self._ajustar_altura()
        self._agendar_correcao()
        return "break"

    def _depois_de_colar(self, evento=None):
        """Depois de colar, o texto de apoio tem que sumir e a caixa
        precisa crescer junto."""
        self.raiz.after_idle(self._ajustar_altura)
        self._agendar_correcao()
        return None

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

    def _sugestoes_no_ponto(self, x, y):
        """Sugestões de correção da palavra que está sob o cursor.

        Devolve uma lista vazia quando não há palavra errada ali (ou quando
        o corretor está desligado). Cada item é (palavra, início, fim), para
        o clique direito e para o `verificar.py` (que testa sem clicar).
        """
        if not self._corretor_ativo():
            return []
        corretor = self._obter_corretor()
        if not corretor:
            return []
        try:
            indice = self.entrada.index("@%d,%d" % (x, y))
            inicio = self.entrada.index("%s wordstart" % indice)
            fim = self.entrada.index("%s wordend" % indice)
        except Exception:
            return []
        palavra = self.entrada.get(inicio, fim).strip()
        # a decisão é do MOTOR (pesquisa_ia.sugerir_correcao), não deste
        # método: o programa novo usa a mesma função no botão direito, e
        # duas cópias dessa lógica iam divergir com o tempo.
        sugestoes = sugerir_correcao(palavra)
        return [(s, inicio, fim) for s in sugestoes]

    def _tem_selecao(self):
        try:
            return bool(self.entrada.tag_ranges("sel"))
        except Exception:
            return False

    def _menu_ortografia(self, evento):
        """Clique direito na caixa de digitar.

        Mostra as correções da palavra sob o cursor (quando houver) e
        sempre os comandos de edição: recortar, copiar, colar e selecionar
        tudo. O que não dá para usar naquele momento fica apagado.
        """
        sugestoes = self._sugestoes_no_ponto(evento.x, evento.y)
        # clicar com o botão direito também coloca o cursor onde foi clicado
        # (senão "Colar" entraria sempre no fim do texto).
        try:
            self.entrada.mark_set("insert", "@%d,%d" % (evento.x, evento.y))
        except Exception:
            pass
        tem_selecao = self._tem_selecao()
        try:
            tem_na_area = bool(self.entrada.clipboard_get())
        except Exception:
            tem_na_area = False

        # Recortar/Copiar só fazem sentido com algo selecionado; Colar só
        # com algo na área de transferência.
        comandos = [
            ("   Recortar", self._recortar, tem_selecao),
            ("   Copiar", self._copiar_selecionado, tem_selecao),
            ("   Colar", self._colar, tem_na_area),
            ("   Selecionar tudo", self._selecionar_tudo, True),
        ]

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

        def item(rotulo, comando=None, negrito=False, ativo=True):
            etiqueta = tk.Label(
                caixa, text=rotulo, bg=COR_BARRA,
                fg=COR_TEXTO if ativo else COR_TEXTO_3,
                font=(FONTE, 9, "bold" if negrito else "normal"),
                cursor="hand2" if ativo else "arrow",
                anchor="w", padx=16, pady=6,
            )
            etiqueta.pack(fill="x")
            if ativo:
                etiqueta.bind("<Enter>", lambda _e: etiqueta.configure(
                    bg=COR_BARRA_MAIS))
                etiqueta.bind("<Leave>", lambda _e: etiqueta.configure(
                    bg=COR_BARRA, fg=COR_TEXTO))
                etiqueta.bind("<Button-1>", lambda _e: comando())
            pop._itens.append(etiqueta)
            return etiqueta

        def separador():
            tk.Frame(caixa, bg=COR_BORDA, height=1).pack(fill="x", padx=8,
                                                          pady=2)

        # 1) as correções da palavra (só quando a palavra está mesmo errada)
        for sugestao, inicio, fim in sugestoes:
            item(
                "   " + sugestao,
                lambda s=sugestao, i=inicio, f=fim: (
                    self._trocar_palavra(i, f, s),
                    self._fechar_menu_ortografia(),
                ),
            )
        if sugestoes:
            item("   Ignorar", lambda: self._fechar_menu_ortografia())
            separador()

        # 2) os comandos de edição de sempre
        for rotulo, comando, ativo in comandos:
            item(rotulo, comando, ativo=ativo)

        self._menu_ortografia_atual = pop
        pop.update_idletasks()
        largura = pop.winfo_reqwidth()
        altura = pop.winfo_reqheight()
        x = evento.x_root
        y = evento.y_root + 4
        # Evita cair fora da tela. Usa a tela VIRTUAL (a união de todos os
        # monitores): com dois monitores, `winfo_screenwidth` devolve só a
        # largura do principal, e o menu ia parar na tela errada.
        tela_x, tela_y, tela_l, tela_a = _tela_virtual()
        if x + largura > tela_x + tela_l:
            x = tela_x + tela_l - largura - 8
        if y + altura > tela_y + tela_a:
            y = max(tela_y + 4, evento.y_root - altura - 4)
        if x < tela_x + 4:
            x = tela_x + 4
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
        self._registrar_clique_global(fora)
        pop.after(6000, self._fechar_menu_ortografia)

    def _recortar(self):
        """Ação "Recortar": apaga o selecionado depois de colocá-lo na área
        de transferência."""
        try:
            texto = self.entrada.get("sel.first", "sel.last")
        except Exception:
            texto = ""
        if texto:
            self._copiar_texto(texto)
            try:
                self.entrada.delete("sel.first", "sel.last")
            except Exception:
                pass
        self._fechar_menu_ortografia()
        self._ajustar_altura()
        self._agendar_correcao()

    def _copiar_selecionado(self):
        try:
            texto = self.entrada.get("sel.first", "sel.last")
        except Exception:
            texto = ""
        if texto:
            self._copiar_texto(texto)
        self._fechar_menu_ortografia()

    def _colar(self):
        try:
            texto = self.entrada.clipboard_get()
        except Exception:
            texto = ""
        if texto:
            try:
                self.entrada.delete("sel.first", "sel.last")
            except Exception:
                pass
            try:
                self.entrada.insert("insert", texto)
            except Exception:
                self.entrada.insert("end", texto)
        self._fechar_menu_ortografia()
        self._ajustar_altura()
        self._agendar_correcao()

    def _fechar_menu_ortografia(self):
        pop = getattr(self, "_menu_ortografia_atual", None)
        fora = getattr(pop, "_fora", None)
        if fora is not None:
            self._remover_clique_global(fora)
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

    def _salvar_resposta(self, texto, nome_sugerido=None):
        """Salva uma resposta num arquivo .txt e avisa onde ele ficou."""
        if not texto or not str(texto).strip():
            self._definir_status("Não tem resposta para salvar.", COR_ERRO_TX)
            return
        if nome_sugerido is None:
            nome_sugerido = _nome_de_resposta(texto)
        # A janela de arquivos é do Windows; pedimos para ela abrir escura.
        _deixar_dialogo_do_sistema_escuro(self.raiz)
        caminho = filedialog.asksaveasfilename(
            parent=self.raiz,
            title="Salvar resposta como...",
            initialfile=nome_sugerido,
            defaultextension=".txt",
            filetypes=[
                ("Arquivo de texto", "*.txt"),
                ("Todos os arquivos", "*.*"),
            ],
        )
        if not caminho:
            return                    # a pessoa cancelou: não é erro
        try:
            with open(caminho, "w", encoding="utf-8-sig") as arquivo:
                arquivo.write(str(texto).rstrip() + "\n")
        except Exception as erro:
            _dialogo_escuro(
                self.raiz, "Erro",
                "Não consegui salvar a resposta em arquivo: %s" % erro,
            )
            return
        self._definir_status("Resposta salva em: %s" % caminho, COR_OK)

    def _salvar_ultima(self):
        """Salva a última resposta em arquivo (Ctrl+S)."""
        for msg in reversed(self.mensagens):
            if msg["role"] == "model":
                self._salvar_resposta(msg["text"])
                return
        self._definir_status("Ainda não tem resposta para salvar.")

    # -- desenho das mensagens ---------------------------------------------

    def _renderizar(self):
        self._redim_id = None
        for filho in self.interno.winfo_children():
            filho.destroy()
        self._telas_bolha = []
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
        bloco.pack(fill="x", pady=(46, 24),
                   padx=max(24, self._largura_bolha() // 3))

        tk.Label(
            bloco, text="Olá!", bg=COR_FUNDO, fg=COR_TEXTO,
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


    def _remover_emojis(self, texto):
        """Remove todos emojis do texto (mantém acentos e cursor de digitação)."""
        if not texto:
            return ""
        # Remove apenas caracteres nas faixas de emoji Unicode (exclui acentos e cursor ▌)
        resultado = []
        for ch in texto:
            cp = ord(ch)
            # Verifica se é emoji (faixas oficiais de emoji, sem símbolos geométricos básicos)
            is_emoji = (
                (0x2600 <= cp <= 0x26FF) or   # Misc symbols (2600-26FF)
                (0x2700 <= cp <= 0x27BF) or   # Dingbats
                (0x1F300 <= cp <= 0x1F5FF) or # Misc symbols & pictographs
                (0x1F600 <= cp <= 0x1F64F) or # Emoticons
                (0x1F680 <= cp <= 0x1F6FF) or # Transport & map
                (0x1F900 <= cp <= 0x1F9FF) or # Supplemental symbols
                (0x1F1E0 <= cp <= 0x1F1FF) or # Flags
                (0x231A <= cp <= 0x231B) or   # Watch
                (0x23E9 <= cp <= 0x23EC) or   # Fast forward/rewind
                (0x23F0 <= cp <= 0x23F3) or   # Audio control
                (0x2B05 <= cp <= 0x2B07) or   # Arrows
                (0x2B50 <= cp <= 0x2B55) or   # Stars
                (0x3030 <= cp <= 0x3030) or   # Wavy dash
                (0x303D <= cp <= 0x303D) or   # Part alternation mark
                (0x3297 <= cp <= 0x3299) or   # Circled
                (0xFE0F <= cp <= 0xFE0F)      # Variation selector
            )
            if not is_emoji:
                resultado.append(ch)
        return "".join(resultado)

    def _limpar_selecoes(self):
        """Desmarca o texto selecionado em todas as bolhas do chat."""
        vivas = []
        for tela in getattr(self, "_telas_bolha", []):
            try:
                if tela.winfo_exists():
                    tela.select_clear()
                    vivas.append(tela)
            except Exception:
                pass
        self._telas_bolha = vivas

    def _despachar_clique(self, evento):
        """Avisa todos os menus abertos que houve um clique."""
        for funcao in list(self._ouvintes_clique):
            try:
                funcao(evento)
            except Exception:
                pass

    def _registrar_clique_global(self, funcao):
        """Liga 'funcao' a todo clique do programa (inclusive em popups).

        Devolve a própria função; guarde-a para chamar
        _remover_clique_global quando o menu fechar. NUNCA use
        unbind_all("<Button-1>"): isso apagaria o atalho de todos os menus.
        """
        self._ouvintes_clique.append(funcao)
        return funcao

    def _remover_clique_global(self, funcao):
        try:
            self._ouvintes_clique.remove(funcao)
        except ValueError:
            pass

    def _ao_clicar_fora(self, _evento):
        """Clique em qualquer lugar da janela (fora das bolhas) tira a seleção.

        As bolhas tratam o próprio clique e devolvem "break", então este
        método só roda para cliques em outras partes da tela.
        """
        self._limpar_selecoes()

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
        linha.pack(fill="x", padx=self._margem_da_coluna(), pady=6)

        coluna = tk.Frame(linha, bg=COR_FUNDO)
        largura = self._largura_bolha()
        tela = tk.Canvas(coluna, bg=COR_FUNDO, highlightthickness=0, bd=0)

        # Item de texto ÚNICO - seleção nativa caractere-a-caractere (sem emojis)
        texto_limpo = self._remover_emojis(texto)
        item = tela.create_text(
            0, 0, text=texto_limpo, font=(FONTE, 11), fill=cor_txt,
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

        # --- Seleção nativa + menu Copiar no botão direito ---
        # Guarda esta bolha na lista, para o clique "lá fora" conseguir
        # desmarcar a seleção de todas elas (ver _limpar_selecoes).
        self._telas_bolha.append(tela)

        def _on_click(event):
            tela.focus_set()
            # Todo clique novo começa desfazendo a seleção anterior, desta
            # bolha e das outras. (O Tk só MOVE o ponto de partida com
            # select_from; ele não apaga a seleção antiga sozinho.)
            self._limpar_selecoes()
            # Esta bolha devolve "break", então avisamos os menus abertos
            # à mão (senão clicar numa bolha não fecharia o menu Copiar).
            self._despachar_clique(event)
            try:
                # Verifica se o click foi sobre o item de texto
                items = tela.find_overlapping(event.x-1, event.y-1, event.x+1, event.y+1)
                text_items = [it for it in items if tela.type(it) == "text"]
                if item not in text_items:
                    return "break"
                # Inicia seleção nativa no item de texto
                tela.icursor(item, "@%d,%d" % (event.x, event.y))
                tela.select_from(item, "@%d,%d" % (event.x, event.y))
            except Exception:
                pass
            return "break"

        def _on_drag(event):
            # Estende seleção durante drag
            try:
                tela.select_to(item, "@%d,%d" % (event.x, event.y))
            except Exception:
                pass
            return "break"

        def _letra_de_palavra(caractere):
            return caractere.isalnum() or caractere == "_"

        def _on_duplo_clique(event):
            """Duplo clique: seleciona a palavra que está sob o mouse."""
            tela.focus_set()
            self._limpar_selecoes()
            self._despachar_clique(event)
            try:
                conteudo = tela.itemcget(item, "text")
                if not conteudo:
                    return "break"
                pos = int(tela.index(item, "@%d,%d" % (event.x, event.y)))
                pos = max(0, min(pos, len(conteudo) - 1))
                if conteudo[pos].isspace():
                    return "break"
                ini = fim = pos
                if _letra_de_palavra(conteudo[pos]):
                    while ini > 0 and _letra_de_palavra(conteudo[ini - 1]):
                        ini -= 1
                    while (fim < len(conteudo) - 1
                           and _letra_de_palavra(conteudo[fim + 1])):
                        fim += 1
                tela.select_from(item, ini)
                tela.select_to(item, fim)
            except Exception:
                pass
            return "break"

        def _on_triplo_clique(event):
            """Triplo clique: seleciona o texto inteiro da bolha."""
            tela.focus_set()
            self._limpar_selecoes()
            self._despachar_clique(event)
            try:
                conteudo = tela.itemcget(item, "text")
                if conteudo:
                    tela.select_from(item, 0)
                    tela.select_to(item, len(conteudo) - 1)
            except Exception:
                pass
            return "break"

        def _selecao_propria():
            """Texto selecionado NESTA bolha ('' se a seleção é de outra)."""
            try:
                if str(tela.select_item() or "") != str(item):
                    return ""
                return tela.selection_get() or ""
            except Exception:
                return ""

        def _show_copiar_menu(canvas, ex, ey):
            try:
                sel = canvas.selection_get()
            except Exception:
                return
            if not sel:
                return
            # Fecha menu anterior
            try:
                if hasattr(canvas, "_copiar_menu") and canvas._copiar_menu:
                    canvas._copiar_menu.destroy()
            except Exception:
                pass
            menu = tk.Toplevel(canvas)
            menu.overrideredirect(True)
            menu.attributes("-topmost", True)
            menu.configure(bg="#2d2d35", bd=1, highlightbackground="#444", highlightthickness=1)
            lbl = tk.Label(menu, text="Copiar", bg="#2d2d35", fg="#ececf1",
                          font=(FONTE, 9), padx=12, pady=6, cursor="hand2")
            lbl.pack()
            def _do_copy():
                try:
                    txt = canvas.selection_get()
                except Exception:
                    txt = ""
                if txt:
                    self._copiar_texto(txt)
                menu.destroy()
                canvas._copiar_menu = None
            lbl.bind("<Button-1>", lambda e: _do_copy())
            # Fecha ao clicar fora
            def _close(e):
                try:
                    if e.widget != lbl and e.widget != menu:
                        menu.destroy()
                        canvas._copiar_menu = None
                except Exception:
                    pass
            self._registrar_clique_global(_close)
            menu.bind(
                "<Destroy>",
                lambda e: self._remover_clique_global(_close)
                if e.widget is menu else None,
            )
            # Posiciona no mouse (coordenadas de tela)
            rx = canvas.winfo_rootx() + ex + 8
            ry = canvas.winfo_rooty() + ey + 8
            menu.geometry("+%d+%d" % (rx, ry))
            menu.focus_set()
            canvas._copiar_menu = menu

        def _on_right_click(event):
            try:
                bb = tela.bbox(item)
                if bb:
                    x1, y1, x2, y2 = bb
                    # Click fora da área do texto -> limpa seleção
                    if not (x1 <= event.x <= x2 and y1 <= event.y <= y2):
                        tela.selection_clear()
                        return "break"
                if _selecao_propria():
                    _show_copiar_menu(tela, event.x, event.y)
            except Exception:
                pass
            return "break"

        def _copiar_canvas(event):
            txt = _selecao_propria()
            if txt:
                self._copiar_texto(txt)
            return "break"

        tela.bind("<Button-1>", _on_click)
        tela.bind("<B1-Motion>", _on_drag)
        tela.bind("<Double-Button-1>", _on_duplo_clique)
        tela.bind("<Triple-Button-1>", _on_triplo_clique)
        tela.bind("<Button-3>", _on_right_click)
        tela.bind("<Control-c>", _copiar_canvas)

        if not usuario and autor != "erro":
            canto = tk.Frame(coluna, bg=COR_FUNDO)
            canto.pack(anchor="w", pady=(2, 0))
            icone = _icone_copiar(
                canto, lambda: self._copiar_texto(texto_completo)
            )
            icone.pack(side="left", padx=(2, 0))
            Dica(icone, "Copiar resposta")
            botao_salvar = _icone_salvar(
                canto, lambda: self._salvar_resposta(texto_completo)
            )
            botao_salvar.pack(side="left", padx=(2, 0))
            Dica(botao_salvar, "Salvar resposta em arquivo")

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
        px, py = 16, BALHA_RESPIRO
        # Remove emojis do texto
        texto_limpo = self._remover_emojis(texto)
        tela.itemconfigure(item, text=texto_limpo, width=ref["largura"])
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
        linha.pack(fill="x", padx=self._margem_da_coluna(), pady=6)
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
        linha.pack(fill="x", padx=self._margem_da_coluna(), pady=6)
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
        # A janela de arquivos é do Windows; pedimos para ela abrir escura.
        _deixar_dialogo_do_sistema_escuro(self.raiz)
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
            _dialogo_escuro(
                self.raiz, "Erro",
                "Não consegui salvar a imagem: %s" % erro,
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
        self.botao_mic.configure(
            cursor="arrow" if (ocupado or self.gravando) else "hand2")
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

        self._iniciar_digitando()
        self._definir_status("Pensando...")

        usar_contexto = bool(self.cfg.get("usar_contexto", True))
        modelo = self.cfg.get("modelo", MODELO_PADRAO)
        modo_cfg = self.cfg.get("modo_pesquisa", "auto")
        if modo_cfg not in ("auto", "sempre", "nunca"):
            modo_cfg = "auto"
        historico = list(self.historico)

        def avisar_progresso(mensagem):
            self.fila.put(("etapa", mensagem))

        def tarefa():
            try:
                # Pedido explícito ("lembra que..."): grava direto na
                # memória, sem gastar chamada de IA.
                try:
                    fato = roteador.fato_pedido(pergunta)
                    if fato:
                        _mesclar_memoria([fato])
                except Exception:
                    pass
                decisao = _decidir_modo(chave, pergunta, historico, modo_cfg)
                modo = decisao.get("modo", "amigo")
                consulta = decisao.get("consulta") or pergunta
                # Notícia explícita continua pesquisando, como antes.
                if _quer_noticias(pergunta):
                    modo = "pesquisa"
                    consulta = pergunta
                if modo == "amigo":
                    avisar_progresso("Conversando com você...")
                    texto, fontes, buscas, origem = self._tentar_com_reserva(
                        lambda chave: conversar(
                            chave, modelo, historico, pergunta, usar_contexto,
                            progresso=avisar_progresso, cfg=self.cfg,
                            id_atual=self._id_conversa,
                        )
                    )
                else:
                    avisar_progresso("Pesquisando na web...")
                    texto, fontes, buscas, origem = self._tentar_com_reserva(
                        lambda chave: perguntar(
                            chave, modelo, historico, pergunta, usar_contexto,
                            progresso=avisar_progresso, cfg=self.cfg,
                            id_atual=self._id_conversa, consulta=consulta,
                        )
                    )
                self.fila.put(("ok", pergunta, texto, fontes, buscas, origem))
            except Exception as erro:
                if _falha_de_chave(erro) and not self._chave_reserva():
                    self.fila.put(("chave_ruim", self._traduzir_erro(erro)))
                else:
                    self.fila.put(("erro", pergunta, self._traduzir_erro(erro)))

        threading.Thread(target=tarefa, daemon=True).start()

    def _traduzir_erro(self, erro):
        """Mete o erro em portugues. A regra esta em traduzir_erro, que
        a tela nova (app_web.py) tambem usa."""
        return traduzir_erro(erro)

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
        # A janela e um pouco maior que antes: o Wolf pediu uma folga maior
        # porque o texto das Configurações ficava espremido. Os textos
        # acompanham a largura (veja _acompanhar_largura).
        jan.geometry("760x800")
        jan.minsize(600, 620)
        jan.transient(self.raiz)
        # Pedido do Wolf: a janela de Configurações abre JUNTO com o
        # programa, no monitor em que ele estiver. Sem isto o Windows
        # escolhe o lugar, e num computador com dois monitores ela
        # aparecia no principal mesmo com o programa no segundo.
        jan.after(60, lambda: _centralizar_sobre(jan, self.raiz))
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
        corpo_id = tela.create_window((24, 0), window=corpo, anchor="nw")

        def _acertar_largura(_evento=None):
            # margem de 24 px dos dois lados, como a aba Memoria
            tela.itemconfigure(
                corpo_id, width=max(320, tela.winfo_width() - 48))

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

        # (o titulo "Chave da API do Google" ja aparece acima, em corpo
        # grande; aqui comeca direto o campo, senão o texto aparecia duas
        # vezes seguidas e parecia um erro)
        moldura = tk.Frame(
            corpo, bg=COR_BARRA, highlightthickness=1,
            highlightbackground=COR_BORDA,
        )
        moldura.pack(fill="x", pady=(14, 0))
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

        # ---- chave reserva (rede de segurança) ----
        tk.Label(
            corpo, text="Chave reserva (opcional)", bg=COR_FUNDO,
            fg=COR_TEXTO_2, font=(FONTE, 10, "bold"),
        ).pack(anchor="w", pady=(20, 6))
        tk.Label(
            corpo,
            text="Cole aqui uma segunda chave do Google. Se um dia a chave de "
                 "cima parar de valer (o Google às vezes recusa uma chave "
                 "do nada), o programa usa esta automaticamente e avisa que "
                 "trocou.",
            bg=COR_FUNDO, fg=COR_TEXTO_2, font=(FONTE, 9), wraplength=540,
            justify="left",
        ).pack(anchor="w")
        moldura_reserva = tk.Frame(
            corpo, bg=COR_BARRA, highlightthickness=1,
            highlightbackground=COR_BORDA,
        )
        moldura_reserva.pack(fill="x", pady=(8, 0))
        var_chave_reserva = tk.StringVar(
            value=self.cfg.get("api_key_reserva", ""))
        entrada_reserva = tk.Entry(
            moldura_reserva, textvariable=var_chave_reserva, show="•",
            font=(FONTE, 11), bg=COR_BARRA, fg=COR_TEXTO,
            insertbackground=COR_ACCENT, relief="flat", borderwidth=0,
        )
        entrada_reserva.pack(side="left", fill="x", expand=True, padx=12,
                             pady=10)
        var_mostrar_reserva = tk.BooleanVar(value=False)

        def alternar_reserva():
            entrada_reserva.configure(
                show="" if var_mostrar_reserva.get() else "•")

        tk.Checkbutton(
            corpo, text="mostrar a chave reserva",
            variable=var_mostrar_reserva, command=alternar_reserva,
            bg=COR_FUNDO, fg=COR_TEXTO_2, selectcolor=COR_BARRA,
            activebackground=COR_FUNDO, activeforeground=COR_TEXTO,
            font=(FONTE, 9), highlightthickness=0, bd=0,
        ).pack(anchor="w", pady=(6, 0))

        botoes = tk.Frame(corpo, bg=COR_FUNDO)
        botoes.pack(fill="x", pady=(14, 0))

        def salvar():
            self.cfg["api_key"] = var_chave.get().strip()
            self.cfg["api_key_reserva"] = var_chave_reserva.get().strip()
            # Se o Wolf trocou a chave na principal, a reserva de antes
            # deixa de fazer sentido como "reserva".
            self._falhou_principal = False
            self.cfg["usar_contexto"] = bool(self.var_contexto.get())
            self.cfg["corretor"] = bool(self.var_corretor.get())
            self.cfg["usar_plano_b"] = bool(self.var_plano_b.get())
            self.cfg["voz_enviar"] = bool(self.var_voz_enviar.get())
            for campo, variavel in vars_reserva.items():
                self.cfg[campo] = variavel.get().strip()
            try:
                salvar_config(self.cfg)
                self._atualizar_status_chave()
                self._checar_ortografia()
                _dialogo_escuro(
                    jan, "Salvo",
                    "As chaves foram salvas no seu computador.",
                )
            except Exception as erro:
                _dialogo_escuro(
                    jan, "Erro", "Não consegui salvar: %s" % erro,
                )

        def testar():
            chave = var_chave.get().strip()
            if not chave:
                _dialogo_escuro(
                    jan, "Falta a chave",
                    "Cole a chave antes de testar.",
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
                    _dialogo_escuro(
                        jan, "Tudo certo",
                        "A chave está funcionando! Já pode pesquisar.",
                    )
                else:
                    self._atualizar_status_chave()
                    _dialogo_escuro(jan, "Problema com a chave", msg)

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

        # ---- voz: microfone ----
        tk.Label(
            corpo, text="Voz (opcional)", bg=COR_FUNDO, fg=COR_TEXTO_2,
            font=(FONTE, 10, "bold"),
        ).pack(anchor="w", pady=(24, 6))
        tk.Label(
            corpo,
            text="Fale a pergunta usando o microfone (ao lado do botão de "
                 "enviar, ou Ctrl+M). O que você falar aparece escrito na "
                 "caixa para você conferir antes de enviar."
            + ("" if voz.microfone_disponivel() else
               "\n\nEste computador não está com microfone disponível, ou a "
               "biblioteca de som não está instalada."),
            bg=COR_FUNDO, fg=COR_TEXTO_2, font=(FONTE, 9),
            wraplength=540, justify="left",
        ).pack(anchor="w")

        self.var_voz_enviar = tk.BooleanVar(
            value=bool(self.cfg.get("voz_enviar", False)))
        tk.Checkbutton(
            corpo,
            text="Enviar sozinho depois de falar (sem conferir o texto)",
            variable=self.var_voz_enviar, bg=COR_FUNDO, fg=COR_TEXTO_2,
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
                    _dialogo_escuro(
                        jan, "Falta a chave",
                        "Cole a chave do %s antes de testar." % nome,
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
        self._preencher_aba_ajuda(quadros["ajuda"])

        # agora que o conteudo inteiro existe, liga a rolagem em tudo
        _ligar_todos(aba_chave)

        # E faz os textos de TODAS as abas quebrarem na largura da janela
        # (sem isso eles usavam larguras fixas e ficavam espremidos).
        _acompanhar_largura(jan)

        # A aba pedida só pode ser mostrada DEPOIS que as abas existem
        # (antes disso o `mostrar_aba` não acha nada, e a janela abriria
        # sempre na Memória, ignorando o pedido).
        mostrar_aba(aba if aba in dict(quadros) else "memoria")
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
        # Garante tamanho mínimo do canvas para scroll funcionar
        tela.configure(height=400)
        lista = tk.Frame(tela, bg=COR_FUNDO)
        lista_id = tela.create_window((0, 0), window=lista, anchor="nw")
        def _atualizar_scroll_memoria(_e=None):
            # Usa bbox do frame interno (lista) para scrollregion correta
            try:
                tela.configure(scrollregion=tela.bbox("all"))
            except Exception:
                pass
            try:
                tela.itemconfigure(lista_id, width=tela.winfo_width())
                tela.coords("empty", tela.winfo_width() // 2, tela.winfo_height() // 2)
            except Exception:
                pass

        lista.bind("<Configure>", _atualizar_scroll_memoria)
        tela.bind("<Configure>", _atualizar_scroll_memoria)
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

        def _ligar_memoria(w):
            """Liga a rolagem do mouse em TODOS os widgets de dentro.

            O Tk nao repassa o evento da roda para o pai: quem tem o
            binding e' o widget que esta debaixo do mouse. Por isso
            precisa ser ligado um por um, e PRECISA ser feito de novo
            sempre que a lista e' redesenhada: `desenhar()` destroi as
            linhas antigas e cria outras, que nasceram sem binding. Sem
            religar aqui, depois de apagar um item a rolagem da aba
            Memoria parava de funcionar.
            """
            try:
                w.bind("<MouseWheel>", _rolar_memoria)
            except Exception:
                pass
            for c in w.winfo_children():
                _ligar_memoria(c)

        def desenhar():
            try:
                desenhar_lista()
            finally:
                # sempre, mesmo no caminho que desenha "nada guardado"
                _ligar_memoria(moldura)

        def desenhar_lista():
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
            if _dialogo_escuro(
                janela, "Apagar a memória",
                "Apagar tudo o que a IA aprendeu sobre você?",
                botoes=("Apagar", "Cancelar"),
            ) != "Apagar":
                return
            esquecer_memoria()
            desenhar()

        botoes = tk.Frame(pai, bg=COR_FUNDO)
        botoes.pack(fill="x", padx=24, pady=(0, 10))
        Botao(botoes, "Apagar tudo", limpar).pack(side="left")

        desenhar()
        # A rolagem do mouse NAO e' ligada aqui: `_desenhar`/`desenhar`
        # ja ligam em tudo, a cada redesenho (ver _ligar_memoria).
        env["tempo"] = janela.after(3000, conferir)

    def _preencher_aba_ajuda(self, pai, ao_rolar=None):
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
            margem, text="Como usar o Eye of Thundera", bg=COR_FUNDO,
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
            "Chave reserva (rede de segurança)",
            "Chaves do Google às vezes param de funcionar sem aviso: o "
            "programa simplesmente deixa de receber respostas.\n\n"
            "Na aba Chave das Configurações tem um campo de chave reserva. "
            "Cole ali uma segunda chave (é só criar outra de graça na mesma "
            "página). Se um dia a chave principal for recusada, o programa "
            "usa a reserva sozinho e avisa embaixo da conversa:\n\n"
            "\"A chave principal do Google parou de valer. Estou usando a "
            "chave reserva.\"\n\n"
            "Se não houver chave reserva, aparece uma janelinha explicando e "
            "com um botão que abre a página do Google direto no navegador. "
            "Essa troca vale só enquanto o programa estiver aberto; no dia "
            "seguinte ele tenta a principal de novo (se ela voltou, volta "
            "a ser usada).",
        )
        bloco(
            "Falar em vez de digitar",
            "Tem um botão de microfone ao lado do botão de enviar. "
            "Clique nele para começar a gravar e clique de novo para parar "
            "(o atalho é Ctrl+M).\n\n"
            "Enquanto grava, o botão fica vermelho e o aviso embaixo da "
            "conversa diz que está ouvindo. A gravação para sozinha depois "
            "de 2 minutos.\n\n"
            "Depois de parar, o que você falou aparece escrito na caixa de "
            "digitar, para você conferir e corrigir antes de apertar Enter. "
            "Se preferir que envie sozinho, ligue a opção nas Configurações.\n\n"
            "Se o Windows reclamar do microfone, vá em Configurações > "
            "Privacidade e ative o acesso ao microfone para aplicativos de "
            "desktop.",
        )
        bloco(
            "Atalhos",
            "Enter envia a pergunta.\n"
            "Shift+Enter quebra a linha sem enviar.\n"
            "F5 começa uma conversa nova.\n"
            "Ctrl+B mostra ou esconde a barra da esquerda.\n"
            "Ctrl+M liga e desliga a gravação do microfone.\n"
            "Ctrl+A seleciona tudo o que está na caixa de digitar.\n"
            "Ctrl+Z desfaz e Ctrl+Y refaz.\n"
            "Ctrl+S salva a última resposta num arquivo de texto.",
        )
        bloco(
            "Cores e tamanho",
            "Numa janela muito larga o programa deixa as bordas em branco "
            "e segura a conversa numa faixa de 820 pixels, para o texto não "
            "ficar comprido demais de lado a lado. A caixa de digitar "
            "acompanha a mesma largura.\n\n"
            "A caixa de digitar mostra um texto de apoio cinza "
            "(\"Pergunte qualquer coisa...\") enquanto está vazia.\n\n"
            "Botão direito dentro da caixa de digitar mostra Recortar, "
            "Copiar, Colar e Selecionar tudo. Se a palavra em que você "
            "clicou estiver errada, as correções vêm em cima. O que não dá "
            "para usar naquele momento fica apagado.",
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
            if alvo is ancora:
                # Este e o MESMO clique que abriu a caixinha (ele ainda
                # sobe ate a janela). Sem isto ela fechava na hora.
                return
            if alvo is not None:
                atual = alvo
                while atual is not None:
                    if atual is pop:
                        return          # o clique foi dentro: deixa
                    atual = getattr(atual, "master", None)
            self._fechar_popup_conversa()

        self._fora_popup_conversa = self._registrar_clique_global(fora)
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
        fora = getattr(self, "_fora_popup_conversa", None)
        if fora is not None:
            self._remover_clique_global(fora)
            self._fora_popup_conversa = None
        pop = getattr(self, "_popup_conversa", None)
        if pop is not None:
            try:
                pop.destroy()
            except Exception:
                pass
            self._popup_conversa = None

    def _confirmar(self, titulo, texto, sim="Sim", nao="Não"):
        """Pergunta de confirmação no tema escuro (sem branco do Windows)."""
        resposta = _dialogo_escuro(
            self.raiz, titulo, texto, botoes=(sim, nao), destaque=0,
        )
        return resposta == sim

    def _janela_chave_ruim(self, texto):
        """Janelinha avisando que a chave do Google parou de valer.

        Tem um botão que abre a página da chave direto no navegador, para
        não obrigar o Wolf a procurar o endereço na memória.
        """
        try:
            self._fechar_menu_ortografia()
        except Exception:
            pass
        escolha = _dialogo_escuro(
            self.raiz, "A chave do Google parou de valer",
            texto + "\n\nEnquanto isso, nenhuma resposta vai aparecer — nem "
            "digitando, nem falando.",
            botoes=("Criar chave nova", "Colar chave nova"),
            destaque=0,
        )
        if escolha == "Criar chave nova":
            webbrowser.open(URL_CHAVE)
        elif escolha == "Colar chave nova":
            self._abrir_config("chave")

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
        # Se a pessoa estava falando quando apertou F5, a gravacao para
        # (o microfone nao pode ficar ligado em silencio para sempre).
        if self.gravando:
            self._parar_gravacao()
        self._definir_ocupado(False)
        self._renderizar()
        self._atualizar_status_chave()
        self.entrada.focus_set()
        if self.lista_conversas.winfo_ismapped():
            self._preencher_lista_conversas()

    def _guardar_e_aprender(self, pergunta, texto):
        """Salva a conversa e deixa a IA aprender sobre o usuario.

        Roda em segundo plano, sem mostrar nada na tela: o usuario nao
        precisa preencher nada e a IA nunca conta que guardou.
        """
        try:
            if getattr(self, "_id_conversa", None) is None:
                self._id_conversa = str(time.time())
            guardar_conversa(self._id_conversa, self.mensagens)
            # Atualiza lista de conversas se visível
            if self.lista_conversas.winfo_ismapped():
                self._preencher_lista_conversas()
        except Exception:
            pass
        if not self.cfg.get("aprender", True):
            return
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
            _dialogo_escuro(
                self.raiz, "Tudo certo",
                "A chave da API está funcionando. Pode pesquisar!",
            )
            return

        if tipo == "teste_erro":
            self._definir_ocupado(False)
            _dialogo_escuro(self.raiz, "Problema com a chave", item[1])
            return

        if tipo == "teste_reserva_ok":
            _, nome, texto = item
            self._definir_ocupado(False)
            self._definir_status("%s está funcionando." % nome, COR_OK)
            _dialogo_escuro(
                self.raiz, "Tudo certo",
                "O %s respondeu: %s\n\nO plano B já pode ser usado."
                % (nome, (texto or "OK")[:120]),
            )
            return

        if tipo == "teste_reserva_erro":
            _, nome, msg = item
            self._definir_ocupado(False)
            self._definir_status("")
            _dialogo_escuro(
                self.raiz, "Problema com o %s" % nome, msg,
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

        if tipo == "voz":
            # Texto falado: entra na caixa de digitar NA POSICAO DO CURSOR,
            # sem mandar sozinho (a pessoa ve antes e pode corrigir).
            self._definir_ocupado(False)
            texto = (item[1] or "").strip()
            if not texto:
                self._definir_status("Não consegui entender o áudio. Tente "
                                     "falar mais perto do microfone.",
                                     COR_ERRO_TX)
                return
            try:
                self.entrada.insert("insert", texto)
            except Exception:
                self.entrada.insert("end", texto)
            self._ajustar_altura()
            self._ao_digitar()
            self._definir_status("Pronto! Confira o texto e aperte Enter "
                                 "para enviar.", COR_OK)
            if self.cfg.get("voz_enviar", False):
                self.raiz.after(60, self._enviar)
            return

        if tipo == "voz_erro":
            self._definir_ocupado(False)
            self._definir_status(item[1] or "Não consegui transcrever o áudio.",
                                 COR_ERRO_TX)
            return

        if tipo == "chave_ruim":
            self._janela_chave_ruim(item[1])
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

    try:
        organizar_memoria()
    except Exception:
        pass

    raiz = tk.Tk()

    # No programa compilado (sem janela preta) qualquer erro ficaria
    # escondido. Aqui tudo que der errado e guardado no erro.log, para
    # poder ser lido e mandado para quem ajuda. A funcao `registrar_erro`
    # e' a do modulo (acima), compartilhada com a tela nova.
    def registrar_erro(onde, erro):
        globals()["registrar_erro"](onde, erro)

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
            _dialogo_escuro(
                raiz_erro, "Eye of Thundera - erro ao abrir",
                "O programa não conseguiu abrir.\n\n"
                "Detalhes foram salvos em:\n%s\n\n"
                "Últimas linhas:\n%s" % (ARQUIVO_ERRO, detalhes[-600:]),
            )
            raiz_erro.destroy()
        except Exception:
            print(detalhes)
        sys.exit(1)
