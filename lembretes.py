"""Lembretes do Eye of Thundera: "me lembra amanhã às 9h de pagar a conta".

Tudo local e sem IA (ver PLANO-LEMBRETES.md). Este módulo só entende a frase,
guarda os lembretes num arquivo e diz quais já venceram. Quem mostra o aviso
na tela é a interface (web/app.js), perguntando de tempos em tempos à ponte.

Funções principais:
- responder(texto, agora, arquivo): se a frase é sobre lembretes, faz o que ela
  pede e devolve o texto da resposta; senão devolve None (aí vai para a IA).
- entender(texto, agora): só interpreta a frase (não grava nada).
- vencidos / concluir / adiar / apagar: o que a ponte usa.
"""
import json
import os
import re
import unicodedata
import uuid
from datetime import datetime, date, time, timedelta
from pathlib import Path

ARQUIVO = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "PesquisaIA" / "lembretes.json"

_DIAS_SEMANA = ["segunda", "terça", "quarta", "quinta", "sexta", "sábado", "domingo"]
_NUM_SEMANA = {"segunda": 0, "terca": 1, "quarta": 2, "quinta": 3,
               "sexta": 4, "sabado": 5, "domingo": 6}
_PADRAO_PERIODO = {"manha": 9, "tarde": 15, "noite": 20, "madrugada": 6}


def _sem_acento(s):
    """Minúsculas e sem acento, MANTENDO o mesmo tamanho (os índices batem)."""
    return "".join(unicodedata.normalize("NFD", c)[0] for c in str(s)).lower()


# --- armazenamento ----------------------------------------------------------

def _ler(arquivo=None):
    arquivo = Path(arquivo or ARQUIVO)
    try:
        dados = json.loads(arquivo.read_text(encoding="utf-8"))
    except Exception:
        return []
    if not isinstance(dados, list):
        return []
    itens = []
    for d in dados:
        if (isinstance(d, dict) and isinstance(d.get("id"), str)
                and isinstance(d.get("texto"), str)):
            try:
                datetime.fromisoformat(str(d.get("quando")))
            except Exception:
                continue
            itens.append({"id": d["id"], "texto": d["texto"],
                          "quando": str(d["quando"]), "feito": bool(d.get("feito"))})
    return itens


