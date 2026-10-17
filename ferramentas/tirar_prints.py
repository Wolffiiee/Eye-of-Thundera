"""
Tira prints da tela do Eye of Thundera para a pasta _troca\prints.
Usa SEMPRE o modo exemplo (--demo): conversas de mentira, nada do Wolf
(nem conversas, nem memoria, nem chaves) aparece nas imagens.
Uso:  .venv\Scripts\python.exe ferramentas\tirar_prints.py
r"""
import ctypes
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PASTA_PRINTS = RAIZ / "_troca" / "prints"
PASTA_PRINTS.mkdir(parents=True, exist_ok=True)
_selo = datetime.now().strftime("rodada-%Y%m%d-%H%M%S")
SAIDA = PASTA_PRINTS / _selo
_sufixo = 2
while SAIDA.exists():
    SAIDA = PASTA_PRINTS / (_selo + "-%d" % _sufixo)
    _sufixo += 1
SAIDA.mkdir()
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
    js(janela, "window.chamar=async function(){return {};}; document.querySelectorAll('.cartao-amostra')[5].click();", 0.5)
    foto("07-tema-aurora.png")
    js(janela, "document.querySelectorAll('.cartao-amostra')[6].click();", 0.5)
    foto("08-tema-por-do-sol.png")
    js(janela, "document.querySelectorAll('.cartao-amostra')[7].click();", 0.5)
    foto("09-tema-rosa-cha.png")
    js(janela, "document.querySelectorAll('.cartao-amostra')[8].click();", 0.5)
    foto("10-tema-grafite-dourado.png")
    hwnd = user32.FindWindowW(None, app_web.TITULO_JANELA)
    if hwnd:
        r = RECT()
        user32.GetWindowRect(hwnd, ctypes.byref(r))
        user32.SetWindowPos(hwnd, None, r.l, r.t, 900, 800, 0x0004)
        time.sleep(0.8)
        foto("06-personalizacao-janela-900px.png")
        js(janela, "var corpo=document.querySelector('.janela-corpo'); corpo.scrollTop=corpo.scrollHeight;", 0.4)
        foto("06b-ultimos-temas-900px.png")
    js(janela, "document.querySelectorAll('.cartao-amostra')[0].click();", 0.5)
    js(janela, "document.querySelector('#btn-fechar-config').click(); var c=document.querySelector('#entrada'); c.value='Esse texto serve para conferir copiar e recortar.'; c.setSelectionRange(5,10); c.focus(); mostrarMenuContexto(window.innerWidth-80,window.innerHeight-80);", 2.0)
    foto("11-menu-selecao-texto.png")
    janela.evaluate_js("""window.__clipboardSyntheticResult=null;(async function(){
      var c=document.querySelector('#entrada'), original=c.value, descr=Object.getOwnPropertyDescriptor(navigator,'clipboard');
      var execOriginal=document.execCommand, textoTentado='';
      try {
        Object.defineProperty(navigator,'clipboard',{configurable:true,value:{writeText:async function(){throw Error('teste');}}});
        document.execCommand=function(){textoTentado=document.activeElement.value;return false;};
        c.value='Esse texto serve para conferir copiar e recortar.'; c.setSelectionRange(5,10);
        mostrarMenuContexto(24,24); await new Promise(function(r){setTimeout(r,0);});
        document.querySelector('#menu-contexto button').click();
        await new Promise(function(r){setTimeout(r,60);});
        var recortePreservado=c.value===original && textoTentado==='texto';
        document.execCommand=function(){return true;};
        var fallbackOk=await escreverClipboard('texto sintético');
        return {recortePreservado:recortePreservado,fallbackOk:fallbackOk};
      } catch(e) { return {erro:String(e)}; }
      finally {document.execCommand=execOriginal;if(descr)Object.defineProperty(navigator,'clipboard',descr);else delete navigator.clipboard;}
    })().then(function(r){window.__clipboardSyntheticResult=r;});""")
    time.sleep(0.2)
    resultado = janela.evaluate_js("window.__clipboardSyntheticResult")
    print("Teste sintético da área de transferência:", resultado)
    js(janela, "fecharMenuContexto(); document.querySelector('#entrada').value='';", 0.3)
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
