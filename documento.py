"""Documento aberto: perguntar sobre um texto longo sem mandá-lo inteiro.

Ver PLANO-DOCUMENTOS-LONGOS.md. O texto (por página) fica só na memória do
programa. Quando o Wolf pergunta algo, a busca é LOCAL (palavras da pergunta,
sem acento) e só os trechos mais relevantes, com o número da página, vão para
a IA. Nada aqui chama a internet nem grava arquivo.
"""
import math
import re
import unicodedata
from collections import Counter

LIMITE_PAGINAS = 300             # os mesmos limites do pdf_leitor
LIMITE_CARACTERES = 200_000
TAMANHO_TRECHO = 1200            # caracteres por pedaço
TRECHOS_POR_PERGUNTA = 6
TRECHOS_NO_RESUMO = 10
PAGINAS_PARA_DOCUMENTO = 10      # PDF maior que isso abre como "documento"
CARACTERES_PARA_DOCUMENTO = 30_000

_COMUNS = set((
    "a o as os um uma uns umas de do da dos das em no na nos nas por para pra com sem "
    "sobre entre e ou mas que se como qual quais quando onde quem foi sao ser ter tem "
    "esta este essa esse isso isto ao aos ja mais muito pelo pela pelos pelas eu me meu "
    "minha voce seu sua ele ela eles elas nao sim the of and to in ha tem fala diz "
    "documento texto arquivo pdf").split())

_INDICE = re.compile(r"^\s*(?:resumir|resuma|resumo)\b.*\bdocumento\b|^\s*resumo\s+do\s+documento\b")
_SUMARIO = re.compile(r"^\s*(?:(?:ver|mostrar?|qual\s+[eé]|me\s+d[aê])\s+)?(?:o\s+)?"
                      r"(?:[ií]ndice|sum[aá]rio)\s+do\s+documento\s*[?.!]*\s*$")


def _sem_acento(s):
    return "".join(unicodedata.normalize("NFD", c)[0] for c in str(s)).lower()


def _palavras(texto):
    """Palavras úteis (sem acento, sem palavras comuns), cortadas em 6 letras
    para 'contrato' e 'contratos' se encontrarem."""
    achadas = re.findall(r"[a-z0-9]+", _sem_acento(texto))
    # "clausula7" nao pode virar "clausu" (todas as clausulas se confundiriam):
    # so a palavra de letras e' cortada; o que tem numero fica inteiro. Numero
    # sozinho ("artigo 7") tambem vale; o resto precisa de 3 letras.
    return [p if any(c.isdigit() for c in p) else p[:6]
            for p in achadas
            if (len(p) >= 3 or p.isdigit()) and p not in _COMUNS]


def eh_longo(paginas):
    """True se o PDF e' grande demais para ir inteiro na caixa de digitar."""
    paginas = list(paginas or [])
    return (len(paginas) > PAGINAS_PARA_DOCUMENTO
            or sum(len(str(p)) for p in paginas) > CARACTERES_PARA_DOCUMENTO)


def eh_pedido_de_resumo(texto):
    return bool(_INDICE.match(_sem_acento(texto)))


def eh_pedido_de_indice(texto):
    return bool(_SUMARIO.match(_sem_acento(texto)))


