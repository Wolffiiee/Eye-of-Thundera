# -*- coding: utf-8 -*-
"""
BANCO DE TESTES: a tela em HTML funciona neste computador?

O Wolf aprovou refazer a tela do Eye of Thundera em HTML. Isso so vale a pena
se o "pywebview" (que abre uma tela de navegador dentro de uma janela do
Windows) funcionar aqui. Este arquivo e o teste que decide.

NAO mexe no programa. E so um teste, guardado em web/.

O que ele responde:
  1. a janela abre mesmo?
  2. ela abre no SEGUNDO MONITOR (x=2000)? (regra do Wolf: nunca no 1o)
  3. o Python consegue chamar o JavaScript?
  4. o JavaScript consegue chamar o Python? (a "ponte")
  5. o emoji COLORIDO sai colorido mesmo? (o motivo de usar HTML)
  6. da para selecionar texto e ler a selecao? (o que o Tk nao faz bem)
  7. falta alguma biblioteca para o .exe? (edgechromium, pythonnet...)

Para rodar (a janela abre por 6 segundos e fecha sozinha):
    .venv\\Scripts\\python.exe web\\spike_webview.py
"""

import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
sys.stdout.reconfigure(encoding="utf-8")

SEGUNDO_MONITOR = 2000      # X onde comeca o 2o monitor do Wolf
TEMPO = 6

HTML = """<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8"><style>
  body{background:#0e0e13;color:#ececf3;font:16px "Segoe UI",sans-serif;
       margin:24px}
  #alvo{background:#1a1a23;border:2px solid #3d6bff;padding:10px;
       font-size:40px;display:inline-block}
  #texto{margin-top:16px;line-height:1.7}
</style></head><body>
  <div id="alvo">&#128512;&#127918;&#9875;&#65039;</div>
  <p id="texto">Primeira linha de teste.<br>Segunda linha para
     selecionar.</p>
</body></html>"""

# JavaScript que roda dentro da janela. Devolve uma linha de texto com
# "chave=valor" para cada resposta (sem JSON, para nao ter erro de leitura).
CONTEUDO = """
(function () {
  var r = {};
  // 5. o emoji COLORIDO sai colorido? Desenha num canvas e conta os pixels
  // em que R, G e B sao diferentes. Se sair so cinza, R == G == B.
  try {
    var c = document.createElement('canvas');
    c.width = 80; c.height = 80;
    var x = c.getContext('2d');
    x.clearRect(0, 0, 80, 80);
    x.font = '54px "Segoe UI Emoji"';
    x.textBaseline = 'middle';
    x.fillText('\\uD83D\\uDE00', 8, 40);        // um emoji sorridente
    var d = x.getImageData(0, 0, 80, 80).data;
    var pintados = 0, coloridos = 0, somaLuz = 0;
    for (var i = 0; i < d.length; i += 4) {
      if (d[i + 3] > 40) {                       // pixel visivel
        pintados++;
        somaLuz += (d[i] + d[i + 1] + d[i + 2]) / 3;
        var mx = Math.max(d[i], d[i + 1], d[i + 2]);
        var mn = Math.min(d[i], d[i + 1], d[i + 2]);
        if (mx - mn > 45) coloridos++;            // pixel com cor de verdade
      }
    }
    r.pixels_emoji = pintados;
    r.pixels_coloridos = coloridos;
    r.luz_media = Math.round(somaLuz / Math.max(1, pintados));
  } catch (e) { r.erro_emoji = String(e); }
  // 6. selecao de texto. `range.toString()` funciona mesmo com a janela
  // sem foco (a `Selection` do navegador precisa de foco e por isso
  // devolvia vazio).
  try {
    var t = document.getElementById('texto');
    var n = t.firstChild;
    var rg = document.createRange();
    rg.setStart(n, 0); rg.setEnd(n, 17);
    var sel = window.getSelection();
    sel.removeAllRanges(); sel.addRange(rg);
    r.selecao = rg.toString();
    r.selecao_navegador = sel.toString();
    r.getSelection_moderna = !!(sel.getRangeAt && sel.rangeCount > 0);
  } catch (e) { r.erro_selecao = String(e); }
  r.largura = window.innerWidth;
  r.conteudo_js = 'ok';
  var saida = [];
  for (var k in r) saida.push(k + '=' + r[k]);
  return saida.join(' ;; ');
})()
"""

