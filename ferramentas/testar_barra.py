"""
Teste de verdade da barra propria (arrasta, maximiza, restaura, minimiza, fecha).
Usa o modo exemplo; mexe so na janela que ele mesmo abre. Ver PLANO-BARRA-PROPRIA.md.
Uso: .venv\Scripts\python.exe ferramentas\testar_barra.py
"""
import ctypes
import json
import sys
import threading
import time
from ctypes import wintypes
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
sys.argv = [sys.argv[0], "--demo"]
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    pass
import webview  # noqa: E402
import app_web  # noqa: E402

u = ctypes.windll.user32
resultados = []


def confere(nome, cond, extra=""):
    resultados.append(bool(cond))
    print(("[OK]    " if cond else "[FALHA] ") + nome + (" " + str(extra) if extra else ""), flush=True)


def hwnd():
    return u.FindWindowW(None, app_web.TITULO_JANELA)


def retangulo():
    r = wintypes.RECT()
    u.GetWindowRect(hwnd(), ctypes.byref(r))
    return r.left, r.top, r.right, r.bottom


def origem_cliente():
    pt = wintypes.POINT(0, 0)
    u.ClientToScreen(hwnd(), ctypes.byref(pt))
    return pt.x, pt.y


def mouse(x, y, baixo=None):
    u.SetCursorPos(int(x), int(y))
    if baixo is True:
        u.mouse_event(0x0002, 0, 0, 0, 0)
    elif baixo is False:
        u.mouse_event(0x0004, 0, 0, 0, 0)


def clique(x, y, vezes=1):
    for _ in range(vezes):
        mouse(x, y)
        time.sleep(0.05)
        u.mouse_event(0x0002, 0, 0, 0, 0)
        time.sleep(0.04)
        u.mouse_event(0x0004, 0, 0, 0, 0)
        time.sleep(0.08)


def js(janela, codigo):
    try:
        return janela.evaluate_js(codigo)
    except Exception as e:
        return "ERRO %s" % e


def roteiro(janela):
    try:
        time.sleep(7)
        u.SetForegroundWindow(hwnd())
        time.sleep(0.5)
        dpr = float(js(janela, "window.devicePixelRatio") or 1)
        ox, oy = origem_cliente()
        def centro(seletor):
            r = json.loads(js(janela, "JSON.stringify((function(){var b=document.querySelector('%s').getBoundingClientRect();return {x:b.x+b.width/2,y:b.y+b.height/2}})())" % seletor))
            return ox + r["x"] * dpr, oy + r["y"] * dpr
        barra = js(janela, "document.querySelector('#barra-titulo') ? 1 : 0")
        confere("a barra propria existe", barra == 1)
        confere("nao ha nome nem icone na lateral", js(janela, "document.querySelector('.marca') ? 1 : 0") == 0)
        confere("sem barra nativa (cliente comeca perto do topo)", origem_cliente()[1] - retangulo()[1] < 12,
                origem_cliente()[1] - retangulo()[1])

        # 1. arrastar pela faixa
        l0, t0, _, _ = retangulo()
        faixa_x = ox + 300 * dpr
        faixa_y = oy + 12 * dpr
        mouse(faixa_x, faixa_y); time.sleep(0.2)
        mouse(faixa_x, faixa_y, True); time.sleep(0.15)
        # movimento RELATIVO de verdade (gera entrada real de mouse; o laco de
        # arrasto do Windows ignora o simples SetCursorPos)
        for i in range(10):
            u.mouse_event(0x0001, 15, 8, 0, 0); time.sleep(0.05)
        u.mouse_event(0x0004, 0, 0, 0, 0); time.sleep(0.6)
        l1, t1, _, _ = retangulo()
        confere("arrastar pela faixa move a janela", (l1 - l0) > 40 and (t1 - t0) > 20,
                (l1 - l0, t1 - t0))

        # 2. maximizar pelo botao
        ox, oy = origem_cliente()
        bx, by = centro("#jan-max")
        clique(bx, by); time.sleep(0.8)
        confere("botao maximizar maximiza", bool(u.IsZoomed(hwnd())))
        confere("a tela sabe que esta maximizada", js(janela, "document.body.classList.contains('maximizada')") is True)

        # 3. restaurar com clique duplo na faixa
        ox, oy = origem_cliente()
        clique(ox + 300 * dpr, oy + 14 * dpr, vezes=2); time.sleep(0.8)
        confere("clique duplo na faixa restaura", not u.IsZoomed(hwnd()))

        # 4. minimizar
        ox, oy = origem_cliente()
        bx, by = centro("#jan-min")
        clique(bx, by); time.sleep(0.8)
        confere("botao minimizar minimiza", bool(u.IsIconic(hwnd())))
        u.ShowWindow(hwnd(), 9); time.sleep(0.6)

        # 5. a borda ainda redimensiona (a janela mantem a moldura)
        l, t, r, b = retangulo()
        hit = u.SendMessageW(hwnd(), 0x0084, 0, ((b - 3) << 16) | ((r - 3) & 0xFFFF))
        confere("a borda inferior direita redimensiona (HTBOTTOMRIGHT)", hit == 17, hit)

        # 6. fechar pelo botao
        ox, oy = origem_cliente()
        bx, by = centro("#jan-fechar")
        clique(bx, by); time.sleep(1.5)
        confere("botao fechar fecha a janela", not hwnd())
    except Exception as e:
        print("[FALHA] o teste quebrou:", repr(e), flush=True)
        resultados.append(False)
    finally:
        print("RESULTADO: %s (%d verificacoes)" % ("TUDO CERTO" if all(resultados) else "HA FALHAS", len(resultados)), flush=True)
        try:
            janela.destroy()
        except Exception:
            pass


_start = webview.start


def start_com_roteiro(func, janela, **kw):
    def ao_abrir(instancia):
        threading.Thread(target=roteiro, args=(janela,), daemon=True).start()
        func(instancia)
    return _start(ao_abrir, janela, **kw)


webview.start = start_com_roteiro
app_web.principal()
