# -*- coding: utf-8 -*-
"""
Verificação automática do Eye of Thundera.

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
import tempfile
import time

if sys.stdout is not None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
from pathlib import Path

# Onde a janela de teste aparece. O segundo monitor do Wolf comeca em
# X=1920; usar +2000+100 joga a janela para la e deixa a tela principal
# dele livre. Se um dia o monitor mudar, e so mexer aqui.
POSICAO_TESTE = "+2000+100"

# Pasta do projeto (onde este arquivo está)
PASTA = Path(__file__).parent

# O arquivo principal do motor
ARQUIVO = PASTA / "pesquisa_ia.py"

falhas = []
avisos = []
verificacoes = 0


def ok(msg):
    global verificacoes
    verificacoes += 1
    print("[OK]     " + msg)


def falha(msg):
    global verificacoes
    verificacoes += 1
    print("[FALHA]  " + msg)
    falhas.append(msg)


def aviso(msg):
    global verificacoes
    verificacoes += 1
    print("[AVISO]  " + msg)
    avisos.append(msg)


# --- 1. sintaxe -------------------------------------------------------------
try:
    py_compile.compile(str(PASTA / "pesquisa_ia.py"), doraise=True)
    ok("pesquisa_ia.py sem erro de sintaxe")
except py_compile.PyCompileError as erro:
    falha("erro de sintaxe: %s" % erro)

# A tela depende deste JavaScript inteiro ser interpretado. Uma única chave
# sobrando impede todos os botões de receberem eventos, embora a janela abra.
node = shutil.which("node")
if node:
    try:
        r_js = subprocess.run(
            [node, "--check", str(PASTA / "web" / "app.js")],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            cwd=str(PASTA), timeout=15,
        )
        if r_js.returncode == 0:
            ok("web/app.js sem erro de sintaxe (Node.js)")
        else:
            detalhe = (r_js.stderr or r_js.stdout or "erro desconhecido").strip()
            falha("erro de sintaxe em web/app.js: " + detalhe.splitlines()[0])
    except Exception as erro:
        aviso("não consegui verificar a sintaxe de web/app.js: %r" % (erro,))
else:
    aviso("Node.js não encontrado; sintaxe de web/app.js não foi verificada")

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
         str(PASTA / "roteador.py"), str(PASTA / "voz.py"),
         str(PASTA / "pdf_leitor.py")],
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

# --- 4b. onde cada janela abre --------------------------------------------
# REGRA DO WOLF, DUAS (elas mudaram em 16/10/2026):
#
# 1. JANELA DE TESTE (`verificar.py`): nasce no SEGUNDO monitor, para
#    nunca cobrir a tela em que ele esta trabalhando. Esta regra continua.
# 2. PROGRAMA DE VERDADE (.exe da tela nova): abre onde o Wolf fechou da
#    ultima vez, caindo no meio da tela principal se ainda nao souber.
web_txt = (PASTA / "app_web.py").read_text(encoding="utf-8")

# (1) a PREVIA (modo 'so olhar') continua no segundo monitor.
# Verifica o COMPROMISSO no codigo, sem copiar trecho nenhum: copiar
# trecho quebrava toda vez que o trecho crescia e passava a usar algo
# novo (16/10/2026: o exec do trecho deu NameError porque o trecho agora
# inclui _telas(), que usa ctypes).
if "if PREVIA:" in web_txt and "(2000, 100)" in web_txt:
    ok("a janela de teste (PREVIA) nasce no segundo monitor")
else:
    falha("a janela de teste (PREVIA) pode abrir na tela do Wolf")
if "else:" in web_txt and "(200, 100)" in web_txt:
    ok("o programa normal nao fica preso no segundo monitor")
else:
    falha("o programa normal pode nascer sempre no segundo monitor")
if "x=abrir_x, y=abrir_y" in web_txt:
    ok("a janela abre na posicao escolhida, e nao num ponto fixo")
else:
    falha("a janela continua a abrir num ponto fixo")

# (2) o PROGRAMA DE VERDADE nao esta preso no segundo monitor
if "X_PADRAO, Y_PADRAO = (200, 100)" in web_txt:
    ok("o programa de verdade nao nasce fixo no 2o monitor")
else:
    # antes era (2000, 100); se voltar, reprova
    falha("o programa de verdade voltou a nascer fixo no 2o monitor")
if "_posicao_de_abertura" in web_txt and "janela.events.closing" in web_txt:
    ok("o programa lembra em que monitor foi fechado")
else:
    falha("o programa ainda nao lembra onde foi fechado")
if "_ler_posicao" in web_txt and "ARQUIVO_POSICAO" in web_txt:
    ok("a posicao da janela e' guardada em arquivo")
else:
    falha("a posicao da janela nao e' guardada em lugar nenhum")
if 'ARQUIVO_POSICAO = p.PASTA_CONFIG / "janela.json"' in web_txt:
    ok("a posicao fica num arquivo separado (janela.json)")
else:
    falha("a posicao esta misturada com o config.json, onde esta a chave da API")

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

# --- 4c2. "outras perguntas": botao, nao automatico -----------------------
# Cada sugestao gasta uma chamada de IA, entao isso NAO pode acontecer
# sozinho a cada resposta: so quando o Wolf aperta. Aqui a IA e' de
# mentira (gastar a cota real num teste seria errado).
try:
    import app_web as _aw
    import google.genai as _genai_real

    class _RespostaDeSugerir:
        def __init__(self, texto):
            self.text = texto

    class _ModelsDeSugerir:
        def __init__(self, texto):
            self._texto = texto
            self.chamadas = 0

        def generate_content(self, **_kw):
            self.chamadas += 1
            return _RespostaDeSugerir(self._texto)

    class _ClienteDeSugerir:
        def __init__(self, texto):
            self.models = _ModelsDeSugerir(texto)

    _pasta = Path(PASTA) / "_tmp" / "teste-sugerir"
    shutil.rmtree(_pasta, ignore_errors=True)
    _pasta.mkdir(parents=True, exist_ok=True)
    _cfg_orig = _aw.p.ARQUIVO_CONFIG
    _demo_orig = _aw.DEMO
    # O Client DE VERDADE e' guardado ANTES de trocar: se nao for
    # restaurado, a IA de mentira continua valendo para o resto da
    # verificacao (e qualquer teste depois dela passa a mentir sem
    # querer). Foi assim que este teste vazava antes.
    _client_original = _genai_real.Client
    try:
        _aw.p.ARQUIVO_CONFIG = _pasta / "config.json"
        _aw.DEMO = False
        _aw.p._gravar_json(_aw.p.ARQUIVO_CONFIG, {"api_key": "AIza-de-teste"})
        _ponte = _aw.Ponte(None)

        # 1. a IA devolve JSON sujo (com texto em volta): tem que ler
        _genai_real.Client = lambda **_kw: _ClienteDeSugerir(
            'Claro! {"perguntas": ["Quem ganhou?", "Quando e o proximo?", '
            '"Onde joga?"]} ate la')
        r = _ponte.sugerir("proximo jogo", "contra o Cruzeiro")
        if r.get("perguntas") == ["Quem ganhou?", "Quando e o proximo?",
                                  "Onde joga?"]:
            ok("outras perguntas: lê o JSON mesmo com texto em volta")
        else:
            falha("outras perguntas: devolveu %r" % (r,))

        # 2. a IA devolve besteira: avisa em vez de quebrar a tela
        _genai_real.Client = lambda **_kw: _ClienteDeSugerir("desculpe, nao sei")
        if _ponte.sugerir("a", "b").get("erro"):
            ok("outras perguntas: resposta fora do formato avisa na tela")
        else:
            falha("outras perguntas: aceitou lixo como se fosse lista")
        _genai_real.Client = lambda **_kw: _ClienteDeSugerir('{"perguntas": []}')
        if _ponte.sugerir("a", "b").get("erro"):
            ok("outras perguntas: lista vazia avisa, não mostra nada")
        else:
            falha("outras perguntas: mostrou lista vazia sem avisar")

        # 3. no maximo 3 perguntas
        _genai_real.Client = lambda **_kw: _ClienteDeSugerir(
            '{"perguntas": ["1", "2", "3", "4", "5"]}')
        if len(_ponte.sugerir("a", "b").get("perguntas", [])) == 3:
            ok("outras perguntas: mostra no máximo 3")
        else:
            falha("outras perguntas: mostrou %d"
                  % len(_ponte.sugerir("a", "b").get("perguntas", [])))

        # 4. sem chave ele diz sem_chave (a tela abre as Configuracoes)
        _aw.p._gravar_json(_aw.p.ARQUIVO_CONFIG, {})
        if _ponte.sugerir("a", "b").get("erro") == "sem_chave":
            ok("outras perguntas: sem chave avisa sem chamar a IA")
        else:
            falha("outras perguntas: sem chave nao avisou")

        # 5. no modo exemplo nao chama a IA (nao gasta cota)
        _aw.DEMO = True
        antes_demo = _ponte.sugerir("a", "b")
        if antes_demo.get("erro"):
            ok("outras perguntas: no modo exemplo não gasta cota")
        else:
            falha("outras perguntas: no modo exemplo respondeu de verdade")
    finally:
        _aw.p.ARQUIVO_CONFIG = _cfg_orig
        _aw.DEMO = _demo_orig
        _genai_real.Client = _client_original
        shutil.rmtree(_pasta, ignore_errors=True)
except Exception as erro:
    falha("os testes de 'outras perguntas' quebraram: %r" % (erro,))

# --- 4c3. backup dos dados dentro do programa (o mesmo do .bat) ----------
# O botao das Configuracoes e o `9 - Fazer backup dos meus dados.bat`
# usam a MESMA funcao do motor: dois jeitos de fazer a mesma coisa e' a
# receita para um deles ficar velho. Aqui a funcao e' testada numa pasta
# de TESTE (os dados do Wolf nunca sao tocados).
try:
    import pesquisa_ia as _pi2
    _tmp_bk = Path(PASTA) / "_tmp" / "teste-backup"
    shutil.rmtree(_tmp_bk, ignore_errors=True)
    _origem = _tmp_bk / "origem"
    _origem.mkdir(parents=True)
    (_origem / "historico.json").write_text("[]", encoding="utf-8")
    (_origem / "memoria.json").write_text('["Gosta de RPG"]', encoding="utf-8")
    _pasta_orig = _pi2.PASTA_CONFIG
    _pi2.PASTA_CONFIG = _origem
    try:
        _zip, _nomes = _pi2.fazer_backup_dados(destino=_tmp_bk / "dados")
    finally:
        _pi2.PASTA_CONFIG = _pasta_orig
    import zipfile as _zf
    with _zf.ZipFile(_zip) as _z:
        _dentro = sorted(_z.namelist())
        _memoria = _z.read("memoria.json").decode("utf-8")
    if _dentro == ["historico.json", "memoria.json"]:
        ok("backup dos dados: copia exatamente os arquivos da pasta")
    else:
        falha("backup dos dados: copiou %r" % (_dentro,))
    if "Gosta de RPG" in _memoria:
        ok("backup dos dados: o conteúdo da memória vai inteiro no .zip")
    else:
        falha("backup dos dados: a memória saiu vazia do .zip")
    _vazia = Path(PASTA) / "_tmp" / "backup-sem-nada"
    shutil.rmtree(_vazia, ignore_errors=True)
    _vazia.mkdir(parents=True)
    _pasta_orig = _pi2.PASTA_CONFIG
    _pi2.PASTA_CONFIG = _vazia
    try:
        _pi2.fazer_backup_dados(destino=_vazia / "dados")
        _aviso_vazio = False
    except Exception:
        _aviso_vazio = True
    finally:
        _pi2.PASTA_CONFIG = _pasta_orig
    if _aviso_vazio:
        ok("backup dos dados: sem arquivos, avisa e não cria zip vazio")
    else:
        falha("backup dos dados: criou um zip sem nenhum arquivo")
    if _pi2.PASTA_CONFIG == _pasta_orig and _pasta_orig.name == "PesquisaIA":
        ok("backup dos dados: a pasta de verdade do Wolf não foi trocada")
    else:
        falha("backup dos dados: a pasta de dados ficou %r" % (_pi2.PASTA_CONFIG,))
    shutil.rmtree(_tmp_bk, ignore_errors=True)
    shutil.rmtree(_vazia, ignore_errors=True)
except Exception as erro:
    falha("os testes do backup dos dados quebraram: %r" % (erro,))

# --- 4c4. datas da memoria: o que o Wolf aprendeu, e quando --------------
# As datas ficam num arquivo AO LADO do memoria.json, nunca dentro dele:
# o memoria.json e' lido pelos dois programas e tem regra de ouro (nunca
# perder uma palavra). O arquivo das datas sai do caminho do
# ARQUIVO_MEMORIA, entao um teste nao escreve na pasta de verdade.
try:
    import pesquisa_ia as _pi3
    _tmp_dt = Path(PASTA) / "_tmp" / "teste-datas"
    shutil.rmtree(_tmp_dt, ignore_errors=True)
    _tmp_dt.mkdir(parents=True)
    _real_datas = Path(_pi3.PASTA_CONFIG) / "memoria_datas.json"
    _datas_antes = _real_datas.read_bytes() if _real_datas.exists() else None
    _mem_orig = _pi3.ARQUIVO_MEMORIA
    _pi3.ARQUIVO_MEMORIA = _tmp_dt / "memoria.json"
    try:
        _pi3.salvar_memoria(["Gosta de RPG", "Mora em Santa Maria"])
        _d1 = _pi3.carregar_memoria_datas()
        if sorted(_d1) == ["Gosta de RPG", "Mora em Santa Maria"] and \
                all(len(v) == 10 and v[2] == "/" for v in _d1.values()):
            ok("memória com data: cada fato novo ganha a data de hoje")
        else:
            falha("memória com data: ficou %r" % (_d1,))
        _pi3.salvar_memoria(["Gosta de RPG", "Mora em Santa Maria", "Novo"])
        if "Novo" in _pi3.carregar_memoria_datas():
            ok("memória com data: o item novo aparece com data na hora")
        else:
            falha("memória com data: o item novo ficou sem data")
        _pi3.esquecer_memoria("Mora em Santa Maria")
        if "Mora em Santa Maria" not in _pi3.carregar_memoria_datas():
            ok("memória com data: o que foi apagado some da lista de datas")
        else:
            falha("memória com data: sobrou data de item apagado")
        # o arquivo do lado NAO pode estar dentro do memoria.json
        _conteudo = json.loads((_tmp_dt / "memoria.json").read_text(
            encoding="utf-8"))
        if _conteudo == ["Gosta de RPG", "Novo"]:
            ok("memória com data: o memoria.json continua só com os fatos")
        else:
            falha("memória com data: o memoria.json mudou de formato (%r)"
                  % (_conteudo,))
        if (_tmp_dt / "memoria_datas.json").exists():
            ok("memória com data: as datas vão num arquivo ao lado")
        else:
            falha("memória com data: não foi criado o arquivo das datas")
        # compara o ANTES com o DEPOIS: o arquivo real pode existir (uso normal)
        if (_real_datas.read_bytes() if _real_datas.exists() else None) \
                == _datas_antes or _pi3.PASTA_CONFIG == _tmp_dt:
            ok("memória com data: a pasta de verdade do Wolf não foi escrita")
        else:
            falha("memória com data: escreveu na pasta de verdade")
    finally:
        _pi3.ARQUIVO_MEMORIA = _mem_orig
        shutil.rmtree(_tmp_dt, ignore_errors=True)
except Exception as erro:
    falha("os testes das datas da memória quebraram: %r" % (erro,))

# --- 4c5. a ponte nao se perde dentro da janela (16/10/2026) --------------
# ESTE FOI O DEFÉITO QUE TRAVOU A TELHA DO WOLF:
# a janela ficava exposta na ponte e o pywebview, ao montar a lista de
# funções, ENTRAVA dentro dela — `native` -> `AccessibilityObject` ->
# `Bounds` -> `Empty` -> `Empty` -> ... sem fim ("maximum recursion depth
# exceeded"). Enquanto isso a ponte ficava VAZIA, e a tela, ja pronta,
# perguntava e levava "TypeError: api[nome] is not a function". Depois
# disso o "pensando" ficava aceso e nao dava mais para perguntar nada.
#
# O teste tem um CONTROLE: uma ponte com a janela exposta DEVE entrar em
# loop. Se o controle nao entrar, o teste nao esta testando nada.
try:
    import inspect as _inspect
    import app_web as _aw

    class _EspelhoInfinito:
        """Imita o `Bounds.Empty.Empty.Empty...` do WebView2: cada coisa
        leva na mesma coisa, para sempre."""

        __module__ = "falso"

        def __dir__(self):
            return ["Empty", "native"]

        def __getattr__(self, _nome):
            return self

    class _JanelaComoWebView2:
        __module__ = "falso"

        def __init__(self):
            self.native = _EspelhoInfinito()

    class _EntrouNoInfinito(Exception):
        pass

    # O orcamento conta nos VISITADOS, e nao a profundidade: a arvore do
    # WebView2 se divide em DOIS a cada nivel (os dois nomes apontam para
    # o mesmo objeto), entao a profundidade sozinha nao diz nada — da para
    # "achar" um limite raso e nao será o defeito real. Com este orcamento
    # o controle estoura em milissegundos.
    ORCAMENTO = 5000

    def _caminhar(obj, restantes=ORCAMENTO):
        """A MESMA caminhada que o pywebview faz (webview/util.py,
        `get_functions`): nada de underline, e se o atributo nao e' funcao
        mas tem `__module__`, entra dentro dele procurando funcoes.

        Devolve quantos atributos visitou (menos = melhor)."""
        if restantes <= 0:
            raise _EntrouNoInfinito()
        for nome in dir(obj):
            if nome.startswith("_"):
                continue
            restantes -= 1
            try:
                attr = getattr(obj, nome)
            except Exception:
                continue
            if _inspect.ismethod(attr) or _inspect.isfunction(attr):
                continue
            if hasattr(attr, "__module__"):
                _caminhar(attr, restantes)
        return ORCAMENTO - restantes

    # --- o CONTROLE: com a janela exposta, a caminhada TEM de se perder
    _controle = _aw.Ponte()
    _controle.janela = _JanelaComoWebView2()      # o defeito, de proposito
    try:
        _caminhar(_controle)
        _controle_entrou = False
    except _EntrouNoInfinito:
        _controle_entrou = True
    except Exception:
        _controle_entrou = True
    if _controle_entrou:
        ok("ponte: o teste sabe detectar a janela envenenada (controle)")
    else:
        falha("ponte: o controle NÃO entrou em loop — o teste não serve "
              "para provar nada")

    # --- e agora a ponte de verdade, que tem a janela ESCONDIDA
    _p = _aw.Ponte()
    if "janela" not in [n for n in dir(_p) if not n.startswith("_")]:
        ok("ponte: a janela não fica exposta para o pywebview entrar nela")
    else:
        falha("ponte: a janela está exposta (o defeito do dia 16/10)")
    _p._janela = _JanelaComoWebView2()
    try:
        _vistos = _caminhar(_p)
        _entrou = False
    except _EntrouNoInfinito:
        _entrou = True
        _vistos = -1
    except Exception:
        # qualquer outro problema tambem e' a ponte se perdendo
        _entrou = True
        _vistos = -1
    if not _entrou:
        ok("ponte: montar a ponte não se perde dentro da janela "
           "(%d atributos)" % _vistos)
    else:
        falha("ponte: a caminhada entrou em loop mesmo com a janela "
              "escondida")
    # a janela continua guardada: sem isso a tela nao receberia nada
    _p._janela = "JANELA-TESTE"
    if _p._janela == "JANELA-TESTE":
        ok("ponte: a janela continua guardada (com nome escondido)")
    else:
        falha("ponte: a janela sumiu")

    # --- e a tela espera a ponte encher, em vez de confiar na ordem
    _js = Path(PASTA / "web" / "app.js").read_text(encoding="utf-8")
    if "esperarPonte" in _js and "ESPERA_PONTE_MS" in _js:
        ok("ponte: a tela espera a ponte ficar pronta antes de perguntar")
    else:
        falha("ponte: a tela não espera a ponte (pode levar "
              "api[nome] is not a function)")
    if "esperar(false)" in _js:
        ok("ponte: se a chamada falhar, a tela destrava em vez de "
           "ficar esperando para sempre")
    else:
        falha("ponte: a tela pode ficar travada depois de um erro")
except Exception as erro:
    falha("os testes da ponte quebraram: %r" % (erro,))

# --- 4c6. botao direito: correcao de palavra na tela nova ---------------
# O WebView2 em PRODUCAO desliga o menu de contexto do navegador
# (`AreDefaultContextMenusEnabled = _state['debug']`), entao o botao
# direito abria NADA. A tela faz o menu dela, e a sugestao vem do MOTOR
# (a mesma funcao que o programa antigo usa) para as duas telas
# concordarem.
try:
    import pesquisa_ia as _p_menu
    _probe = _aw.Ponte()
    if not callable(getattr(_probe, "sugerir_correcao", None)):
        falha("menu do botão direito: a ponte não tem sugerir_correcao")
    else:
        ok("menu do botão direito: a ponte tem sugerir_correcao")

    _casos = [("gobiln", True), ("represetndo", True), ("casa", False),
              ("1999", False), ("x", False), ("", False), (None, False)]
    _achou, _falhou = 0, []
    _goblin = None
    for _palavra, _deveria in _casos:
        _lista = _p_menu.sugerir_correcao(_palavra) or []
        if _palavra == "gobiln":
            _goblin = _lista
        if _deveria and _lista:
            _achou += 1
        elif not _deveria and not _lista:
            _achou += 1
        else:
            _falhou.append((_palavra, _lista[:3]))
    if _achou == len(_casos):
        ok("menu do botão direito: corrige palavra errada e respeita "
           "palavra certa, número e lixo")
    else:
        falha("menu do botão direito: %r deram diferente do esperado"
              % (_falhou,))
    if "goblin" in (_goblin or []):
        ok("menu do botão direito: 'gobiln' vira 'goblin'")
    else:
        falha("menu do botão direito: 'gobiln' não virou 'goblin'")
    # o programa ANTIGO usa a MESMA funcao: uma cópia só, para as duas
    # telas nunca discordarem do que é "palavra errada".
    _antigo = Path(PASTA / "pesquisa_ia.py").read_text(encoding="utf-8")
    if ("sugerir_correcao" in _antigo
            and _antigo.count("def sugerir_correcao") == 1):
        ok("menu do botão direito: o programa antigo usa a função do motor")
    else:
        falha("menu do botão direito: o programa antigo tem cópia própria "
              "da correção")

    _js2 = Path(PASTA / "web" / "app.js").read_text(encoding="utf-8")
    for _precisa, _rotulo in (
            ("contextmenu", "a tela escuta o botão direito"),
            ("preventDefault", "a tela cancela o menu do navegador"),
            ("ligarMenuContexto", "o menu é ligado na abertura"),
            ("itemMenu", "o menu é desenhado com botões"),
            ("setRangeText", "escolher a sugestão troca a palavra certa"),
            ("caretRangeFromPoint", "o cursor vai para onde foi clicado"),
            ("menu-contexto", "o menu tem lugar na tela")):
        if _precisa in _js2:
            ok("menu do botão direito: %s" % _rotulo)
        else:
            falha("menu do botão direito: falta %s" % _precisa)
    _html2 = Path(PASTA / "web" / "index.html").read_text(encoding="utf-8")
    if 'id="menu-contexto"' in _html2 and 'class="oculto"' in _html2:
        ok("menu do botão direito: começa escondido na tela")
    else:
        falha("menu do botão direito: o #menu-contexto não existe (ou "
              "não começa escondido)")
    _trecho_recortar = _js2.split('itemMenu("Recortar"', 1)[1].split('itemMenu("Copiar"', 1)[0]
    if ("function escreverClipboard" in _js2
            and 'document.execCommand("copy")' in _js2
            and 'await escreverClipboard(trecho)' in _trecho_recortar
            and 'if (copiou)' in _trecho_recortar
            and 'o texto foi mantido.' in _trecho_recortar
            and _trecho_recortar.index('await escreverClipboard(trecho)')
                < _trecho_recortar.index('campo.setRangeText("",')):
        ok("menu do botão direito: Recortar só apaga após confirmar a cópia")
    else:
        falha("menu do botão direito: Recortar pode apagar texto sem copiá-lo")
    if ('setAttribute("role", "menuitem")' in _js2
            and 'menu.addEventListener("keydown"' in _js2
            and all(k in _js2 for k in ("ArrowDown", "ArrowUp", "Escape", "Home", "End"))
            and 'foco.focus({ preventScroll: true })' in _js2):
        ok("menu do botão direito: atalhos visíveis, teclado e retorno de foco")
    else:
        falha("menu do botão direito: acessibilidade por teclado incompleta")
    if ("function indiceTextareaNoPonto" in _js2
            and "faixa.getBoundingClientRect()" in _js2
            and "Não consegui acessar a área de transferência. Use Ctrl+V." in _js2):
        ok("seleção de texto: clique direito posiciona o cursor e colar avisa quando falha")
    else:
        falha("seleção de texto: posicionamento ou retorno do comando Colar incompleto")
except Exception as erro:
    falha("os testes do menu do botão direito quebraram: %r" % (erro,))

# --- 4c7. galeria de imagens: a tela nova tambem mostra fotos ----------
# Era a ÚLTIMA coisa que o programa antigo tinha e a tela nova nao. Sem
# isto, o antigo nao podia ser aposentado.
try:
    import app_web as _aw2
    import pesquisa_ia as _pg_p          # o mesmo modulo, nome curto aqui
    import io as _io2
    from PIL import Image as _Img, ImageDraw as _Drw

    def _foto(cor, nome):
        # `ImageDraw` e' o MODULO: a classe e' `ImageDraw.Draw`. Do
        # mesmo modo `Image.new` existe, mas so nas versoes novas.
        _i = _Img.new("RGB", (640, 400), cor)
        _Drw.Draw(_i).text((20, 20), nome, fill=(255, 255, 255))
        _b = _io2.BytesIO()
        _i.save(_b, format="JPEG")
        return _b.getvalue()

    _pasta_gal = Path(PASTA) / "_tmp" / "teste-galeria"
    shutil.rmtree(_pasta_gal, ignore_errors=True)
    _pasta_gal.mkdir(parents=True)
    _guardado = (_pg_p.ARQUIVO_CONFIG, _pg_p.ARQUIVO_HISTORICO,
                 _pg_p.ARQUIVO_MEMORIA, _pg_p.PASTA_CONFIG,
                 _pg_p._buscar_imagens, _pg_p._precarregar_imagens,
                 _aw2.DEMO)
    try:
        _pg_p.ARQUIVO_CONFIG = _pasta_gal / "config.json"
        _pg_p.ARQUIVO_HISTORICO = _pasta_gal / "historico.json"
        _pg_p.ARQUIVO_MEMORIA = _pasta_gal / "memoria.json"
        _pg_p.PASTA_CONFIG = _pasta_gal
        _pg_p.ARQUIVO_CONFIG.write_text(json.dumps({"api_key": "x"}),
                                    encoding="utf-8")
        _pg_p.ARQUIVO_HISTORICO.write_text("[]", encoding="utf-8")
        _pg_p.ARQUIVO_MEMORIA.write_text("[]", encoding="utf-8")
        _aw2.DEMO = False

        # a internet nao e' chamada: o teste finge a busca
        _itens = [{
            "titulo": "Lobo %d" % _i,
            "pagina": "https://exemplo.com/%d" % _i,
            "imagem": "https://exemplo.com/%d.jpg" % _i,
            "thumb_url": "https://exemplo.com/%dt.jpg" % _i,
            "thumb": _foto((60 + _i * 40, 90, 150), "Lobo %d" % _i),
            "_grande": _Img.new("RGB", (1200, 800), (30, 60, 120)),
        } for _i in range(3)]
        _foi_pedido = []

        def _busca_falsa(termo, quantidade=9):
            _foi_pedido.append(termo)
            return [_d.copy() for _d in _itens]

        _pg_p._buscar_imagens = _busca_falsa
        _pg_p._precarregar_imagens = lambda itens: None

        class _JanelaFalsa:
            def __init__(self):
                self.recebido = []

            def evaluate_js(self, codigo):
                self.recebido.append(
                    json.loads(codigo[codigo.find("(") + 1:codigo.rfind(")")]))
                return None

        _pg = _aw2.Ponte()
        _pg._janela = _JanelaFalsa()
        _pg._gravar_conversa = lambda *a, **k: None

        # --- a pergunta de imagem NAO exige chave de API
        _r = _pg.enviar("imagens de lobos")
        if _r == {} and _foi_pedido == ["lobos"]:
            ok("galeria: 'imagens de lobos' vai para a busca, sem gastar "
               "chave de API")
        else:
            falha("galeria: a pergunta de imagem nao chegou na busca (%r, %r)"
                  % (_r, _foi_pedido))
        for _ in range(60):
            if not _pg.ocupado:
                break
            time.sleep(0.2)
        if not _pg.ocupado:
            ok("galeria: a tela destrava depois de mostrar as fotos")
        else:
            falha("galeria: a tela ficou travada esperando as fotos")

        _eventos = [e.get("tipo") for e in _pg._janela.recebido]
        if "imagens" in _eventos:
            ok("galeria: o evento com as fotos chega na tela")
        else:
            falha("galeria: nenhum evento de imagens (veio %r)" % (_eventos,))
        _ev = next((e for e in _pg._janela.recebido
                    if e.get("tipo") == "imagens"), {})
        _fotos = _ev.get("fotos") or []
        if (len(_fotos) == 3
                and all(str(f.get("miniatura", "")).startswith("data:image/")
                        for f in _fotos)):
            ok("galeria: as miniaturas viajam prontas para a tela "
               "(%d caracteres cada)" % len(_fotos[0]["miniatura"]))
        else:
            falha("galeria: as miniaturas não chegaram prontas (%r)"
                  % ([str(f)[:30] for f in _fotos],))
        if any(m.get("role") == "user" and m.get("text") == "imagens de lobos"
               for m in _pg.mensagens):
            ok("galeria: a pergunta fica na conversa")
        else:
            falha("galeria: a pergunta não ficou na conversa")

        # --- a foto grande vem quando o Wolf clica
        _grande = _pg.imagem_ampliada(0)
        if str(_grande.get("base64", "")).startswith("data:image/"):
            ok("galeria: a foto grande vem quando o Wolf clica")
        else:
            falha("galeria: a foto grande não veio (%r)" % (_grande,))
        if (_pg.imagem_ampliada(99).get("erro")
                and _pg.imagem_ampliada("x").get("erro")
                and _pg.imagem_ampliada(-1).get("erro")):
            ok("galeria: clique fora da lista não derruba o programa")
        else:
            falha("galeria: índice inventado devolveu algo")

        # --- pergunta normal NAO entra na busca de imagens
        _foi_pedido.clear()
        _pg.ocupado = False
        _pg.enviar("como faz arroz?")
        if not _foi_pedido:
            ok("galeria: pergunta normal não vira busca de imagens")
        else:
            falha("galeria: 'como faz arroz?' foi para a busca de imagens")

        # --- e a tela sabe desenhar e abrir a foto
        _js3 = Path(PASTA / "web" / "app.js").read_text(encoding="utf-8")
        for _precisa, _rotulo in (
                ('o.tipo === "imagens"', "a tela entende o evento de fotos"),
                ("function desenharGaleria", "a tela desenha a grade"),
                ("function ampliarFoto", "a tela abre a foto grande"),
                ('chamar("imagem_ampliada"', "a tela pede a foto grande"),
                ("estado.ultimaBolha", "as fotos entram na bolha da resposta")):
            if _precisa in _js3:
                ok("galeria: %s" % _rotulo)
            else:
                falha("galeria: falta %s na tela" % _precisa)
        _css3 = Path(PASTA / "web" / "estilo.css").read_text(encoding="utf-8")
        if ".galeria {" in _css3 and ".foto-aberta {" in _css3:
            ok("galeria: a grade e a foto aberta tem desenho (sempre escuro)")
        else:
            falha("galeria: falta o desenho da grade ou da foto aberta")
    finally:
        (_pg_p.ARQUIVO_CONFIG, _pg_p.ARQUIVO_HISTORICO, _pg_p.ARQUIVO_MEMORIA,
         _pg_p.PASTA_CONFIG, _pg_p._buscar_imagens, _pg_p._precarregar_imagens,
         _aw2.DEMO) = _guardado
        shutil.rmtree(_pasta_gal, ignore_errors=True)
except Exception as erro:
    falha("os testes da galeria de imagens quebraram: %r" % (erro,))

# --- 4c8. o visor de fotos: passar para a proxima sem fechar --------------
# O Wolf pediu exatamente isto: nao diminuir a foto e clicar na outra.
# A tela de foto grande virou um VISOR com varias fotos: setas do teclado,
# botao embaixo e arrastar com o mouse.
try:
    _js4 = Path(PASTA / "web" / "app.js").read_text(encoding="utf-8")
    for _precisa, _rotulo, _por_que in (
            ("function abrirVisorFotos",
             "a tela tem um visor de fotos", "abrirVisorFotos"),
            ('ArrowRight', "as setas do teclado passam de uma para outra",
             "seta para a direita"),
            ("ArrowLeft", "a seta da esquerda volta", "seta para esquerda"),
            ("mouseBaixo", "dá para arrastar a foto com o mouse",
             "arrastar"),
            ("soltarMouse", "soltar o arrasto troca de foto", "soltar"),
            ("FOTOS_COM_ARRASTO",
             "com muita foto o arrastar some (senão trava)", "limite"),
            ("foto-conta", "a tela mostra em qual foto se está",
             "contador"),
            ("ampliarFoto(i, f, fotos)",
             "o clique sabe TODAS as fotos, não só a clicada", "lista")):
        if _precisa in _js4:
            ok("visor de fotos: %s" % _rotulo)
        else:
            falha("visor de fotos: falta %s na tela" % _por_que)
    # O visor tem que ESCUTAR o teclado e PARAR de escutar quando fecha:
    # se nao remover o ouvinte, cada foto aberta deixaria um para tras.
    if ("removeEventListener(\"keydown\", teclas)" in _js4
            and "function teclas" in _js4):
        ok("visor de fotos: o teclado para de ser ouvido ao fechar")
    else:
        falha("visor de fotos: o teclado continua sendo ouvido depois de "
              "fechar (cada foto deixaria um ouvinte)")
    _css4 = Path(PASTA / "web" / "estilo.css").read_text(encoding="utf-8")
    for _precisa, _rotulo in ((".foto-barra", "a barra de baixo"),
                              (".foto-seta", "os botões de ir e voltar"),
                              (".foto-conta", "o 'N de M'"),
                              (".foto-dica", "a dica de como passar")):
        if _precisa in _css4:
            ok("visor de fotos: %s tem desenho" % _rotulo)
        else:
            falha("visor de fotos: falta o desenho de %s" % _precisa)
except Exception as erro:
    falha("os testes do visor de fotos quebraram: %r" % (erro,))

# --- 4c9. o portugues e' do BRASIL, nao de Portugal -----------------------
# O Wolf leu respostas com sotaque de Portugal e riu (16/10/2026). A causa:
# o prompt de CONVERSA nao dizia qual portugues — e sem isso o modelo
# escolhe a variante que ele acha mais neutra, que e' a de Portugal.
try:
    import pesquisa_ia as _pg_id
    for _nome, _prompt in (("conversa", _pg_id.INSTRUCOES_AMIGO),
                          ("pesquisa", _pg_id.INSTRUCOES),
                          ("aprender", _pg_id.INSTRUCOES_APRENDER)):
        if "português do BRASIL" in _prompt or "portugues do Brasil" in _prompt:
            ok("idioma: o prompt de %s diz que é do Brasil" % _nome)
        else:
            falha("idioma: o prompt de %s NÃO diz que é do Brasil "
                  "(a resposta vai sair em português de Portugal)" % _nome)
    # as palavras que ele usa quando escorrega, uma a uma
    for _pt, _br in (("de certeza", "com certeza"),
                     ("a nível de", "no sentido de"),
                     ("ecrã", "tela"),
                     ("equipa", "equipe"),
                     ("ficheiro", "arquivo"),
                     ("estou a fazer", "estou fazendo")):
        if _pt in _pg_id.IDIOMA_BR and _br in _pg_id.IDIOMA_BR:
            ok("idioma: a regra mostra '%s' → '%s'" % (_pt, _br))
        else:
            falha("idioma: a regra não mostra '%s' → '%s'" % (_pt, _br))
    if "gerundiz" in _pg_id.IDIOMA_BR:
        ok("idioma: a regra avisa que Portugal gerundiza e o Brasil não")
    else:
        falha("idioma: a regra não fala do gerúndio (é o erro mais comum)")
    # a regra tem que estar DENTRO dos prompts, não só existir solta
    if "IDIOMA_BR" in Path(PASTA / "pesquisa_ia.py").read_text(encoding="utf-8"):
        ok("idioma: a regra do português brasileiro é usada pelos prompts")
    else:
        falha("idioma: a regra existe mas ninguém usa")
except Exception as erro:
    falha("os testes do idioma quebraram: %r" % (erro,))

# --- 4c10. dois defeitos que o Wolf viu com o programa na mao -----------
# 1) "Abrindo a foto..." ficava escrito NO MEIO da imagem, para sempre.
#    A causa: o aviso era escondido em mostrar(), mas nao quando a foto
#    chegava — e e' quando a foto chega que ele tem de sair.
# 2) O .exe abria uma JANELA PRETA (CMD) atras do programa.
try:
    _js5 = Path(PASTA / "web" / "app.js").read_text(encoding="utf-8")
    # 1) o aviso some
    if "function esconderAviso" in _js5:
        ok("foto: existe um jeito de tirar o aviso 'Abrindo a foto...'")
    else:
        falha("foto: nao ha como tirar o aviso 'Abrindo a foto...'")
    # o ponto exato: esconderAviso tem de ser chamado JUNTO de img.src
    _linhas5 = _js5.split("\n")
    _achou_justo = False
    for _n, _l in enumerate(_linhas5):
        if "img.src = r.base64" in _l:
            # olha as 4 linhas de cima: alguma tem de esconder o aviso
            _janela = "\n".join(_linhas5[max(0, _n - 5):_n])
            if "esconderAviso()" in _janela:
                _achou_justo = True
            break
    if _achou_justo:
        ok("foto: o aviso some no momento em que a foto chega")
    else:
        falha("foto: a foto aparece mas o aviso 'Abrindo a foto...' fica "
              "escrito por cima dela (foi o que o Wolf viu)")
    if "mostrarAviso(" in _js5:
        ok("foto: o aviso reaparece quando se troca de foto")
    else:
        falha("foto: ao trocar de foto o Wolf nao ve aviso nenhum, e "
              "pensa que travou")

    # 2) nada de janela preta atras do programa
    _spec5 = (Path(PASTA / "Eye of Thundera.spec")
              .read_text(encoding="utf-8"))
    # Olhar so' a LINHA que manda, e nao o arquivo inteiro: o proprio
    # comentario do spec explica que a tela NAO tem console, e a palavra
    # "console=True" aparece la' — o teste acusava o comentario.
    _secao_exe = _spec5[_spec5.index("EXE("):]
    _linhas_spec = [l.strip() for l in _secao_exe.split(chr(10))]
    _manda = [l for l in _linhas_spec if l.startswith("console=")]
    if _manda and _manda[0] == "console=False,":
        ok("programa: o .exe e' gerado sem janela de console (CMD)")
    else:
        falha("programa: o .exe abre uma janela preta atras do programa "
              "(%r)" % (_manda,))
    # e o aviso sobre o erro.log, que e' o que substitui a janela preta
    if ("erro.log" in _spec5 or "erro.log" in
            Path(PASTA / "app_web.py").read_text(encoding="utf-8")):
        ok("programa: sem janela de console, os erros vão para o erro.log")
    else:
        falha("programa: sem a janela preta, o erro nao tem onde aparecer")
except Exception as erro:
    falha("os testes dos defeitos que o Wolf viu quebraram: %r" % (erro,))

# --- 4c11. onde a janela abre: ela lembra do monitor ---------------------
# O Wolf pediu (16/10/2026): acaba com a regra do segundo monitor, abre
# onde ele fechou da ultima vez, e se adapta a quantas telas tiver.
try:
    import app_web as _aw3
    import pesquisa_ia as _pg_pos2

    _UM = [(0, 0, 1920, 1080)]
    _DOIS = [(0, 0, 1920, 1080), (1920, 0, 3840, 1080)]
    _INVERTIDO = [(1920, 0, 3840, 1080), (0, 0, 1920, 1080)]
    _NOTEBOOK = [(0, 0, 1366, 768)]

    _pasta_pos = Path(PASTA) / "_tmp" / "teste-posicao"
    shutil.rmtree(_pasta_pos, ignore_errors=True)
    _pasta_pos.mkdir(parents=True)
    _pos_original = _aw3.ARQUIVO_POSICAO
    _telas_original = _aw3._telas
    try:
        _aw3.ARQUIVO_POSICAO = _pasta_pos / "janela.json"

        def _com_telas(telas, funcao):
            _aw3._telas = lambda: list(telas)
            try:
                return funcao()
            finally:
                _aw3._telas = _telas_original

        def _caso(telas, guardada, esperado):
            if guardada:
                _aw3._guardar_posicao(*guardada)
            else:
                _aw3.ARQUIVO_POSICAO.unlink(missing_ok=True)
            x, y = _com_telas(telas, _aw3._posicao_de_abertura)
            dentro = any(e <= x < d and tp <= y < b
                        for e, tp, d, b in telas)
            return dentro and (x, y) == esperado

        if _caso(_DOIS, (2100, 300), (2100, 300)):
            ok("janela: fecha no segundo monitor e abre no segundo")
        else:
            falha("janela: não voltou para o segundo monitor")
        if _caso(_DOIS, (200, 150), (200, 150)):
            ok("janela: fecha no principal e abre no principal")
        else:
            falha("janela: não voltou para o monitor principal")
        if _caso(_INVERTIDO, (200, 150), (200, 150)):
            ok("janela: acha o principal mesmo se o Windows inverter a ordem")
        else:
            falha("janela: a ordem das telas do Windows atrapalhou")

        # sem nada guardado: o meio da tela principal
        x, y = _caso and _com_telas(_DOIS, lambda: (
            _aw3.ARQUIVO_POSICAO.unlink(missing_ok=True),
            _aw3._posicao_de_abertura())[1])
        if 0 <= x < 1920 and 0 <= y < 1080:
            ok("janela: nunca movida, abre no meio da tela principal (%d,%d)"
               % (x, y))
        else:
            falha("janela: nunca movida, abriu em (%d,%d), fora da principal"
                  % (x, y))
        # uma tela so
        x, y = _com_telas(_NOTEBOOK, lambda: (
            _aw3.ARQUIVO_POSICAO.unlink(missing_ok=True),
            _aw3._posicao_de_abertura())[1])
        if 0 <= x < 1366 and 0 <= y < 768:
            ok("janela: num notebook de uma tela so, abre em cima dela")
        else:
            falha("janela: num notebook de uma tela abriu em (%d,%d)" % (x, y))
        # o monitor guardado sumiu
        if _caso(_UM, (2100, 300), (370, 130)):
            ok("janela: se o monitor guardado sumiu, abre no meio da outra")
        else:
            falha("janela: ficou presa num monitor que não existe mais")

        # posicao corrompida: nunca derruba o programa
        _sobrou = True
        for _ruim in ('{"x": "abc"}', "isto nao e json", "[]", "{}"):
            _aw3.ARQUIVO_POSICAO.write_text(_ruim, encoding="utf-8")
            try:
                _com_telas(_UM, _aw3._posicao_de_abertura)
            except Exception:
                _sobrou = False
        if _sobrou:
            ok("janela: arquivo de posição estragado não derruba o programa")
        else:
            falha("janela: posição estragada derrubou o programa")

        # e nao e' o config.json (que tem a chave da API)
        if _aw3.ARQUIVO_POSICAO.name == "janela.json" and \
                _aw3.ARQUIVO_POSICAO != _pg_pos2.ARQUIVO_CONFIG:
            ok("janela: a posição fica em arquivo separado do config.json")
        else:
            falha("janela: a posição está misturada com o config.json")

        # o .exe NAO pode ter janela de console
        _spec3 = (Path(PASTA / "Eye of Thundera.spec")
                  .read_text(encoding="utf-8"))
        _linhas3 = [l.strip() for l in _spec3.split(chr(10))]
        _manda3 = [l for l in _linhas3 if l.startswith("console=")]
        if _manda3 and _manda3[0] == "console=False,":
            ok("programa: o .exe não abre janela preta (CMD) atrás")
        else:
            falha("programa: o .exe ainda abre janela de console (%r)"
                  % (_manda3,))
    finally:
        _aw3.ARQUIVO_POSICAO = _pos_original
        _aw3._telas = _telas_original
        shutil.rmtree(_pasta_pos, ignore_errors=True)
except Exception as erro:
    falha("os testes da posição da janela quebraram: %r" % (erro,))

# --- 4d. sites consultados: o que a busca traz, limpo e honesto ---------
# Sao os RESULTADOS DA BUSCA, nao citacoes: por isso a tela escreve
# "sites consultados" e mostra o link, para o Wolf conferir com os
# proprios olhos. O que nao pode: repetir link, trazer link quebrado, nem
# aceitar link perigoso (javascript:).
try:
    _pi = importlib.import_module("pesquisa_ia")
    _sites = _pi._sites_consultados(
        [{"title": "Globo", "href": "https://ge.globo.com/x", "body": "a"},
         {"title": "UOL", "url": "http://uol.com.br/y", "body": "b"},
         {"title": "Repetido", "href": "https://ge.globo.com/x"},
         {"title": "Perigo", "href": "javascript:alerta(1)"},
         {"title": "Nem link", "href": ""},
         {"body": "sem titulo e sem link"}],
        [{"title": "Noticia", "url": "https://cnn.com/z"}])
    if [s["url"] for s in _sites] == ["https://ge.globo.com/x",
                                      "http://uol.com.br/y",
                                      "https://cnn.com/z"]:
        ok("sites consultados: tira o link repetido e o que não é link")
    else:
        falha("sites consultados: sobrou %r" % ([s["url"] for s in _sites],))
    if not any(s["url"].startswith("javascript:") for s in _sites):
        ok("sites consultados: nunca aceita link perigoso (javascript:)")
    else:
        falha("sites consultados: aceitou um link perigoso")
    if _sites and all(s["titulo"] for s in _sites):
        ok("sites consultados: todo site tem um título para aparecer na tela")
    else:
        falha("sites consultados: entrou site sem título")
    if _pi._sites_consultados([], []) == []:
        ok("sites consultados: sem resultados, a lista fica vazia")
    else:
        falha("sites consultados: inventou site sem busca nenhuma")
except Exception as erro:
    falha("a lista de sites consultados deu erro: %r" % (erro,))

# --- 4e. Salvar resposta é testado com diálogo pywebview falso ao final ---

# --- 4f. tamanho da letra: existe e não mexe em nada do Python --------------
# A letra e' so aparencia (fica no navegador), mas um erro aqui quebraria
# a tela INTEIRA na hora de abrir, entao precisa de prova de que os botoes
# e os atalhos existem e que a funcao nao mexe em arquivo nenhum.
web_js = (PASTA / "web" / "app.js").read_text(encoding="utf-8")
web_css = (PASTA / "web" / "estilo.css").read_text(encoding="utf-8")
faltando = [x for x in ("function aplicarTamanho", "function mudarLetra",
                        "function tamanhoAtual", 'id = "rotulo-letra"',
                        "aplicarTamanho(tamanhoAtual())")
            if x not in web_js]
if not faltando:
    ok("o tamanho da letra tem função, botões e é aplicado ao abrir a tela")
else:
    falha("o tamanho da letra está incompleto: falta %r" % (faltando,))
if "var(--tamanho" in web_css and 'setProperty("--tamanho"' in web_js:
    ok("o tamanho da letra usa a variável do CSS (a tela inteira acompanha)")
else:
    falha("a letra não usa a variável do CSS: só o corpo mudaria")
if 'localStorage.setItem("pia_letra"' in web_js and \
        'getItem("pia_letra")' in web_js:
    ok("o tamanho da letra fica guardado (a tela abre do jeito que ficou)")
else:
    falha("o tamanho da letra não fica guardado entre uma abertura e outra")
corpo_aplicar = web_js.split("function aplicarTamanho")[1].split("}")[0]
if "chamar(" not in corpo_aplicar:
    ok("mudar a letra não chama o Python (não arrisca as conversas)")
else:
    falha("mudar a letra chama o Python: não deveria")


# --- Tarefa D (pesquisa profunda) evidence ---------------------------
_tarefad = Path(PASTA / "web" / "app.js").read_text(encoding="utf-8") + "\n" + Path(PASTA / "app_web.py").read_text(encoding="utf-8") + "\n" + Path(PASTA / "pesquisa_ia.py").read_text(encoding="utf-8")
if "btn-deep" in _tarefad and "profundo" in _tarefad:
    ok("Tarefa D: pesquisa profunda (botao + flag) presente no codigo")
else:
    falha("Tarefa D: plumbagem deepresearch ausente")


# --- Tarefa D: o botão e o atalho realmente forçam pesquisa profunda ---
_ui_html = Path(PASTA / "web" / "index.html").read_text(encoding="utf-8")
_js_deep = Path(PASTA / "web" / "app.js").read_text(encoding="utf-8")
if ("async function enviar(texto, profundo = estado.profundo)" in _js_deep
        and 'chamar("enviar", texto, !!profundo)' in _js_deep
        and '$("#btn-serio").addEventListener("click", () => {' in _js_deep
        and 'enviar(undefined, true);' in _js_deep
        and 'id="btn-serio" class="pilula"' in _ui_html
        and _ui_html.count('id="btn-serio"') == 1
        and _ui_html.index('class="menu-modos-lista"') < _ui_html.index('id="btn-serio"')
        and _ui_html.index('id="btn-serio"') < _ui_html.index('id="btn-privada"')
        and _ui_html.index('id="btn-serio"') < _ui_html.index('id="btn-enviar"')):
    ok("Tarefa D: botão e atalho forçam pesquisa profunda; envio normal respeita o alternador")
else:
    falha("Tarefa D: botão/atalho não garantem o envio em pesquisa profunda")


# --- UX: opções secundárias agrupadas sem perder os estados ativos ----------
_ui_html = Path(PASTA / "web" / "index.html").read_text(encoding="utf-8")
_ui_css = Path(PASTA / "web" / "estilo.css").read_text(encoding="utf-8")
if ('<details id="menu-modos" class="menu-modos">' in _ui_html
        and 'id="btn-deep"' in _ui_html and 'id="btn-privada"' in _ui_html
        and 'id="btn-resumo"' in _ui_html
        and 'function atualizarMenuModos()' in _js_deep
        and 'menu.classList.toggle("tem-ativo", ativos > 0)' in _js_deep
        and 'bottom: calc(100% + 8px)' in _ui_css
        and '#menu-modos:not([open]) .menu-modos-lista { display: none; }' in _ui_css):
    ok("UX: modos secundários agrupados, ativos indicados e menu abre para cima")
else:
    falha("UX: menu de modos ou indicação de estado está incompleto")
if ('controle: {' in _js_deep
        and 'titulo: "Usar o Gemini (principal)"' in _js_deep
        and 'if (opc.controle)' in _js_deep):
    ok("configurações: ativação do Gemini agrupada ao cartão da chave")
else:
    falha("configurações: ativação do Gemini separada do cartão da chave")
if ('opc.destaque ? " cartao-destaque" : ""' in _js_deep
        and 'destaque: true' in _js_deep
        and 'const cartao = el("div", "cartao cartao-tema")' in _js_deep
        and 'setAttribute("aria-label", "Tema da interface")' in _js_deep
        and '.cartao-destaque { border-color: var(--azul);' in _ui_css
        and '.grade-temas { display: grid;' in _ui_css
        and 'setAttribute("role", "radiogroup")' in _js_deep
        and '.linha-opcao:hover {' in _ui_css):
    ok("configurações: hierarquia visual, tema em cartão e controles mais legíveis")
else:
    falha("configurações: hierarquia visual ou cartão do tema incompleto")
if ('if (botao.disabled) return;' in _js_deep
        and 'botao.textContent = "Salvando...";' in _js_deep
        and 'const controles = $$("#corpo-config input, #corpo-config select, #corpo-config button");' in _js_deep
        and 'controles.forEach((controle) => { controle.disabled = true; });' in _js_deep
        and 'finally {' in _js_deep and 'liberarControles();' in _js_deep
        and 'Array.isArray(atual.servicos)' in _js_deep
        and '#config-aviso.erro' in _ui_css):
    ok("configurações: bloqueia edições durante salvamento e libera controles após falha")
else:
    falha("configurações: falta bloqueio de edição ou recuperação após falha")
if ('inp.addEventListener("input", () => {' in _js_deep
        and 'estado.rascunho.chaves[campo] = inp.value' in _js_deep
        and 'const chaves = { ...(estado.rascunho.chaves || {}) };' in _js_deep
        and 'estado.rascunho.chaves = {};' in _js_deep):
    ok("configurações: chaves digitadas sobrevivem à troca de aba e limpam após salvar")
else:
    falha("configurações: chaves digitadas podem se perder ao trocar de aba")
if ('config_salvar", { tema: tema.nome, temaIdx: idx, chaves: {} }' in _js_deep
        and '"config_salvar", {\n      ...estado.rascunho' not in _js_deep):
    ok("configurações: trocar o tema não confirma opções de conversa em rascunho")
else:
    falha("configurações: trocar o tema também pode salvar opções em rascunho")


# --- Tarefa D + drag-drop UI evidence ----------------------------
_d = (Path(PASTA / 'web' / 'app.js').read_text(encoding='utf-8') + '\n' +
     Path(PASTA / 'web' / 'index.html').read_text(encoding='utf-8'))
if "btn-deep" in _d and "profundo" in _d and "drop" in _d:
    ok("Tarefa D: pesquisa profunda + drag-drop UI presentes")
else:
    falha("UI: elementos deep/drag-drop ausentes")


# --- gavetas por assunto / memoria evidence ----------------------
try:
    import memoria as _mem
    _f = _mem.gavetas_por_assunto([
        "Gosta de jogar videogame", "Mora em Santa Maria",
        "Prefere ser chamado de Wolf"])
    if isinstance(_f, dict) and len(_f) >= 1:
        ok("gavetas por assunto: agrupa fatos em dict")
    else:
        falha("gavetas por assunto: resultado inesperado %r" % (_f,))
    if _mem.assunto_de("Gosta de jogar videogame"):
        ok("assunto_de: retorna rotulo nao vazio")
    else:
        falha("assunto_de: retornou vazio")
except Exception as _e:
    falha("gavetas por assunto quebrou: %r" % (_e,))

_g = Path(PASTA / "web" / "app.js").read_text(encoding="utf-8")
if "assuntos" in _g and "gavetas" in _g:
    ok("UI: assuntos e gavetas presentes na tela")
else:
    falha("UI: assuntos/gavetas ausentes")

# --- personalização: cartões de tema com amostra (PLANO-PERSONALIZACAO.md) ---
_amostra_js = (PASTA / "web" / "app.js").read_text(encoding="utf-8")
_amostra_css = (PASTA / "web" / "estilo.css").read_text(encoding="utf-8")
_temas_bloco_ui = _amostra_js.split("const TEMAS_UI = [", 1)[1].split("\n];", 1)[0]
_temas_nomes_ui = re.findall(r'\{ nome: "([^"]+)", cores:', _temas_bloco_ui)
_amostra_ok = (
    'role", "radiogroup"' in _amostra_js
    and 'setAttribute("role", "radio")' in _amostra_js
    and 'setAttribute("aria-checked", i === idx ? "true" : "false")' in _amostra_js
    and 'b.tabIndex = i === idx ? 0 : -1' in _amostra_js
    and 'b.type = "button"' in _amostra_js
    and "TEMAS_UI.forEach((tema, i)" in _amostra_js
    and len(_temas_nomes_ui) == 10
    and all(n in _temas_nomes_ui for n in ("Aurora", "Pôr do Sol", "Rosa Chá", "Grafite Dourado"))
    and all(k in _amostra_js for k in ("ArrowRight", "ArrowDown", "ArrowLeft", "ArrowUp"))
    and 'chamar("config_salvar", { tema: tema.nome, temaIdx: idx, chaves: {} })' in _amostra_js
    and ".grade-temas" in _amostra_css
    and ".cartao-amostra.ativo" in _amostra_css
    and "--m-bg" in _amostra_css
    and 'el("select", "select-tema")' not in _amostra_js
)
if _amostra_ok:
    ok("personalização: temas em cartões com amostra de cores, teclado e mesmo salvamento")
else:
    falha("personalização: cartões de tema incompletos (ver PLANO-PERSONALIZACAO.md)")

_paletas_parseadas = re.findall(r'\{ nome: "([^"]+)", cores: \{ ([^}]+) \} \}', _temas_bloco_ui)
_fundos_da_paleta = ("--bg", "--painel", "--superficie", "--superficie-2")
_paletas_legiveis = len(_paletas_parseadas) == 10
_roteiro_cores = []            # pares ainda abaixo do mínimo: avisam, não travam
for _nome_paleta, _texto_cores in _paletas_parseadas:
    _cores_paleta = dict(re.findall(r'"(--[\w-]+)": "(#[0-9a-fA-F]{6})"', _texto_cores))
    if len(_cores_paleta) != 10:
        _paletas_legiveis = False
        continue
    def _lum(hex_cor):
        _rgb = [int(hex_cor[_i:_i + 2], 16) / 255 for _i in (1, 3, 5)]
        _rgb = [v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4 for v in _rgb]
        return .2126 * _rgb[0] + .7152 * _rgb[1] + .0722 * _rgb[2]
    def _contraste(_cor_a, _cor_b):
        _la, _lb = _lum(_cor_a), _lum(_cor_b)
        return (max(_la, _lb) + .05) / (min(_la, _lb) + .05)

    # Texto de verdade em cima de CADA fundo do tema — antes só checava o --bg,
    # e um tema pode ficar ilegível sobre o --superficie-2 sem ninguém notar.
    for _chave_texto in ("--texto", "--texto-2"):
        for _fundo in _fundos_da_paleta:
            if _contraste(_cores_paleta[_chave_texto], _cores_paleta[_fundo]) < 4.5:
                _paletas_legiveis = False
    # O link (--azul-2) aparece sempre sobre o --bg, onde a resposta é escrita.
    if _contraste(_cores_paleta["--azul-2"], _cores_paleta["--bg"]) < 4.5:
        _paletas_legiveis = False

    # --- pendências conhecidas do contraste (ver PROXIMOS-PASSOS.md) -------
    # texto apagado (horário da conversa, notas): é texto pequeno -> 4,5
    for _fundo in _fundos_da_paleta:
        _c = _contraste(_cores_paleta["--texto-3"], _cores_paleta[_fundo])
        if _c < 4.5:
            _roteiro_cores.append((_c, "%s: --texto-3 em %s" % (_nome_paleta, _fundo)))
    # o botão principal e o Enviar pintam o fundo de --azul/--azul-2 com
    # texto branco; no hover o fundo vira --azul-2, que em vários temas é claro
    for _acento in ("--azul", "--azul-2"):
        _c = _contraste("#ffffff", _cores_paleta[_acento])
        if _c < 4.5:
            _roteiro_cores.append((_c, "%s: branco sobre %s (botão)" % (_nome_paleta, _acento)))
    # borda e anel de foco não são texto: aí 3,0 já basta (WCAG 1.4.11)
    for _fundo in ("--bg", "--superficie-2"):
        _c = _contraste(_cores_paleta["--azul"], _cores_paleta[_fundo])
        if _c < 3.0:
            _roteiro_cores.append((_c, "%s: --azul como borda em %s" % (_nome_paleta, _fundo)))

if _paletas_legiveis:
    ok("personalização: dez paletas completas e texto legível sobre todos os fundos (4,5:1)")
else:
    falha("personalização: paleta incompleta ou contraste de texto abaixo de 4,5:1")
if _roteiro_cores:
    _roteiro_cores.sort()
    _temas_gap = len({d.split(":")[0] for _c, d in _roteiro_cores})
    aviso("contraste: %d pares em %d temas ainda abaixo do mínimo (pior: %s = %.2f:1); "
          "só texto apagado, botão e borda — pendência em PROXIMOS-PASSOS.md"
          % (len(_roteiro_cores), _temas_gap, _roteiro_cores[0][1], _roteiro_cores[0][0]))

# --- personalização: aba, tema inicial e gravação isolada -------------------
try:
    _tema_html = (PASTA / "web" / "index.html").read_text(encoding="utf-8")
    _tema_js = (PASTA / "web" / "app.js").read_text(encoding="utf-8")
    _tema_py = (PASTA / "app_web.py").read_text(encoding="utf-8")
    _tema_pastas = PASTA / "_tmp"
    _tema_pastas.mkdir(parents=True, exist_ok=True)
    _ui_tema_ok = (
        'data-aba="personalizacao"' in _tema_html
        and "function abaPersonalizacao" in _tema_js
        and "function aplicarTema" in _tema_js
        and "aplicarTema(estado.cfg.temaIdx ?? 0)" in _tema_js
        and '"temaIdx": tema_idx' in _tema_py
        and '"cfg": self._cfg_curta()' in _tema_py.split("def iniciar", 1)[1].split("def abrir_conversa", 1)[0]
    )
    if _ui_tema_ok:
        ok("personalização: aba visível e tema aplicado na abertura")
    else:
        falha("personalização: aba, aplicação inicial ou configuração incompleta")

    _tema_aw = importlib.import_module("app_web")
    _tema_pasta_original = _tema_aw.p.PASTA_CONFIG
    _tema_arquivo_original = _tema_aw.p.ARQUIVO_CONFIG
    _temas_esperados = [
        "Clássico Dark", "Purpurina", "Amethyst", "Ocean", "Forest",
        "Aurora", "Pôr do Sol", "Rosa Chá", "Grafite Dourado",
        "Thundera",
    ]
    if _temas_nomes_ui == _temas_esperados and list(_tema_aw.TEMAS_VALIDOS) == _temas_esperados:
        ok("personalização: dez paletas sincronizadas entre interface e backend")
    else:
        falha("personalização: nomes ou índices de paleta divergem entre tela e backend")
    _temas_gravaram = True
    _tema_invalido = True
    try:
        with tempfile.TemporaryDirectory(prefix="teste-temas-", dir=str(_tema_pastas)) as _tmp_tema:
            _tema_aw.p.PASTA_CONFIG = Path(_tmp_tema)
            _tema_aw.p.ARQUIVO_CONFIG = Path(_tmp_tema) / "config.json"
            _tema_aw.p.salvar_config({})
            _ponte_tema = _tema_aw.Ponte()
            for _idx, _nome_tema in enumerate(_temas_esperados):
                _ret_tema = _ponte_tema.config_salvar({
                    "tema": _nome_tema, "temaIdx": _idx, "chaves": {}
                })
                _gravado = json.loads(_tema_aw.p.ARQUIVO_CONFIG.read_text(encoding="utf-8"))
                _lido_tela = _tema_aw._cfg_tela()
                _inicio_tema = _ponte_tema.iniciar()
                _cfg_inicio = _inicio_tema.get("cfg", {})
                if (_ret_tema.get("erro") or _gravado.get("temaIdx") != _idx
                        or _gravado.get("tema") != _nome_tema
                        or _lido_tela.get("temaIdx") != _idx
                        or _lido_tela.get("tema") != _nome_tema
                        or _cfg_inicio.get("temaIdx") != _idx
                        or _cfg_inicio.get("tema") != _nome_tema):
                    _temas_gravaram = False
                    break
            for _indice_ruim in (10, -1, True):
                _ponte_tema.config_salvar({"tema": "não permitido", "temaIdx": _indice_ruim, "chaves": {}})
                _cfg_ruim = json.loads(_tema_aw.p.ARQUIVO_CONFIG.read_text(encoding="utf-8"))
                if _cfg_ruim.get("temaIdx") != 9 or _cfg_ruim.get("tema") != _temas_esperados[9]:
                    _tema_invalido = False
    finally:
        _tema_aw.p.PASTA_CONFIG = _tema_pasta_original
        _tema_aw.p.ARQUIVO_CONFIG = _tema_arquivo_original
    if _temas_gravaram:
        ok("personalização: os 10 temas são salvos e carregados sem tocar nos dados reais")
    else:
        falha("personalização: um tema não foi salvo ou carregado corretamente")
    if _tema_invalido:
        ok("personalização: índices fora da faixa não substituem a paleta salva")
    else:
        falha("personalização: índice de tema inválido alterou a paleta")
except Exception as _erro_tema:
    falha("personalização: teste isolado falhou: %r" % (_erro_tema,))


# --- configurações: persistência e proteção das chaves em ambiente isolado ---
try:
    _cfg_aw = importlib.import_module("app_web")
    _cfg_p = _cfg_aw.p
    _cfg_pasta_original = _cfg_p.PASTA_CONFIG
    _cfg_arquivo_original = _cfg_p.ARQUIVO_CONFIG
    _cfg_ok = False
    _cfg_pastas = PASTA / "_tmp"
    _cfg_pastas.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="teste-config- ", dir=str(_cfg_pastas)) as _tmp_cfg:
        _cfg_p.PASTA_CONFIG = Path(_tmp_cfg)
        _cfg_p.ARQUIVO_CONFIG = Path(_tmp_cfg) / "config.json"
        _cfg_p.salvar_config({
            "api_key": "chave-principal-preservada",
            "api_key_reserva": "chave-reserva-antiga",
            "campo_privado_teste": "nao-alterar",
        })
        _cfg_ponte = _cfg_aw.Ponte()
        _cfg_ret = _cfg_ponte.config_salvar({
            "modo_pesquisa": "sempre",
            "usar_contexto": False,
            "aprender": False,
            "voz_enviar": False,
            "usar_plano_b": False,
            "usar_gemini": False,
            "web_corretor": False,
            "temaIdx": 3,
            "chaves": {
                "api_key": " ",
                "api_key_reserva": "chave-reserva-nova",
                "campo_nao_permitido": "nao-gravar",
            },
        })
        _cfg_gravado = json.loads(_cfg_p.ARQUIVO_CONFIG.read_text(encoding="utf-8"))
        _cfg_lido = _cfg_aw._cfg_tela()
        _cfg_ok = (
            not _cfg_ret.get("erro")
            and _cfg_gravado.get("api_key") == "chave-principal-preservada"
            and _cfg_gravado.get("api_key_reserva") == "chave-reserva-nova"
            and "campo_nao_permitido" not in _cfg_gravado
            and _cfg_gravado.get("campo_privado_teste") == "nao-alterar"
            and _cfg_lido.get("modo_pesquisa") == "sempre"
            and _cfg_lido.get("usar_contexto") is False
            and _cfg_lido.get("aprender") is False
            and _cfg_lido.get("voz_enviar") is False
            and _cfg_lido.get("usar_plano_b") is False
            and _cfg_lido.get("usar_gemini") is False
            and _cfg_lido.get("web_corretor") is False
            and _cfg_lido.get("temaIdx") == 3
        )
        # Simula falha na troca final: a versão anterior deve continuar intacta.
        from unittest.mock import patch as _patch
        _cfg_bytes_antes = _cfg_p.ARQUIVO_CONFIG.read_bytes()
        _cfg_replace_falhou = False
        try:
            with _patch.object(_cfg_p.os, "replace", side_effect=OSError("falha simulada")):
                _cfg_p.salvar_config({"api_key": "nao-gravar"})
        except OSError:
            _cfg_replace_falhou = True
        _cfg_atomico_ok = (
            _cfg_replace_falhou
            and _cfg_p.ARQUIVO_CONFIG.read_bytes() == _cfg_bytes_antes
            and not list(Path(_tmp_cfg).glob(".config-*.tmp"))
        )
        _cfg_ok = _cfg_ok and _cfg_atomico_ok
    _cfg_p.PASTA_CONFIG = _cfg_pasta_original
    _cfg_p.ARQUIVO_CONFIG = _cfg_arquivo_original
    if _cfg_ok:
        ok("configurações: persistência e proteção das chaves; falha simulada preserva o arquivo anterior")
    else:
        falha("configurações: persistência, proteção das chaves ou gravação atômica falhou")
except Exception as _erro_cfg:
    try:
        _cfg_p.PASTA_CONFIG = _cfg_pasta_original
        _cfg_p.ARQUIVO_CONFIG = _cfg_arquivo_original
    except Exception:
        pass
    falha("configurações: teste isolado falhou: %r" % (_erro_cfg,))


# --- logs: a função de registro sanitiza credenciais -----------------------
_log_p = importlib.import_module("pesquisa_ia")
_log_fonte = ARQUIVO.read_text(encoding="utf-8")
_log_api = "s" * 24
_log_bearer = "x" * 36
_log_google = "AIza" + ("a" * 24)
_log_openrouter = "sk-or-" + ("b" * 16)
_log_groq = "gsk_" + ("c" * 16)
_log_openai = "sk-" + ("d" * 20)
_log_amostra = (
    "api" + "_key=" + _log_api + "; " + "Be" + "arer " + _log_bearer
    + "; " + _log_google + "; " + _log_openrouter + "; "
    + _log_groq + "; " + _log_openai
)
_log_limpado = _log_p._sanitizar_erro_log(_log_amostra)
if ("def _sanitizar_erro_log(texto):" in _log_fonte
        and "[CHAVE REDIGIDA]" in _log_fonte
        and "[TOKEN REDIGIDO]" in _log_fonte
        and "mensagem = _sanitizar_erro_log(erro)" in _log_fonte
        and all(segredo not in _log_limpado for segredo in (
            _log_api, _log_bearer, _log_google, _log_openrouter,
            _log_groq, _log_openai
        ))
        and "[SEGREDO REDIGIDO]" in _log_limpado
        and "[TOKEN REDIGIDO]" in _log_limpado
        and _log_limpado.count("[CHAVE REDIGIDA]") >= 4):
    ok("logs: sanitização de credenciais verificada com valores sintéticos")
else:
    falha("logs: sanitização de credenciais falhou no teste isolado")


# --- salvar resposta: diálogo da própria janela, sem criar uma raiz Tk ------
try:
    _save_aw = importlib.import_module("app_web")
    _save_webview = importlib.import_module("webview")
    _save_pasta_tmp = PASTA / "_tmp"
    _save_pasta_tmp.mkdir(parents=True, exist_ok=True)
    _salvar_ok = False
    with tempfile.TemporaryDirectory(prefix="teste-salvar-resposta-", dir=str(_save_pasta_tmp)) as _tmp_save:
        _destino_save = Path(_tmp_save) / "resposta.txt"

        class _JanelaDialogoFalso:
            def __init__(self, destino):
                self.destino = destino
                self.chamada = None

            def create_file_dialog(self, tipo, **kwargs):
                self.chamada = (tipo, kwargs)
                return [str(self.destino)]

        _janela_save = _JanelaDialogoFalso(_destino_save)
        _ponte_save = _save_aw.Ponte(janela=_janela_save)
        _ret_save = _ponte_save.salvar_texto("Resposta de teste")
        _texto_save = _destino_save.read_text(encoding="utf-8-sig") if _destino_save.exists() else ""
        _salvar_ok = (
            not _ret_save.get("erro")
            and _ret_save.get("caminho") == str(_destino_save)
            and _texto_save == "Resposta de teste\n"
            and _janela_save.chamada is not None
            and _janela_save.chamada[0] == _save_webview.FileDialog.SAVE
            and "Arquivo de texto (*.txt)" in _janela_save.chamada[1].get("file_types", ())
        )
    if _salvar_ok:
        ok("Salvar resposta: usa o diálogo pywebview e grava o texto em teste isolado")
    else:
        falha("Salvar resposta: diálogo pywebview ou gravação falhou")
except Exception as _erro_save:
    falha("Salvar resposta: teste isolado falhou: %r" % (_erro_save,))


# --- leitura de PDF: extracao local, sem biblioteca no teste --------------
# Monta PDFs sinteticos (um simples e um comprimido com FlateDecode) e
# confere que o leitor tira o texto certo. Usa so arquivo temporario em
# `_tmp`: nenhum documento pessoal e' lido.
try:
    import base64 as _b64
    import zlib as _zlib

    _aw_pdf = importlib.import_module("app_web")
    _pl = importlib.import_module("pdf_leitor")

    def _pdf_sintetico(texto, comprimir=False):
        bruto = ("BT /F1 18 Tf 72 700 Td (" + texto + ") Tj ET").encode("latin-1")
        if comprimir:
            fluxo = _zlib.compress(bruto)
            filtro = b" /Filter /FlateDecode"
        else:
            fluxo = bruto
            filtro = b""
        objs = [
            b"<< /Type /Catalog /Pages 2 0 R >>",
            b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            b"/Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>",
            b"<< /Length " + str(len(fluxo)).encode() + filtro + b" >>\nstream\n"
            + fluxo + b"\nendstream",
            b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        ]
        import io as _io
        saida = _io.BytesIO()
        saida.write(b"%PDF-1.4\n")
        offsets = []
        for i, obj in enumerate(objs, 1):
            offsets.append(saida.tell())
            saida.write(str(i).encode() + b" 0 obj\n" + obj + b"\nendobj\n")
        xref = saida.tell()
        saida.write(b"xref\n0 " + str(len(objs) + 1).encode() + b"\n")
        saida.write(b"0000000000 65535 f \n")
        for off in offsets:
            saida.write(("%010d 00000 n \n" % off).encode())
        saida.write(b"trailer\n<< /Size " + str(len(objs) + 1).encode()
                    + b" /Root 1 0 R >>\nstartxref\n"
                    + str(xref).encode() + b"\n%%EOF")
        return saida.getvalue()

    # 1) extracao direta (simples e comprimido)
    _t1, _e1 = _pl.texto_de_pdf(_pdf_sintetico("Wolf e Thundera"))
    _t2, _e2 = _pl.texto_de_pdf(_pdf_sintetico("Texto comprimido", comprimir=True))
    # 2) casos que devem dar erro claro, sem estourar
    _t3, _e3 = _pl.texto_de_pdf(b"")
    _t4, _e4 = _pl.texto_de_pdf(b"nao sou um pdf")
    _t5, _e5 = _pl.texto_de_pdf(b"%PDF-1.4\ntodo estragado")
    if (_e1 == "" and "Wolf e Thundera" in _t1
            and _e2 == "" and "Texto comprimido" in _t2
            and _e3 and _e4 and _e5):
        ok("PDF: extrai texto local (simples e comprimido) e avisa nos casos ruins")
    else:
        falha("PDF: extracao falhou (%r/%r/%r/%r/%r)"
              % (_t1, _e1, _t2, _e2, _e3))

    # 3) a ponte recebe em pedacos e devolve o texto
    _ponte_pdf = _aw_pdf.Ponte()
    _dados = _pdf_sintetico("Intervalo de Thundera")
    _b64pdf = _b64.b64encode(_dados).decode("ascii")
    _id_pdf = "teste-pdf-123"
    _r_ini = _ponte_pdf.pdf_iniciar(_id_pdf)
    _partes_ok = not _r_ini.get("erro")
    for _i in range(0, len(_b64pdf), 100000):
        _rr = _ponte_pdf.pdf_parte(_id_pdf, _b64pdf[_i:_i + 100000])
        if _rr.get("erro"):
            _partes_ok = False
            break
    _r_fim = _ponte_pdf.pdf_extrair(_id_pdf)
    if _partes_ok and not _r_fim.get("erro") and "Intervalo de Thundera" in _r_fim.get("texto", ""):
        ok("PDF: a ponte junta os pedacos base64 e devolve o texto")
    else:
        falha("PDF: ponte falhou (%r / %r)" % (_r_ini, _r_fim))

    # 4) pedaco sem iniciar -> erro claro (nao trava a tela)
    _ponte_pdf2 = _aw_pdf.Ponte()
    _r_sem = _ponte_pdf2.pdf_extrair("nao-existe")
    if _r_sem.get("erro"):
        ok("PDF: envio expirado avisa em vez de travar")
    else:
        falha("PDF: envio sem iniciar devolveu sucesso indevido")

    # 5) a tela sabe tratar .pdf e usa os metodos da ponte
    _js_pdf = (PASTA / "web" / "app.js").read_text(encoding="utf-8")
    if ("extrairPdf" in _js_pdf and "pdf_iniciar" in _js_pdf
            and "pdf_parte" in _js_pdf and "pdf_extrair" in _js_pdf
            and 'ext === "pdf"' in _js_pdf):
        ok("PDF: a tela manda o PDF em pedacos e mostra o texto para revisao")
    else:
        falha("PDF: a tela nao trata o arquivo .pdf")
except Exception as _erro_pdf:
    falha("PDF: teste isolado falhou: %r" % (_erro_pdf,))


# --- responsividade e acessibilidade da interface -------------------------
try:
    _css_ui = (PASTA / "web" / "estilo.css").read_text(encoding="utf-8")
    _html_ui = (PASTA / "web" / "index.html").read_text(encoding="utf-8")
    _ui_responsiva = (
        "@media (max-width: 620px)" in _css_ui
        and "@media (max-height: 560px)" in _css_ui
        and "@media (prefers-reduced-motion: reduce)" in _css_ui
        and ".janela-corpo { min-height: 0;" in _css_ui
        and ".abas { overflow-x: auto;" in _css_ui
        and ":focus-visible" in _css_ui
        and 'aria-modal="true"' in _html_ui
        and 'aria-labelledby="titulo-config"' in _html_ui
        and '<h2 id="titulo-config">Configurações</h2>' in _html_ui
    )
    if _ui_responsiva:
        ok("interface: layout compacto, rolagem, foco visível e diálogo acessível")
    else:
        falha("interface: faltam regras responsivas ou atributos de acessibilidade")
except Exception as _erro_ui:
    falha("interface: teste de responsividade/acessibilidade falhou: %r" % (_erro_ui,))


# --- lista de conversas e menus: navegação por teclado --------------------
# Sem isso, quem não usa o mouse não abre uma conversa nem usa o menu "...".
try:
    _js_kb = (PASTA / "web" / "app.js").read_text(encoding="utf-8")
    _css_kb = (PASTA / "web" / "estilo.css").read_text(encoding="utf-8")
    _html_kb = (PASTA / "web" / "index.html").read_text(encoding="utf-8")
    _teclado_ok = (
        # conversa: a área do título é um botão que abre com Enter/Espaço
        'textos.setAttribute("role", "button")' in _js_kb
        and "textos.tabIndex = 0" in _js_kb
        and 'ev.key === "Enter" || ev.key === " "' in _js_kb
        # o "..." tem nome acessível e aparece quando focado
        and 'mais.setAttribute("aria-label"' in _js_kb
        and ".conv .mais:focus-visible { opacity: 1; }" in _css_kb
        # menu da conversa com papel, itens e navegação por setas
        and 'pop.setAttribute("role", "menu")' in _js_kb
        and 'fixar.setAttribute("role", "menuitem")' in _js_kb
        and '"ArrowDown", "ArrowUp", "Home", "End"' in _js_kb
        # foco volta ao botão que abriu, ao fechar pelo teclado
        and "function fecharMenu(voltarFoco)" in _js_kb
        and "fecharMenu(true)" in _js_kb
        # Esc fecha também o menu "Mais" e devolve o foco
        and 'modos.open = false' in _js_kb
        # rótulos acessíveis no campo de busca e na lista
        and 'aria-label="Procurar nas conversas"' in _html_kb
        and 'aria-label="Conversas"' in _html_kb
    )
    if _teclado_ok:
        ok("teclado: conversas abrem com Enter/Espaço; menus com setas, Esc e foco de volta")
    else:
        falha("teclado: falta acesso por teclado na lista de conversas ou nos menus")
except Exception as _erro_teclado:
    falha("teclado: teste de navegação falhou: %r" % (_erro_teclado,))


# --- textos: acentos e padronizacao das mensagens ao usuario --------------
# O Wolf ve estas frases na tela: precisam estar em portugues correto e a
# mesma situacao nao pode aparecer escrita de dois jeitos diferentes.
try:
    _py_txt = (PASTA / "app_web.py").read_text(encoding="utf-8")
    _js_txt = (PASTA / "web" / "app.js").read_text(encoding="utf-8")
    _sem_acento = [
        "Nao consegui sugerir perguntas agora.",
        "Nao consegui ler esse arquivo (parece corrompido).",
        "Falta o modulo de leitura de PDF neste programa.",
        "No modo exemplo nada e gravado. Abra sem ",
        "Nao foi possivel abrir a area de transferencia.",
        "Nenhum texto na area de transferencia.",
        "Nao foi possivel ler a area de transferencia.",
        "Voce esta vendo uma resposta de EXEMPLO",
        "Conversando com voce...",
        "Na tela nova isso ainda nao funciona",
    ]
    _com_acento = [
        "Não consegui sugerir perguntas agora.",
        "Não consegui ler esse arquivo (parece corrompido).",
        "Falta o módulo de leitura de PDF neste programa.",
        "No modo exemplo nada é gravado. Abra sem ",
        "Não foi possível abrir a área de transferência.",
        "Nenhum texto na área de transferência.",
        "Não foi possível ler a área de transferência.",
        "Você está vendo uma resposta de EXEMPLO",
        "Conversando com você...",
        "Na tela nova isso ainda não funciona",
    ]
    _faltando = [t for t in _sem_acento if t in _py_txt]
    _textos_ok = (
        not _faltando
        and all(t in _py_txt for t in _com_acento)
        # mesma situacao ("ocupado"), mesma frase, nos dois lados da ponte
        and "Espere a resposta terminar" not in _js_txt
        and "Espere a resposta terminar" not in _py_txt
        # a mesma acao ("sem chave"), a mesma frase
        and "Cole a sua chave do Google nas Configurações" not in _js_txt
        and _js_txt.count(
            "Cole a sua chave do Google em Configurações > Chaves para começar."
        ) == 2
    )
    if _textos_ok:
        ok("textos: mensagens ao usuário com acentos corretos e linguagem única")
    else:
        falha("textos: acento ou padronização de mensagem fora do padrão: %r" % (_faltando,))
except Exception as _erro_textos:
    falha("textos: teste de padronização falhou: %r" % (_erro_textos,))


# --- janela: a barra de título sai, o redimensionamento fica ---------------
# Regressão: a primeira versão da barra própria tirava o WS_THICKFRAME junto
# com o CAPTION, e a janela perdeu a borda que você arrasta para redimensionar
# (e o encaixe com Win+setas). A correção tira só o CAPTION.
try:
    import app_web as _aw5

    _CAPTION = 0x00C00000      # WS_BORDER | WS_DLGFRAME: a barra branca
    _THICKFRAME = 0x00040000   # WS_SIZEBOX: borda redimensionável
    _SYSMENU = 0x00080000      # botão fechar/minimizar/maximizar do sistema
    _MENUMIN = 0x00020000      # WS_MINIMIZEBOX
    _MENUMAX = 0x00010000      # WS_MAXIMIZEBOX
    _estilo_cheio = (_CAPTION | _THICKFRAME | _SYSMENU | _MENUMIN | _MENUMAX)
    _novo = _aw5._estilo_sem_barra(_estilo_cheio)
    _fonte = (PASTA / "app_web.py").read_text(encoding="utf-8")
    _janela_ok = (
        not (_novo & _CAPTION)          # a barra saiu
        and bool(_novo & _THICKFRAME)   # redimensionamento ficou
        and bool(_novo & _SYSMENU)
        and bool(_novo & _MENUMIN)
        and bool(_novo & _MENUMAX)
        # ninguém tirando o THICKFRAME em outro lugar do arquivo
        and "~0x00040000" not in _fonte
        # e o resto do estilo passa intacto (nenhuma outra marca perdida)
        and _novo == (_estilo_cheio & ~_CAPTION)
    )
    if _janela_ok:
        ok("janela: barra de título sai e a janela continua redimensionável (WS_THICKFRAME intacto)")
    else:
        falha("janela: a correção removeu o WS_THICKFRAME e deixou a janela sem borda redimensionável")
except Exception as _erro_janela:
    falha("janela: teste da barra de título falhou: %r" % (_erro_janela,))


# --- janela: faixas de redimensionar na tela (PLANO-BORDAS-REDIMENSIONAR.md) ---
try:
    _html_b = (PASTA / "web" / "index.html").read_text(encoding="utf-8")
    _js_b = (PASTA / "web" / "app.js").read_text(encoding="utf-8")
    _css_b = (PASTA / "web" / "estilo.css").read_text(encoding="utf-8")
    _nomes = ["esquerda", "direita", "topo", "topo-esq", "topo-dir", "base", "base-esq", "base-dir"]
    import app_web as _aw6
    _mapa_ok = (sorted(_aw6.Ponte._BORDAS_HT) == sorted(_nomes)
                and sorted(_aw6.Ponte._BORDAS_HT.values()) == list(range(10, 18)))
    _faixas_ok = all('data-borda="%s"' % b in _html_b for b in _nomes)
    if _mapa_ok and _faixas_ok and "janela_redimensionar" in _js_b and "#bordas" in _css_b:
        ok("janela: 8 faixas de redimensionar na tela chamam a ponte (bordas e cantos)")
    else:
        falha("janela: faixas de redimensionar incompletas (html/css/js/ponte)")
except Exception as _erro_b:
    falha("janela: teste das faixas de redimensionar falhou: %r" % (_erro_b,))


# --- diálogo de Configurações: foco preso e devolvido (teclado) -----------
# O Tab não pode escapar para a tela de trás enquanto a janela de
# Configurações está aberta; e o foco deve entrar nela ao abrir e
# voltar ao botão que a abriu ao fechar.
try:
    _js_foco = (PASTA / "web" / "app.js").read_text(encoding="utf-8")
    _foco_trampa = (
        # armadilha de foco: Tab preso dentro do diálogo aberto
        'e.key === "Tab" && !$("#modal").classList.contains("oculto")' in _js_foco
        and "janela.contains(atual)" in _js_foco
        # o foco entra na janela assim que ela abre
        and "alvo.focus({ preventScroll: true })" in _js_foco
        # e volta ao controle que a abriu ao fechar
        and "_configTrigger.focus" in _js_foco
        # Escape fecha o diálogo
        and 'if (!$("#modal").classList.contains("oculto")) fecharConfig();' in _js_foco
    )
    if _foco_trampa:
        ok("diálogo: Tab preso dentro, foco entra ao abrir e volta ao fechar (Escape fecha)")
    else:
        falha("diálogo: faltam armadilha de Tab, foco ao abrir/devolver ou Escape")
except Exception as _erro_foco:
    falha("diálogo: teste de foco do diálogo falhou: %r" % (_erro_foco,))


# --- recuperação de falha: nenhuma operação deixa a tela travada ---------
# Toda thread que trabalha em segundo plano (resposta da IA, galeria de
# imagens, transcrição de voz) precisa liberar `ocupado` no `finally` e
# avisar a tela — senão o botão Enviar ficaria desabilitado para sempre.
try:
    _appw_rec = (PASTA / "app_web.py").read_text(encoding="utf-8")

    def _tem_finally_ocupado(inicio, fim):
        """Confere que o trecho entre `inicio` e `fim` libera `ocupado`."""
        _i = _appw_rec.find(inicio)
        if _i < 0:
            return False
        _j = _appw_rec.find(fim, _i + len(inicio))
        _fim = _j if _j > 0 else len(_appw_rec)
        _bloco = _appw_rec[_i:_fim]
        return "finally:" in _bloco and "self.ocupado = False" in _bloco

    _rec_ok = (
        _tem_finally_ocupado("def _responder(", "def _responder_exemplo")
        and _tem_finally_ocupado("def _responder_exemplo", "def _aprender")
        and _tem_finally_ocupado("def _responder_imagens", "def imagem_ampliada")
        and _tem_finally_ocupado("def tarefa():", "threading.Thread(target=tarefa")
        # a tela também destrava se a chamada da ponte falhar
        and 'if (estado.ocupado) esperar(false);' in _js_foco
        # e o envio solta os eventos mesmo quando dá erro
        and "finally {" in _js_foco and "esperar(!r.erro" in _js_foco
    )
    if _rec_ok:
        ok("falhas: resposta, galeria e voz liberam a tela no finally; ponte também")
    else:
        falha("falhas: alguma operação pode deixar a tela travada (finally/ocupado ausente)")
except Exception as _erro_rec:
    falha("falhas: teste de recuperação falhou: %r" % (_erro_rec,))


# --- avisos de erro: ficam mais tempo e dá para fechar --------------------
try:
    _css_aviso = (PASTA / "web" / "estilo.css").read_text(encoding="utf-8")
    _aviso_ok = (
        # erro fica mais tempo que aviso normal
        "erro ? 8000 : 4200" in _js_foco
        # clicar esconde na hora
        and 'a.addEventListener("click"' in _js_foco
        # o aviso parece clicável
        and "cursor: pointer" in _css_aviso
    )
    if _aviso_ok:
        ok("avisos: erros ficam mais tempo na tela e podem ser fechados com clique")
    else:
        falha("avisos: erro ainda some rápido demais ou não pode ser fechado")
except Exception as _erro_aviso:
    falha("avisos: teste de duração/clique falhou: %r" % (_erro_aviso,))


# --- resumo -----------------------------------------------------------------
print()
print('VERIFICACOES: %d | FALHA: %d | AVISO: %d' % (verificacoes, len(falhas), len(avisos)))
if falhas:
    print('RESULTADO: %d FALHA(S). Corrija antes de entregar.' % len(falhas))
    sys.exit(1)
else:
    print('RESULTADO: TUDO CERTO')
