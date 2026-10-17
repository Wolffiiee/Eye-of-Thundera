# -*- coding: utf-8 -*-
"""Leitura local de PDF (nada sai do computador).

Usa a biblioteca `pypdf` quando ela esta instalada. Se nao estiver,
devolve uma mensagem clara ensinando a instalar -- em vez de tentar
adivinhar o conteudo (o que daria texto errado).

Nenhuma funcao aqui chama a internet nem grava arquivos: so le os bytes
que ja estao na memoria. Quem decide mandar o texto para a IA e' o
usuario, pelo botao Enviar.
"""

import io
import logging

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


# Limites de seguranca: o texto de um PDF gigante travaria a janela.
LIMITE_BYTES = 25 * 1024 * 1024   # tamanho do arquivo (25 MB)
LIMITE_PAGINAS = 300              # quantas paginas no maximo
LIMITE_CARACTERES = 200_000       # tamanho do texto final


def _resumo_erro(erro):
    """Nome curto do erro, sem caminho nem detalhe interno."""
    return type(erro).__name__


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
        return "", ("Nao encontrei texto nesse PDF -- ele pode ser "
                    "digitalizado (uma foto da pagina).")
    if len(texto) > LIMITE_CARACTERES:
        texto = texto[:LIMITE_CARACTERES] + "\n[... texto cortado ...]"
    return texto, ""
