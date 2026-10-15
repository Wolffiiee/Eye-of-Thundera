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
# Respostas vazias do modelo quando nao ha fato novo. NAO sao informacao
# sobre o usuario e nunca podem virar "lembra do programa".
_SEM_INFORMACAO = frozenset(
    "nada nenhum nenhuma nao ha sem nada sem novidade n/a -".split()
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


def tem_informacao(fato):
    """Falso quando o 'fato' e so a resposta vazia do modelo ("NADA")."""
    return _sem_acento(fato).strip(" .-*_") not in _SEM_INFORMACAO


def juntar(a, b):
    """Junta dois fatos da MESMA gaveta sem perder nenhum dos dois.

    Devolve o texto junto, ou None quando nao cabe em TAMANHO_MAXIMO
    (nesse caso os dois ficam guardados separados, que e melhor do que
    cortar a ponta de um deles).
    """
    if _sem_acento(a) == _sem_acento(b):
        return a
    junto = "%s | %s" % (a, b)
    return junto if len(junto) <= TAMANHO_MAXIMO else None


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
    """Junta fatos novos aos atuais. Devolve (lista, mudou).

    REGRA DE OURO: nunca perder informacao. Se um fato sumir da lista, e
    porque o que ficou diz a mesma coisa (ou diz mais). Isso e conferido
    pelo autoteste().
    """
    original = list(atuais)
    lista = [f for f in (limpar(x) for x in original) if f and tem_informacao(f)]
    for bruto in novos:
        fato = limpar(bruto)
        if len(fato) < 4 or not tem_informacao(fato):
            continue
        gaveta = _gaveta(fato)
        if gaveta:
            mesmo = [i for i, f in enumerate(lista) if _gaveta(f) == gaveta]
            if mesmo:
                juntado = fato
                sobrando = []
                for i in mesmo:
                    cabem = juntar(lista[i], juntado)
                    if cabem is None:
                        # nao da para juntar sem cortar: os dois ficam
                        sobrando.append(lista[i])
                    else:
                        juntado = cabem
                for i in reversed(mesmo):
                    del lista[i]
                lista.extend(sobrando)
                lista.append(juntado)
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
    limpos = [f for f in (limpar(x) for x in lista) if f and tem_informacao(f)]
    novo, _ = mesclar([], limpos)
    return novo, novo != list(lista)


def _informacoes(fatos):
    """Todo o conteudo dos fatos, como um conjunto de palavras."""
    return set().union(*[_tokens(f) for f in fatos]) if fatos else set()


def autoteste():
    """Devolve a lista de problemas (vazia = tudo certo)."""
    erros = []

    def esperar(nome, obtido, esperado):
        if obtido != esperado:
            erros.append("%s: obtido %r, esperado %r" % (nome, obtido, esperado))

    # Apelido e nome andam juntos na mesma gaveta: o resultado tem que ser
    # UM fato (nao cinco) e tem que guardar as palavras dos dois.
    juntado = mesclar(["Prefere ser chamado de Wolf"],
                      ["O apelido do usuario e Wolf"])[0]
    esperar("apelido em outras palavras vira 1 so", len(juntado), 1)
    esperar("juntar nomes nao perde palavra",
            _tokens(juntado[0]) >= _tokens("Prefere ser chamado de Wolf"),
            True)
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
    # "Mora no Sul" e "Mora em Santa Maria": o novo nao apaga o velho
    # (o antigo e mais geral, e um dia pode ser o unico que vale).
    onde = mesclar(["Mora no Sul do Brasil"], ["Mora em Santa Maria"])[0]
    esperar("onde mora: fica um so fato", len(onde), 1)
    esperar("onde mora: nao perde a regiao",
            "Brasil" in onde[0], True)
    esperar("fato de outra pessoa nao some na gaveta do nome",
            len(mesclar(["A irma dele se chama Ana"],
                        ["Prefere ser chamado de Wolf"])[0]), 2)
    esperar("quantos anos de jogo nao e a idade",
            len(mesclar(["Tem 30 anos"], ["Joga ha 10 anos"])[0]), 2)
    esperar("repetido exato nao muda nada",
            mesclar(["Gosta de RPG"], ["gosta de rpg."])[1], False)
    esperar("fato curto demais e ignorado",
            mesclar([], ["ok"])[0], [])

    # --- o modelo respondendo "NADA" nao pode virar lembrança --------------
    esperar('resposta "NADA" do modelo e descartada',
            mesclar(["Gosta de RPG"], ["NADA"])[0], ["Gosta de RPG"])
    esperar('"NADA" dentro de uma memoria antiga e limpo',
            "NADA" in consolidar(["Gosta de RPG", "NADA"])[0], False)

    # --- REGRA DE OURO: organizar NUNCA pode perder informacao -------------
    # Antes de tidy-up, a memoria do Wolf guardava o nome verdadeiro E o
    # apelido em fatos separados. A versao antiga da gaveta trocava um pelo
    # outro e o nome "Igor" sumia para sempre. Este teste barra isso.
    antes = [
        "Nome: Igor (pode ser chamado de Wolf)",
        "Quer ser chamado pelo apelido Wolf",
        "Nome ou como quer ser chamado: Wolf",
        "Nome ou apelido: Wolf",
        "Fez 30 anos em 2 de outubro de 2026",
        "Idade: mais de 30 anos",
        "Mora em Santa Maria",
        "Natural de Santa Maria, Rio Grande do Sul",
        "Gosta de jogar videogame",
    ]
    depois, _ = consolidar(antes)
    perdido = _informacoes(antes) - _informacoes(depois)
    if perdido:
        erros.append(
            "organizar perdeu informacao: %s" % ", ".join(sorted(perdido)))
    # o mesmo vale quando chega fato novo (e nao so quando limpa a memoria)
    perdido2 = _informacoes(antes) - _informacoes(
        mesclar(antes, ["Prefere ser chamado de Jorge"])[0])
    if perdido2:
        erros.append(
            "mesclar perdeu informacao: %s" % ", ".join(sorted(perdido2)))
    if not any("Igor" in f for f in depois):
        erros.append("organizar esqueceu o nome verdadeiro (Igor)")
    if not any("2 de outubro" in f for f in depois):
        erros.append("organizar esqueceu a data de nascimento")
    if not any("Igor" in f and "Wolf" in f for f in depois):
        erros.append("o nome e o apelido deviam ficar juntos no mesmo fato")
    return erros


if __name__ == "__main__":
    problemas = autoteste()
    print("TUDO CERTO" if not problemas else "\n".join(problemas))
