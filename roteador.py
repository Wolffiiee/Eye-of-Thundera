# -*- coding: utf-8 -*-
"""Roteador: decide se a mensagem precisa de pesquisa na web ou é só papo.

Funções puras, só com a biblioteca padrão. Não importa `eye_of_thundera`
(de propósito, para dar para testar sem abrir a janela e sem internet).

- `regra_local(texto, modo)` responde rápido, sem IA: "pesquisa", "amigo"
  ou None (quando não tem certeza e deixa o modelo decidir).
- `decidir(texto, historico, chamar_modelo, modo)` tenta nesta ordem:
  regra local -> modelo (função recebida) -> heurística de reserva.
- `heuristica_pesquisa(texto)` só pesquisa com palavras de "agora".
- `fato_pedido(texto)` reconhece "lembra que..." e devolve o fato.
"""

import json
import re

# Cumprimento, agradecimento e risada: papo curto, sem interrogação.
_PAPO_CURTO = {
    "oi", "olá", "ola", "opa", "eai", "e ai", "opa!", "tchau", "valeu",
    "obrigado", "obrigada", "brigado", "tmj", "beleza", "tudo bem",
    "como vai", "boa", "bom dia", "boa tarde", "boa noite", "até mais",
    "ate mais", "kkk", "kkkk", "haha", "hehe", "rsrs", "rs",
}

# Começos que pedem pesquisa de forma explícita.
_PREFIXOS_PESQUISA = (
    "/web",
    "pesquise",
    "pesquisa",
    "pesquisar",
    "busque",
    "procure",
    "dá uma olhada na internet",
    "da uma olhada na internet",
)

# Começos que pedem para NÃO pesquisar.
_PREFIXOS_PAPO = (
    "/papo",
    "sem pesquisar",
    "não pesquise",
    "nao pesquise",
)

# Palavrinhas de ligação tiradas da consulta ("pesquise sobre X" -> "X").
_CONECTORES = {
    "sobre", "de", "do", "da", "dos", "das", "em", "no", "na", "nos",
    "nas", "um", "uma", "o", "a", "os", "as", "por", "favor",
}

# Palavras de "agora": fato atual ou que muda. Na dúvida, é papo.
_PALAVRAS_AGORA = (
    "hoje", "atual", "atualmente", "atualizado", "ultimo", "último",
    "ultima", "última", "noticia", "notícia", "preco", "preço",
    "cotacao", "cotação", "clima", "placar", "lancamento", "lançamento",
    "quanto custa", "onde comprar", "ano atual",
)


def _tirar_prefixo(texto):
    """Separa comando de pesquisa do resto. Devolve (achou, resto)."""
    baixo = (texto or "").strip().lower()
    for prefixo in _PREFIXOS_PESQUISA:
        if baixo == prefixo or baixo.startswith(prefixo + " ") or \
                baixo.startswith(prefixo + ":"):
            resto = texto.strip()[len(prefixo):].lstrip(" :").strip()
            palavras = resto.split()
            while palavras and palavras[0].lower() in _CONECTORES:
                palavras.pop(0)
            return True, " ".join(palavras)
    return False, (texto or "").strip()


def regra_local(texto, modo="auto"):
    """Resposta rápida sem IA: "pesquisa", "amigo" ou None (sem certeza)."""
    if modo == "sempre":
        return "pesquisa"
    if modo == "nunca":
        return "amigo"
    t = (texto or "").strip()
    baixo = t.lower()
    if not t:
        return "amigo"
    achou, _resto = _tirar_prefixo(t)
    if achou:
        return "pesquisa"
    for prefixo in _PREFIXOS_PAPO:
        if baixo.startswith(prefixo):
            return "amigo"
    if "sem pesquisar" in baixo or "não pesquise" in baixo \
            or "nao pesquise" in baixo:
        return "amigo"
    palavras = t.split()
    if "?" not in t and len(palavras) <= 3:
        nucleo = baixo.strip(" !.,;:")
        if nucleo in _PAPO_CURTO:
            return "amigo"
        for sinal in ("kkk", "haha", "hehe", "rsrs"):
            if sinal in baixo:
                return "amigo"
    return None


def heuristica_pesquisa(texto):
    """Reserva sem IA: pesquisa só com palavras de 'agora', senão é papo."""
    baixo = (texto or "").lower()
    for palavra in _PALAVRAS_AGORA:
        if palavra in baixo:
            return "pesquisa"
    return "amigo"


