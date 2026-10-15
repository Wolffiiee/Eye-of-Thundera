# Teste de bancada: pywebview funciona neste PC? (janela fora da tela principal)
import sys, threading, time
import webview

print("pywebview", webview.__version__ if hasattr(webview, "__version__") else "?")
resultado = {}


class Ponte:
    def ola(self, nome):
        return "Ola, %s! (veio do Python)" % nome


def depois(janela):
    try:
        time.sleep(1.5)
        resultado["conta"] = janela.evaluate_js("1 + 1")
        resultado["emoji_ok"] = janela.evaluate_js(
            "document.getElementById('e').textContent.length")
        resultado["ponte"] = janela.evaluate_js(
            "window.pywebview.api.ola('Wolf')")
        resultado["gui"] = webview.renderer if hasattr(webview, "renderer") else "?"
    except Exception as erro:
        resultado["erro"] = repr(erro)
    finally:
        janela.destroy()


html = "<html><body style='background:#14141a;color:#eee'><p id='e'>\U0001F600\U0001F3AE</p></body></html>"
j = webview.create_window("teste", html=html, js_api=Ponte(), x=2000, y=100,
                          width=400, height=300)
webview.start(depois, j, gui="edgechromium")
print(resultado)
