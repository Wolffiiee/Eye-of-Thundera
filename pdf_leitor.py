# -*- coding: utf-8 -*-
"""Leitura local de PDF (nada sai do computador).

Usa a biblioteca `pypdf` quando ela esta instalada. Se nao estiver,
devolve uma mensagem clara ensinando a instalar -- em vez de tentar
adivinhar o conteudo (o que daria texto errado).

PDF digitalizado (uma foto da pagina, sem camada de texto) vai para o OCR
local: a pagina e' renderizada na memoria (`pypdfium2`) e lida pelo OCR do
proprio Windows (`winsdk`), tambem em memoria. Os dois sao opcionais e
extras: sem eles, o programa continua avisando que o PDF pode ser
digitalizado -- saber ler depois e' o que esta aqui.

Nenhuma funcao aqui chama a internet nem grava arquivos: so le os bytes
que ja estao na memoria. Quem decide mandar o texto para a IA e' o
usuario, pelo botao Enviar.
"""

import asyncio
import io
import logging
import threading

# pypdf costuma reclamar no console de PDF meio estragado. O programa
# roda sem console; quem avisa o usuario (com texto claro) e' o proprio
# texto_de_pdf. Por isso calamos o aviso da biblioteca.
logging.getLogger("pypdf").addHandler(logging.NullHandler())
logging.getLogger("pypdf").propagate = False

# pypdf e' opcional: o programa inteiro continua funcionando sem ela
# (so nao le PDF). Mesmo padrao do Pillow em pesquisa_ia.py.
try:
    import pypdf

    TEM_PDF = True
except Exception:
    pypdf = None
    TEM_PDF = False

# OCR local (PDF digitalizado): renderiza a pagina e le com o OCR do Windows.
# Tambem opcional: sem as duas, o programa segue avisando que o PDF pode ser
# digitalizado. Nada aqui usa internet nem grava arquivo.
try:
    import pypdfium2

    TEM_PDFIUM = True
except Exception:
    pypdfium2 = None
    TEM_PDFIUM = False

try:
    import winsdk.windows.media.ocr  # noqa: F401

    TEM_OCR = True
except Exception:
    winsdk = None
    TEM_OCR = False


# Limites de seguranca: o texto de um PDF gigante travaria a janela.
LIMITE_BYTES = 25 * 1024 * 1024   # tamanho do arquivo (25 MB)
LIMITE_PAGINAS = 300              # quantas paginas no maximo
LIMITE_CARACTERES = 200_000       # tamanho do texto final
LIMITE_PAGINAS_OCR = 20           # paginas lidas por OCR (cada uma leva ~0,1 s)
ESCALA_OCR = 2.0                  # zoom da renderizacao: 2.0 da ~140 dpi
LIMITE_SEGUNDOS_OCR = 60          # espera maxima do OCR antes de desistir


def _resumo_erro(erro):
    """Nome curto do erro, sem caminho nem detalhe interno."""
    return type(erro).__name__