def prompt_roteador(texto, historico):
    """Monta o pedido para o modelo decidir (temperatura 0, só JSON)."""
    falas = []
    for turno in (historico or [])[-4:]:
        fala = (turno.get("text") or "").strip()[:300]
        if not fala:
            continue
        quem = "PESSOA" if turno.get("role") == "user" else "ASSISTENTE"
        falas.append("%s: %s" % (quem, fala))
    conversa = "\n".join(falas) if falas else "(conversa nova, sem histórico)"
    return (
        "Você decide se a mensagem precisa de pesquisa na web. "
        "Responda SÓ com JSON: "
        '{"pesquisar": true|false, "consulta": "...", "motivo": "..."}.\n'
        "\n"
        "PESQUISAR quando: fato atual ou que muda (notícia, preço, cotação, "
        "clima, placar, lançamento, horário, regra ou lei em vigor), coisa "
        "específica que o modelo pode não saber (produto, jogo, versão, "
        "pessoa, empresa), ou o usuário pede para pesquisar ou conferir.\n"
        "NÃO pesquisar: papo, opinião, desabafo, cumprimento, perguntas "
        "sobre a IA ou sobre o próprio usuário, conhecimento estável "
        "(história, ciência, conceitos, matemática, tradução, escrever ou "
        "ajustar texto, código), recomendação baseada nos gostos dele, "
        "continuação do assunto anterior.\n"
        'A "consulta" deve ser completa e curta, sem depender do histórico '
        '("e o euro?" vira "cotação do euro hoje").\n'
        "\n"
        "Conversa recente:\n%s\n\nMensagem: %s"
        % (conversa, (texto or "").strip()[:500])
    )


def _ler_json(texto):
    """Lê o JSON mesmo com cerca ```json ou texto em volta. Sem JSON: None."""
    t = (texto or "").strip()
    if not t:
        return None
    cercado = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", t, re.S)
    if cercado:
        t = cercado.group(1)
    else:
        inicio, fim = t.find("{"), t.rfind("}")
        if 0 <= inicio < fim:
            t = t[inicio:fim + 1]
    try:
        dado = json.loads(t)
    except Exception:
        return None
    return dado if isinstance(dado, dict) else None


def decidir(texto, historico, chamar_modelo, modo="auto"):
    """Escolhe entre pesquisa e papo. Nunca trava: sem modelo, usa a regra.

    Devolve {"modo": "pesquisa"|"amigo", "consulta": str,
    "origem": "regra"|"modelo"|"padrao"}.
    """
    if modo == "sempre":
        return {"modo": "pesquisa", "consulta": (texto or "").strip(),
                "origem": "regra"}
    if modo == "nunca":
        return {"modo": "amigo", "consulta": (texto or "").strip(),
                "origem": "regra"}
    regra = regra_local(texto, modo)
    if regra == "pesquisa":
        _achou, resto = _tirar_prefixo(texto)
        return {"modo": "pesquisa",
                "consulta": resto or (texto or "").strip(),
                "origem": "regra"}
    if regra == "amigo":
        return {"modo": "amigo", "consulta": (texto or "").strip(),
                "origem": "regra"}
    try:
        resposta = chamar_modelo(prompt_roteador(texto, historico))
    except Exception:
        resposta = None
    dado = _ler_json(resposta)
    if dado is not None:
        pesquisar = dado.get("pesquisar")
        if isinstance(pesquisar, str):
            pesquisar = pesquisar.strip().lower() in ("true", "sim", "1")
        if isinstance(pesquisar, bool):
            consulta = str(dado.get("consulta") or "").strip()
            if pesquisar and not consulta:
                consulta = (texto or "").strip()
            return {"modo": "pesquisa" if pesquisar else "amigo",
                    "consulta": consulta or (texto or "").strip(),
                    "origem": "modelo"}
    reserva = heuristica_pesquisa(texto)
    return {"modo": reserva, "consulta": (texto or "").strip(),
            "origem": "padrao"}


_PEDIDO_FATO = re.compile(
    r"(?i)\b(lembra(?:-se)?|lembre(?:-se)?|anota|anote|guarda|guarde|"
    r"n[aã]o\s+esque[çc]a)\b\s+(que|de)\s+(.+)$",
)


def fato_pedido(texto):
    """Reconhece 'lembra que...' e devolve o fato. Sem pedido: None."""
    encontro = _PEDIDO_FATO.search((texto or "").strip())
    if not encontro:
        return None
    fato = encontro.group(3).strip().strip(" .!").strip()
    if fato[:3].lower() == "eu ":
        fato = fato[3:].strip()
    return fato or None
