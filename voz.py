# -*- coding: utf-8 -*-
"""
Voz para texto do Eye of Thundera.

Este arquivo cuida de duas coisas, sem depender do programa:

  1. `Gravador`  - abre o microfone, junta o áudio e entrega um WAV pronto;
  2. `transcrever` - manda esse WAV para o Gemini e devolve o texto falado.

Ele foi escrito para NÃO importar o `eye_of_thundera` (assim dá para testar
sozinho, sem abrir a janela). A biblioteca de áudio (`sounddevice`) é
opcional: se ela não estiver instalada, o programa continua funcionando
normalmente e só o botão de microfone avisa que faltou a biblioteca.
"""

import array
import io
import wave

# A biblioteca que fala com o microfone. Sem ela, nada quebra: apenas o
# microfone fica indisponivel.
try:
    import sounddevice as _sd
    TEM_SOM = True
except Exception:
    _sd = None
    TEM_SOM = False

# 16 kHz, mono, 16 bits: é o formato que o Gemini entende melhor e é o que
# cabe num pedido de graça sem estourar o limite de tamanho.
TAXA = 16000
CANAIS = 1
LARGURA = 2                # int16 = 2 bytes por amostra
TEMPO_MAXIMO = 120         # segundos; depois disso a gravação para sozinha

# Piso absoluto de volume: abaixo disso (RMS) não há voz nenhuma. Medido
# na sala do Wolf, o microfone parado fica entre 5 e 20; a voz passando
# por ele passa de 500. Este valor é só a rede de segurança final.
VOLUME_MINIMO = 60.0

# Além do piso, o áudio tem que ser bem mais forte do que o ruído de
# fundo da própria gravação. Sem isso, um fone ligado perto do microfone
# (ou um ventilador) seria confundido com a voz da pessoa.
ACIMA_DO_RUIDO = 8.0

PEDIDO = (
    "Transcreva fielmente em português do Brasil. "
    "Devolva só o texto, com pontuação, sem comentar."
)


def microfone_disponivel():
    """True quando existe um microfone que o programa possa usar."""
    if not TEM_SOM:
        return False
    try:
        entrada = _sd.query_devices(kind="input")
        return bool(entrada) and entrada.get("max_input_channels", 0) > 0
    except Exception:
        return False


def microfone_erro(erro):
    """Traduz a exceção do somdevice para uma frase que dá para resolver."""
    texto = ("%s %s" % (type(erro).__name__, erro)).lower()
    if "permission" in texto or "access is denied" in texto:
        return (
            "O Windows não deixou o programa usar o microfone. "
            "Abra Configurações > Privacidade e ative o acesso ao "
            "microfone para aplicativos de desktop."
        )
    if ("no input" in texto or "was not found" in texto
            or "hostapi" in texto or "no sound" in texto):
        return "Não achei nenhum microfone ligado neste computador."
    return "Não consegui abrir o microfone (%s)." % erro


def _rms(dados):
    """Volume médio de um bloco de áudio (0 = silêncio)."""
    amostras = array.array("h")
    try:
        amostras.frombytes(bytes(dados))
    except Exception:
        return 0.0
    if not amostras:
        return 0.0
    total = 0
    for valor in amostras:
        total += valor * valor
    return (total / float(len(amostras))) ** 0.5


def _para_wav(audio, taxa=TAXA):
    """Junta os blocos de áudio e embrulha num arquivo WAV (bytes)."""
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as arquivo:
        arquivo.setnchannels(CANAIS)
        arquivo.setsampwidth(LARGURA)
        arquivo.setframerate(taxa)
        arquivo.writeframes(audio)
    return buffer.getvalue()


def wav_tem_som(wav, minimo=VOLUME_MINIMO):
    """Diz se o WAV gravado tem voz o suficiente para chamar a IA.

    Dois criterios, porque um so nao da conta:
      1. o volume geral passa de um piso ( microfone parado fica em ~5-20);
      2. o trecho mais alto e bem mais forte que o mais baixo (o silencio
         entre as palavras). Se a pessoa so respirou, os dois ficam
         parecidos e o audio e descartado sem gastar chamada da IA.
    """
    try:
        with wave.open(io.BytesIO(wav), "rb") as arquivo:
            taxa = arquivo.getframerate() or TAXA
            quadros = arquivo.readframes(arquivo.getnframes())
    except Exception:
        return False

    amostras = array.array("h")
    try:
        amostras.frombytes(quadros)
    except Exception:
        return False
    if not amostras:
        return False

    # Um volume por bloco de ~50 ms, para dar para comparar partes.
    bloco = max(1, int(taxa * 0.05))
    niveis = []
    for inicio in range(0, len(amostras) - bloco + 1, bloco):
        pedaco = amostras[inicio:inicio + bloco].tobytes()
        niveis.append(_rms(pedaco))
    if not niveis:
        return False

    geral = _rms(quadros)
    if geral <= minimo:
        return False

    niveis.sort()
    mais_fraco = niveis[0]
    mais_forte = niveis[-1]
    return mais_forte >= max(mais_fraco * ACIMA_DO_RUIDO, minimo)


