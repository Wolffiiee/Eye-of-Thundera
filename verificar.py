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
import py_compile
import re
import subprocess
import sys
import time
import tkinter as tk
import traceback
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

PASTA = Path(__file__).resolve().parent
ARQUIVO = PASTA / "pesquisa_ia.py"
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
        [sys.executable, "-m", "pyflakes", str(ARQUIVO), str(Path(__file__))],
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

# --- 5. testes com a janela de verdade -------------------------------------


def testes_de_tela():
    sys.path.insert(0, str(PASTA))
    import pesquisa_ia as p

    raiz = tk.Tk()
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


if not falhas:
    try:
        testes_de_tela()
    except Exception as erro:
        falha("os testes de tela quebraram: %r" % (erro,))
        print(traceback.format_exc()[-900:])
else:
    aviso("testes de tela pulados porque houve falha acima")

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

print()
if falhas:
    print("RESULTADO: %d FALHA(S). Corrija antes de entregar." % len(falhas))
    sys.exit(1)
print("TUDO CERTO" + (" (com %d aviso(s))" % len(avisos) if avisos else ""))