class Documento:
    def __init__(self, nome, paginas):
        self.nome = (str(nome or "documento").strip() or "documento")[:120]
        self.paginas = []
        total = 0
        lista = list(paginas or [])
        self.aviso = ""
        # O leitor de PDF deixa uma nota no fim quando nao leu tudo
        # ("[... OCR aplicado so as primeiras 20 paginas ...]"): vira aviso.
        if lista and str(lista[-1]).strip().startswith("[...") \
                and str(lista[-1]).strip().endswith("...]"):
            self.aviso = str(lista.pop()).strip().strip("[]").strip(". ").strip()
        if len(lista) > LIMITE_PAGINAS and not self.aviso:
            self.aviso = "so as primeiras %d paginas foram carregadas" % LIMITE_PAGINAS
        for texto in lista[:LIMITE_PAGINAS]:
            texto = str(texto or "")
            if total + len(texto) > LIMITE_CARACTERES:
                texto = texto[:max(0, LIMITE_CARACTERES - total)]
            self.paginas.append(texto)
            total += len(texto)
            if total >= LIMITE_CARACTERES:
                break
        self.caracteres = total
        if total >= LIMITE_CARACTERES and not self.aviso:
            self.aviso = "o texto foi cortado em %d caracteres" % LIMITE_CARACTERES
        self._pedacos = []        # (pagina 1-based, texto, Counter de palavras)
        for numero, texto in enumerate(self.paginas, 1):
            for pedaco in self._dividir(texto):
                self._pedacos.append((numero, pedaco, Counter(_palavras(pedaco))))
        self._df = Counter()
        for _, _, contagem in self._pedacos:
            self._df.update(contagem.keys())

    @staticmethod
    def _dividir(texto):
        """Pedaços de ~TAMANHO_TRECHO caracteres, cortando em fim de linha."""
        pedacos, atual = [], ""
        for linha in texto.splitlines():
            while len(linha) > TAMANHO_TRECHO:        # linha gigante: corta
                if atual.strip():
                    pedacos.append(atual.strip())
                    atual = ""
                pedacos.append(linha[:TAMANHO_TRECHO])
                linha = linha[TAMANHO_TRECHO:]
            if len(atual) + len(linha) + 1 > TAMANHO_TRECHO and atual.strip():
                pedacos.append(atual.strip())
                atual = ""
            atual += linha + "\n"
        if atual.strip():
            pedacos.append(atual.strip())
        return pedacos

    def info(self):
        return {"nome": self.nome, "paginas": len(self.paginas),
                "caracteres": self.caracteres, "aviso": self.aviso}

    def trechos(self, pergunta, quantos=TRECHOS_POR_PERGUNTA):
        """Os pedaços que mais combinam com a pergunta: [(pagina, texto)],
        na ordem do documento. Lista vazia se nada combina."""
        busca = set(_palavras(pergunta))
        if not busca or not self._pedacos:
            return []
        n = len(self._pedacos)
        pontuados = []
        for indice, (pagina, texto, contagem) in enumerate(self._pedacos):
            nota = 0.0
            for p in busca:
                if p in contagem:
                    idf = math.log(1 + n / (1 + self._df[p]))
                    nota += (1 + math.log(contagem[p])) * idf
            if nota > 0:
                pontuados.append((nota, indice))
        pontuados.sort(key=lambda x: (-x[0], x[1]))
        escolhidos = sorted(i for _, i in pontuados[:max(1, int(quantos))])
        return [(self._pedacos[i][0], self._pedacos[i][1]) for i in escolhidos]

    def indice(self, maximo=40):
        """Títulos prováveis: [(pagina, titulo)]. Linha curta que começa com
        número ('1.2 Objeto'), 'Capítulo/Seção/Artigo' ou está em CAIXA ALTA."""
        achados = []
        for numero, texto in enumerate(self.paginas, 1):
            for linha in texto.splitlines():
                t = linha.strip()
                if not (4 <= len(t) <= 80) or t.endswith((".", ",", ";")):
                    continue
                letras = [c for c in t if c.isalpha()]
                numerado = re.match(r"^\d+(?:\.\d+)*[.)]?\s+\S", t)
                palavra = re.match(r"^(?:cap[ií]tulo|se[cç][aã]o|artigo|parte)\s+\S", t, re.I)
                caixa_alta = len(letras) >= 4 and t.upper() == t
                if numerado or palavra or caixa_alta:
                    achados.append((numero, t))
                    if len(achados) >= maximo:
                        return achados
        return achados

    def indice_texto(self):
        itens = self.indice()
        cab = "Documento \"%s\": %d página(s)." % (self.nome, len(self.paginas))
        if not itens:
            # Sem títulos claros: a primeira linha de cada página já ajuda a se
            # localizar (e o Wolf pode perguntar direto pelo assunto).
            linhas = []
            for numero, texto in enumerate(self.paginas, 1):
                for linha in texto.splitlines():
                    if linha.strip():
                        linhas.append("%s (pág. %d)" % (linha.strip()[:80], numero))
                        break
                if len(linhas) >= 40:
                    break
            if not linhas:
                return cab + "\n\nNão achei texto para montar um índice."
            return (cab + "\n\nNão achei títulos claros; esta é a primeira linha "
                    "de cada página:\n\n" + "\n".join(linhas))
        linhas = ["%s (pág. %d)" % (t, p) for p, t in itens]
        return cab + "\n\nPartes que encontrei:\n\n" + "\n".join(linhas)

    def montar_pergunta(self, pergunta):
        """Texto que vai para a IA (trechos + pergunta). None se nada combina."""
        achados = self.trechos(pergunta)
        if not achados:
            return None
        blocos = ["[pág. %d]\n%s" % (p, t) for p, t in achados]
        return ("Responda usando SOMENTE os trechos do documento \"%s\" abaixo. "
                "Cite a página no formato (pág. N). Se a resposta não estiver nos "
                "trechos, diga que não encontrou no documento.\n\n%s\n\nPergunta: %s"
                % (self.nome, "\n\n".join(blocos), str(pergunta).strip()))

    def montar_resumo(self):
        """Pedido de resumo com trechos espalhados pelo documento todo."""
        n = len(self._pedacos)
        if n == 0:
            return None
        passo = max(1, n // TRECHOS_NO_RESUMO)
        escolhidos = self._pedacos[::passo][:TRECHOS_NO_RESUMO]
        blocos = ["[pág. %d]\n%s" % (p, t) for p, t, _ in escolhidos]
        return ("Faça um resumo curto do documento \"%s\" a partir destes trechos "
                "espalhados por ele (não é o texto inteiro; diga isso se for "
                "relevante). Cite páginas no formato (pág. N).\n\n%s"
                % (self.nome, "\n\n".join(blocos)))
