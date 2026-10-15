# -*- coding: utf-8 -*-
"""Memoria do Pesquisa IA: junta fatos SEM repetir (funcoes puras, sem tela).

Regras (tudo local, custa zero token):
 - fato repetido (mesmas palavras importantes) nao entra de novo;
 - fato parecido mas MAIS COMPLETO troca o antigo;
 - fato que CONTRADIZ o antigo ("passou a nao gostar") troca o antigo;
 - "lugares fixos": nome/apelido, cidade onde mora e idade tem UM lugar cada,
   e o mais novo vence (ex.: "chamado de Wolf" e "apelido Wolf" = 1 fato);
 - fato sobre OUTRA pessoa (irma, amigo, pet...) nunca vai para as gavetas.

Como usar no programa (ver PROXIMOS-PASSOS.md):
    novos, mudou = memoria.mesclar(atuais, fatos_novos)
    limpa, mudou = memoria.consolidar(lista_antiga)   # arruma o que ja existe
Para testar: `python memoria.py` (ou memoria.autoteste() no verificar.py).
"""

import re
import unicodedata

TAMANHO_MAXIMO = 200

_PARADAS = frozenset(
    "a o as os um uma uns umas de da do das dos em no na nos nas ao aos que "
    "e para por com se ser eh sao foi sempre muito mais usuario pessoa gosta "
    "gostar prefere preferir tem ter costuma quer".split()
)
_NEGATIVAS = frozenset("nao nunca odeia detesta evita sem jamais".split())

_TERCEIROS = re.compile(
    r"\b(irma|irmao|pai|mae|filho|filha|esposa|esposo|marido|namorado|"
    r"namorada|amigo|amiga|primo|prima|tio|tia|avo|cachorro|cachorra|gato|"
    r"gata|pet|chefe|colega)\b"
)
_GAVETAS = (
    ("nome", re.compile(
        r"\b(chamad[oa]|chamar|apelido|nick|nickname)\b"
        r"|\bnome (do )?(usuario|pessoa)\b")),
    ("mora", re.compile(r"\b(mora|moro|reside)\b")),
    ("idade", re.compile(
        r"\b(tem|completou|fez) \d{1,3} anos\b|\bidade\b|\bnasceu\b")),
)


def _sem_acento(texto):
    return "".join(
        c for c in unicodedata.normalize("NFKD", str(texto).lower())
        if not unicodedata.combining(c)
    )


def limpar(fato):
    texto = " ".join(str(fato).split()).lstrip("-*\u2022 ").strip()
    return texto[:TAMANHO_MAXIMO]


def _tokens(fato):
    saida = set()
    for p in re.findall(r"[a-z0-9]+", _sem_acento(fato)):
        if p in _PARADAS:
            continue
        if p in _NEGATIVAS:
            saida.add(p)
            continue
        if len(p) > 4 and p.endswith("s"):
            p = p[:-1]
        saida.add(p[:5] if len(p) > 5 else p)
    return saida


def _gaveta(fato):
    t = _sem_acento(fato)
    if _TERCEIROS.search(t):
        return None
    for nome, rx in _GAVETAS:
        if rx.search(t):
            return nome
    return None


def _relacao(velho, novo):
    """'diferente' | 'repetido' | 'melhor' | 'contradiz' (do ponto de vista
    do fato NOVO em relacao ao VELHO)."""
    ta, tb = _tokens(velho), _tokens(novo)
    na, nb = ta & _NEGATIVAS, tb & _NEGATIVAS
    a, b = ta - _NEGATIVAS, tb - _NEGATIVAS
    if not a or not b:
        return "repetido" if ta == tb else "diferente"
    if a == b:
        return "repetido" if na == nb else "contradiz"
    if min(len(a), len(b)) < 2:
        return "diferente"
    dentro = len(a & b)
    contem = dentro / min(len(a), len(b))
    jaccard = dentro / len(a | b)
    if na != nb:
        return "contradiz" if contem >= 0.8 else "diferente"
    if b < a:
        return "repetido"          # o novo e so um pedaco do que ja existe
    if a < b:
        return "melhor"            # o novo diz tudo o que o velho dizia e mais
    return "repetido" if jaccard >= 0.6 else "diferente"


