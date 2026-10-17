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
_js_deep = Path(PASTA / "web" / "app.js").read_text(encoding="utf-8")
if ("async function enviar(texto, profundo = estado.profundo)" in _js_deep
        and 'chamar("enviar", texto, !!profundo)' in _js_deep
        and '$("#btn-serio").addEventListener("click", () => enviar(undefined, true));' in _js_deep
        and 'enviar(undefined, true);' in _js_deep):
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
    _temas_esperados = ["Clássico Dark", "Purpurina", "Amethyst", "Ocean", "Forest"]
    _temas_gravaram = True
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
    finally:
        _tema_aw.p.PASTA_CONFIG = _tema_pasta_original
        _tema_aw.p.ARQUIVO_CONFIG = _tema_arquivo_original
    if _temas_gravaram:
        ok("personalização: os 5 temas são salvos e carregados sem tocar nos dados reais")
    else:
        falha("personalização: um tema não foi salvo ou carregado corretamente")
except Exception as _erro_tema:
    falha("personalização: teste isolado falhou: %r" % (_erro_tema,))


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


# --- resumo -----------------------------------------------------------------
print()
print('VERIFICACOES: %d | FALHA: %d | AVISO: %d' % (verificacoes, len(falhas), len(avisos)))
if falhas:
    print('RESULTADO: %d FALHA(S). Corrija antes de entregar.' % len(falhas))
    sys.exit(1)
else:
    print('RESULTADO: TUDO CERTO')
