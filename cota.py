# -*- coding: utf-8 -*-
"""Aviso de que a cota do Gemini acabou (o "plano de reserva").

O programa ja trocava de provedor sozinho quando a cota acabava, mas de
forma **invisivel**: o Wolf via as respostas mudarem de estilo sem saber
por que. Aqui isso vira um aviso honesto.

Duas regras que importam mais do que parece:

1. **Nao encher o saco.** Se a cota acabou as 14h e o Wolf pergunta 20 vezes,
   ele precisa ver UMA vez, nao 20. Depois de avisar, fica quieto por
   `ESPACO_MINUTOS` (1 hora).
2. **Perdoar.** Se a cota voltar a funcionar, o programa esquece o aviso
   anterior. Sem isso, a segunda vez que a cota acabasse no mesmo dia o Wolf
   ficaria sem aviso nenhum.

Isso e' estado da SESSAO, e' proposital: nao vai para arquivo nenhum. E' uma
coisa temporaria, nao dado do Wolf, e nao deve sobreviver ao fechamento do
programa.

O reconhecimento de "isso e' cota" mora no motor (`eye_of_thundera.
_falha_de_cota`), junto com o texto de erro. Aqui nao ha uma segunda lista
de palavras: duas listas divergem com o tempo.
"""

import re
import time

ESPACO_MINUTOS = 60       # depois de avisar, fica quieto por uma hora

_ultimo_aviso = 0.0        # quando foi o ultimo aviso (ver `ja_avisou`)
_avisou_com_reserva = None  # o ultimo aviso foi "tem reserva" ou "sem reserva"?

# O Google diz quanto tempo falta no proprio erro:
#   "Quota exceeded for quota metric '...': limit 15, duration 1m0s"
#   "limit 1500, duration 1d"  (1 dia = cota diaria, bem pior que 1 minuto)
# Traduzir isso vale mais do que um vago "espere alguns minutos": o Wolf
# sabe se pode esperar 1 minuto ou se e' melhor voltar amanha.
_DURACAO = re.compile(
    r"duration\s+(\d+)\s*([smhd])",          # duration 1m0s / 30s / 1d
    re.IGNORECASE,
)
_LIMITE = re.compile(r"\blimit\s+(\d+)", re.IGNORECASE)


def _duracao_do_erro(erro):
    """Quanto tempo o Google pediu para esperar. Devolve texto ou None.

    Reconhece `duration 30s`, `1m0s`, `2h`, `1d`. O padrao do Google e'
    "1m0s" (um minuto), que e' o caso mais comum: cota por minuto.
    """
    try:
        texto = ("%s %s" % (type(erro).__name__, erro)).lower()
        achado = _DURACAO.search(texto)
        if not achado:
            return None
        numero = int(achado.group(1))
        letra = achado.group(2).lower()
        if numero <= 0:
            return None
        if letra == "s":
            if numero < 60:
                return "uns %d segundos" % numero
            return "cerca de %d minutos" % max(1, round(numero / 60))
        if letra == "m":
            if numero == 1:
                return "cerca de 1 minuto"
            return "cerca de %d minutos" % numero
        if letra == "h":
            if numero == 1:
                return "cerca de 1 hora"
            return "cerca de %d horas" % numero
        # dia: cota diaria esgotada. Vale avisar que so volta amanha.
        if numero == 1:
            return "amanhã"
        return "daqui a %d dias" % numero
    except Exception:
        return None


def _limite_do_erro(erro):
    """O limite que o Google Restaurou (ex.: 15 por minuto). Ou None."""
    try:
        achado = _LIMITE.search(str(erro))
        return int(achado.group(1)) if achado else None
    except Exception:
        return None


def _agora():
    return time.time()


def ja_avisou(agora=None):
    """True se ainda estamos no silencio depois de um aviso."""
    momento = _agora() if agora is None else agora
    return (momento - _ultimo_aviso) < (ESPACO_MINUTOS * 60)


def esquecer():
    """Esquece o aviso anterior (a cota voltou a funcionar)."""
    global _ultimo_aviso, _avisou_com_reserva
    _ultimo_aviso = 0.0
    _avisou_com_reserva = None


def _marcar(agora):
    global _ultimo_aviso, _avisou_com_reserva
    _ultimo_aviso = _agora() if agora is None else agora


def avisar(erro, tem_reserva, agora=None):
    """Devolve o texto do aviso, ou None se nao for a hora de avisar.

    `tem_reserva` diz se existe chave de reserva cadastrada: muda so' a
    ultima frase, porque o que o Wolf pode fazer e' diferente em cada caso.
    """
    try:
        # O reconhecimento e' do motor: aqui nao repetimos a lista de
        # palavras (duplicar isso e' como os avisos ficam errados depois).
        from eye_of_thundera import _falha_de_cota
        if not _falha_de_cota(erro):
            return None
        if ja_avisou(agora):
            return None
        _marcar(agora)
        global _avisou_com_reserva
        _avisou_com_reserva = bool(tem_reserva)

        # O que o Google disse que falta. Quando ele nao diz nada (a
        # mensagem veio curta, sem "duration"), mantemos o texto vago de
        # antes — e' melhor assim do que inventar um tempo.
        quanto = _duracao_do_erro(erro)
        quando_texto = ("O limite recarrega %s." % quanto if quanto
                        else "O limite recarrega em pouco tempo.")
        limite = _limite_do_erro(erro)
        if limite and limite > 1:
            quando_texto += " O plano de graça faz %d por vez." % limite

        if tem_reserva:
            return ("A cota do Gemini acabou por agora. %s Estou "
                    "respondendo com a chave de reserva — as respostas "
                    "podem vir um pouco diferentes."
                    % quando_texto)
        return ("A cota do Gemini acabou e não há chave de reserva "
                "cadastrada. %s O programa continua tentando o Gemini; "
                "quando o limite voltar, ele responde de novo."
                % quando_texto)
    except Exception:
        # Um aviso nunca pode derrubar a resposta que ja saiu.
        return None


def estado():
    """Para os testes e para o debug: o que o modulo esta lembrando."""
    return {
        "ja_avisou": ja_avisou(),
        "com_reserva": _avisou_com_reserva,
    }