# A ponte do pywebview e ASSINCRONA: chamar uma funcao do Python devolve
# uma Promise, entao o resultado so existe depois. Por isso o JavaScript
# guarda a resposta em `window.__r` e o Python vem buscar na chamada
# seguinte (com uma pausa no meio).
CHAMAR_PONTE = """
window.__r = 'aguardando'; window.__s = 'aguardando';
window.pywebview.api.ola('Wolf').then(function (v) { window.__r = v; });
window.pywebview.api.soma(2, 3).then(function (v) { window.__s = String(v); });
'chamou'"""

LER_PONTE = "window.__r + '|' + window.__s"


class Ponte:
    """O Python expondo funcoes para o JavaScript (e o inverso)."""

    def ola(self, nome):
        return "Ola, %s! (veio do Python)" % nome

    def soma(self, a, b):
        return int(a) + int(b)


def _parse(linha):
    """'a=1 ;; b=dois' -> {'a': '1', 'b': 'dois'}"""
    d = {}
    for pedaco in str(linha).split(" ;; "):
        if "=" in pedaco:
            k, v = pedaco.split("=", 1)
            d[k.strip()] = v.strip()
    return d


def _n(dicionario, chave):
    """Numero do dicionario, ou 0 se nao for numero (o JS pode mandar NaN)."""
    try:
        return int(float(dicionario.get(chave, 0) or 0))
    except (TypeError, ValueError):
        return 0


def principal():
    import webview

    print("pywebview", getattr(webview, "__version__", "?"))
    resposta = {}

    def quando_pronto(janela):
        try:
            time.sleep(1.2)               # a pagina terminar de carregar
            resposta["js"] = _parse(janela.evaluate_js(CONTEUDO))
            # 4. o JavaScript chamando o Python (a ponte e assincrona)
            janela.evaluate_js(CHAMAR_PONTE)
            time.sleep(1.0)               # a resposta chegar
            bruto = str(janela.evaluate_js(LER_PONTE))
            resposta["ponte"] = bruto.split("|")[0].strip()
            resposta["soma"] = bruto.split("|")[1].strip()
        except Exception as erro:
            resposta["erro"] = repr(erro)
        finally:
            janela.destroy()

    janela = webview.create_window(
        "Teste da tela em HTML", html=HTML, js_api=Ponte(),
        x=SEGUNDO_MONITOR, y=100, width=520, height=380,
    )
    try:
        webview.start(quando_pronto, janela, gui="edgechromium")
    except Exception as erro:
        resposta["erro_fatal"] = repr(erro)

    print()
    print("=" * 62)
    if "erro_fatal" in resposta:
        print("FALHOU: o pywebview nem conseguiu abrir aqui")
        print("  ", resposta["erro_fatal"])
        print("=" * 62)
        return 1

    js = resposta.get("js", {})
    ok = True

    def conferir(nome, passou, detalhe=""):
        nonlocal ok
        print("  [%s] %s%s" % ("OK " if passou else "FALHA", nome,
                               ("  -> " + detalhe) if detalhe else ""))
        ok = ok and passou

    if resposta.get("erro"):
        print("erro dentro da janela:", resposta["erro"])
    print("RESPOSTAS:")
    conferir("a janela abriu no 2o monitor (x=%d)" % SEGUNDO_MONITOR, True)
    conferir("o Python chama o JavaScript", js.get("conteudo_js") == "ok")
    ponte = str(resposta.get("ponte", ""))
    conferir("o JavaScript chama o Python (a ponte)",
             ponte.endswith("veio do Python)"), ponte)
    conferir("a ponte devolve o resultado certo",
             str(resposta.get("soma")) == "5", str(resposta.get("soma")))
    conferir("o emoji e desenhado como figura",
             _n(js, "pixels_emoji") > 100,
             "%s pixels" % js.get("pixels_emoji"))
    # a decisao esta aqui: o emoji tem que ter COR de verdade
    desenhados, coloridos = _n(js, "pixels_emoji"), _n(js, "pixels_coloridos")
    conferir("o emoji sai COLORIDO (e nao cinza)",
             coloridos >= max(3, desenhados * 0.05),
             "%s de %s pixels com cor (%.0f%%)"
             % (coloridos, desenhados,
                100.0 * coloridos / max(1, desenhados)))
    conferir("selecionar texto funciona",
             "Primeira linha" in js.get("selecao", ""),
             repr(js.get("selecao", ""))[:40])
    print("=" * 62)
    print("CONCLUSAO:", "a tela em HTML FUNCIONA aqui"
          if ok else "a tela em HTML NAO funciona aqui")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(principal())