def _texto_por_ocr(dados):
    """Le um PDF como imagem, com o OCR do proprio Windows.

    Devolve (texto, erro): texto vazio + erro claro quando o OCR nao esta
    disponivel ou nao achou nada. A pagina vira imagem na memoria e o OCR
    le dali -- sem internet e sem gravar arquivo.
    """
    if not (TEM_PDFIUM and TEM_OCR):
        return "", ("Nao encontrei texto nesse PDF -- ele pode ser "
                    "digitalizado (uma foto da pagina).")

    try:
        from winsdk.windows.globalization import Language
        from winsdk.windows.graphics.imaging import BitmapDecoder
        from winsdk.windows.media.ocr import OcrEngine
        from winsdk.windows.storage.streams import (
            DataWriter, InMemoryRandomAccessStream)

        documento = pypdfium2.PdfDocument(io.BytesIO(dados))
    except Exception as erro:
        return "", "Nao consegui abrir esse PDF (%s)." % _resumo_erro(erro)

    try:
        total = len(documento)
        paginas = []
        for i in range(min(total, LIMITE_PAGINAS_OCR)):
            try:
                # Uma pagina ruim nao derruba as outras.
                paginas.append(documento[i].render(scale=ESCALA_OCR).to_pil())
            except Exception:
                paginas.append(None)
    finally:
        documento.close()

    async def _ler_pagina(imagem):
        memoria = io.BytesIO()
        imagem.save(memoria, format="PNG")
        stream = InMemoryRandomAccessStream()
        escritor = DataWriter(stream)
        escritor.write_bytes(memoria.getvalue())
        await escritor.store_async()
        await escritor.flush_async()
        stream.seek(0)
        decodificador = await BitmapDecoder.create_async(stream)
        bitmap = await decodificador.get_software_bitmap_async()
        # O programa e' em portugues: tenta pt-BR primeiro e cai para os
        # idiomas do Windows se o pacote de OCR do portugues faltar.
        motor = OcrEngine.try_create_from_language(Language("pt-BR"))
        if motor is None:
            motor = OcrEngine.try_create_from_user_profile_languages()
        if motor is None:
            return ""
        return (await motor.recognize_async(bitmap)).text or ""

    async def _ler_tudo():
        partes = []
        for imagem in paginas:
            if imagem is None:
                partes.append("")
                continue
            partes.append(await _ler_pagina(imagem))
        if total > LIMITE_PAGINAS_OCR:
            partes.append("\n[... OCR aplicado so as primeiras %d paginas ...]"
                          % LIMITE_PAGINAS_OCR)
        return partes

    # O OCR e' assincrono e depende do loop de eventos da thread. Na thread
    # principal -- depois do pywebview, que deixa a thread em STA -- o
    # `await` do OCR nunca volta e a chamada ficaria presa para sempre. Por
    # isso o OCR roda em uma thread propria, com seu proprio loop, e quem
    # chamou so espera (com limite) o resultado.
    resultado = {}

    def _alvo():
        try:
            resultado["partes"] = asyncio.run(_ler_tudo())
        except Exception as erro:
            resultado["erro"] = erro

    trabalho = threading.Thread(target=_alvo, daemon=True)
    trabalho.start()
    trabalho.join(LIMITE_SEGUNDOS_OCR)
    if trabalho.is_alive():
        return "", "Nao consegui ler esse PDF (o OCR demorou demais)."
    if "erro" in resultado:
        return "", "Nao consegui ler esse PDF (%s)." % _resumo_erro(resultado["erro"])
    partes = resultado["partes"]

    texto = "\n".join(partes).strip()
    if not texto:
        return "", ("Nao encontrei texto nesse PDF -- ele pode ser "
                    "digitalizado (uma foto da pagina).")
    if len(texto) > LIMITE_CARACTERES:
        texto = texto[:LIMITE_CARACTERES] + "\n[... texto cortado ...]"
    return texto, ""


def texto_de_pdf(dados):
    """Extrai o texto de um PDF. Devolve uma tupla (texto, erro).

    - texto: o que foi lido (string vazia se deu erro).
    - erro: mensagem clara para a tela (string vazia se deu certo).
    """
    if not dados:
        return "", "O arquivo esta vazio."
    if dados[:5] != b"%PDF-":
        return "", "Esse arquivo nao parece ser um PDF."
    if len(dados) > LIMITE_BYTES:
        return "", "Esse PDF e' grande demais (limite de 25 MB)."
    if not TEM_PDF:
        return "", ("Para ler PDF, rode o arquivo '1 - Instalar.bat' "
                    "de novo (falta a biblioteca de leitura).")

    try:
        leitor = pypdf.PdfReader(io.BytesIO(dados))
    except Exception as erro:
        return "", "Nao consegui abrir esse PDF (%s)." % _resumo_erro(erro)

    # PDF com senha: tenta a senha vazia (a mais comum). Se nao abrir,
    # avisa com clareza em vez de estourar.
    if getattr(leitor, "is_encrypted", False):
        try:
            resultado = leitor.decrypt("")
            if not resultado:
                return "", "Esse PDF tem senha, por isso nao consegui abrir."
        except Exception:
            return "", "Esse PDF tem senha, por isso nao consegui abrir."

    partes = []
    try:
        for i, pagina in enumerate(leitor.pages):
            if i >= LIMITE_PAGINAS:
                partes.append("\n[... o resto do PDF foi ignorado ...]")
                break
            try:
                partes.append(pagina.extract_text() or "")
            except Exception:
                # Uma pagina ruim nao derruba as outras.
                partes.append("")
    except Exception as erro:
        return "", "Nao consegui ler esse PDF (%s)." % _resumo_erro(erro)

    texto = "\n".join(partes).strip()
    if not texto:
        # Sem camada de texto: provavelmente digitalizado (uma foto da pagina).
        # Tenta o OCR local antes de avisar que nao achou nada.
        return _texto_por_ocr(dados)
    if len(texto) > LIMITE_CARACTERES:
        texto = texto[:LIMITE_CARACTERES] + "\n[... texto cortado ...]"
    return texto, ""