def mesclar(atuais, novos):
    """Junta fatos novos aos atuais. Devolve (lista, mudou)."""
    original = list(atuais)
    lista = [limpar(f) for f in original if limpar(f)]
    for bruto in novos:
        fato = limpar(bruto)
        if len(fato) < 4:
            continue
        gaveta = _gaveta(fato)
        if gaveta:
            mesmos = [i for i, f in enumerate(lista) if _gaveta(f) == gaveta]
            if mesmos:
                if any(_tokens(lista[i]) == _tokens(fato) for i in mesmos):
                    continue
                lista[mesmos[0]] = fato
                for i in reversed(mesmos[1:]):
                    del lista[i]
                continue
        acao = None
        for i, f in enumerate(lista):
            rel = _relacao(f, fato)
            if rel == "repetido":
                acao = ("pula", i)
                break
            if rel in ("melhor", "contradiz"):
                acao = ("troca", i)
                break
        if acao is None:
            lista.append(fato)
        elif acao[0] == "troca":
            lista[acao[1]] = fato
    return lista, lista != original


def consolidar(lista):
    """Arruma uma memoria que ja existe (tira repetidos). (lista, mudou)."""
    limpos = [limpar(f) for f in lista if limpar(f)]
    novo, _ = mesclar([], limpos)
    return novo, novo != list(lista)


def autoteste():
    """Devolve a lista de problemas (vazia = tudo certo)."""
    erros = []

    def esperar(nome, obtido, esperado):
        if obtido != esperado:
            erros.append("%s: obtido %r, esperado %r" % (nome, obtido, esperado))

    esperar("apelido em outras palavras vira 1 so",
            mesclar(["Prefere ser chamado de Wolf"],
                    ["O apelido do usuario e Wolf"])[0],
            ["O apelido do usuario e Wolf"])
    esperar("3 jeitos de dizer o apelido viram 1",
            len(consolidar(["Prefere ser chamado de Wolf",
                            "Gosta de ser chamado de Wolf",
                            "Quer ser chamado de Wolf"])[0]), 1)
    esperar("gosto que virou desgosto troca o antigo",
            mesclar(["Gosta de pizza"], ["Odeia pizza"])[0], ["Odeia pizza"])
    esperar("negacao troca o antigo",
            mesclar(["Gosta de jogos de RPG"],
                    ["Nao gosta de jogos de RPG"])[0],
            ["Nao gosta de jogos de RPG"])
    esperar("fato mais completo troca o simples",
            mesclar(["Gosta de jogos de RPG"],
                    ["Gosta de jogos de RPG e cloud gaming"])[0],
            ["Gosta de jogos de RPG e cloud gaming"])
    esperar("fato mais simples nao entra",
            mesclar(["Gosta de jogos de RPG e cloud gaming"],
                    ["Gosta de jogos de RPG"])[0],
            ["Gosta de jogos de RPG e cloud gaming"])
    esperar("fatos diferentes ficam os dois",
            len(mesclar(["Gosta de RPG"], ["Joga cloud gaming"])[0]), 2)
    esperar("gostos parecidos mas diferentes ficam",
            len(mesclar(["Gosta de jogos de tiro"],
                        ["Gosta de jogos de RPG"])[0]), 2)
    esperar("onde mora: o mais novo vence",
            mesclar(["Mora no Sul do Brasil"],
                    ["Mora em Santa Maria"])[0], ["Mora em Santa Maria"])
    esperar("fato de outra pessoa nao some na gaveta do nome",
            len(mesclar(["A irma dele se chama Ana"],
                        ["Prefere ser chamado de Wolf"])[0]), 2)
    esperar("quantos anos de jogo nao e a idade",
            len(mesclar(["Tem 30 anos"], ["Joga ha 10 anos"])[0]), 2)
    esperar("repetido exato nao muda nada",
            mesclar(["Gosta de RPG"], ["gosta de rpg."])[1], False)
    esperar("fato curto demais e ignorado",
            mesclar([], ["ok"])[0], [])
    return erros


if __name__ == "__main__":
    problemas = autoteste()
    print("TUDO CERTO" if not problemas else "\n".join(problemas))
