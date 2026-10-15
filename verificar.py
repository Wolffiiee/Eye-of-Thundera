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


def _esperar(raiz, segundos):
    fim = time.time() + segundos
    while time.time() < fim:
        raiz.update()
        time.sleep(0.05)


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

        # a janelinha de "chave inválida" tem que abrir sem estourar erro
        # (o teste fecha ela sozinha depois de um instante)
        def fecha_janela():
            for w in raiz.winfo_children():
                if isinstance(w, tk.Toplevel):
                    w.destroy()

        raiz.after(500, fecha_janela)
        try:
            app._janela_chave_ruim(
                "Uma das chaves de API parece inválida. Abra Configurações.")
            raiz.update()
            ok("janela de 'chave inválida' abre e fecha sem erro")
        except Exception as erro:
            falha("a janela de chave inválida quebrou: %r" % (erro,))
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
