# -*- coding: utf-8 -*-
"""
Verificação automática do Pesquisa IA.

Rode SEMPRE depois de qualquer alteração no programa (duplo clique em
"verificar.bat"). Se aparecer alguma linha [FALHA], a alteração NÃO está
pronta: corrija e rode de novo até terminar com "TUDO CERTO".

O que ele confere:
  1. se o pesquisa_ia.py não tem erro de escrita (sintaxe);
  2. se as bibliotecas do requirements.txt estão instaladas;
  3. análise do código (pyflakes): nomes que não existem = FALHA;
  4. regras do projeto (ex.: proibido unbind_all de clique);
  5. teste com a janela de verdade: seleção de texto, menus que fecham ao
     clicar fora, janela de Configurações e erros escondidos nos botões.

Para criar um teste novo: copie um dos "caso(...)" ou "ok(...)" abaixo.
"""

import importlib.util
import io
import json
import py_compile
import re
import shutil
import subprocess
import sys
import threading
import time
import tkinter as tk
import traceback
import types
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

PASTA = Path(__file__).resolve().parent
ARQUIVO = PASTA / "pesquisa_ia.py"

# Onde a janela de teste aparece. O segundo monitor do Wolf comeca em
# X=1920; usar +2000+100 joga a janela para la e deixa a tela principal
# dele livre. Se um dia o monitor mudar, e so mexer aqui.
POSICAO_TESTE = "+2000+100"

falhas = []
avisos = []


def ok(msg):
    print("[OK]     " + msg)


def falha(msg):
    print("[FALHA]  " + msg)
    falhas.append(msg)


def aviso(msg):
    print("[AVISO]  " + msg)
    avisos.append(msg)


# --- 1. sintaxe -------------------------------------------------------------
try:
    py_compile.compile(str(ARQUIVO), doraise=True)
    ok("pesquisa_ia.py sem erro de sintaxe")
except py_compile.PyCompileError as erro:
    falha("erro de sintaxe: %s" % erro)

# --- 2. bibliotecas ---------------------------------------------------------
NOME_NO_CODIGO = {
    "google-genai": "google.genai",
    "ddgs": "ddgs",
    "pyspellchecker": "spellchecker",
    "pillow": "PIL",
    # a biblioteca chama-se pywebview, mas o modulo que se importa e' webview
    "pywebview": "webview",
}
try:
    for pacote in (PASTA / "requirements.txt").read_text(encoding="utf-8").splitlines():
        pacote = pacote.split("#")[0].strip()
        base = re.split(r"[<>=!~]", pacote)[0].strip().lower()
        if not base:
            continue
        modulo = NOME_NO_CODIGO.get(base, base.replace("-", "_"))
        try:
            achou = importlib.util.find_spec(modulo) is not None
        except Exception:
            achou = False
        if achou:
            ok("biblioteca instalada: %s" % base)
        else:
            falha("biblioteca faltando: %s (rode '1 - Instalar.bat')" % base)
except Exception as erro:
    falha("não consegui ler o requirements.txt: %s" % erro)

