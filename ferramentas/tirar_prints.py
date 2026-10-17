"""
Tira prints da tela do Eye of Thundera para a pasta _troca\prints.
Usa SEMPRE o modo exemplo (--demo): conversas de mentira, nada do Wolf
(nem conversas, nem memoria, nem chaves) aparece nas imagens.
Uso:  .venv\Scripts\python.exe ferramentas\tirar_prints.py
"""
import ctypes
import sys
import threading
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SAIDA = RAIZ / "_troca" / "prints"
SAIDA.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(RAIZ))
sys.argv = [sys.argv[0], "--demo"]          # modo exemplo, sempre
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    pass

import webview  # noqa: E402
from PIL import ImageGrab  # noqa: E402

import app_web  # noqa: E402

user32 = ctypes.windll.user32


class RECT(ctypes.Structure):
    _fields_ = [("l", ctypes.c_long), ("t", ctypes.c_long),
                ("r", ctypes.c_long), ("b", ctypes.c_long)]


def foto(nome):
    hwnd = user32.FindWindowW(None, app_web.TITULO_JANELA)
    if not hwnd:
        print("janela nao achada"); return
    user32.ShowWindow(hwnd, 9)
    user32.SetForegroundWindow(hwnd)
    time.sleep(0.8)
    r = RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(r))
    img = ImageGrab.grab(bbox=(r.l, r.t, r.r, r.b), all_screens=True)
    img.save(SAIDA / nome)
    print("salvo", nome, img.size)


def js(janela, codigo, espera=1.0):
    try:
        janela.evaluate_js(codigo)
    except Exception as erro:
        print("js falhou:", erro)
    time.sleep(espera)


def roteiro(janela):
    time.sleep(7)
    foto("01-tela-inicial.png")
    js(janela, "var c=document.querySelectorAll('.conversa, .item-conversa, #lista-conversas > *'); if(c[1]) c[1].click();", 1.5)
    foto("02-conversa-aberta.png")
    js(janela, "document.querySelector('#btn-config').click()", 1.5)
    for aba in ("memoria", "conversa", "chaves", "ajuda", "personalizacao"):
        js(janela, "var b=document.querySelector('.aba[data-aba=\"%s\"]'); if(b) b.click();" % aba, 1.0)
        foto("03-config-%s.png" % aba)
    js(janela, "var b=document.querySelector('.aba[data-aba=personalizacao]'); if(b) b.click(); aplicarTema(3); document.querySelectorAll('.cartao-amostra').forEach(function(x,i){x.classList.toggle('ativo',i===3);x.setAttribute('aria-checked',i===3?'true':'false');x.tabIndex=i===3?0:-1;});", 1.0)
    foto("05-tema-ocean-aplicado.png")
    hwnd = user32.FindWindowW(None, app_web.TITULO_JANELA)
    if hwnd:
        r = RECT()
        user32.GetWindowRect(hwnd, ctypes.byref(r))
        user32.SetWindowPos(hwnd, None, r.l, r.t, 900, 800, 0x0004)
        time.sleep(0.8)
        foto("06-personalizacao-janela-900px.png")
    js(janela, "aplicarTema(0); document.querySelectorAll('.cartao-amostra').forEach(function(x,i){x.classList.toggle('ativo',i===0);x.setAttribute('aria-checked',i===0?'true':'false');x.tabIndex=i===0?0:-1;});", 0.5)
    js(janela, "document.querySelector('#btn-fechar-config').click()", 0.8)
    foto("04-voltou-ao-chat.png")
    janela.destroy()


_start = webview.start


def start_com_roteiro(func, janela, **kw):
    def ao_abrir(instancia):
        threading.Thread(target=roteiro, args=(janela,), daemon=True).start()
        func(instancia)
    return _start(ao_abrir, janela, **kw)


webview.start = start_com_roteiro
app_web.principal()
