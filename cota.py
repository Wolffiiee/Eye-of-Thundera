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

import time

ESPACO_MINUTOS = 60       # depois de avisar, fica quieto por uma hora

_ultimo_aviso = 0.0        # quando foi o ultimo aviso (ver `ja_avisou`)
_avisou_com_reserva = None  # o ultimo aviso foi "tem reserva" ou "sem reserva"?


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
        if tem_reserva:
            return ("A cota do Gemini acabou por agora. Estou respondendo "
                    "com a chave de reserva — as respostas podem vir um "
                    "pouco diferentes.")
        return ("A cota do Gemini acabou e não há chave de reserva "
                "cadastrada. O programa continua tentando o Gemini; quando a "
                "cota voltar, ele responde de novo.")
    except Exception:
        # Um aviso nunca pode derrubar a resposta que ja saiu.
        return None


def estado():
    """Para os testes e para o debug: o que o modulo esta lembrando."""
    return {
        "ja_avisou": ja_avisou(),
        "com_reserva": _avisou_com_reserva,
    }