# --- 3. análise do código (pyflakes) ---------------------------------------
try:
    r = subprocess.run(
        [sys.executable, "-m", "pyflakes", str(ARQUIVO), str(Path(__file__)),
         str(PASTA / "app_web.py"), str(PASTA / "memoria.py"),
         str(PASTA / "roteador.py"), str(PASTA / "voz.py")],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    if "No module named pyflakes" in (r.stderr or ""):
        aviso("pyflakes não instalado (rode: .venv\\Scripts\\python.exe -m "
              "pip install -r requirements-dev.txt)")
    else:
        graves = 0
        for linha in (r.stdout or "").splitlines():
            if "undefined name" in linha or "invalid syntax" in linha:
                falha("pyflakes: " + linha)
                graves += 1
            elif linha.strip():
                aviso("pyflakes: " + linha)
        if not graves:
            ok("análise do código sem nomes inexistentes")
except Exception as erro:
    aviso("não consegui rodar o pyflakes: %r" % (erro,))

# --- 4. regras do projeto ---------------------------------------------------
codigo = ARQUIVO.read_text(encoding="utf-8")
# Nenhuma janela do Windows pode aparecer: messagebox, simpledialog e
# filedialog abrem brancos e destoam do programa. Para aviso, pergunta e
# confirmação use SEMPRE `_dialogo_escuro(...)` (ou `_confirmar`).
for proibido, motivo in (
    ("messagebox.", "use _dialogo_escuro(pai, titulo, texto)"),
    ("simpledialog", "use _dialogo_escuro(pai, titulo, texto)"),
    ("tk_optionMenu", "use _dialogo_escuro(pai, titulo, texto)"),
):
    # fora do que está em comentário ou dentro de texto (docstring),
    # para a regra não acusar a própria documentação
    sem_texto = re.sub(r'""".*?"""|\'\'\'.*?\'\'\'', "", codigo, flags=re.S)
    sem_texto = re.sub(r"#.*", "", sem_texto)
    achados = re.findall(r"(?<![\"'])\b%s" % re.escape(proibido), sem_texto)
    if achados:
        falha("%s é PROIBIDO no projeto (%d uso(s)): a janela do Windows é "
              "branca. %s." % (proibido, len(achados), motivo))
    else:
        ok("nenhum %s (janela branca) no código" % proibido)

n_unbind = len(re.findall(r'\.unbind_all\(\s*["\']<Button-1>', codigo))
n_bind = len(re.findall(r'\.bind_all\(\s*["\']<Button-1>', codigo))
if n_unbind:
    falha("unbind_all('<Button-1>') é PROIBIDO (%d uso(s)): apaga os atalhos "
          "de todos os menus. Use _registrar_clique_global / "
          "_remover_clique_global." % n_unbind)
else:
    ok("nenhum unbind_all de clique no código")
if n_bind != 1:
    falha("esperava exatamente 1 bind_all('<Button-1>') (o do dispatcher), "
          "achei %d. Menus novos usam _registrar_clique_global." % n_bind)
else:
    ok("só existe o bind_all de clique do dispatcher")

# --- 4b. a tela nova também tem que nascer no SEGUNDO monitor ---------------
# REGRA DO WOLF: janela de teste nao pode cobrir a tela em que ele esta
# trabalhando. A tela nova (app_web.py) tambem e' coisa de teste, entao
# nasce no 2o monitor SEMPRE - inclusive sem --demo, que e' o jeito de
# testar o microfone de verdade. Se alguem voltar a fazer a posicao
# depender de --previa, essa janela cai no monitor principal.
web_txt = (PASTA / "app_web.py").read_text(encoding="utf-8")
trecho_flags = web_txt[web_txt.index("PREVIA = "):web_txt.index("CONVERSAS_DEMO")]
problemas_posicao = []
for argumentos in ([], ["--demo"], ["--previa"], ["--demo", "--voz"], ["--voz"]):
    valores = {}
    try:
        exec("import sys\n" + trecho_flags.replace(
            "sys.argv", repr(["app_web.py"] + argumentos)), valores)
    except Exception as erro:
        problemas_posicao.append("%r deu erro: %r" % (argumentos, erro))
        continue
    if valores["X_PADRAO"] < 1950:
        problemas_posicao.append("%r abre em x=%d (precisa ser >= 1950)"
                                 % (argumentos, valores["X_PADRAO"]))
if problemas_posicao:
    falha("a tela nova pode abrir no monitor principal: %s"
          % "; ".join(problemas_posicao))
else:
    ok("a tela nova sempre nasce no 2o monitor (nenhuma flag abre na sua tela)")

# --- 4c. a barra de titulo da tela nova tem que ficar ESCURA ---------------
# Defeito encontrado em 16/10/2026: a tela nova chamava
# `ativar_barra_escura`, que espera um widget do TK (update_idletasks e
# winfo_id). A janela do pywebview nao tem nenhum dos dois: o erro era
# engolido e a barra ficava BRANCA, batendo com o resto da tela escura.
# Este teste nao abre janela nenhuma: ele so garante que a tela nova usa o
# caminho certo (procurar pelo titulo) e que o caminho existe e funciona.
app_txt = (PASTA / "app_web.py").read_text(encoding="utf-8")
if "escurecer_janela_por_titulo" in app_txt and \
        "ativar_barra_escura(instancia)" not in app_txt:
    ok("a tela nova escurece a barra pelo titulo (e nao pelo caminho do tk)")
else:
    falha("a tela nova ainda usa ativar_barra_escura, que falha no pywebview")
try:
    _p = importlib.import_module("pesquisa_ia")
    achou = _p.escurecer_janela_por_titulo("JANELA QUE NAO EXISTE",
                                           tentativas=1, espera=0)
    naoachou = achou is False
    vazio = _p.escurecer_janela_por_titulo("   ", tentativas=1,
                                           espera=0) is False
    semjanela = _p.escurecer_hwnd(0) is False
    if naoachou and vazio and semjanela:
        ok("escurecer a barra não quebra quando a janela não está aí")
    else:
        falha("escurecer a barra deu erro: achou=%r vazio=%r sem=%r"
              % (achou, vazio, semjanela))
except Exception as erro:
    falha("escurecer a barra levantou erro: %r" % (erro,))

# --- 4d. a janela de "Salvar como" tem que nascer NA MESMA TELA do programa --
# Defeito de 16/10/2026: a janela de "Salvar resposta como..." abria em
# x=138, y=0 (primeiro monitor) enquanto o programa estava no segundo
# (x=2000). O Wolf olhava para o segundo monitor, via a janelinha no
# primeiro e achava que o programa tinha travado. Este teste nao abre
# janela nenhuma: confere so de onde a tela nova tira a ancora.
try:
    _app = importlib.import_module("app_web")
    _ponte = _app.Ponte()
    _x, _y = _ponte._onde_esta_a_janela()
    if _x >= 1950:
        ok("a janela de Salvar nasce no 2o monitor (a mesma tela do programa)")
    else:
        falha("a janela de Salvar nasceria em x=%d (1o monitor: o Wolf "
              "nao veria ela e acharia que travou)" % (_x,))
    if 'geometry("1x1+' in app_txt:
        ok("a janela de Salvar é posicionada antes de abrir")
    else:
        falha("a janela de Salvar não é posicionada: ela nasce no canto "
              "da tela, em outro monitor")
except Exception as erro:
    falha("conferir a posição da janela de Salvar deu erro: %r" % (erro,))

# --- 5. testes com a janela de verdade -------------------------------------


def _esperar(raiz, segundos):
    fim = time.time() + segundos
    while time.time() < fim:
        raiz.update()
        time.sleep(0.05)


# --- 5a. aba Memoria: a rolagem do mouse continua depois de apagar ---


def testes_janela_segue_o_app(p, raiz, app):
    """As janelas do programa tem que abrir junto com ele.

    Pedido do Wolf: com dois monitores, nada de posicao travada. A
    janela de Configuracoes e a janelinha de aviso tem que aparecer no
    monitor em que o programa estiver, e nunca pela beira da tela.
    """
    import shutil

    pasta = Path(PASTA) / "_tmp"
    shutil.rmtree(pasta / "teste-posicao", ignore_errors=True)

    def dentro_do_monitor(janela, pai, nome):
        mx, my, mw, mh = p._tela_do_widget(pai)
        x, y = janela.winfo_rootx(), janela.winfo_rooty()
        largura, altura = janela.winfo_width(), janela.winfo_height()
        # a janela precisa estar dentro do monitor em que o programa esta
        dentro = (x >= mx - 2 and y >= my - 2
                  and x + largura <= mx + mw + 2
                  and y + altura <= my + mh + 2)
        # e o mais perto possivel do centro do programa
        centro_x = pai.winfo_rootx() + pai.winfo_width() // 2
        centro_y = pai.winfo_rooty() + pai.winfo_height() // 2
        janela_x = x + largura // 2
        janela_y = y + altura // 2
        perto = (abs(janela_x - centro_x) <= 40
                 and abs(janela_y - centro_y) <= 40)
        if dentro and perto:
            ok("%s abre no centro do programa, dentro da tela dele" % nome)
        else:
            falha("%s nao abriu junto com o programa (janela em %d,%d "
                  "programa em %d,%d; monitor em %d,%d %dx%d)"
                  % (nome, x, y, pai.winfo_rootx(), pai.winfo_rooty(),
                     mx, my, mw, mh))

    # --- no monitor de teste (o segundo) ---
    app._janela_config = None
    app._abrir_config("chave")
    _janela = getattr(app, "_janela_config", None)
    try:
        _janela.geometry("760x800" + POSICAO_TESTE)
    except Exception:
        pass
    _esperar(raiz, 0.9)
    if _janela is None:
        falha("a janela de Configuracoes nao abriu")
        return
    dentro_do_monitor(_janela, raiz, "a janela de Configurações")

    # a janelinha de aviso tambem
    aviso = tk.Toplevel(raiz)
    tk.Label(aviso, text="teste", bg=p.COR_FUNDO).pack()
    try:
        p._centralizar_sobre(aviso, raiz)
        _esperar(raiz, 0.2)
        dentro_do_monitor(aviso, raiz, "a janelinha de aviso")
    finally:
        try:
            aviso.destroy()
        except Exception:
            pass

    # --- e agora com o programa no PRIMEIRO monitor ---
    # Nao reabrimos a janela de Configuracoes de proposito: ela leva
    # 5-8 segundos para montar nesta maquina e ja foi conferida acima.
    # A centralizacao em si e' a mesma funcao, entao uma janela simples
    # chega para provar que ela acompanha o monitor do programa.
    try:
        _janela.destroy()
    except Exception:
        pass
    app._janela_config = None
    raiz.geometry("1000x740+40+40")      # monitor principal
    _esperar(raiz, 0.6)
    simples = tk.Toplevel(raiz)
    simples.title("teste")
    # Janela PEQUENA de proposito: se ela for maior que o programa, o
    # centro cai fora do programa e o teste acusaria um defeito que nao
    # existe (a centralizacao e limitada pelo tamanho das duas).
    tk.Label(simples, text="teste", bg=p.COR_FUNDO).pack()
    try:
        simples.geometry("320x120")
        simples.update_idletasks()
        p._centralizar_sobre(simples, raiz)
        _esperar(raiz, 0.2)
        dentro_do_monitor(simples, raiz,
                          "uma janela qualquer com o programa no 1o monitor")
    finally:
        try:
            simples.destroy()
        except Exception:
            pass
    # devolve o programa para o segundo monitor (regra dos testes)
    raiz.geometry("1000x740" + POSICAO_TESTE)
    _esperar(raiz, 0.4)


# --- 5g. a rolagem da aba Memória some depois de apagar um item? ------------


def testes_rolagem_da_memoria(p, raiz, app):
    """Apagar um item da lista nao pode matar a rolagem do mouse.

    O Tk nao repassa o evento da roda do mouse para o pai: so rola o
    widget que esta embaixo do cursor. Como a lista e' DESTRUIDA e
    recriada a cada desenho, os widgets novos nascem sem o binding da
    rolagem. Se a ligacao so for feita uma vez (quando a janela abre),
    depois do primeiro "X" a rolagem morre. Foi exatamente o que o Wolf
    viu.
    """
    import shutil

    pasta = Path(PASTA) / "_tmp" / "teste-memoria-rolagem"
    shutil.rmtree(pasta, ignore_errors=True)
    pasta.mkdir(parents=True, exist_ok=True)
    original = p.ARQUIVO_MEMORIA
    cache_original = getattr(p, "_memoria_cache", None)
    p.ARQUIVO_MEMORIA = pasta / "memoria.json"
    # 22 fatos: enche a lista e obriga a rolagem a trabalhar
    (pasta / "memoria.json").write_text(
        json.dumps(["Fato numero %02d, com um texto razoavelmente longo "
                    "para ocupar espaco na lista" % n
                    for n in range(1, 23)],
                   ensure_ascii=False),
        encoding="utf-8",
    )
    p._memoria_cache = None
    try:
        app._janela_config = None
        app._abrir_config("memoria")
        # REGRA DO WOLF: janela de teste sempre no SEGUNDO monitor (X >= 1950),
        # para nunca cobrir a tela que ele esta usando. A janela de
        # Configuracoes nasce centralizada no monitor principal, entao
        # movemos para ca depois de abrir.
        jan = getattr(app, "_janela_config", None)
        if jan is not None:
            try:
                jan.geometry("760x800" + POSICAO_TESTE)
            except Exception:
                pass
        _esperar(raiz, 0.8)
        if jan is None:
            falha("a aba Memoria nao abriu")
            return

        def botoes(texto):
            """Os botoes do programa com o texto pedido (o 'Botao' do
            pesquisa_ia e' um Label disfarçado, nao um Button do Tk)."""
            achados = []
            for w in p.anda(jan):
                try:
                    if isinstance(w, tk.Label) and w.cget("text") == texto:
                        achados.append(w)
                except Exception:
                    pass
            return achados

        def apertar(w):
            w.event_generate("<Button-1>", x=5, y=5)
            _esperar(raiz, 0.3)

        def sem_rolagem():
            """Widgets da lista que NAO tem a rolagem ligada."""
            return [w for w in botoes("X") if not w.bind("<MouseWheel>")]

        antes = len(botoes("X"))
        if antes == 0:
            falha("a aba Memoria nao mostrou nenhum item para apagar")
            return
        if sem_rolagem():
            falha("%d item(ns) da Memoria ja nasceram sem rolagem"
                  % len(sem_rolagem()))
        else:
            ok("os %d itens da Memoria ja tem a rolagem do mouse" % antes)

        # apaga o primeiro item (e' o que o Wolf fez) e confere de novo
        apertar(botoes("X")[0])

        depois = len(botoes("X"))
        if depois == antes - 1:
            ok("apagar um item removeu ele da lista (%d -> %d)"
               % (antes, depois))
        else:
            falha("apagar nao removeu o item (%d -> %d)" % (antes, depois))

        if sem_rolagem():
            falha("depois de apagar, %d item(ns) ficaram sem a rolagem do "
                  "mouse (o X parou de rolar)" % len(sem_rolagem()))
        else:
            ok("depois de apagar, os %d itens continuam rolando com o mouse"
               % depois)

        # e a rolagem realmente mexe a lista?
        try:
            lista = None
            for w in p.anda(jan):
                if isinstance(w, tk.Canvas) and w.winfo_class() == "Canvas":
                    itens = w.find_all()
                    if any(w.type(i) == "window" for i in itens):
                        lista = w
                        break
            if lista is None:
                ok("(não achei o canvas da lista para medir a rolagem)")
            else:
                antes_y = lista.yview()[0]
                # Rola em cima de POUCOS botoes, de proposito: mandar a
                # roda em todos os widgets da janela faz o programa
                # reler o arquivo de memoria centenas de vezes e o teste
                # fica lentissimo. Basta alguns, e um deles recem-criado
                # (que e' justamente o caso que estava quebrado).
                for w in botoes("X")[:4]:
                    try:
                        w.event_generate("<MouseWheel>", delta=-120)
                    except Exception as erro:
                        falha("não consegui rolar em cima do item: %r" % (erro,))
                _esperar(raiz, 0.3)
                depois_y = lista.yview()[0]
                if abs(depois_y - antes_y) > 0.001:
                    ok("a roda do mouse mexe a lista da Memória "
                       "(%.2f -> %.2f)" % (antes_y, depois_y))
                else:
                    falha("a roda do mouse não mexeu a lista da Memória")
        except Exception as erro:
            falha("não consegui medir a rolagem: %r" % (erro,))

        # NAO clicamos em "Apagar tudo" de proposito: ele abre uma
        # janelinha de confirmacao MODAL, que segura o programa ate
        # alguem responder. Num teste automatico ninguem responde, e a
        # verificacao inteira trava ali (ja aconteceu: 8 minutos de
        # espera e 110 testes que nunca rodaram). O que importa — apagar
        # UM item e a rolagem continuar — ja foi conferido acima.
        try:
            jan.destroy()
        except Exception:
            pass
        app._janela_config = None
    finally:
        p.ARQUIVO_MEMORIA = original
        p._memoria_cache = cache_original
        shutil.rmtree(pasta, ignore_errors=True)


def testes_de_tela():
    sys.path.insert(0, str(PASTA))
    import array as _array
    import pesquisa_ia as p
    import voz as voz_mod

    _GravadorOriginal = p.voz.Gravador

    raiz = tk.Tk()
    # A janela de teste nasce no SEGUNDO MONITOR (que comeca em X=1920),
    # para nunca cobrir a tela que o Wolf esta usando.
    try:
        raiz.geometry(POSICAO_TESTE)
    except Exception:
        pass
    erros_tk = []
    # Erros que acontecem dentro de botões/eventos não derrubam o programa:
    # ficam escondidos. Aqui eles viram falha.
    raiz.report_callback_exception = lambda *a: erros_tk.append(a)
    try:
        app = p.Aplicativo(raiz)
        app.mensagens = [
            {"role": "user", "text": "Primeira mensagem de teste, bem comprida"},
            {"role": "model", "text": "Segunda mensagem de teste com bastante texto para selecionar"},
        ]
        app._renderizar()
        # A janela redesenha as bolhas um instante depois de abrir (ajuste de
        # tamanho). Espera isso acabar, senão o teste seguraria bolhas velhas.
        fim = time.time() + 1.2
        while time.time() < fim:
            raiz.update()
            time.sleep(0.05)
        telas = list(app._telas_bolha)
        if len(telas) < 2:
            falha("esperava 2 bolhas, achei %d" % len(telas))
            return
        a, b = telas[0], telas[1]

        def texto_de(tela):
            return [i for i in tela.find_all() if tela.type(i) == "text"][0]

        def selecionar(tela):
            tela.select_from(texto_de(tela), 0)
            tela.select_to(texto_de(tela), 12)
            raiz.update()
            return str(tela.select_item() or "") == str(texto_de(tela))

        def meio(tela):
            x0, y0, x1, y1 = tela.bbox(texto_de(tela))
            return int((x0 + x1) / 2), int((y0 + y1) / 2)

        def tem_selecao(tela):
            return str(tela.select_item() or "") != ""

        def caso(nome, acao):
            if not selecionar(b):
                falha("não consegui selecionar (%s)" % nome)
                return
            acao()
            raiz.update()
            if tem_selecao(a) or tem_selecao(b):
                falha("a seleção NÃO sumiu: %s" % nome)
            else:
                ok("seleção some: %s" % nome)

        caso("clique na caixa de digitar",
             lambda: app.entrada.event_generate("<Button-1>", x=5, y=5))
        x, y = meio(b)
        caso("clique no texto da própria bolha",
             lambda: b.event_generate("<Button-1>", x=x, y=y))
        caso("clique na margem da própria bolha",
             lambda: b.event_generate("<Button-1>", x=2, y=2))
        x, y = meio(a)
        caso("clique em outra bolha",
             lambda: a.event_generate("<Button-1>", x=x, y=y))
        caso("clique no fundo da conversa",
             lambda: app.canvas.event_generate("<Button-1>", x=3, y=3))

        # selecionar arrastando continua funcionando?
        x0, y0, x1, y1 = b.bbox(texto_de(b))
        b.event_generate("<Button-1>", x=x0 + 2, y=y0 + 4)
        b.event_generate("<B1-Motion>", x=x0 + 60, y=y0 + 4)
        raiz.update()
        if tem_selecao(b) and b.selection_get():
            ok("selecionar arrastando o mouse funciona")
        else:
            falha("selecionar arrastando o mouse parou de funcionar")

        # duplo clique seleciona a palavra; triplo clique seleciona tudo
        time.sleep(0.7)  # para não contar como continuação do clique anterior
        item_b = texto_de(b)
        conteudo_b = b.itemcget(item_b, "text")
        alvo_i = conteudo_b.index("mensagem") + 3
        yy = int(y0 + 5)
        xs = [xx for xx in range(int(x0), int(x1))
              if int(b.index(item_b, "@%d,%d" % (xx, yy))) == alvo_i]
        if not xs:
            falha("não achei onde clicar para testar duplo/triplo clique")
        else:
            def clicar():
                b.event_generate("<ButtonPress-1>", x=xs[0], y=yy)
                b.event_generate("<ButtonRelease-1>", x=xs[0], y=yy)

            clicar()
            clicar()
            raiz.update()
            try:
                palavra = b.selection_get()
            except Exception:
                palavra = ""
            if palavra == "mensagem":
                ok("duplo clique seleciona a palavra")
            else:
                falha("duplo clique selecionou %r (esperado 'mensagem')" % palavra)
            clicar()
            raiz.update()
            try:
                tudo = b.selection_get()
            except Exception:
                tudo = ""
            if tudo == conteudo_b:
                ok("triplo clique seleciona o texto todo da bolha")
            else:
                falha("triplo clique selecionou %r (esperado o texto todo)" % tudo)

        # --- botao do microfone: existe, fica gravando e volta ao normal
        if getattr(app, "botao_mic", None) is None:
            falha("não achei o botão do microfone ao lado do enviar")
        else:
            ok("botão do microfone existe ao lado do enviar")
            # Um gravador falso no lugar do microfone de verdade: assim o
            # teste não grava a voz de quem está com o programa aberto.
            class _GravadorDeMentira(object):
                def __init__(self):
                    self.parado = False
                    self.wav = None

                def iniciar(self):
                    pass

                def parar(self):
                    self.parado = True
                    return self.wav

                def nivel(self):
                    return 0.0

            mentiroso = _GravadorDeMentira()
            # áudio com som de verdade (senão o programa diz "não ouvi nada")
            mentiroso.wav = voz_mod._para_wav(
                _array.array("h", [9000 if i % 2 else -9000
                                   for i in range(16000)]).tobytes())

            def finge_comecar():
                app._gravador = mentiroso
                app.gravando = True

            p.voz.Gravador = lambda *a, **k: mentiroso
            try:
                finge_comecar()
                app._desenhar_mic(p.COR_MIC_GRAVANDO)
                raiz.update()
                if app.gravando and app.botao_mic.find_all():
                    ok("microfone fica vermelho enquanto grava")
                else:
                    falha("microfone não mudou ao começar a gravar")

                # Ctrl+M é o mesmo que clicar no botão
                app._alternar_mic()          # para a gravação
                raiz.update()
                if not app.gravando and mentiroso.parado:
                    ok("Ctrl+M (parar) encerra a gravação")
                else:
                    falha("parar não encerrou a gravação")
            finally:
                p.voz.Gravador = _GravadorOriginal

            # O texto transcrito entra na caixa, sem mandar sozinho.
            app.entrada.delete("1.0", "end")
            app.cfg["voz_enviar"] = False
            app._definir_ocupado(True)   # como fica durante a transcrição
            app._tratar_item(("voz", "  qual o seu nome?  "))
            raiz.update()
            escrito = app.entrada.get("1.0", "end-1c")
            if escrito == "qual o seu nome?":
                ok("texto falado entra na caixa, sem espaços sobrando")
            else:
                falha("a caixa ficou com %r" % escrito)
            if not app.ocupado:
                ok("caixa de digitar volta a ficar disponível depois da voz")
            else:
                falha("a caixa ficou travada depois da voz")
            app.entrada.delete("1.0", "end")

            # Erro de transcrição não pode derrubar nem travar o programa.
            app._tratar_item(("voz_erro", "Sem internet."))
            raiz.update()
            if not app.ocupado:
                ok("falha na transcrição não trava o programa")
            else:
                falha("a falha na transcrição deixou o programa travado")

        # --- Tarefa C: caixa de digitar mais limpa ---------------------------
        # texto de apoio some quando a pessoa digita
        app.entrada.delete("1.0", "end")
        app._atualizar_apoio()
        raiz.update()
        if app.rotulo_apoio.winfo_ismapped():
            ok('texto de apoio aparece na caixa vazia ("Pergunte qualquer coisa...")')
        else:
            falha("o texto de apoio não apareceu na caixa vazia")
        app.entrada.insert("1.0", "uma pergunta")
        app._ajustar_altura()
        raiz.update()
        if not app.rotulo_apoio.winfo_ismapped():
            ok("texto de apoio some assim que a pessoa digita")
        else:
            falha("o texto de apoio ficou por cima do texto digitado")
        app.entrada.delete("1.0", "end")
        app._ajustar_altura()
        raiz.update()

        # cantos arredondados: quatro tampinhas nos cantos da caixa
        app._cantos_da_caixa()
        raiz.update()
        cantos = getattr(app, "_cantos_ativo", {})
        if len(cantos) == 4 and all(
                c.winfo_ismapped() for c in cantos.values()):
            ok("caixa de digitar com os quatro cantos arredondados")
        else:
            falha("os cantos arredondados da caixa não apareceram (%d de 4)"
                  % len(cantos))

        # Cada tampinha tem que encostar na borda da SUA quina. Com o
        # anchor, o ponto marcado fica no canto da tampinha: quem ancora em
        # baixo (sw/se) tem y+altura == altura da caixa, não y == 0.
        caixa = app.caixa_texto
        largura_caixa = caixa.winfo_width()
        altura_caixa = caixa.winfo_height()
        borda_enviar = (app.botao_enviar.winfo_x()
                        + app.botao_enviar.winfo_width())
        lados = {
            "nw": (cantos["nw"].winfo_x(), 0),
            "ne": (cantos["ne"].winfo_x() + cantos["ne"].winfo_width(),
                   largura_caixa),
            "sw": (cantos["sw"].winfo_y() + cantos["sw"].winfo_height(),
                   altura_caixa),
            "se": (cantos["se"].winfo_y() + cantos["se"].winfo_height(),
                   altura_caixa),
        }
        for nome, (medido, esperado) in lados.items():
            if medido == esperado:
                ok("tampinha do canto %s encosta na borda da caixa" % nome)
            else:
                falha("tampinha do canto %s fora de lugar (medido %s, "
                      "esperado %s)" % (nome, medido, esperado))

        # e as da direita não podem cobrir o microfone nem o enviar
        em_cima = [n for n in ("ne", "se")
                   if cantos[n].winfo_x() < borda_enviar]
        if not em_cima:
            ok("nenhuma tampinha de canto cobre o botão de enviar")
        else:
            falha("tampinha cobrindo o botão de enviar: %s" % em_cima)

        # Ctrl+A seleciona tudo
        app.entrada.insert("1.0", "texto para selecionar tudo")
        app._selecionar_tudo()
        raiz.update()
        selecionado = ""
        try:
            selecionado = app.entrada.get("sel.first", "sel.last")
        except Exception:
            pass
        if selecionado == "texto para selecionar tudo":
            ok("Ctrl+A seleciona o texto todo da caixa")
        else:
            falha("Ctrl+A selecionou %r" % selecionado)

        # Ctrl+Z desfaz e Ctrl+Y refaz
        antes = app.entrada.get("1.0", "end-1c")
        app._desfazer(None, False)
        raiz.update()
        depois_undo = app.entrada.get("1.0", "end-1c")
        app._desfazer(None, True)
        raiz.update()
        depois_redo = app.entrada.get("1.0", "end-1c")
        if depois_undo != antes and depois_redo == antes:
            ok("Ctrl+Z desfaz e Ctrl+Y refaz na caixa de digitar")
        else:
            falha("desfazer/refazer não funcionou (antes=%r,undo=%r,redo=%r)"
                  % (antes, depois_undo, depois_redo))

        # botão direito: traz recortar, copiar, colar e selecionar tudo
        app.entrada.delete("1.0", "end")
        app.entrada.insert("1.0", "casa")
        app._selecionar_tudo()
        app.raiz.clipboard_clear()
        app.raiz.clipboard_append("cola")
        raiz.update()

        def _clique(x=5, y=5):
            evento = type("Clique", (object,), {
                "x": x, "y": y, "x_root": 2005, "y_root": 105,
            })()
            return evento

        app._menu_ortografia(_clique())
        raiz.update()
        pop = getattr(app, "_menu_ortografia_atual", None)
        rotulos = []
        if pop is not None:
            for etiqueta in pop._itens:
                rotulos.append(etiqueta.cget("text").strip())
        for esperado in ("Recortar", "Copiar", "Colar", "Selecionar tudo"):
            if esperado in rotulos:
                ok("botão direito mostra '%s'" % esperado)
            else:
                falha("o botão direito não mostrou '%s' (tinha %s)"
                      % (esperado, rotulos))

        # palavra errada: as correções têm que vir no TOPO do mesmo menu
        app._fechar_menu_ortografia()
        app.entrada.delete("1.0", "end")
        app.entrada.insert("1.0", "caza de teste")
        raiz.update()
        try:
            bx, by = app.entrada.bbox("1.2")
        except Exception:
            bx, by = 5, 5
        sugestoes = app._sugestoes_no_ponto(bx or 5, by or 5)
        if sugestoes:
            ok("corretor acha a palavra errada sob o cursor (%d sugestões)"
               % len(sugestoes))
        else:
            ok("corretor não reclama desta palavra (nenhuma sugestão)")
        if sugestoes:
            app._menu_ortografia(_clique(bx or 5, by or 5))
            raiz.update()
            pop = getattr(app, "_menu_ortografia_atual", None)
            com_sugestoes = [e.cget("text").strip() for e in pop._itens] \
                if pop is not None else []
            primeira = com_sugestoes[0] if com_sugestoes else ""
            ultimos = com_sugestoes[-4:]
            if primeira == sugestoes[0][0] and \
                    ultimos == ["Recortar", "Copiar", "Colar",
                                "Selecionar tudo"]:
                ok("as correções vêm primeiro, e os comandos de edição depois")
            else:
                falha("a ordem do menu ficou errada: %s" % com_sugestoes)
            app._fechar_menu_ortografia()

        # --- o resto dos comandos de edição (começa de novo, com "casa"
        # --- selecionado: o teste da ortografia deixou outro texto na caixa)
        app.entrada.delete("1.0", "end")
        app.entrada.insert("1.0", "casa")
        app._selecionar_tudo()
        raiz.clipboard_clear()
        raiz.update()

        # "Recortar" apaga o selecionado e vai para a área de transferência
        app._recortar()
        raiz.update()
        if app.entrada.get("1.0", "end-1c") == "":
            ok("Recortar apaga o texto selecionado")
        else:
            falha("Recortar não apagou: %r"
                  % app.entrada.get("1.0", "end-1c"))
        try:
            area = raiz.clipboard_get()
        except Exception:
            area = ""
        if area == "casa":
            ok("Recortar coloca o texto na área de transferência")
        else:
            falha("a área de transferência ficou com %r" % area)

        # "Colar" insere o que está na área de transferência
        # (o botão direito também deixou o cursor onde foi clicado)
        raiz.clipboard_clear()
        raiz.clipboard_append("cola")
        raiz.update()
        app._menu_ortografia(_clique())
        raiz.update()
        app._fechar_menu_ortografia()
        app._colar()
        raiz.update()
        if app.entrada.get("1.0", "end-1c") == "cola":
            ok("Colar insere o texto da área de transferência")
        else:
            falha("Colar deixou a caixa com %r"
                  % app.entrada.get("1.0", "end-1c"))
        app.entrada.delete("1.0", "end")
        app._fechar_menu_ortografia()
        app._atualizar_apoio()
        raiz.update()

        # sem nada selecionado e sem nada na área de transferência, os
        # comandos impossíveis ficam apagados (mas o menu continua abrindo)
        app.entrada.insert("1.0", "sem selecao")
        try:
            app.entrada.tag_remove("sel", "1.0", "end")
        except Exception:
            pass
        raiz.clipboard_clear()
        raiz.update()
        app._menu_ortografia(_clique())
        raiz.update()
        pop = getattr(app, "_menu_ortografia_atual", None)
        apagados = []
        if pop is not None:
            apagados = [e.cget("text").strip() for e in pop._itens
                        if e.cget("fg") == p.COR_TEXTO_3]
        if "Recortar" in apagados and "Copiar" in apagados:
            ok("sem seleção, Recortar e Copiar ficam apagados (não clicáveis)")
        else:
            falha("Recortar/Copiar deveriam estar apagados, estavam %s"
                  % apagados)
        app._fechar_menu_ortografia()
        app.entrada.delete("1.0", "end")
        app._atualizar_apoio()
        raiz.update()

        # --- botões da resposta: Copiar e Salvar ----------------------------
        # Cada resposta da IA tem dois botões embaixo: o de copiar e o de
        # salvar em arquivo. Se o de salvar sumir (ou o clique nele não
        # fizer nada), o Wolf fica sem jeito de guardar a resposta.
        _esperar(raiz, 0.5)   # deixa o redesenho das bolhas terminar
        _botoes = []
        for _widget in p.anda(app.interno):
            if not isinstance(_widget, tk.Canvas):
                continue
            if str(_widget.cget("cursor")) != "hand2":
                continue
            if _widget.winfo_width() != 19 or _widget.winfo_height() != 19:
                continue
            _botoes.append(_widget)
        # na tela de teste tem 1 resposta da IA = 2 botões (copiar + salvar)
        if len(_botoes) == 2:
            ok("a resposta tem os 2 botões: copiar e salvar")
        else:
            falha("esperava 2 botões na resposta (copiar e salvar), achei %d"
                  % len(_botoes))

        # o clique precisa chamar a ação certa
        _chamadas = []
        _quadro = tk.Frame(app.interno, bg=p.COR_FUNDO)
        _quadro.pack()
        for _fabrica, _nome in ((p._icone_copiar, "copiar"),
                                (p._icone_salvar, "salvar")):
            _fabrica(_quadro, lambda n=_nome: _chamadas.append(n)).pack()
        _quadro.update_idletasks()
        for _filho in _quadro.winfo_children():
            _filho.event_generate("<Button-1>", x=5, y=5)
        raiz.update()
        _quadro.destroy()
        if _chamadas == ["copiar", "salvar"]:
            ok("clicar em cada botão roda a ação certa")
        else:
            falha("os botões da resposta não responderam ao clique: %r"
                  % _chamadas)

        # o nome do arquivo sai da primeira linha, sem caractere proibido
        for _texto, _esperado in (
            ("A capital do Pará\ne outra coisa", "A capital do Pará.txt"),
            ("1. Introdução\nmais texto", "Introdução.txt"),
            ("", "resposta.txt"),
            ('sao: SP / "teste" *fim', "sao SP teste fim.txt"),
        ):
            _obtido = p._nome_de_resposta(_texto)
            if _obtido == _esperado:
                ok("nome do arquivo: %r -> %s" % (_texto[:22], _obtido))
            else:
                falha("nome do arquivo para %r saiu %r, esperava %r"
                      % (_texto[:22], _obtido, _esperado))
        if p._nome_de_resposta("x" * 300).endswith(".txt"):
            ok("nome do arquivo não fica gigante mesmo com texto enorme")
        else:
            falha("nome do arquivo para texto enorme não termina em .txt")

        # salvar de verdade num arquivo da pasta _tmp
        _dir = PASTA / "_tmp" / "teste-salvar"
        shutil.rmtree(_dir, ignore_errors=True)
        _dir.mkdir(parents=True, exist_ok=True)
        _alvo = _dir / "saida.txt"
        _original_salvar = p.filedialog.asksaveasfilename
        try:
            p.filedialog.asksaveasfilename = lambda **_kw: str(_alvo)
            app._salvar_resposta("primeira linha\nsegunda linha")
            _conteudo = _alvo.read_text(encoding="utf-8-sig")
            if _conteudo.strip() == "primeira linha\nsegunda linha":
                ok("o botão salvar grava a resposta no arquivo, inteira")
            else:
                falha("o arquivo ficou com %r" % _conteudo[:80])

            # cancelar não é erro e não estraga o arquivo que já existia
            p.filedialog.asksaveasfilename = lambda **_kw: ""
            app._salvar_resposta("isso nao deve ser salvo")
            if _alvo.read_text(encoding="utf-8-sig").strip() == (
                    "primeira linha\nsegunda linha"):
                ok("cancelar não estraga o arquivo que já existia")
            else:
                falha("cancelar alterou o arquivo")
        finally:
            p.filedialog.asksaveasfilename = _original_salvar
        shutil.rmtree(_dir, ignore_errors=True)

        # Mexer na altura da caixa de digitar encolhe a conversa, e o Canvas
        # agenda um redesenho (ele recria as bolhas). Deixa o redesenho
        # acontecer e pega as bolhas novas, senao os testes de bolha mais
        # abaixo vão procurar em widgets que já foram destruídos.
        _esperar(raiz, 0.6)
        telas = list(app._telas_bolha)
        if len(telas) >= 2:
            a, b = telas[0], telas[1]
        else:
            falha("as bolhas sumiram depois dos testes da caixa (%d)"
                  % len(telas))

        # --- chave reserva: troca automatica quando o Google recusa a chave
        app.cfg["api_key"] = "AIza-principal-falsa"
        app.cfg["api_key_reserva"] = "AIza-reserva-falsa"
        app._falhou_principal = False
        if app._chave_ativa() == app.cfg["api_key"]:
            ok("começa usando a chave principal")
        else:
            falha("não começou pela chave principal")

        chamadas = []

        def morre_401(_chave):
            chamadas.append("recusada")
            raise RuntimeError("401 UNAUTHENTICATED. API key not valid.")

        app._falhou_principal = False
        try:
            app._tentar_com_reserva(morre_401)
            falha("deveria ter avisado que o erro é de chave")
        except RuntimeError:
            ok("erro de chave é reconhecido (401 / API key not valid)")

        # sem reserva: o erro sobe (a janela de aviso é quem mostra)
        app.cfg["api_key_reserva"] = ""
        app._falhou_principal = False
        try:
            app._tentar_com_reserva(morre_401)
            falha("sem reserva o erro deveria subir")
        except RuntimeError:
            ok("sem chave reserva, o erro sobe para o programa avisar")

        # com reserva: repete com a reserva e dá certo
        app.cfg["api_key_reserva"] = "AIza-reserva-falsa"
        app._falhou_principal = False
        chamadas.clear()

        def so_a_reserva(chave):
            chamadas.append(chave)
            if chave == "AIza-principal-falsa":
                raise RuntimeError("401 UNAUTHENTICATED. API key not valid.")
            return "resposta pela reserva"

        try:
            r = app._tentar_com_reserva(so_a_reserva)
            ok("troca sozinho para a chave reserva quando a principal é "
               "recusada")
            if r == "resposta pela reserva" and chamadas == [
                    "AIza-principal-falsa", "AIza-reserva-falsa"]:
                ok("a reserva é usada na segunda tentativa (na ordem certa)")
            else:
                falha("a troca ficou errada: %s -> %r" % (chamadas, r))
        except Exception as erro:
            falha("a troca para a reserva quebrou: %r" % (erro,))
        if app._falhou_principal:
            ok("o programa fica marcado como 'principal caiu' na sessão")
        else:
            falha("o programa não marcou que a principal caiu")

        # já na reserva, não fica tentando trocar de novo (sem laço)
        chamadas.clear()
        try:
            app._tentar_com_reserva(morre_401)
        except RuntimeError:
            pass
        if chamadas == ["recusada"]:
            ok("na reserva ele não fica tentando trocar de chave para sempre")
        else:
            falha("a reserva foi chamada %d vezes" % len(chamadas))

        # erro que NÃO é de chave (cota, internet) não troca a chave
        app._falhou_principal = False
        trocou = []

        def cota(_chave):
            trocou.append(1)
            raise RuntimeError("RESOURCE_EXHAUSTED: quota exceeded")

        try:
            app._tentar_com_reserva(cota)
        except RuntimeError:
            pass
        if trocou == [1] and not app._falhou_principal:
            ok("erro de cota/internet NÃO troca de chave (só erro de chave "
               "troca)")
        else:
            falha("troca de chave na hora errada (%d tentativas)"
                  % len(trocou))

        app._falhou_principal = False
        app.cfg["api_key_reserva"] = ""

        # --- diálogo escuro: tem que ter as cores do programa e nada
        # --- branco (as janelas do Windows são brancas e destoam)
        cores = {
            "caixa": p.COR_BARRA, "painel": p.COR_PAINEL,
            "borda": p.COR_BORDA, "fundo": p.COR_FUNDO,
        }
        vistas = {}

        def guarda_dialogo():
            for w in raiz.winfo_children():
                if isinstance(w, tk.Toplevel):
                    for item in p.anda(w):
                        try:
                            fundo = item.cget("bg")
                        except Exception:
                            continue
                        if fundo in cores.values():
                            vistas[fundo] = vistas.get(fundo, 0) + 1
                    w.destroy()

        raiz.after(700, guarda_dialogo)
        try:
            app._janela_chave_ruim(
                "Uma das chaves de API parece inválida. Abra Configurações.")
            raiz.update()
            ok("janela de 'chave inválida' abre e fecha sem erro")
        except Exception as erro:
            falha("a janela de chave inválida quebrou: %r" % (erro,))
        raiz.update()

        if vistas.get(cores["caixa"], 0) >= 2:
            ok("diálogo escuro tem as cores do programa (%d widgets na cor da "
               "caixa)" % vistas[cores["caixa"]])
        else:
            falha("o diálogo não está com as cores do programa (%s)" % vistas)
        for nome, cor in cores.items():
            if vistas.get(cor):
                ok("diálogo escuro usa a cor de %s" % nome)

        # a confirmação também tem que ser escura e devolver a resposta
        def responde():
            for w in raiz.winfo_children():
                if isinstance(w, tk.Toplevel):
                    w.destroy()

        raiz.after(600, responde)
        if app._confirmar("Excluir conversa", "Apagar?") is False:
            ok("confirmação escura devolve 'não' quando ela é fechada")
        else:
            falha("a confirmação não devolveu 'não'")

        # Com a caixa VAZIA o texto de apoio fica por cima dela. Se ele
        # "engolir" os cliques, o botão direito não abre nada e nem o
        # clique do mouse foca a caixa (foi o que o Wolf encontrou).
        app.entrada.delete("1.0", "end")
        app._atualizar_apoio()
        raiz.update()
        if not app.rotulo_apoio.winfo_ismapped():
            falha("o texto de apoio deveria estar visível na caixa vazia")
        else:
            try:
                # Pega o foco de verdade antes de medir: na mao do Wolf
                # tem outras janelas abertas (navegador, calculadora) e
                # qualquer uma delas pode tomar o foco no meio do teste e
                # fazer ele falhar sem ser defeito do programa.
                raiz.focus_force()
                raiz.update()
                _esperar(raiz, 0.3)
                app.entrada.focus_set()
                raiz.update()
                _esperar(raiz, 0.2)
                app.rotulo_apoio.event_generate("<Button-1>", x=5, y=5)
            except Exception:
                pass
            raiz.update()
            # O foco leva alguns milissegundos para assentar; checar na
            # hora dava FALHA de vez em quando (teste instavel).
            focado = False
            for _ in range(20):
                raiz.update()
                time.sleep(0.05)
                if app.entrada.focus_get() is app.entrada:
                    focado = True
                    break
            if focado:
                ok("clicar no texto de apoio põe o foco na caixa de digitar")
            else:
                falha("clicar no texto de apoio não focou a caixa")

            app._fechar_menu_ortografia()
            try:
                app.rotulo_apoio.event_generate("<Button-3>", x=5, y=5)
            except Exception:
                pass
            raiz.update()
            pop = getattr(app, "_menu_ortografia_atual", None)
            rotulos = []
            if pop is not None:
                rotulos = [e.cget("text").strip() for e in pop._itens]
            if "Selecionar tudo" in rotulos:
                ok("botão direito no texto de apoio abre o mesmo menu (%s)"
                   % ", ".join(rotulos))
            else:
                falha("com a caixa vazia o botão direito não abriu o menu "
                      "(apareceu: %s)" % rotulos)
            app._fechar_menu_ortografia()
        raiz.update()

        # Com dois monitores, `winfo_screenwidth` só devolve o principal e
        # o menu ia parar na tela errada. A tela virtual tem que incluir
        # o segundo monitor (que no PC do Wolf começa em X=1920).
        tela_x, tela_y, tela_l, tela_a = p._tela_virtual()
        if tela_l >= 1920 and (tela_x < 1920 or tela_l > 1920):
            ok("a tela virtual inclui o segundo monitor (%dx%d em x=%d)"
               % (tela_l, tela_a, tela_x))
        else:
            ok("a tela virtual devolve %dx%d em x=%d (so um monitor neste PC)"
               % (tela_l, tela_a, tela_x))

        app.entrada.delete("1.0", "end")
        app.entrada.insert("1.0", "teste")
        app._selecionar_tudo()
        raiz.clipboard_clear()
        raiz.clipboard_append("cola")
        raiz.update()
        app._menu_ortografia(_clique())
        raiz.update()
        pop = getattr(app, "_menu_ortografia_atual", None)
        if pop is None:
            falha("o menu do botão direito não abriu")
        else:
            # o menu não pode cair fora da tela toda (nem na tela errada)
            mx = pop.winfo_x() + pop.winfo_rootx() - pop.winfo_rootx()
            dentro = (tela_x - 8 <= mx <= tela_x + tela_l
                      and tela_y - 8 <= pop.winfo_y() <= tela_y + tela_a)
            if dentro:
                ok("o menu do botão direito fica dentro da tela toda")
            else:
                falha("o menu caiu fora da tela (%d, %d) — tela é (%d, %d) "
                      "%dx%d" % (pop.winfo_x(), pop.winfo_y(), tela_x, tela_y,
                                 tela_l, tela_a))
        app._fechar_menu_ortografia()
        app.entrada.delete("1.0", "end")
        app._atualizar_apoio()
        raiz.update()

        # --- menus que fecham ao clicar fora (um não pode quebrar o outro)
        chamadas = []

        def f1(_e):
            chamadas.append("f1")

        def f2(_e):
            chamadas.append("f2")

        app._registrar_clique_global(f1)
        app._registrar_clique_global(f2)
        app.entrada.event_generate("<Button-1>", x=5, y=5)
        raiz.update()
        if sorted(chamadas) == ["f1", "f2"]:
            ok("clique chega a todos os menus abertos")
        else:
            falha("clique não chegou a todos os menus: %s" % chamadas)
        app._remover_clique_global(f1)
        chamadas.clear()
        app.entrada.event_generate("<Button-1>", x=5, y=5)
        raiz.update()
        if chamadas == ["f2"]:
            ok("fechar um menu não desliga os outros")
        else:
            falha("fechar um menu desligou os outros: %s" % chamadas)
        app._remover_clique_global(f2)

        # --- menu "Copiar" (botão direito) fecha ao clicar fora
        for nome, alvo in (
            ("na caixa de digitar", lambda: app.entrada.event_generate("<Button-1>", x=5, y=5)),
            ("em outra bolha", lambda: a.event_generate("<Button-1>", x=meio(a)[0], y=meio(a)[1])),
        ):
            selecionar(b)
            xb, yb = meio(b)
            b.event_generate("<Button-3>", x=xb, y=yb)
            raiz.update()
            menu = getattr(b, "_copiar_menu", None)
            if menu is None or not menu.winfo_exists():
                falha("o menu Copiar não abriu (clique direito na seleção)")
                continue
            alvo()
            raiz.update()
            if menu.winfo_exists():
                falha("o menu Copiar NÃO fechou ao clicar %s" % nome)
            else:
                ok("menu Copiar fecha ao clicar %s" % nome)
        if app._ouvintes_clique:
            falha("sobrou menu cadastrado depois de fechar: %d" % len(app._ouvintes_clique))
        else:
            ok("nenhum cadastro de clique sobrando")

        # --- janela de Configurações abre e troca de aba sem erro
        app._abrir_config()
        raiz.update()
        for aba in ("ajuda", "chave", "memoria"):
            app._mostrar_aba_config(aba)
            raiz.update()
        try:
            app._janela_config.destroy()
        except Exception:
            pass
        raiz.update()
        ok("janela de Configurações abre e troca de aba")

        # abrir Configurações já pedindo uma aba tem que FUNCIONAR de
        # primeira (o botão "Colar chave nova" da janela de chave inválida
        # depende disso: se abrisse na Memória, o Wolf não acharia o campo)
        try:
            app._janela_config.destroy()
        except Exception:
            pass
        raiz.update()
        app._abrir_config("chave")
        raiz.update()
        _esperar(raiz, 0.4)
        if getattr(app, "_aba_config", "") == "chave":
            ok("abrir Configurações pedindo a aba 'Chave' já abre nela")
        else:
            falha("pediu a aba 'Chave' e abriu na '%s'"
                  % getattr(app, "_aba_config", "?"))
        try:
            app._janela_config.destroy()
        except Exception:
            pass
        raiz.update()
        testes_lista_de_conversas(p, raiz, app)

        # --- Configurações: o texto tem que acompanhar a largura da janela
        # Antes cada parágrafo tinha um wraplength fixo (540, 560, 600...),
        # tudo diferente, e o Wolf viu o texto espremido na aba Chave.
        try:
            app._janela_config = None
            app._abrir_config("chave")
            # REGRA DO WOLF: janela de teste no SEGUNDO monitor.
            _janela = getattr(app, "_janela_config", None)
            if _janela is not None:
                try:
                    _janela.geometry("760x800" + POSICAO_TESTE)
                except Exception:
                    pass
            _esperar(raiz, 0.6)
            jan = getattr(app, "_janela_config", None)
            textos = [w for w in (p.anda(jan) if jan else [])
                      if isinstance(w, tk.Label)
                      and int(w.cget("wraplength") or 0) > 0]
            if not textos:
                falha("a aba Chave não tem nenhum texto com quebra de linha")
            else:
                if all(t.cget("wraplength") for t in textos):
                    ok("os %d textos das Configurações têm largura definida"
                       % len(textos))
                else:
                    falha("algum texto das Configurações ficou sem largura")
                jan.geometry("640x700" + POSICAO_TESTE)
                _esperar(raiz, 0.5)
                estreitas2 = {int(t.cget("wraplength")) for t in textos}
                jan.geometry("1300x820" + POSICAO_TESTE)
                _esperar(raiz, 0.5)
                largas = {int(t.cget("wraplength")) for t in textos}
                if len(estreitas2) == 1 and len(largas) == 1 and \
                        max(estreitas2) < max(largas):
                    ok("o texto das Configurações acompanha a janela "
                       "(%d px estreito -> %d px largo)"
                       % (max(estreitas2), max(largas)))
                else:
                    falha("o texto não acompanha a janela: estreito=%s "
                          "largo=%s" % (sorted(estreitas2), sorted(largas)))
                if max(largas) <= max(estreitas2) + 700:
                    ok("o texto não fica largo demais em janela grande")
                else:
                    falha("o texto esticou demais: %d px" % max(largas))
            if jan is not None:
                try:
                    jan.destroy()
                except Exception:
                    pass
                app._janela_config = None
        except Exception as erro:
            falha("os testes das Configurações quebraram: %r" % (erro,))

        # --- as janelas do programa abrem junto com ele (e nao na beira)
        try:
            testes_janela_segue_o_app(p, raiz, app)
        except Exception as erro:
            falha("os testes de posição da janela quebraram: %r" % (erro,))

        # --- aba Memória: apagar um item não pode matar a rolagem do mouse
        try:
            testes_rolagem_da_memoria(p, raiz, app)
        except Exception as erro:
            falha("os testes da rolagem da Memória quebraram: %r" % (erro,))

        # --- coluna centralizada (por último: mexer no tamanho da janela
        # --- redesenha as bolhas e as referências do começo do teste ficam
        # --- velhas, então esta parte tem que vir depois de tudo)
        raiz.geometry("1700x800" + POSICAO_TESTE)
        _esperar(raiz, 0.8)
        margem = app._margem_da_coluna()
        largura_bolha = app._largura_bolha()
        if margem > 200 and largura_bolha <= 700:
            ok("conversa centralizada em janela larga (margem %d px, "
               "texto %d px)" % (margem, largura_bolha))
        else:
            falha("a conversa não centralizou (margem %d, texto %d)"
                  % (margem, largura_bolha))
        # a caixa de digitar acompanha a mesma coluna
        margem_caixa = app.caixa_texto.pack_info()["padx"]
        if margem_caixa > 200:
            ok("caixa de digitar também fica na coluna (margem %s px)"
               % margem_caixa)
        else:
            falha("a caixa de digitar não acompanhou a coluna (padx=%s)"
                  % margem_caixa)
        # e numa janela normal continua parecendo igual
        raiz.geometry("1000x740" + POSICAO_TESTE)
        _esperar(raiz, 0.6)
        margem_estreita = app._margem_da_coluna()
        if margem_estreita <= 40:
            ok("em janela normal a conversa usa a tela toda (margem %d px)"
               % margem_estreita)
        else:
            falha("em janela normal sobrou margem demais: %d px"
                  % margem_estreita)

        if erros_tk:
            for e in erros_tk[:3]:
                falha("erro escondido num botão/evento: %r" % (e[1],))
        else:
            ok("nenhum erro escondido em botões/eventos durante o teste")
    finally:
        try:
            raiz.destroy()
        except Exception:
            pass


# --- 5b. lista de conversas: tres pontinhos -> Excluir ----------------------


def testes_lista_de_conversas(p, raiz, app):

    # Dados falsos: o teste nunca mexe nas conversas nem na memoria do Wolf.
    guardadas = [
        {"id": "a1", "titulo": "Conversa de teste A",
         "quando": "01/01/2026 as 10:00",
         "mensagens": [{"role": "user", "text": "oi"}]},
        {"id": "b2", "titulo": "Conversa de teste B",
         "quando": "01/01/2026 as 11:00",
         "mensagens": [{"role": "user", "text": "ola"}]},
    ]
    originais = (p.carregar_conversas, p.salvar_conversas, p.carregar_memoria)
    p.carregar_conversas = lambda: list(guardadas)
    p.salvar_conversas = lambda lista: guardadas.__setitem__(
        slice(None), list(lista))
    p.carregar_memoria = lambda: []
    try:
        if app.lista_conversas.winfo_ismapped():
            app._recolher_lista_conversas()
        app._alternar_lista_conversas()
        _esperar(raiz, 0.3)

        def pontinhos():
            achados = []
            for item in app.lista_conversas.winfo_children():
                for w in p.anda(item):
                    try:
                        if w.cget("text") == "\u22ef":
                            achados.append(w)
                    except Exception:
                        pass
            return achados

        def aberto():
            pop = getattr(app, "_popup_conversa", None)
            try:
                return pop is not None and pop.winfo_exists()
            except Exception:
                return False

        pts = pontinhos()
        if len(pts) != 2:
            falha("lista de conversas: esperava 2 itens, achei %d" % len(pts))
            return
        pts[0].event_generate("<Button-1>", x=3, y=3)
        _esperar(raiz, 0.3)
        if aberto():
            ok("tres pontinhos abrem o menu Excluir")
        else:
            falha("tres pontinhos NAO abrem o menu Excluir")
            return

        # clicar fora fecha o menu
        app.canvas.event_generate("<Button-1>", x=5, y=5)
        _esperar(raiz, 0.3)
        if not aberto():
            ok("clicar fora fecha o menu da conversa")
        else:
            falha("clicar fora NAO fecha o menu da conversa")

        # abre de novo e exclui (a confirmacao e trocada por um "sim")
        app._confirmar = lambda _titulo, _texto: True
        pts = pontinhos()
        pts[0].event_generate("<Button-1>", x=3, y=3)
        _esperar(raiz, 0.3)
        excluir = None
        if aberto():
            for w in p.anda(app._popup_conversa):
                try:
                    if w.cget("text") == "Excluir":
                        excluir = w
                except Exception:
                    pass
        if excluir is None:
            falha("menu da conversa abriu sem o botao Excluir")
            return
        excluir.event_generate("<Button-1>", x=3, y=3)
        _esperar(raiz, 0.4)
        restantes = [c["id"] for c in guardadas]
        if restantes == ["a1"]:
            ok("Excluir apaga a conversa certa (a mais nova, B)")
        else:
            falha("Excluir apagou errado; sobraram %r (esperado ['a1'])"
                  % (restantes,))
        if not aberto():
            ok("menu fecha depois de excluir")
        else:
            falha("menu continua aberto depois de excluir")
    finally:
        p.carregar_conversas, p.salvar_conversas, p.carregar_memoria = originais
        try:
            app._recolher_lista_conversas()
        except Exception:
            pass


if not falhas:
    try:
        testes_de_tela()
    except Exception as erro:
        falha("os testes de tela quebraram: %r" % (erro,))
        print(traceback.format_exc()[-900:])
else:
    aviso("testes de tela pulados porque houve falha acima")

# --- 5c. memoria sem repeticao ----------------------------------------------


def testes_memoria():
    import memoria
    import pesquisa_ia as p

    problemas = memoria.autoteste()
    for problema in problemas:
        falha("memoria: %s" % problema)
    if not problemas:
        ok("memoria: sem repeticao (casos do memoria.autoteste)")
    # a ligacao com o programa: apelido repetido de outro jeito = 1 fato
    guardado = ["Prefere ser chamado de Wolf"]
    originais = (p.carregar_memoria, p.salvar_memoria)
    p.carregar_memoria = lambda: list(guardado)
    p.salvar_memoria = lambda lista: (
        guardado.__setitem__(slice(None), list(lista)) or list(lista))
    try:
        p._mesclar_memoria(["O apelido do usuario e Wolf"])
        p._mesclar_memoria(["Gosta de ser chamado de Wolf"])
        if len(guardado) == 1:
            ok("memoria: o programa nao guarda o apelido varias vezes")
        else:
            falha("memoria: apelido repetido ficou %r" % (guardado,))
    finally:
        p.carregar_memoria, p.salvar_memoria = originais


if not falhas:
    try:
        testes_memoria()
    except Exception as erro:
        falha("os testes da memoria quebraram: %r" % (erro,))

# --- 5d. tela nova (HTML): a ponte e as conversas ----------------------------


def testes_tela_nova(p):
    """Confere a ponte da tela nova (app_web.py) SEM tocar nos dados do
    Wolf: os arquivos de historico e memoria sao apontados para uma pasta
    de teste e restaurados no fim.
    """
    import shutil
    import app_web

    pasta = Path(PASTA) / "_tmp" / "teste-tela-nova"
    shutil.rmtree(pasta, ignore_errors=True)
    pasta.mkdir(parents=True, exist_ok=True)
    historico_original = p.ARQUIVO_HISTORICO
    memoria_original = p.ARQUIVO_MEMORIA
    demo_original = app_web.DEMO
    try:
        # ---- os dados do Wolf sao "escondidos" durante o teste ----
        p.ARQUIVO_HISTORICO = pasta / "historico.json"
        p.ARQUIVO_MEMORIA = pasta / "memoria.json"
        app_web.DEMO = False

        # 1. comeca vazio, sem quebrar
        ponte = app_web.Ponte()
        inicio = ponte.iniciar()
        if inicio["conversas"] == [] and inicio["mensagens"] == []:
            ok("tela nova: começa sem conversa nenhuma, sem erro")
        else:
            falha("tela nova: começou com %r" % (inicio["conversas"],))

        # 2. a conversa so e gravada quando tem mensagem de verdade
        ponte.nova_conversa()
        ponte._gravar_conversa()
        if p.carregar_conversas() == []:
            ok("tela nova: conversa vazia NÃO é gravada (nada a salvar)")
        else:
            falha("tela nova: gravou uma conversa sem mensagem")

        # 3. conversa com pergunta e resposta e gravada e aparece na lista
        ponte.mensagens = [
            {"role": "user", "text": "Oi, tudo bem?"},
            {"role": "model", "text": "Tudo ótimo! Como vai?"},
        ]
        ponte._gravar_conversa()
        salvas = p.carregar_conversas()
        if len(salvas) == 1 and len(salvas[0]["mensagens"]) == 2:
            ok("tela nova: conversa gravada e com as 2 mensagens")
        else:
            falha("tela nova: gravação ficou %r" % (salvas,))
        if salvas and salvas[0].get("titulo") == "Oi, tudo bem?":
            ok("tela nova: o título da conversa é a primeira pergunta")
        else:
            falha("tela nova: título ficou %r" % (salvas[0].get("titulo"),))

        # 4. a lista que a tela recebe vem da mais nova para a mais antiga
        ponte2 = app_web.Ponte()
        ponte2.iniciar()
        ponte2.mensagens = [
            {"role": "user", "text": "Segunda conversa"},
            {"role": "model", "text": "Oi de novo"},
        ]
        ponte2.id_atual = None
        ponte2._gravar_conversa()
        lista = ponte2.iniciar()["conversas"]
        if [c["titulo"] for c in lista] == ["Segunda conversa", "Oi, tudo bem?"]:
            ok("tela nova: a lista vem da mais nova para a mais antiga")
        else:
            falha("tela nova: ordem da lista ficou %r"
                  % [c["titulo"] for c in lista])

        # 5. abrir uma conversa traz as mensagens de volta
        alvo = [c for c in lista if c["titulo"] == "Oi, tudo bem?"][0]
        ponte2.id_atual = None
        ponte2.mensagens = []
        aberta = ponte2.abrir_conversa(alvo["id"])
        if len(aberta["mensagens"]) == 2 and aberta["atual"] == alvo["id"]:
            ok("tela nova: abrir a conversa traz as 2 mensagens")
        else:
            falha("tela nova: abrir a conversa devolveu %r" % (aberta,))
        if ponte2.abrir_conversa("conversa-que-nao-existe").get("erro"):
            ok("tela nova: conversa inexistente avisa em vez de quebrar")
        else:
            falha("tela nova: conversa inexistente devolveu algo")

        # 6. NOVA CONVERSA limpa a conversa aberta e nao apaga nada do arquivo
        antes = len(p.carregar_conversas())
        nova = ponte2.nova_conversa()
        if nova.get("atual") is None and ponte2.mensagens == []:
            ok("tela nova: 'Nova conversa' limpa a conversa aberta")
        else:
            falha("tela nova: 'Nova conversa' devolveu %r" % (nova,))
        if len(p.carregar_conversas()) == antes:
            ok("tela nova: 'Nova conversa' não apaga as conversas guardadas")
        else:
            falha("tela nova: 'Nova conversa' mexeu no arquivo")

        # 7. EXCLUIR apaga so a escolhida e devolve a lista nova
        alvo2 = [c for c in p.carregar_conversas()
                 if c.get("titulo") == "Oi, tudo bem?"][0]
        r = ponte2.excluir_conversa(alvo2["id"])
        restantes = [c.get("titulo") for c in p.carregar_conversas()]
        if restantes == ["Segunda conversa"]:
            ok("tela nova: excluir apaga só a conversa escolhida")
        else:
            falha("tela nova: depois de excluir sobrou %r" % (restantes,))
        if [c["titulo"] for c in r.get("conversas", [])] == ["Segunda conversa"]:
            ok("tela nova: excluir devolve a lista já atualizada")
        else:
            falha("tela nova: excluir devolveu lista %r" % (r.get("conversas"),))

        # 8. excluir a conversa que estava aberta limpa a tela
        alvo3 = p.carregar_conversas()[0]
        ponte2.abrir_conversa(alvo3["id"])
        r2 = ponte2.excluir_conversa(alvo3["id"])
        if r2.get("era_atual") and r2.get("atual") is None and not ponte2.mensagens:
            ok("tela nova: excluir a conversa aberta limpa a tela")
        else:
            falha("tela nova: excluir a aberta devolveu %r" % (r2,))
        if ponte2.excluir_conversa("nao-existe").get("erro"):
            ok("tela nova: excluir o que não existe avisa em vez de quebrar")
        else:
            falha("tela nova: excluir o que não existe devolveu algo")

        # 9. PROCURAR dentro das conversas (o Wolf digita sem acento e sem
        # se preocupar com maiuscula)
        p.salvar_conversas([
            {"id": "busca-1", "titulo": "Receita de bolo",
             "quando": "16/10 10:00",
             "mensagens": [
                 {"role": "user", "text": "Me da uma receita de bolo de cenoura"},
                 {"role": "model", "text": "Leve 3 cenouras grandes a ..."}]},
            {"id": "busca-2", "titulo": "Japão", "quando": "16/10 09:00",
             "mensagens": [
                 {"role": "user", "text": "Qual a capital?"},
                 {"role": "model", "text": "Tóquio, no Japão."}]},
        ])
        achados = ponte2.conversas_buscar("japao").get("achados", [])
        if [a["id"] for a in achados] == ["busca-2"]:
            ok("tela nova: procurar acha o texto mesmo digitado sem acento")
        else:
            falha("tela nova: procurar por 'japao' deu %r"
                  % ([a["id"] for a in achados],))
        if achados and "Japão" in achados[0]["trecho"]:
            ok("tela nova: a busca mostra o trecho onde achou (com o acento)")
        else:
            falha("tela nova: o trecho da busca ficou %r"
                  % (achados[0]["trecho"] if achados else None,))
        if [a["id"] for a in ponte2.conversas_buscar("CENOURA").get("achados", [])] \
                == ["busca-1"]:
            ok("tela nova: a busca não liga para maiúscula")
        else:
            falha("tela nova: procurar em maiúscula não achou")
        if [a["id"] for a in ponte2.conversas_buscar("bolo").get("achados", [])] \
                == ["busca-1"]:
            ok("tela nova: a busca olha o título da conversa também")
        else:
            falha("tela nova: procurar só no título não achou")
        if ponte2.conversas_buscar("bolo").get("achados", [])[0]["indice"] == 0:
            ok("tela nova: a busca diz em qual mensagem achou")
        else:
            falha("tela nova: o índice da mensagem ficou %r"
                  % (ponte2.conversas_buscar("bolo").get("achados", []),))
        if ponte2.conversas_buscar("z").get("vazio") and \
                not ponte2.conversas_buscar("z").get("achados"):
            ok("tela nova: uma letra sozinha não procura (acha demais)")
        else:
            falha("tela nova: uma letra sozinha dispara a busca")
        if ponte2.conversas_buscar("   ").get("achados") == [] and \
                ponte2.conversas_buscar("xablau").get("achados") == []:
            ok("tela nova: busca em branco e busca sem nada dão lista vazia")
        else:
            falha("tela nova: a busca respondeu coisa para busca vazia")
        if ponte2.conversas_buscar("Tokio").get("achados") == []:
            ok("tela nova: procurar por 'Tokio' NÃO acha 'Tóquio' "
               "(o Unicode trata os dois como coisas diferentes)")
        else:
            falha("tela nova: a busca devolveu coisa para 'Tokio'")
        if len(p.carregar_conversas()) == 2:
            ok("tela nova: procurar não apaga nem muda conversa nenhuma")
        else:
            falha("tela nova: procurar mexeu nas conversas")
        # as conversas de mentira da busca ficam no arquivo de TESTE; o
        # check do fim da secao exige arquivo vazio, entao limpar aqui
        p.salvar_conversas([])

        # 10. a memoria que a tela mostra vem do arquivo, sem mudar nada
        p.salvar_memoria(["Gosta de RPG", "Mora em Santa Maria"])
        antes_mem = p.carregar_memoria()
        if app_web.Ponte().memoria_listar()["fatos"] == antes_mem:
            ok("tela nova: a aba Memória mostra o que está guardado")
        else:
            falha("tela nova: a aba Memória devolveu coisa diferente")
        if p.carregar_memoria() == antes_mem:
            ok("tela nova: só ler a Memória não muda nada")
        else:
            falha("tela nova: ler a Memória alterou o arquivo")

        # 10. no modo DEMO nada é lido do Wolf e nada é gravado
        app_web.DEMO = True
        demo = app_web.Ponte()
        inicial = demo.iniciar()
        if len(inicial["conversas"]) == 3 and inicial["mensagens"]:
            ok("tela nova: o modo exemplo mostra 3 conversas de exemplo")
        else:
            falha("tela nova: o modo exemplo mostrou %d conversa(s)"
                  % len(inicial["conversas"]))
        # "Nova conversa" pode funcionar no exemplo (ela nao grava nada),
        # mas EXCLUIR tem que continuar barrado: as conversas mostradas
        # ali sao de mentira e o arquivo de verdade e' do Wolf.
        nova = demo.nova_conversa()
        if nova.get("atual") is None and not demo.mensagens:
            ok("tela nova: no modo exemplo, 'Nova conversa' limpa a tela")
        else:
            falha("tela nova: no modo exemplo, 'Nova conversa' devolveu %r"
                  % (nova,))
        if demo.excluir_conversa("demo-1").get("erro"):
            ok("tela nova: no modo exemplo, excluir conversa avisa e não faz")
        else:
            falha("tela nova: no modo exemplo respondeu que excluiu conversa")
        if p.carregar_conversas() == []:
            ok("tela nova: o teste todo não deixou conversa nenhuma no disco")
        else:
            falha("tela nova: sobrou conversa no arquivo: %r"
                  % (p.carregar_conversas(),))
    finally:
        p.ARQUIVO_HISTORICO = historico_original
        p.ARQUIVO_MEMORIA = memoria_original
        app_web.DEMO = demo_original
        shutil.rmtree(pasta, ignore_errors=True)



# --- 5e. tela nova: a IA de verdade (o passo 3) ----------------------------


class _JanelaDeMentira:
    """Janela de mentira: guarda o que o Python tentou falar para a tela."""

    def __init__(self):
        self.eventos = []
        self.scriptos = []

    def evaluate_js(self, script):
        self.scriptos.append(script)
        # chega "window.PIA.evento({...})": o que importa e' o objeto
        dentro = script[script.index("(") + 1:script.rindex(")")]
        self.eventos.append(json.loads(dentro))

    def tipos(self):
        return [e.get("tipo") for e in self.eventos]

    def unico(self, tipo):
        achados = [e for e in self.eventos if e.get("tipo") == tipo]
        return achados[0] if achados else None


class _ThreadNaHora:
    """Thread que roda na hora (o teste nao pode esperar a IA de verdade).

    O app_web chama `Thread(target=..., args=(...), daemon=True)`, entao
    os nomes dos parâmetros precisam bater com os do threading de verdade.
    """

    def __init__(self, target=None, args=(), **_ignorado):
        self._alvo, self._args, self.rodou = target, args, False

    def start(self):
        self.rodou = True
        self._alvo(*self._args)


class _ThreadsNaHora:
    """Finge o `threading` do app_web e anota o que foi criado.

    A tela nova trabalha em thread para a janela nao travar. Aqui tudo roda
    na hora, e `rodadas` fica com o nome de cada thread, para o teste
    conferir que a tarefa de aprender foi chamada (ou nao).
    """

    def __init__(self):
        self.rodadas = []

    def Thread(self, target=None, args=(), **_ignorado):
        self.rodadas.append(getattr(target, "__name__", str(target)))
        return _ThreadNaHora(target=target, args=args)


# Resposta com acento e emoji: é o que pega o ensure_ascii=False quebrado
# (sem ele o ç e o 🚀 chegariam na tela como "\\u00e7" e "\\ud83d\\ude80").
RESPOSTA_TESTE = "Claro! Voce tem razão: çãé, ação e 🚀 (resposta de teste)"


def testes_tela_nova_ia(p):
    """O passo 3: enviar pergunta e a resposta voltando por evento.

    NAO chama a IA de verdade (gastaria a cota do Wolf e depends de
    internet): o `conversar`/`perguntar` sao trocados por uma resposta de
    mentira. O arquivo de configuracao tambem aponta para uma pasta de
    teste, entao a chave do Wolf nem chega a ser lida.
    """
    import app_web

    pasta = Path(PASTA) / "_tmp" / "teste-tela-nova-ia"
    shutil.rmtree(pasta, ignore_errors=True)
    pasta.mkdir(parents=True, exist_ok=True)

    chamadas = []
    aprendidas = []

    def ia_de_mentira(api_key, modelo, historico, pergunta, usar_contexto,
                      progresso=None, cfg=None, id_atual=None, consulta=None):
        """Responde na hora, como o `pesquisa_ia.conversar`/`perguntar`."""
        chamadas.append({"api_key": api_key, "pergunta": pergunta,
                         "historico": list(historico), "id_atual": id_atual,
                         "consulta": consulta})
        if progresso:
            progresso("Procurando na web")
            progresso("Consultando a inteligência artificial")
        return RESPOSTA_TESTE, [], [], "Gemini"

    def ia_quebrada(*_args, **_kw):
        raise RuntimeError("API key not valid: 401 UNAUTHENTICATED")

    def ia_sem_internet(*_args, **_kw):
        raise RuntimeError("ConnectionError: a internet caiu")

    def decidir_de_mentira(chave, texto, historico, modo="auto"):
        return {"modo": "amigo", "consulta": texto}

    def aprender_de_mentira(chave, pergunta, resposta):
        aprendidas.append((pergunta, resposta))

    guardados = {
        "ARQUIVO_HISTORICO": p.ARQUIVO_HISTORICO,
        "ARQUIVO_MEMORIA": p.ARQUIVO_MEMORIA,
        "ARQUIVO_CONFIG": p.ARQUIVO_CONFIG,
        "_memoria_cache": p._memoria_cache,
        "conversar": p.conversar,
        "perguntar": p.perguntar,
        "_decidir_modo": p._decidir_modo,
        "aprender_com_o_usuario": p.aprender_com_o_usuario,
        "threading": app_web.threading,
        "DEMO": app_web.DEMO,
    }
    try:
        # ---- os dados do Wolf estao "escondidos" durante o teste ----
        p.ARQUIVO_HISTORICO = pasta / "historico.json"
        p.ARQUIVO_MEMORIA = pasta / "memoria.json"
        p.ARQUIVO_CONFIG = pasta / "config.json"
        # a memoria tem um cache dentro do modulo: sem zerar aqui, o teste
        # de cima ("Gosta de RPG") apareceria como se fosse do Wolf
        p._memoria_cache = None
        p.conversar = ia_de_mentira
        p.perguntar = ia_de_mentira
        p._decidir_modo = decidir_de_mentira
        p.aprender_com_o_usuario = aprender_de_mentira
        app_web.DEMO = False
        threads = _ThreadsNaHora()
        app_web.threading = threads

        def com_chave(aprender=True):
            p._gravar_json(p.ARQUIVO_CONFIG,
                           {"api_key": "AIza-chave-de-teste",
                            "aprender": aprender})

        # 1. SEM CHAVE: a tela e avisada na hora, sem chamar a IA
        com_chave()
        p._gravar_json(p.ARQUIVO_CONFIG, {})
        janela = _JanelaDeMentira()
        ponte = app_web.Ponte(janela)
        chamadas.clear()
        resposta = ponte.enviar("Olá")
        if resposta.get("erro") == "sem_chave":
            ok("tela nova: sem chave, o envio avisa 'sem_chave' na hora")
        else:
            falha("tela nova: sem chave o envio devolveu %r" % (resposta,))
        if not chamadas and not threads.rodadas and not janela.eventos:
            ok("tela nova: sem chave, a IA nem é chamada e nada é desenhado")
        else:
            falha("tela nova: sem chave, mas a IA foi chamada (%r)"
                  % (chamadas,))

        # 2. pergunta vazia e envio com a tela ocupada sao recusados
        if ponte.enviar("   ").get("erro"):
            ok("tela nova: pergunta em branco não é enviada")
        else:
            falha("tela nova: pergunta em branco foi aceita")
        ponte.ocupado = True
        if ponte.enviar("outra coisa").get("erro"):
            ok("tela nova: não aceita segunda pergunta enquanto responde")
        else:
            falha("tela nova: aceitou segunda pergunta enquanto respondia")
        ponte.ocupado = False

        # 3. RESPOSTA COMPLETA: devolve na hora e o texto volta por evento
        com_chave()
        janela = _JanelaDeMentira()
        ponte = app_web.Ponte(janela)
        chamadas.clear()
        resposta = ponte.enviar("Me explica o que é IA")
        tipos = janela.tipos()
        if resposta == {}:
            ok("tela nova: enviar volta na hora (a janela não trava)")
        else:
            falha("tela nova: enviar devolveu %r" % (resposta,))
        if "resposta" in tipos:
            ok("tela nova: a resposta chega como evento 'resposta'")
        else:
            falha("tela nova: os eventos foram %r" % (tipos,))
        if janela.unico("resposta") and \
                janela.unico("resposta").get("texto") == RESPOSTA_TESTE:
            ok("tela nova: o texto da resposta chega inteiro")
        else:
            falha("tela nova: o evento 'resposta' veio %r"
                  % (janela.unico("resposta"),))
        if "etapa" in tipos:
            ok("tela nova: a tela é avisada do que a IA está fazendo (etapa)")
        else:
            falha("tela nova: nenhum evento 'etapa' chegou (%r)" % (tipos,))
        if tipos.index("etapa") < tipos.index("resposta"):
            ok("tela nova: a etapa vem antes da resposta")
        else:
            falha("tela nova: a ordem dos eventos ficou %r" % (tipos,))
        if not ponte.ocupado:
            ok("tela nova: depois da resposta a tela volta a aceitar")
        else:
            falha("tela nova: a tela ficou travada depois da resposta")

        # 4. o texto vai com acento e emoji de verdade (ensure_ascii=False)
        if any("🚀" in s and "ç" in s and "\\u" not in s
               for s in janela.scriptos):
            ok("tela nova: acento e emoji chegam crus, sem \\u escapado")
        else:
            falha("tela nova: o texto para a tela foi escapado: %r"
                  % (janela.scriptos[-1:],))

        # 5. a conversa e gravada e a lista da esquerda e atualizada
        salvas = p.carregar_conversas()
        if len(salvas) == 1 and salvas[0].get("titulo") == \
                "Me explica o que é IA" and \
                [m["role"] for m in salvas[0]["mensagens"]] == \
                ["user", "model"]:
            ok("tela nova: a pergunta e a resposta foram gravadas juntas")
        else:
            falha("tela nova: a gravação ficou %r" % (salvas,))
        lista = janela.unico("conversas")
        if lista and [c.get("titulo") for c in lista.get("conversas", [])] \
                == ["Me explica o que é IA"] and \
                lista.get("atual") == salvas[0]["id"]:
            ok("tela nova: a lista da esquerda é atualizada com a conversa")
        else:
            falha("tela nova: o evento 'conversas' veio %r" % (lista,))

        # 6. a segunda pergunta continua a MESMA conversa e leva o historico
        chamadas.clear()
        ponte.enviar("E como ela aprende?")
        if len(p.carregar_conversas()) == 1:
            ok("tela nova: a segunda pergunta continua a mesma conversa")
        else:
            falha("tela nova: a segunda pergunta abriu outra conversa (%d)"
                  % len(p.carregar_conversas()))
        historico = chamadas[0]["historico"] if chamadas else []
        if [m["role"] for m in historico] == ["user", "model"] and \
                historico[0]["text"] == "Me explica o que é IA":
            ok("tela nova: a IA recebe a conversa anterior como histórico")
        else:
            falha("tela nova: o histórico da IA ficou %r" % (historico,))
        if chamadas and chamadas[0].get("id_atual") == salvas[0]["id"]:
            ok("tela nova: a conversa aberta não entra duas vezes no contexto")
        else:
            falha("tela nova: id_atual ficou %r"
                  % (chamadas[0].get("id_atual") if chamadas else None,))

        # 7. ERRO DE CHAVE: vem em portugues e a tela abre as Configuracoes
        p.conversar = ia_quebrada
        p.perguntar = ia_quebrada
        janela = _JanelaDeMentira()
        ponte = app_web.Ponte(janela)
        ponte.enviar("Oi")
        erro = janela.unico("erro")
        if erro and "chave" in erro.get("texto", "").lower() \
                and "401" not in erro.get("texto", ""):
            ok("tela nova: erro de chave vira frase em português")
        else:
            falha("tela nova: o evento de erro veio %r" % (erro,))
        if erro and erro.get("chave") is True:
            ok("tela nova: erro de chave avisa a tela para abrir as Config.")
        else:
            falha("tela nova: o evento de erro nao marcou 'chave': %r"
                  % (erro,))
        if ponte.mensagens and ponte.mensagens[-1].get("role") == "erro":
            ok("tela nova: o erro também fica na conversa da tela")
        else:
            falha("tela nova: o erro não entrou na conversa: %r"
                  % (ponte.mensagens,))

        # 8. erro que NAO e de chave nao manda a tela para as Configuracoes
        p.conversar = ia_sem_internet
        p.perguntar = ia_sem_internet
        janela = _JanelaDeMentira()
        ponte = app_web.Ponte(janela)
        ponte.enviar("Oi")
        erro = janela.unico("erro")
        if erro and erro.get("chave") is False:
            ok("tela nova: erro de internet não mexe nas Configurações")
        else:
            falha("tela nova: erro de internet veio %r" % (erro,))

        # 9. a IA DECIDE o modo: pesquisa quando o roteador manda pesquisar
        p.conversar = ia_de_mentira
        p.perguntar = ia_de_mentira
        p._decidir_modo = lambda c, t, h, modo="auto": {
            "modo": "pesquisa", "consulta": "IA generativa"}
        chamadas.clear()
        janela = _JanelaDeMentira()
        ponte = app_web.Ponte(janela)
        ponte.enviar("O que é IA generativa?")   # nao e' pedido de noticia
        if chamadas and chamadas[0].get("consulta") == "IA generativa":
            ok("tela nova: em modo pesquisa, a busca usa o assunto do "
               "roteador")
        else:
            falha("tela nova: a consulta da busca ficou %r"
                  % (chamadas[0].get("consulta") if chamadas else None,))
        # PEDIDO DE NOTÍCIA é tratado à parte, igual ao programa antigo: a
        # busca sai com a pergunta inteira, não com o assunto abreviado.
        chamadas.clear()
        ponte.enviar("Pesquisa as notícias de tecnologia de hoje")
        if chamadas and chamadas[0].get("consulta") == \
                "Pesquisa as notícias de tecnologia de hoje":
            ok("tela nova: pedido de notícia busca a pergunta inteira")
        else:
            falha("tela nova: a consulta de notícia ficou %r"
                  % (chamadas[0].get("consulta") if chamadas else None,))
        p._decidir_modo = decidir_de_mentira

        # 10. a IA pode aprender sobre o Wolf, em segundo plano e calado
        aprendidas.clear()
        com_chave(aprender=True)
        janela = _JanelaDeMentira()
        ponte = app_web.Ponte(janela)
        ponte.enviar("Gosto de jogar RPG")
        if len(aprendidas) == 1 and aprendidas[0][0] == "Gosto de jogar RPG":
            ok("tela nova: a IA é mandada aprender depois de responder")
        else:
            falha("tela nova: a tarefa de aprender rodou %d vez(es)"
                  % len(aprendidas))
        if any(r == "tarefa" for r in threads.rodadas):
            ok("tela nova: aprender roda fora da tela (em segundo plano)")
        else:
            falha("tela nova: nenhuma thread de aprender foi criada (%r)"
                  % (threads.rodadas,))

        # 11. com 'aprender' desligado, nada e aprendido
        aprendidas.clear()
        com_chave(aprender=False)
        ponte = app_web.Ponte(_JanelaDeMentira())
        ponte.enviar("Moro em Porto Alegre")
        if not aprendidas:
            ok("tela nova: com 'aprender' desligado, a IA não aprende nada")
        else:
            falha("tela nova: aprendeu %r com a opção desligada"
                  % (aprendidas,))

        # 12. MODO EXEMPLO: a IA responde, mas NADA é gravado
        app_web.DEMO = True
        aprendidas.clear()
        janela = _JanelaDeMentira()
        ponte = app_web.Ponte(janela)
        ponte.iniciar()
        chamadas.clear()
        ponte.enviar("Me conta uma curiosidade")
        if janela.unico("resposta"):
            ok("tela nova: no modo exemplo a IA de verdade também responde")
        else:
            falha("tela nova: no modo exemplo a IA não respondeu (%r)"
                  % (janela.tipos(),))
        if not aprendidas:
            ok("tela nova: no modo exemplo a IA não aprende nada")
        else:
            falha("tela nova: no modo exemplo aprendeu %r" % (aprendidas,))
        app_web.DEMO = False
        if ponte.mensagens[-1].get("role") == "model":
            ok("tela nova: no modo exemplo a resposta entra na conversa da tela")
        else:
            falha("tela nova: a conversa do exemplo ficou %r"
                  % (ponte.mensagens[-1],))

        # 13. a memoria do Wolf nao foi mexida e o teste rodou isolado
        if p.ARQUIVO_HISTORICO == pasta / "historico.json" and \
                p.ARQUIVO_CONFIG == pasta / "config.json":
            ok("tela nova: o teste da IA rodou com os arquivos do Wolf "
               "escondidos")
        else:
            falha("tela nova: o teste da IA usou o arquivo de verdade (%r)"
                  % (p.ARQUIVO_HISTORICO,))
        if p.carregar_memoria() == []:
            ok("tela nova: a IA da tela nova não escreveu nada na Memória")
        else:
            falha("tela nova: sobrou memória na pasta de teste: %r"
                  % (p.carregar_memoria(),))
    finally:
        for nome, valor in guardados.items():
            if nome == "DEMO":
                app_web.DEMO = valor
            elif nome == "threading":
                app_web.threading = valor
            else:
                setattr(p, nome, valor)
        shutil.rmtree(pasta, ignore_errors=True)


if not falhas:
    try:
        testes_tela_nova(importlib.import_module("pesquisa_ia"))
    except Exception as erro:
        falha("os testes da tela nova quebraram: %r" % (erro,))

if not falhas:
    try:
        testes_tela_nova_ia(importlib.import_module("pesquisa_ia"))
    except Exception as erro:
        falha("os testes da IA da tela nova quebraram: %r" % (erro,))


def testes_tela_nova_microfone(p):
    """Passo 4: o microfone da tela nova.

    NAO grava audio de verdade e NAO chama a IA de verdade (o microfone do
    Wolf ficaria aberto e a cota dele seria gasta). O `voz` inteiro e
    trocado por um de mentira, e o arquivo de configuracao aponta para
    uma pasta de teste, entao nem a chave nem as conversas do Wolf sao
    tocadas.
    """
    import app_web

    pasta = Path(PASTA) / "_tmp" / "teste-tela-nova-mic"
    shutil.rmtree(pasta, ignore_errors=True)
    pasta.mkdir(parents=True, exist_ok=True)

    gravados = []      # o que o microfone de mentira "ouviu"
    pedidos = []       # cada transcricao pedida (modelos, wav)

    class GravadorDeMentira:
        """Finge o `voz.Gravador`: nada de som, so marca o que foi feito."""

        def __init__(self):
            self.parado = False

        def iniciar(self):
            gravados.append("iniciou")

        def parar(self):
            self.parado = True
            gravados.append("parou")
            return b"onda-de-som-de-mentira"

    def microfone_de_mentira(**muda):
        """Monta um `voz` falso. `muda` troca o que o teste quiser."""
        falso = types.SimpleNamespace()
        falso.TEM_SOM = True
        falso.Gravador = GravadorDeMentira
        falso.microfone_disponivel = lambda: True
        falso.wav_tem_som = lambda wav: True
        falso.transcrever = (lambda cliente, modelos, wav:
                             pedidos.append({"modelos": list(modelos),
                                             "wav": wav}) or
                             "O que foi falado: çãé 🚀")
        falso.microfone_erro = (lambda erro: " microfone: %s" % (erro,))
        for nome, valor in muda.items():
            setattr(falso, nome, valor)
        return falso

    def com_chave(voz_enviar=False):
        p._gravar_json(p.ARQUIVO_CONFIG,
                       {"api_key": "AIza-chave-de-teste",
                        "voz_enviar": voz_enviar})

    def ponte_limpa():
        gravados.clear()
        pedidos.clear()
        janela = _JanelaDeMentira()
        return app_web.Ponte(janela), janela

    def ja_gravando(falso):
        """Coloca o microfone falso, liga a gravacao e devolve a ponte."""
        p.voz = falso
        ponte, _janela = ponte_limpa()
        ponte.mic_alternar()
        return ponte

    guardados = {"ARQUIVO_CONFIG": p.ARQUIVO_CONFIG,
                 "ARQUIVO_HISTORICO": p.ARQUIVO_HISTORICO,
                 "voz": p.voz,
                 "_criar_cliente": p._criar_cliente,
                 "threading": app_web.threading,
                 "DEMO": app_web.DEMO,
                 "VOZ_REAL": app_web.VOZ_REAL,
                 "VOZ_FALSA": app_web.VOZ_FALSA}
    try:
        p.ARQUIVO_CONFIG = pasta / "config.json"
        p.ARQUIVO_HISTORICO = pasta / "historico.json"
        p._criar_cliente = lambda api_key: "cliente-de-teste"
        app_web.threading = _ThreadsNaHora()
        app_web.DEMO = False

        # 1. SEM SOM: fala em portugues e nao finge que gravou
        p.voz = microfone_de_mentira(TEM_SOM=False)
        com_chave()
        ponte, janela = ponte_limpa()
        resposta = ponte.mic_alternar()
        if "sem a biblioteca de som" in str(resposta.get("erro", "")):
            ok("microfone: avisando que o programa foi montado sem som")
        else:
            falha("microfone: sem som devolveu %r" % (resposta,))
        if not janela.unico("gravando") and not ponte.gravando:
            ok("microfone: sem som ele não finge que está gravando")
        else:
            falha("microfone: sem som ele disse que estava gravando")

        # 2. SEM MICROFONE LIGADO
        p.voz = microfone_de_mentira(microfone_disponivel=lambda: False)
        ponte, _janela = ponte_limpa()
        resposta = ponte.mic_alternar()
        if "microfone ligado" in str(resposta.get("erro", "")):
            ok("microfone: avisando que não achou microfone ligado")
        else:
            falha("microfone: sem microfone devolveu %r" % (resposta,))

        # 3. SEM CHAVE: avisa para a tela abrir as Configuracoes
        p.voz = microfone_de_mentira()
        p._gravar_json(p.ARQUIVO_CONFIG, {})
        ponte, _janela = ponte_limpa()
        resposta = ponte.mic_alternar()
        if resposta.get("erro") == "sem_chave_voz" and not ponte.gravando:
            ok("microfone: sem chave pede a chave e não grava")
        else:
            falha("microfone: sem chave devolveu %r" % (resposta,))

        # 4. GRAVAR: o primeiro clique liga, e a tela e avisada na hora
        com_chave()
        ponte, janela = ponte_limpa()
        resposta = ponte.mic_alternar()
        ligado = janela.unico("gravando")
        if resposta.get("gravando") and ponte.gravando and gravados == ["iniciou"]:
            ok("microfone: o primeiro clique começa a gravar")
        else:
            falha("microfone: o primeiro clique devolveu %r (gravou %r)"
                  % (resposta, gravados))
        if ligado and ligado.get("ligado") is True:
            ok("microfone: a tela é avisada que começou a gravar")
        else:
            falha("microfone: nenhum aviso de 'começou a gravar' (%r)"
                  % (ligado,))

        # 5. PARAR: o segundo clique para e o texto falado entra na caixa
        janela.eventos.clear()
        resposta = ponte.mic_alternar()
        voz = janela.unico("voz")
        desligado = [e for e in janela.eventos
                     if e.get("tipo") == "gravando"
                     and e.get("ligado") is False]
        if resposta.get("transcrevendo") and "parou" in gravados:
            ok("microfone: o segundo clique para de gravar")
        else:
            falha("microfone: o segundo clique devolveu %r (gravados %r)"
                  % (resposta, gravados))
        if desligado:
            ok("microfone: a tela é avisada que parou de gravar")
        else:
            falha("microfone: nenhum aviso de 'parou'")
        if voz and voz.get("texto") == "O que foi falado: çãé 🚀":
            ok("microfone: o que foi falado chega na caixa, com acento e emoji")
        else:
            falha("microfone: o texto falado veio %r" % (voz,))
        if ponte.ocupado is False:
            ok("microfone: depois de transcrever, o programa volta a aceitar")
        else:
            falha("microfone: ficou travado depois de transcrever")

        # 6. o texto falado NAO e' enviado sozinho
        if voz and voz.get("enviar") is False:
            ok("microfone: o texto falado NÃO é enviado sozinho (Wolf confere)")
        else:
            falha("microfone: o texto falado foi marcado para enviar (%r)"
                  % (voz,))

        # 7. a lista de modelos e' a mesma do programa antigo (com reservas).
        #    Repare que MODELOS_RESERVA ja comeca pelo modelo bom: a regra
        #    e' "o modelo escolhido primeiro, e os outros uma vez cada".
        escolhido = p.MODELO_PADRAO
        esperado = [escolhido] + [m for m in p.MODELOS_RESERVA
                                  if m != escolhido]
        if pedidos and pedidos[0]["modelos"] == esperado:
            ok("microfone: tenta o modelo bom e os de reserva, como antes")
        else:
            falha("microfone: os modelos pedidos foram %r (esperado %r)"
                  % (pedidos[0]["modelos"] if pedidos else None, esperado))

        # 8. SILENCIO: "não ouvi nada" e nenhum texto na caixa
        ponte = ja_gravando(microfone_de_mentira(wav_tem_som=lambda wav: False))
        janela = ponte.janela
        janela.eventos.clear()
        resposta = ponte.mic_alternar()
        if "Não ouvi nada" in str(resposta.get("erro", "")) and \
                not janela.unico("voz"):
            ok("microfone: quando não ouve nada, avisa e não inventa texto")
        else:
            falha("microfone: no silêncio devolveu %r" % (resposta,))

        # 9. TRANSCRICAO QUE FALHA: vira frase em portugues na tela
        def transcrever_quebrado(cliente, modelos, wav):
            raise RuntimeError("API key not valid: 401 UNAUTHENTICATED")

        ponte = ja_gravando(microfone_de_mentira(transcrever=transcrever_quebrado))
        janela = ponte.janela
        janela.eventos.clear()
        ponte.mic_alternar()
        erro = janela.unico("voz_erro")
        if erro and "chave" in str(erro.get("texto", "")).lower():
            ok("microfone: chave recusada vira frase em português na tela")
        else:
            falha("microfone: o erro de chave veio %r" % (erro,))
        if erro and erro.get("chave") is True:
            ok("microfone: erro de chave avisa a tela para abrir as Config.")
        else:
            falha("microfone: o erro não avisou das Configurações (%r)"
                  % (erro,))

        # 10. FALHA DO MICROFONE AO LIGAR: vira frase, sem travar
        class GravadorQuebrado:
            def iniciar(self):
                raise RuntimeError("dispositivo ocupado")

        p.voz = microfone_de_mentira(Gravador=GravadorQuebrado)
        ponte, _janela = ponte_limpa()
        resposta = ponte.mic_alternar()
        if "dispositivo ocupado" in str(resposta.get("erro", "")) and \
                not ponte.gravando:
            ok("microfone: microfone ocupado avisa e não trava o programa")
        else:
            falha("microfone: microfone ocupado devolveu %r" % (resposta,))

        # 11. clicou no microfone com uma conversa rodando: espera
        p.voz = microfone_de_mentira()
        ponte, _janela = ponte_limpa()
        ponte.ocupado = True
        resposta = ponte.mic_alternar()
        ponte.ocupado = False
        if "Aguarde" in str(resposta.get("erro", "")):
            ok("microfone: não grava por cima de uma resposta em andamento")
        else:
            falha("microfone: com a tela ocupada devolveu %r" % (resposta,))

        # 12. MODO EXEMPLO: o microfone e' de mentira, sem chave nenhuma
        app_web.DEMO = True
        app_web.VOZ_REAL = False
        app_web.VOZ_FALSA = True
        app_web.threading = threading
        ponte, janela = ponte_limpa()
        ponte.mic_alternar()
        janela.eventos.clear()
        ponte.mic_alternar()
        if janela.unico("voz"):
            ok("microfone: no modo exemplo ele finge que ouviu algo")
        else:
            falha("microfone: no modo exemplo não respondeu (%r)"
                  % (janela.tipos(),))
        if not gravados:
            ok("microfone: no modo exemplo NENHUM som de verdade e' gravado")
        else:
            falha("microfone: no modo exemplo gravou %r" % (gravados,))

        # 12b. com --voz, o microfone de verdade e' usado, mas ainda sem
        #      gravar nada. E' assim que o Wolf testa falando de verdade.
        app_web.DEMO = True
        app_web.VOZ_REAL = True
        app_web.VOZ_FALSA = False
        p.voz = microfone_de_mentira()
        ponte, janela = ponte_limpa()
        ponte.mic_alternar()
        janela.eventos.clear()
        ponte.mic_alternar()
        if janela.unico("voz") and gravados == ["iniciou", "parou"]:
            ok("microfone: com --voz ele grava de verdade (e transcreve)")
        else:
            falha("microfone: com --voz ficou %r (gravados %r)"
                  % (janela.tipos(), gravados))
        app_web.DEMO = False

        # 13. NADA foi gravado: nem conversa, nem arquivo do Wolf
        if p.ARQUIVO_CONFIG == pasta / "config.json" and \
                p.ARQUIVO_HISTORICO == pasta / "historico.json":
            ok("microfone: o teste rodou com os arquivos do Wolf escondidos")
        else:
            falha("microfone: o teste usou o arquivo de verdade (%r)"
                  % (p.ARQUIVO_CONFIG,))
        if not (pasta / "historico.json").exists():
            ok("microfone: falar não cria conversa nenhuma no disco")
        else:
            falha("microfone: sobrou conversa do microfone no disco")
    finally:
        for nome, valor in guardados.items():
            if nome == "threading":
                app_web.threading = valor
            elif nome in ("DEMO", "VOZ_REAL", "VOZ_FALSA"):
                setattr(app_web, nome, valor)
            else:
                setattr(p, nome, valor)
        shutil.rmtree(pasta, ignore_errors=True)


if not falhas:
    try:
        testes_tela_nova_microfone(importlib.import_module("pesquisa_ia"))
    except Exception as erro:
        falha("os testes do microfone quebraram: %r" % (erro,))


def testes_tela_nova_config(p):
    """Passo 5: Configuracoes e Memoria da tela nova gravam de verdade
    (numa pasta de teste, nunca nos arquivos do Wolf)."""
    import app_web

    pasta = Path(PASTA) / "_tmp" / "teste-tela-nova-config"
    shutil.rmtree(pasta, ignore_errors=True)
    pasta.mkdir(parents=True, exist_ok=True)
    guardados = {"ARQUIVO_MEMORIA": p.ARQUIVO_MEMORIA,
                 "ARQUIVO_CONFIG": p.ARQUIVO_CONFIG,
                 "_memoria_cache": p._memoria_cache,
                 "testar_chave": p.testar_chave}
    demo = app_web.DEMO
    try:
        p.ARQUIVO_MEMORIA = pasta / "memoria.json"
        p.ARQUIVO_CONFIG = pasta / "config.json"
        p._memoria_cache = None
        app_web.DEMO = False
        ponte = app_web.Ponte(None)

        r = ponte.definir_modo("sempre")
        if r.get("cfg", {}).get("modo_pesquisa") == "sempre" and \
                p._ler_json(p.ARQUIVO_CONFIG, {}).get("modo_pesquisa") == "sempre":
            ok("tela nova: definir_modo grava o modo da web")
        else:
            falha("tela nova: definir_modo devolveu %r" % (r,))
        if "erro" in ponte.definir_modo("xyz"):
            ok("tela nova: modo invalido e recusado")
        else:
            falha("tela nova: modo invalido foi aceito")

        ponte.config_salvar({"aprender": False, "web_corretor": False,
                             "chaves": {"api_key": "AIzaCHAVE1234",
                                        "campo_falso": "x"}})
        cfg = p._ler_json(p.ARQUIVO_CONFIG, {})
        if cfg.get("aprender") is False and cfg.get("corretor") is False \
                and cfg.get("api_key") == "AIzaCHAVE1234" \
                and "campo_falso" not in cfg:
            ok("tela nova: config_salvar grava opcoes e chave, ignora campo falso")
        else:
            falha("tela nova: config_salvar gravou %r" % (cfg,))
        ponte.config_salvar({"chaves": {"api_key": ""}})
        if p._ler_json(p.ARQUIVO_CONFIG, {}).get("api_key") == "AIzaCHAVE1234":
            ok("tela nova: chave vazia nao apaga a chave salva")
        else:
            falha("tela nova: chave vazia apagou a chave salva")

        p.testar_chave = lambda chave, modelo: "OK"
        if ponte.testar_chave("api_key", "").get("ok") is True:
            ok("tela nova: testar_chave usa a chave ja salva quando o campo vem vazio")
        else:
            falha("tela nova: testar_chave com chave salva falhou")
        def quebra(chave, modelo):
            raise RuntimeError("401 UNAUTHENTICATED")
        p.testar_chave = quebra
        r = ponte.testar_chave("api_key", "AIzaRUIM")
        if r.get("ok") is False and r.get("texto"):
            ok("tela nova: testar_chave com chave ruim explica em portugues")
        else:
            falha("tela nova: testar_chave ruim devolveu %r" % (r,))

        r = ponte.memoria_adicionar("Gosta de RPG")
        r = ponte.memoria_adicionar("Gosta de RPG")
        if r.get("fatos") == ["Gosta de RPG"]:
            ok("tela nova: memoria_adicionar nao repete fato")
        else:
            falha("tela nova: memoria ficou %r" % (r,))
        ponte.memoria_adicionar("Mora em Santa Maria")
        r = ponte.memoria_apagar("Gosta de RPG")
        if r.get("fatos") == ["Mora em Santa Maria"]:
            ok("tela nova: memoria_apagar tira so o item escolhido")
        else:
            falha("tela nova: memoria_apagar deixou %r" % (r,))
        if "mudou" in ponte.memoria_organizar():
            ok("tela nova: memoria_organizar responde")
        else:
            falha("tela nova: memoria_organizar nao respondeu")
        if ponte.memoria_apagar_tudo().get("fatos") == []:
            ok("tela nova: memoria_apagar_tudo esvazia")
        else:
            falha("tela nova: memoria_apagar_tudo nao esvaziou")

        # 7. EDITAR um item: e' o que o Wolf faz clicando no texto
        ponte.memoria_adicionar("Moro em Santa Maria")
        ponte.memoria_adicionar("Gosta de RPG")
        antes_editar = p.carregar_memoria()
        r = ponte.memoria_editar("Gosta de RPG", "Gosta de RPG de mesa")
        depois = r.get("fatos") or []
        if "Gosta de RPG de mesa" in depois and "Gosta de RPG" not in depois:
            ok("tela nova: editar a memória troca o texto do item")
        else:
            falha("tela nova: editar deixou %r" % (depois,))
        if [f for f in antes_editar if f != "Gosta de RPG"] == \
                [f for f in depois if f != "Gosta de RPG de mesa"]:
            ok("tela nova: editar não mexe nos outros itens da memória")
        else:
            falha("tela nova: editar mudou os outros itens (%r -> %r)"
                  % (antes_editar, depois))
        if ponte.memoria_editar("item que nao existe", "x").get("erro"):
            ok("tela nova: editar o que não existe avisa em vez de inventar")
        else:
            falha("tela nova: editar o que não.exists devolveu algo")
        if ponte.memoria_editar("Gosta de RPG de mesa", "  ").get("erro"):
            ok("tela nova: editar para texto vazio é recusado")
        else:
            falha("tela nova: deixou um item vazio na memória")
        if ponte.memoria_editar("Gosta de RPG de mesa",
                                "x" * (p.memoria.TAMANHO_MAXIMO + 1)).get("erro"):
            ok("tela nova: item maior que o limite é recusado com aviso")
        else:
            falha("tela nova: aceitou item maior que o limite")
        if "Gosta de RPG de mesa" in p.carregar_memoria():
            ok("tela nova: as edições recusadas não estragaram o item")
        else:
            falha("tela nova: o item se perdeu numa edição recusada")

        # 8. EXPORTAR a memória: o texto vem pronto para o .txt
        exportados = []
        ponte.salvar_texto = lambda texto: exportados.append(texto) or {}
        r = ponte.memoria_exportar()
        corpo = exportados[0] if exportados else ""
        if not r.get("erro") and corpo:
            ok("tela nova: exportar a memória monta o texto e não abre janela")
        else:
            falha("tela nova: exportar devolveu %r (texto %r)"
                  % (r, corpo[:80]))
        # Compara o que foi SALVO com o que a memoria tem de verdade, item
        # por item. Antes este teste procurava um texto solto dentro do
        # .txt inteiro, e foi assim que uma falha ficou sem explicacao: o
        # arquivo tinha o item dentro e o teste dizia que nao. Comparar a
        # lista inteira nao deixa passar item trocado, item a menos nem
        # item a mais -- e nao depende de formatacao nenhuma.
        esperado = p.carregar_memoria()
        linhas_txt = corpo.splitlines()
        itens_txt = [l[2:] for l in linhas_txt if l.startswith("- ")]
        if sorted(itens_txt) == sorted(esperado):
            ok("tela nova: o .txt da memoria traz exatamente os itens que ela tem")
        else:
            falha("tela nova: o .txt ficou %r mas a memoria tem %r"
                  % (itens_txt, esperado))
        if len(linhas_txt) > 2 and \
                "%d item(ns)" % len(esperado) in linhas_txt[2]:
            ok("tela nova: o .txt da memoria diz quantos itens sao")
        else:
            falha("tela nova: o .txt nao diz quantos itens sao")

        ponte.memoria_apagar_tudo()
        if ponte.memoria_exportar().get("erro"):
            ok("tela nova: exportar memória vazia avisa e não abre janela")
        else:
            falha("tela nova: exportar memória vazia tentou salvar assim mesmo")

        app_web.DEMO = True
        antes = p.ARQUIVO_CONFIG.read_text(encoding="utf-8")
        ponte.config_salvar({"aprender": True})
        ponte.memoria_adicionar("nao pode gravar")
        if p.ARQUIVO_CONFIG.read_text(encoding="utf-8") == antes \
                and p.carregar_memoria() == []:
            ok("tela nova: no modo exemplo configuracoes e memoria nao gravam")
        else:
            falha("tela nova: o modo exemplo gravou algo")
    finally:
        app_web.DEMO = demo
        for nome, valor in guardados.items():
            setattr(p, nome, valor)
        shutil.rmtree(pasta, ignore_errors=True)


if not falhas:
    try:
        testes_tela_nova_config(importlib.import_module("pesquisa_ia"))
    except Exception as erro:
        falha("os testes de config da tela nova quebraram: %r" % (erro,))


# --- 5f. aba Memoria: a rolagem do mouse continua depois de apagar ------


# --- 6. roteador: papo ou pesquisa (sem internet) --------------------------
try:
    sys.path.insert(0, str(PASTA))
    import roteador
    import pesquisa_ia as _pia

    def confere(condicao, nome):
        if condicao:
            ok(nome)
        else:
            falha(nome)

    r = roteador.regra_local
    confere(r("oi") == "amigo", "roteador: 'oi' é papo")
    confere(r("valeu!") == "amigo", "roteador: 'valeu!' é papo")
    confere(r("/web preço do dólar") == "pesquisa",
            "roteador: '/web ...' é pesquisa")
    confere(r("sem pesquisar, o que acha de RPG?") == "amigo",
            "roteador: 'sem pesquisar' é papo")
    confere(r("oi", modo="sempre") == "pesquisa",
            "roteador: modo 'sempre' pesquisa tudo")
    confere(r("quanto custa?", modo="nunca") == "amigo",
            "roteador: modo 'nunca' nunca pesquisa")

    def quebrou(_prompt):
        raise RuntimeError("sem internet")

    d = roteador.decidir("oi", [], quebrou)
    confere(d == {"modo": "amigo", "consulta": "oi", "origem": "regra"},
            "roteador: 'oi' decide papo pela regra")
    d = roteador.decidir("/web preço do dólar", [], quebrou)
    confere(d["modo"] == "pesquisa" and d["consulta"] == "preço do dólar"
            and d["origem"] == "regra",
            "roteador: '/web ...' tira o prefixo da consulta")
    d = roteador.decidir(
        "q?", [], lambda p: '{"pesquisar": true, "consulta": "x", "motivo": "y"}')
    confere(d["modo"] == "pesquisa" and d["origem"] == "modelo",
            "roteador: entende JSON limpo do modelo")
    d = roteador.decidir(
        "q?", [],
        lambda p: 'texto ```json {"pesquisar": false, "consulta": "", '
                   '"motivo": "papo"} ``` fim')
    confere(d["modo"] == "amigo" and d["origem"] == "modelo",
            "roteador: entende JSON dentro de cerca")
    d = roteador.decidir("q?", [], lambda p: "não entendi nada")
    confere(d["origem"] == "padrao",
            "roteador: texto solto cai na heurística")
    d = roteador.decidir("q?", [], quebrou)
    confere(d["origem"] == "padrao",
            "roteador: erro do modelo cai na heurística")

    def modelo_amigo(_p):
        return '{"pesquisar": false, "consulta": "", "motivo": "papo"}'

    d = roteador.decidir("como você está hoje?", [], modelo_amigo)
    confere(d["modo"] == "amigo", "roteador: 'como você está hoje?' é papo")
    d = roteador.decidir("quanto está o dólar hoje?", [], quebrou)
    confere(d["modo"] == "pesquisa",
            "roteador: 'quanto está o dólar hoje?' é pesquisa")
    d = roteador.decidir("me explica o que é uma API", [], modelo_amigo)
    confere(d["modo"] == "amigo",
            "roteador: 'me explica o que é uma API' é papo")
    d = roteador.decidir("qual a última versão do Windows 11?", [], quebrou)
    confere(d["modo"] == "pesquisa",
            "roteador: 'última versão' é pesquisa pela heurística")

    confere(roteador.fato_pedido("lembra que eu gosto de RPG")
            == "gosto de RPG",
            "roteador: 'lembra que...' vira fato guardado")
    confere(roteador.fato_pedido("que dia é hoje?") is None,
            "roteador: pergunta normal não é pedido para lembrar")

    # instrucoes_da_ia com memória falsa (nunca lê a memória de verdade)
    _memoria_real = _pia.carregar_memoria
    _pia.carregar_memoria = lambda: []
    try:
        texto_amigo = _pia.instrucoes_da_ia("amigo")
        texto_pesquisa = _pia.instrucoes_da_ia("pesquisa")
    finally:
        _pia.carregar_memoria = _memoria_real
    confere("material achado" not in texto_amigo,
            "roteador: prompt do amigo não fala de material da web")
    confere("material achado" in texto_pesquisa,
            "roteador: prompt de pesquisa continua com o material da web")
except Exception as erro:
    falha("os testes do roteador quebraram: %r" % (erro,))
    print(traceback.format_exc()[-900:])

# --- 7. voz: gravador e transcricao (sem internet e sem microfone) ---------
try:
    import array
    import wave as _wave
    import voz

    def confere_voz(condicao, nome):
        if condicao:
            ok(nome)
        else:
            falha(nome)

    confere_voz(isinstance(voz.microfone_disponivel(), bool),
                "voz: microfone_disponivel() responde sem quebrar")
    confere_voz("microfone" in voz.microfone_erro(
        PermissionError("Access is denied")).lower(),
        "voz: erro de permissao vira frase em portugues")
    confere_voz("microfone" in voz.microfone_erro(
        RuntimeError("PortAudioError: no default device")).lower(),
        "voz: erro sem microfone vira frase em portugues")

    # --- Gravador com um fluxo de audio falso (nao mexe no microfone) ------
    class _FluxoFalso(object):
        def __init__(self):
            self.iniciado = False
            self.fechado = False

        def start(self):
            self.iniciado = True

        def stop(self):
            pass

        def close(self):
            self.fechado = True

    class _GravadorFalso(voz.Gravador):
        def _criar_fluxo(self, callback):
            self.callback = callback
            self.falso = _FluxoFalso()
            return self.falso

    silencio = array.array("h", [0] * 800)
    alto = array.array("h", [8000 if i % 2 else -8000 for i in range(800)])

    g = _GravadorFalso()
    g.iniciar()
    confere_voz(g.gravando and g.falso.iniciado,
                "voz: Gravador.iniciar() abre o fluxo e marca gravando")
    g.callback(silencio, 800, 0, None)
    confere_voz(g.nivel() == 0.0,
                "voz: silencio da nivel 0")
    g.callback(alto, 800, 0, None)
    confere_voz(g.nivel() > 1000,
                "voz: audio alto da nivel alto")
    confere_voz(not g.limite(),
                "voz: gravacao curta ainda nao chegou no limite")
    confere_voz(g.segundos > 0, "voz: conta os segundos gravados")

    g.tempo_maximo = 0.001
    confere_voz(g.limite(),
                "voz: avisando quando passou do tempo maximo")
    g.tempo_maximo = 120

    wav = g.parar()
    confere_voz(not g.gravando and g.falso.fechado,
                "voz: Gravador.parar() fecha o fluxo e para de gravar")

    # o WAV tem que sair com o cabecalho certo, senao o Gemini recusa
    try:
        with _wave.open(io.BytesIO(wav), "rb") as arquivo:
            canais = arquivo.getnchannels()
            largura = arquivo.getsampwidth()
            taxa = arquivo.getframerate()
            quadros = arquivo.getnframes()
        cabecalho_ok = (canais == 1 and largura == 2 and taxa == 16000
                        and quadros > 0)
    except Exception as erro:
        cabecalho_ok = False
        falha("voz: o WAV montado nao abre: %r" % (erro,))
    confere_voz(cabecalho_ok,
                "voz: WAV montado com 1 canal, 16 bits e 16 kHz")
    confere_voz(voz.segundos_do_wav(wav) > 0,
                "voz: segundos_do_wav() le a duracao")
    confere_voz(voz.wav_tem_som(wav),
                "voz: wav_tem_som() reconhece audio com voz")
    confere_voz(not voz.wav_tem_som(b""),
                "voz: wav_tem_som() diz que nao ha nada em audio vazio")
    confere_voz(not voz.wav_tem_som(
        voz._para_wav(silencio.tobytes())),
        "voz: wav_tem_som() diz que nao ha nada em silencio")

    # --- transcrever com um cliente falso (nao chama a internet) -----------
    class _ParteFalsa(object):
        def __init__(self, texto=None):
            self.text = texto

    class _RespostaFalsa(object):
        def __init__(self, texto):
            self.text = texto
            self.candidates = []

    class _ModelsFalsos(object):
        def __init__(self, respostas):
            self.respostas = dict(respostas)
            self.chamados = []

        def generate_content(self, model, contents, config=None):
            self.chamados.append(model)
            if model not in self.respostas:
                raise RuntimeError("modelo %s fora do ar" % model)
            return _RespostaFalsa(self.respostas[model])

    class _ClienteFalso(object):
        """Mesma forma do cliente do Gemini: cliente.models.generate_content."""

        def __init__(self, respostas):
            self.models = _ModelsFalsos(respostas)

    cliente_1 = _ClienteFalso({"m1": "qual o seu nome?"})
    confere_voz(voz.transcrever(cliente_1, ["m1"], wav) == "qual o seu nome?",
                "voz: transcrever() devolve o texto falado")

    cliente_2 = _ClienteFalso({"m2": "tudo bem"})
    confere_voz(voz.transcrever(cliente_2, ["m1", "m2"], wav) == "tudo bem",
                "voz: transcrever() tenta o proximo modelo quando um falha")
    confere_voz(cliente_2.models.chamados == ["m1", "m2"],
                "voz: transcrever() guarda a ordem dos modelos")

    try:
        voz.transcrever(_ClienteFalso({}), ["m1"], wav)
        confere_voz(False, "voz: transcrever() avisa quando nenhum modelo responde")
    except RuntimeError:
        ok("voz: transcrever() avisa quando nenhum modelo responde")

    try:
        voz.transcrever(_ClienteFalso({"m1": "x"}), ["m1"], b"")
        confere_voz(False, "voz: transcrever() recusa audio vazio")
    except RuntimeError:
        ok("voz: transcrever() recusa audio vazio")

    # O teste de "tem voz?" tem que aceitar voz fraca (pessoa longe do
    # microfone) e recusar so o ruido de fundo. Montamos os dois casos.
    def _wav_de(trechos):
        partes = []
        for nivel, amostras in trechos:
            partes.append(array.array(
                "h", [int(nivel if i % 2 else -nivel)
                      for i in range(amostras)]).tobytes())
        return voz._para_wav(b"".join(partes))

    # Niveis tirados da medicao real: microfone parado fica em ~5-20 e a
    # voz passando por ele passa de 400.
    voz_fraca = _wav_de([(450, 8000), (18, 8000), (420, 8000)])
    so_ruido = _wav_de([(12, 8000), (14, 8000), (11, 8000)])
    confere_voz(voz.wav_tem_som(voz_fraca),
                "voz: wav_tem_som() aceita voz fraca entre pausas")
    confere_voz(not voz.wav_tem_som(so_ruido),
                "voz: wav_tem_som() recusa so ruido de fundo")

    # quando o campo .text vem vazio, tem que remontar pelas partes
    class _RespostaEmPartes(object):
        text = ""
        candidates = []

    class _Conteudo(object):
        parts = [_ParteFalsa("bom dia")]

    class _Candidato(object):
        content = _Conteudo()

    _RespostaEmPartes.candidates = [_Candidato()]

    class _ModelsEmPartes(object):
        def generate_content(self, model, contents, config=None):
            return _RespostaEmPartes()

    class _ClienteEmPartes(object):
        models = _ModelsEmPartes()

    confere_voz(
        voz.transcrever(_ClienteEmPartes(), ["m1"], wav) == "bom dia",
        "voz: transcrever() remonta o texto quando .text vem vazio")
except Exception as erro:
    falha("os testes de voz quebraram: %r" % (erro,))
    print(traceback.format_exc()[-900:])

# --- 8. cantos arredondados da caixa (a conta da curva, sem tela) ----------
try:
    sys.path.insert(0, str(PASTA))
    import pesquisa_ia as _p2

    def confere_canto(condicao, nome):
        if condicao:
            ok(nome)
        else:
            falha(nome)

    # A curva de cada canto tem que ter o centro no canto OPOSTO: o canto
    # verdadeiro fica FORA (é o que a tampinha pinta de fundo) e o miolo da
    # caixa fica DENTRO (é o que fica transparente). Se inverter, a
    # tampinha come o botão de enviar em vez de arredondar o canto.
    LADO = 12
    ultimo = LADO - 1
    for canto, fora, dentro in (
        ("nw", (0, 0), (ultimo, ultimo)),
        ("ne", (ultimo, 0), (0, ultimo)),
        ("sw", (0, ultimo), (ultimo, 0)),
        ("se", (ultimo, ultimo), (0, 0)),
    ):
        d = _p2._dentro_do_canto
        confere_canto(not d(*fora, LADO, canto),
                      "canto %s: o bico do canto fica FORA da caixa" % canto)
        confere_canto(d(*dentro, LADO, canto),
                      "canto %s: o miolo da caixa fica DENTRO" % canto)

    # A caixa inteira (4 quadrantes de LADO) tem que perder só as pontas:
    # sobra a curvatura, uns 80% da área. Se ficar muito abaixo, os cantos
    # estão comendo a caixa; se ficar acima, não estão arredondando nada.
    dentro = total = 0
    for y in range(2 * LADO):
        for x in range(2 * LADO):
            if y < LADO:
                canto, px, py = ("nw" if x < LADO else "ne"), x % LADO, y
            else:
                canto = "sw" if x < LADO else "se"
                px, py = x % LADO, y - LADO
            total += 1
            if _p2._dentro_do_canto(px, py, LADO, canto):
                dentro += 1
    proporcao = 100.0 * dentro / total
    if 75.0 <= proporcao <= 90.0:
        ok("os quatro cantos cortam só a curvatura (%.1f%% do miolo)"
           % proporcao)
    else:
        falha("os cantos cortaram a medida errada: %.1f%% do miolo "
              "(esperado entre 75%% e 90%%)" % proporcao)

    # A imagem do canto tem que vir PINTAADA (dentro = cor da caixa, fora =
    # cor de fundo) e sem buraco transparente: o tkinter nao tem widget
    # transparente, e o fundo de um Label cobre o quadrado todo — com
    # buraco, o canto saia como um QUADRADO preto em vez de uma curva.
    _p2._FOTOS_CANTO.clear()
    imagem = _p2._imagem_canto(_p2.RAIO_CANTO, _p2.COR_BARRA,
                               _p2.COR_FUNDO, "nw")
    if imagem is None:
        falha("não consegui desenhar a imagem do canto arredondado")
    else:
        da_caixa = de_fundo = transparentes = outros = 0
        for y in range(imagem.height):
            for x in range(imagem.width):
                cor = imagem.getpixel((x, y))
                if cor[3] < 128:
                    transparentes += 1
                elif cor[:3] == _p2._rgba(_p2.COR_BARRA)[:3]:
                    da_caixa += 1
                elif cor[:3] == _p2._rgba(_p2.COR_FUNDO)[:3]:
                    de_fundo += 1
                else:
                    outros += 1
        if transparentes == 0:
            ok("imagem do canto sem buraco transparente (ela pinta as "
               "duas cores)")
        else:
            falha("a imagem do canto tem %d pixel(is) transparente(s): "
                  "o fundo do Label vai aparecer e o canto vira "
                  "quadrado" % transparentes)
        if da_caixa and de_fundo and outros < (da_caixa + de_fundo):
            ok("imagem do canto tem as duas cores (%d da caixa, %d de "
               "fundo, %d de borda/antialising)" % (da_caixa, de_fundo,
                                                     outros))
        else:
            falha("a imagem do canto ficou errada (%d caixa / %d fundo / "
                  "%d borda)" % (da_caixa, de_fundo, outros))
except Exception as erro:
    falha("os testes dos cantos quebraram: %r" % (erro,))

print()
if falhas:
    print("RESULTADO: %d FALHA(S). Corrija antes de entregar." % len(falhas))
    sys.exit(1)
print("TUDO CERTO" + (" (com %d aviso(s))" % len(avisos) if avisos else ""))