def segundos_do_wav(wav):
    """Duração do WAV em segundos (0 se não der para ler)."""
    try:
        with wave.open(io.BytesIO(wav), "rb") as arquivo:
            return arquivo.getnframes() / float(arquivo.getframerate())
    except Exception:
        return 0.0


class Gravador(object):
    """Grava o microfone e entrega o áudio como WAV.

    Uso normal:

        gravador = Gravador()
        gravador.iniciar()
        ...
        wav = gravador.parar()

    A leitura acontece numa thread do próprio sounddevice; aqui só juntamos
    os blocos e medimos o volume para a bolinha do botão poder pulsar.
    """

    def __init__(self, taxa=TAXA, tempo_maximo=TEMPO_MAXIMO):
        self.taxa = taxa
        self.tempo_maximo = tempo_maximo
        self._partes = []
        self._fluxo = None
        self._nivel = 0.0
        self.segundos = 0.0
        self.gravando = False

    # O fluxo é separado para os testes poderem trocar por um falso.
    def _criar_fluxo(self, callback):
        return _sd.RawInputStream(
            samplerate=self.taxa,
            blocksize=0,
            device=None,
            channels=CANAIS,
            dtype="int16",
            callback=callback,
        )

    def iniciar(self):
        """Começa a gravar. Levanta exceção se o microfone não abrir."""
        if self.gravando:
            return
        self._partes = []
        self.segundos = 0.0
        self._nivel = 0.0

        def entrada(dados, quadros, _tempo, _estado):
            self._partes.append(bytes(dados))
            self.segundos = (len(dados) // LARGURA) / float(self.taxa)
            self._nivel = _rms(dados)

        fluxo = self._criar_fluxo(entrada)
        fluxo.start()
        self._fluxo = fluxo
        self.gravando = True

    def limite(self):
        """True quando a gravação passou do tempo máximo."""
        return self.gravando and self.segundos >= self.tempo_maximo

    def nivel(self):
        """Volume do último bloco (0 = silêncio)."""
        return self._nivel

    def parar(self):
        """Para de gravar e devolve o áudio em WAV (bytes)."""
        fluxo, self._fluxo = self._fluxo, None
        self.gravando = False
        if fluxo is not None:
            for metodo in ("stop", "close"):
                try:
                    getattr(fluxo, metodo)()
                except Exception:
                    pass
        audio = b"".join(self._partes)
        self._partes = []
        return _para_wav(audio, self.taxa)


def _juntar_partes(resposta):
    """Remonta o texto quando o campo .text não vem preenchido."""
    pedacos = []
    try:
        for candidato in (resposta.candidates or []):
            partes = getattr(getattr(candidato, "content", None), "parts", None)
            for parte in (partes or []):
                texto = getattr(parte, "text", None)
                if texto:
                    pedacos.append(texto)
    except Exception:
        pass
    return "".join(pedacos).strip()


def transcrever(cliente, modelos, wav):
    """Manda o áudio (WAV) para o Gemini e devolve o texto falado.

    Tenta os modelos na ordem dada; se um falhar, passa para o próximo.
    Levanta a última exceção se nenhum responder.
    """
    from google.genai import types

    if not wav:
        raise RuntimeError("não foi gravado nenhum áudio")

    ultimo_erro = None
    for modelo in (modelos or []):
        try:
            conteudo = types.Content(
                role="user",
                parts=[
                    types.Part.from_bytes(data=wav, mime_type="audio/wav"),
                    types.Part(text=PEDIDO),
                ],
            )
            resposta = cliente.models.generate_content(
                model=modelo,
                contents=[conteudo],
                config=types.GenerateContentConfig(temperature=0.0),
            )
            texto = (getattr(resposta, "text", "") or "").strip()
            if not texto:
                texto = _juntar_partes(resposta)
            if texto:
                return texto
            ultimo_erro = RuntimeError("a IA não devolveu texto")
        except Exception as erro:
            ultimo_erro = erro
            continue

    raise ultimo_erro or RuntimeError("não consegui transcrever o áudio")