def _gravar(itens, arquivo=None):
    arquivo = Path(arquivo or ARQUIVO)
    arquivo.parent.mkdir(parents=True, exist_ok=True)
    tmp = arquivo.with_name(arquivo.name + ".tmp")
    tmp.write_text(json.dumps(itens, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, arquivo)


def criar(texto, quando, arquivo=None):
    itens = _ler(arquivo)
    item = {"id": uuid.uuid4().hex[:8], "texto": str(texto).strip(),
            "quando": quando.replace(microsecond=0).isoformat(), "feito": False}
    itens.append(item)
    _gravar(itens, arquivo)
    return item


def pendentes(arquivo=None):
    """Lembretes ainda não concluídos, do mais próximo ao mais distante."""
    return sorted((i for i in _ler(arquivo) if not i["feito"]),
                  key=lambda i: i["quando"])


def vencidos(agora=None, arquivo=None):
    """Pendentes cuja hora já chegou (continuam aqui até serem concluídos)."""
    agora = agora or datetime.now()
    return [i for i in pendentes(arquivo)
            if datetime.fromisoformat(i["quando"]) <= agora]


def concluir(id_, arquivo=None):
    itens = _ler(arquivo)
    achou = False
    for i in itens:
        if i["id"] == id_:
            i["feito"] = True
            achou = True
    if achou:
        _gravar(itens, arquivo)
    return achou


def adiar(id_, minutos=10, agora=None, arquivo=None):
    agora = agora or datetime.now()
    try:
        minutos = max(1, min(int(minutos), 7 * 24 * 60))
    except (TypeError, ValueError):
        minutos = 10
    itens = _ler(arquivo)
    achou = False
    for i in itens:
        if i["id"] == id_ and not i["feito"]:
            i["quando"] = (agora + timedelta(minutes=minutos)).replace(
                second=0, microsecond=0).isoformat()
            achou = True
    if achou:
        _gravar(itens, arquivo)
    return achou


def apagar(id_, arquivo=None):
    itens = _ler(arquivo)
    novos = [i for i in itens if i["id"] != id_]
    if len(novos) != len(itens):
        _gravar(novos, arquivo)
        return True
    return False


# --- entender a frase -------------------------------------------------------

_INTENCAO = re.compile(
    r"^\s*(?:por favor,?\s*)?(?:me\s+(?:lembra|lembre|lembrar|avisa|avise|avisar)"
    r"|lembra-me|lembre-me|avisa-me|lembrete)\b[\s:,-]*")
_LISTAR = re.compile(
    r"^\s*(?:meus\s+lembretes|(?:quais|ver|listar|mostrar?)\s+(?:(?:os|meus)\s+)*lembretes?)"
    r"\s*[?.!]*\s*$")
_CANCELAR = re.compile(
    r"^\s*(?:apagar|apaga|cancelar|cancela|remover|remove|excluir|exclui)\s+(?:o\s+)?"
    r"lembrete\s+(\d+)\s*[.!]*\s*$")

_REL = re.compile(r"\b(?:daqui\s+a|daqui|em)\s+(\d+|uma?|meia)\s*"
                  r"(minutos?|mins?|horas?|h|dias?)\b")
_HORA_AS = re.compile(
    r"\bas\s+(\d{1,2})(?::(\d{2})|\s*(?:h|hs|horas?)(?:\s*e?\s*(\d{2}))?)?"
    r"(?=\s*(?:da\s+(?:manha|tarde|noite|madrugada)|$|[,.;!?]|\s(?:de|pra|para|e|do|da|pro)\b))")
_HORA_H = re.compile(r"\b(\d{1,2})\s*(?:h|hs|horas?)(?:\s*e?\s*(\d{2}))?\b")
_HORA_DP = re.compile(r"\b(\d{1,2}):(\d{2})\b")
_HORA_PERIODO = re.compile(r"\b(\d{1,2})\s+(?=da\s+(?:manha|tarde|noite|madrugada)\b)")
_PERIODO = re.compile(r"\b(?:da|de|na|pela|a)\s+(manha|tarde|noite|madrugada)\b")
_DEPOIS_AMANHA = re.compile(r"\bdepois\s+de\s+amanha\b")
_AMANHA = re.compile(r"\bamanha\b")
_HOJE = re.compile(r"\bhoje\b")
_DMA = re.compile(r"\b(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?\b")
_DIA = re.compile(r"\bdia\s+(\d{1,2})\b(?!\s*/)")
_SEMANA = re.compile(r"\b(?:(?:na|no|proxim[oa]|essa|esta|este)\s+)?"
                     r"(segunda|terca|quarta|quinta|sexta|sabado|domingo)"
                     r"(?:\s*-?\s*feira)?\b")

_MSG_QUANDO = ("Não entendi quando devo te lembrar. Tente assim: "
               "me lembra amanhã às 9h de pagar a conta.")


def _hora_valida(h, m):
    return 0 <= h <= 23 and 0 <= m <= 59


def _limpar(bruto, cortes):
    """O texto do lembrete: a frase sem a parte de intenção e de horário."""
    tira = [False] * len(bruto)
    for a, b in cortes:
        for i in range(a, min(b, len(bruto))):
            tira[i] = True
    t = "".join(c for c, x in zip(bruto, tira) if not x)
    t = re.sub(r"\s+", " ", t).strip(" ,.;:-–—")
    for _ in range(3):
        t = re.sub(r"^(?:de|que|para|pra|disso)\s+", "", t, flags=re.I)
        t = re.sub(r"\s+(?:de|para|pra|as|às|a|em|no|na|e)$", "", t, flags=re.I)
        t = t.strip(" ,.;:-–—")
    return t


def _data_futura(candidata, agora, avanca):
    """Se a data/hora já passou, avança com `avanca` até ficar no futuro."""
    for _ in range(14):
        if candidata > agora:
            return candidata
        nova = avanca(candidata)
        if nova is None:
            return None
        candidata = nova
    return None


def _mes_seguinte(d, dia):
    """Mesmo `dia` no próximo mês em que ele existe (31 pula meses curtos)."""
    ano, mes = d.year, d.month
    for _ in range(14):
        mes += 1
        if mes > 12:
            mes, ano = 1, ano + 1
        try:
            return date(ano, mes, dia)
        except ValueError:
            continue
    return None


def entender(texto, agora=None):
    """Interpreta "me lembra ...". Devolve None, {"erro": ...} ou
    {"texto": ..., "quando": datetime}."""
    agora = (agora or datetime.now()).replace(second=0, microsecond=0)
    bruto = str(texto or "")
    n = _sem_acento(bruto)
    m = _INTENCAO.match(n)
    if not m:
        return None
    verbo_avisa = "avis" in m.group(0)
    cortes = [(0, m.end())]
    cur = list(n)

    def atual():
        return "".join(cur)

    def mascarar(a, b):
        cortes.append((a, b))
        for i in range(a, b):
            cur[i] = " "

    def sem_horario():
        # "me avisa quando X..." sem horario pode ser pergunta normal
        return None if verbo_avisa else {"erro": _MSG_QUANDO}

    # 1) "daqui a 30 minutos", "em 2 horas", "daqui a 2 dias"
    dias_a_frente = None
    mr = _REL.search(atual())
    if mr:
        qtd_txt, unid = mr.group(1), mr.group(2)
        qtd = int(qtd_txt) if qtd_txt.isdigit() else (1 if qtd_txt.startswith("um") else None)
        mascarar(mr.start(), mr.end())
        if unid.startswith("dia"):
            dias_a_frente = qtd if qtd is not None else 1
        else:
            if qtd_txt == "meia":
                delta = timedelta(minutes=30) if unid.startswith("hora") or unid == "h" else None
            elif unid.startswith("min"):
                delta = timedelta(minutes=qtd)
            else:
                delta = timedelta(hours=qtd)
            if delta is None or delta <= timedelta(0):
                return sem_horario()
            alvo = agora + delta
            return _resultado(bruto, cortes, alvo)

    # 2) horário
    hora = minuto = None
    for rx in (_HORA_AS, _HORA_H, _HORA_DP, _HORA_PERIODO):
        mt = rx.search(atual())
        if not mt:
            continue
        h = int(mt.group(1))
        mi = 0
        if rx in (_HORA_AS, _HORA_H):
            mi = int(mt.group(2) or (mt.group(3) if rx is _HORA_AS else None) or 0)
        elif rx is _HORA_DP:
            mi = int(mt.group(2))
        if _hora_valida(h, mi):
            hora, minuto = h, mi
            mascarar(mt.start(), mt.end())
            break

    # 3) período do dia ("da noite") e dia
    periodo = None
    mp = _PERIODO.search(atual())
    if mp:
        periodo = mp.group(1)
        mascarar(mp.start(), mp.end())
    if hora is not None and periodo in ("tarde", "noite") and hora < 12:
        hora += 12
    if hora is not None and periodo == "madrugada" and hora == 12:
        hora = 0

    data, tipo, arg = None, None, None
    if dias_a_frente is not None:
        data, tipo = agora.date() + timedelta(days=dias_a_frente), "fixo"
    else:
        achou = None
        for rx, t in ((_DEPOIS_AMANHA, "depois"), (_AMANHA, "amanha"), (_HOJE, "hoje"),
                      (_DMA, "dma"), (_DIA, "dia"), (_SEMANA, "semana")):
            mt = rx.search(atual())
            if mt:
                achou, tipo = mt, t
                break
        if achou is not None:
            if tipo == "depois":
                data = agora.date() + timedelta(days=2)
            elif tipo == "amanha":
                data = agora.date() + timedelta(days=1)
            elif tipo == "hoje":
                data = agora.date()
            elif tipo == "dma":
                dd, mm = int(achou.group(1)), int(achou.group(2))
                ano = achou.group(3)
                try:
                    if ano:
                        ano = int(ano) + (2000 if len(ano) <= 2 else 0)
                        data = date(ano, mm, dd)
                        arg = None
                    else:
                        data = date(agora.year, mm, dd)
                        arg = (dd, mm)
                except ValueError:
                    return {"erro": "Essa data não existe. " + _MSG_QUANDO}
            elif tipo == "dia":
                dd = int(achou.group(1))
                try:
                    data = date(agora.year, agora.month, dd)
                except ValueError:
                    data = _mes_seguinte(agora.date(), dd)
                    if data is None:
                        return {"erro": "Esse dia não existe. " + _MSG_QUANDO}
                arg = dd
            else:  # dia da semana
                alvo = _NUM_SEMANA[achou.group(1)]
                data = agora.date() + timedelta(days=(alvo - agora.weekday()) % 7)
            mascarar(achou.start(), achou.end())

    if data is None and hora is None and periodo is None:
        return sem_horario()

    if hora is None:
        hora, minuto = _PADRAO_PERIODO.get(periodo, 9), 0

    if data is None:
        data, tipo = agora.date(), "hoje_hora"

    alvo = datetime.combine(data, time(hora, minuto))
    if alvo <= agora:
        if tipo == "semana":
            alvo = _data_futura(alvo, agora, lambda c: c + timedelta(days=7))
        elif tipo == "dia":
            alvo = _data_futura(alvo, agora, lambda c: (
                lambda nd: datetime.combine(nd, c.time()) if nd else None)(
                    _mes_seguinte(c.date(), arg)))
        elif tipo == "dma" and arg:
            try:
                alvo = datetime.combine(date(data.year + 1, data.month, data.day), alvo.time())
            except ValueError:
                alvo = None
        elif tipo in ("hoje", "hoje_hora"):
            alvo = alvo + timedelta(days=1)
        else:
            return {"erro": "Esse horário já passou. " + _MSG_QUANDO}
        if alvo is None or alvo <= agora:
            return {"erro": "Esse horário já passou. " + _MSG_QUANDO}
    return _resultado(bruto, cortes, alvo)


def _resultado(bruto, cortes, alvo):
    texto = _limpar(bruto, cortes)
    if not texto:
        return {"erro": "Do que devo te lembrar? Tente: me lembra amanhã às 9h de pagar a conta."}
    return {"texto": texto, "quando": alvo}


# --- frases bonitas ---------------------------------------------------------

def descrever(quando, agora=None):
    """"hoje às 18:00", "amanhã às 09:00", "segunda, 19/10 às 14:30"."""
    agora = agora or datetime.now()
    dias = (quando.date() - agora.date()).days
    if dias == 0:
        rotulo = "hoje"
    elif dias == 1:
        rotulo = "amanhã"
    else:
        rotulo = "%s, %02d/%02d" % (_DIAS_SEMANA[quando.weekday()], quando.day, quando.month)
        if quando.year != agora.year:
            rotulo += "/%d" % quando.year
    return "%s às %02d:%02d" % (rotulo, quando.hour, quando.minute)


def responder(texto, agora=None, arquivo=None):
    """Se a frase é sobre lembretes, faz e devolve a resposta. Senão, None."""
    agora = agora or datetime.now()
    n = _sem_acento(texto)

    if _LISTAR.match(n):
        itens = pendentes(arquivo)
        if not itens:
            return "Você não tem lembretes pendentes. Para criar um: me lembra amanhã às 9h de pagar a conta."
        linhas = ["Seus lembretes:", ""]
        for k, i in enumerate(itens, 1):
            quando = datetime.fromisoformat(i["quando"])
            atraso = " (atrasado)" if quando <= agora else ""
            linhas.append("%d. %s%s: %s" % (k, descrever(quando, agora), atraso, i["texto"]))
        linhas += ["", "Para tirar um: cancelar lembrete 1"]
        return "\n".join(linhas)

    mc = _CANCELAR.match(n)
    if mc:
        itens = pendentes(arquivo)
        k = int(mc.group(1))
        if not (1 <= k <= len(itens)):
            return "Não achei o lembrete %d. Digite \"meus lembretes\" para ver os números." % k
        apagar(itens[k - 1]["id"], arquivo)
        return "Pronto, cancelei o lembrete %d: %s" % (k, itens[k - 1]["texto"])

    r = entender(texto, agora)
    if r is None:
        return None
    if "erro" in r:
        return r["erro"]
    criar(r["texto"], r["quando"], arquivo)
    return ("⏰ Combinado! Vou te lembrar %s: %s.\n\n"
            "O aviso aparece aqui na tela quando o programa estiver aberto."
            % (descrever(r["quando"], agora), r["texto"]))
