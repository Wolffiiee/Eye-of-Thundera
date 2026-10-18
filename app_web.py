import sys
import webbrowser
import time
from datetime import datetime
import json
import io
import base64
import threading
from pathlib import Path
import sys as _sys_web
if getattr(_sys_web, "frozen", False) and hasattr(_sys_web, "_MEIPASS"):
    RAIZ = Path(_sys_web._MEIPASS)
else:
    RAIZ = Path(__file__).resolve().parent
# Nome do app na barra de tarefas (em vez de "pythonw"/"IDLE").
try:
    import ctypes
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
        "Eye of Thundera")
except Exception:
    pass

WEB = RAIZ / "web"
if not WEB.exists():
    WEB = Path(__file__).resolve().parent / "web"
INDEX = WEB / "index.html"
ESTILO = WEB / "estilo.css"
SCRIPT = WEB / "app.js"

sys.path.insert(0, str(RAIZ))
if sys.stdout is not None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
# Com console=False (o .exe de verdade) NAO ha stdout: ele e' None.
# Chamar reconfigure em None derruba o programa na largada com
# "AttributeError: 'NoneType' object has no attribute 'reconfigure'"
# (foi o que o Wolf viu em 16/10/2026). So' reconfigura se houver.
# O pywebview e' a unica coisa que esta tela usa de fora. Se faltar, o
# erro diz o que fazer em vez de dar uma excecao gigante.
try:
    import webview
except ImportError:
    sys.exit(
        "Falta a biblioteca pywebview.\n"
        "Rode isto na pasta do projeto:\n"
        "    .venv\\Scripts\\python.exe -m pip install pywebview\n"
    )

# O mesmo modulo do programa antigo: os dados (conversas, memoria,
# chaves) ficam nos mesmos arquivos, entao a tela nova ve o que o Wolf
# ja tem. Importar o modulo NAO abre janela nenhuma.
import pesquisa_ia as p

TEMAS_VALIDOS = (
    "Clássico Dark", "Purpurina", "Amethyst", "Ocean", "Forest",
    "Aurora", "Pôr do Sol", "Rosa Chá", "Grafite Dourado",
    "Thundera",
)

WEB = RAIZ / "web"
INDEX = WEB / "index.html"
ESTILO = WEB / "estilo.css"
SCRIPT = WEB / "app.js"

# Janela de PREVIA: nasce no segundo monitor, nunca no principal, para
# nunca cobrir a tela que o Wolf esta usando.
PREVIA = "--previa" in sys.argv
# Modo DEMO: conversas de exemplo (com emoji COLORIDO) para o Wolf ver a
# tela cheia e poder decidir. NAO le nem grava nada do Wolf: e' so olhar.
DEMO = "--demo" in sys.argv or PREVIA
# `--voz` deixa o MICROFONE DE VERDADE mesmo no modo exemplo. Sao duas
# coisas diferentes: "nao gravar nada" (so olhar a tela) e "microfone
# falso" (para o botao poder ser testado sem microfone nenhum). Com
# `--demo --voz` o Wolf fala de verdade e a IA responde, mas nenhuma
# conversa e' salva.
VOZ_REAL = "--voz" in sys.argv
VOZ_FALSA = DEMO and not VOZ_REAL
# ONDE A JANELA ABRE. (16/10/2026)
#
# Antes era fixo no SEGUNDO monitor, porque a tela nova ainda era teste e
# nao podia cobrir a tela em que o Wolf estava trabalhando. Ele pediu
# para acabar com isso, mas com UMA excecao:
#
#   - --previa (modo "so olhar") -> continua no segundo monitor, porque
#     la ele esta *trabalhando* no editor e o programa e' apenas uma
#     janela de lado.
#   - programa normal -> lembra onde foi fechado, e se ainda nao sabe,
#     abre no CENTRO da tela principal (que e' onde um programa de
#     verdade nasce, e nao num canto fixo).
#
# O arquivo e' separado do config.json de proposito: e' uma posicao de
# janela, nao uma preferencia, e mexer no config.json seria mexer no
# arquivo que tem a chave da API.
if PREVIA:
    X_PADRAO, Y_PADRAO = (2000, 100)
else:
    X_PADRAO, Y_PADRAO = (200, 100)
ARQUIVO_POSICAO = p.PASTA_CONFIG / "janela.json"


def _ler_posicao():
    """Onde a janela ficou da ultima vez, ou None se nunca foi movida."""
    try:
        d = p._ler_json(ARQUIVO_POSICAO, {})
        x, y = d.get("x"), d.get("y")
        if isinstance(x, int) and isinstance(y, int):
            return x, y
    except Exception:
        pass
    return None


def _telas():
    """Todas as telas do Windows: [(esq, topo, dir, baixo), ...].

    Devolve lista vazia se nao conseguir perguntar ao Windows: quem chama
    trata (caindo no padrao) em vez de travar o programa.
    """
    try:
        import ctypes
        from ctypes import wintypes
        # `ctypes.wintypes` NAO vem junto com `import ctypes`: sem este
        # `from`, a linha abaixo levanta AttributeError - que o `except`
        # engolia e devolvia "nao tem monitor" para QUALQUER posicao
        # (16/10/2026: o programa nunca mais abriria no monitor certo).

        class _RECT(ctypes.Structure):
            _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long),
                        ("right", ctypes.c_long),
                        ("bottom", ctypes.c_long)]

        encontradas = []
        proc = ctypes.windll.user32.EnumDisplayMonitors
        CALLBACK = ctypes.WINFUNCTYPE(
            ctypes.c_int, wintypes.HMONITOR, wintypes.HDC,
            ctypes.POINTER(_RECT), ctypes.c_ulong)

        def pegar(_h, _hdc, lprc, _d):
            r = lprc.contents
            encontradas.append((r.left, r.top, r.right, r.bottom))
            return 1

        proc(0, 0, CALLBACK(pegar), None)
        return encontradas
    except Exception as erro:
        p.registrar_erro("_telas", erro)
        return []


def _tela_principal():
    """A tela que contem o ponto (0,0) - a 'principal' do Windows.

    Nao e' 'a primeira que o Windows devolveu': ele pode ordenar como
    quiser, e em varias maquinas o monitor 0 e' o do notebook.
    """
    telas = _telas()
    for esq, topo, dir_, baixo in telas:
        if esq <= 0 < dir_ and topo <= 0 < baixo:
            return esq, topo, dir_, baixo
    return telas[0] if telas else None


def _onde_tem_monitor(x, y):
    """A posicao ainda cai em algum monitor que exista HOJE?

    Precisa disso: o Wolf fecha o programa no segundo monitor, leva o
    notebook para a casa, liga e so tem a tela do notebook. Sem esta
    conferida, o programa abriria em x=2000 - fora de qualquer tela, e
    pareceria ter sumido.
    """
    return any(esq <= x < dir_ and topo <= y < baixo
               for esq, topo, dir_, baixo in _telas())


def _centro_da_tela_principal():
    """O meio da tela principal, com a janela em cima.

    E' o que um programa de verdade faz: nascer no meio da tela, e nao
    num ponto fixo que so faz sentido naquele computador.
    """
    tela = _tela_principal()
    if not tela:
        return X_PADRAO, Y_PADRAO
    esq, topo, dir_, baixo = tela
    return (esq + max(0, (dir_ - esq - LARGURA) // 2),
            topo + max(0, (baixo - topo - ALTURA) // 2))


def _posicao_de_abertura():
    """Onde abrir agora, decidindo pelo que existe HOJE.

    As regras, nesta ordem:
    1. onde o Wolf fechou da ultima vez, se ainda houver esse monitor;
    2. o meio da tela principal (so um monitor, ou nada guardado ainda);
    3. o padrao, se o Windows nao souber dizer nada.
    """
    guardada = _ler_posicao()
    if guardada and _onde_tem_monitor(*guardada):
        return guardada
    return _centro_da_tela_principal()


def _guardar_posicao(x, y):
    try:
        ARQUIVO_POSICAO.parent.mkdir(parents=True, exist_ok=True)
        p._gravar_json(ARQUIVO_POSICAO, {"x": int(x), "y": int(y)})
    except Exception:
        pass

TITULO_JANELA = "Eye of Thundera"


# ---------------- imagens: da busca para a tela -------------------------
# A tela (que e' uma pagina) nao sabe ler bytes. As miniaturas vao
# dentro do evento ja em base64 — sao pequenas (umas 6 KB cada), e nove
# cabem folgadas. As grandes NAO: uma foto de 2 MB em base64 viraria uma
# string de 2,7 MB, e o pywebview manda isso por `evaluate_js`, o que
# trava a janela. Por isso a grande fica guardada aqui e a tela pede uma
# por vez, so quando o Wolf clica.
def _para_base64(dados, tipo="image/jpeg"):
    """Bytes da imagem -> string base64 pronta para a tela."""
    if not dados:
        return ""
    try:
        return "data:%s;base64,%s" % (
            tipo, base64.b64encode(dados).decode("ascii"))
    except Exception:
        return ""


def _imagem_para_base64(imagem, lado=1400, qualidade=85):
    """Imagem do Pillow -> base64 (usado para a foto ampliada)."""
    if imagem is None or p.Image is None:
        return ""
    try:
        buffer = io.BytesIO()
        foto = imagem
        if foto.mode not in ("RGB", "L"):
            foto = foto.convert("RGB")
        if max(foto.size) > lado:
            foto.thumbnail((lado, lado))
        foto.save(buffer, format="JPEG", quality=qualidade)
        return _para_base64(buffer.getvalue())
    except Exception:
        return ""
LARGURA, ALTURA = (1180, 820) if not PREVIA else (1100, 760)

CONVERSAS_DEMO = [
    {
        "id": "demo-1",
        "titulo": "Me conta uma curiosidade legal",
        "quando": "15/10/2026 às 19:40",
        "mensagens": [
            {"role": "user",
             "text": "Me conta uma curiosidade legal sobre o espaço"},
            {"role": "model", "text":
                "Claro! 🚀 Uma das coisas mais esquisitas do universo é que "
                "você está flutuando no espaço agora mesmo.\n\n"
                "A gravidade te puxa para o centro da Terra com tanta força "
                "que, se ela parasse de repente, você sairia correndo a uns "
                "465 km/h — mais rápido que um avião de linha! 😱\n\n"
                "E tem mais: a Lua se afasta da Terra uns 3,8 cm por ano. "
                "Daqui a bilhões de anos ela vira um planeta duplo. 🌕✨"},
        ],
    },
    {
        "id": "demo-2",
        "titulo": "Pesquisa as notícias de tecnologia",
        "quando": "15/10/2026 às 18:05",
        "mensagens": [
            {"role": "user",
             "text": "Pesquisa as notícias de tecnologia de hoje"},
            {"role": "model", "text":
                "Aqui vão os destaques de hoje: 📰\n\n"
                "• **Modelos de IA menores** — rodam no seu próprio "
                "computador, sem depender da internet. 🔒\n"
                "• **Tela dobrável** — já virou commonplace e o preço caiu. 📱\n"
                "• **Bateria de sódio** — cerca de 30% mais barata que a de "
                "lítio. 🔋\n\n"
                "Se quiser, eu aprofundo algum desses. 🙂"},
        ],
    },
    {
        "id": "demo-3",
        "titulo": "Dicas para começar um RPG",
        "quando": "14/10/2026 às 21:12",
        "mensagens": [
            {"role": "user",
             "text": "Me dá dicas para começar um jogo de RPG"},
            {"role": "model", "text":
                "Para começar sem se perder: 🗺️\n\n"
                "1. Escolha um jogo com **trilha sonora** — ajuda a entrar no "
                "clima.\n"
                "2. Anote no mapa onde achou cada loja. 🏪\n"
                "3. Não tenha pressa: jogo de RPG é sobre explorar, não "
                "sobre terminar rápido. 🎉\n\n"
                "Você prefere jogar de magio, lutador ou inventor?"},
        ],
    },
]

# O que AINDA nao esta ligado nesta tela. O passo 3 (a IA) ja foi feito,
# por isso "enviar" saiu daqui.
PASSO = {
    "microfone": "4",
    "config": "5",
}


def aviso_honesto(assunto):
    """Resposta para o que ainda nao foi ligado nesta tela."""
    return {
        "erro": "Na tela nova isso ainda não funciona (passo %s). "
                "Use o programa de sempre, que continua funcionando."
                % PASSO.get(assunto, "?"),
    }


# --- leitura dos dados ------------------------------------------------------

def _tem_chave(valor):
    """A tela so mostra os ultimos caracteres da chave, nunca ela toda."""
    return {
        "definida": bool(valor),
        "final": (str(valor)[-4:] if valor else ""),
    }


def _trecho_em_torno(texto, alvo, largura=110):
    """Recorta o texto mostrando o trecho onde o termo aparece.

    Compara sem acento (o `alvo` ja vem em minusculas e sem acento) e
    devolve o pedaco com reticencias na frente e no fim quando corta.
    """
    limpo = p._sem_acento(texto).lower()
    pos = limpo.find(alvo)
    if pos < 0:
        return texto[:largura].strip()
    comeco = max(0, pos - largura // 2)
    fim = min(len(texto), pos + len(alvo) + largura // 2)
    pedaco = texto[comeco:fim].replace("\n", " ").strip()
    if comeco > 0:
        pedaco = "… " + pedaco
    if fim < len(texto):
        pedaco = pedaco + " …"
    return pedaco


def _cfg_tela():
    """O que as abas de Configuracoes precisam mostrar (so leitura)."""
    cfg = p._ler_json(p.ARQUIVO_CONFIG, {})
    servicos = []
    for s in p.SERVICOS_RESERVA:
        chave = cfg.get(s["campo_chave"], "")
        servicos.append({
            "nome": s["nome"],
            "campo": s["campo_chave"],
            "resumo": s.get("resumo", ""),
            "passos": s.get("passos", ""),
            "pagina": s.get("pagina", ""),
            "definida": bool(chave),
            "final": (str(chave)[-4:] if chave else ""),
        })
    tema_idx = cfg.get("temaIdx", 0)
    if not isinstance(tema_idx, int) or isinstance(tema_idx, bool) or not 0 <= tema_idx < len(TEMAS_VALIDOS):
        tema_idx = 0
    return {
        "modo_pesquisa": cfg.get("modo_pesquisa", "auto"),
        "usar_contexto": bool(cfg.get("usar_contexto", True)),
        "aprender": cfg.get("aprender", True) is not False,
        "web_corretor": bool(cfg.get("corretor", True)),
        "voz_enviar": bool(cfg.get("voz_enviar", True)),
        "usar_plano_b": bool(cfg.get("usar_plano_b", True)),
        "usar_gemini": bool(cfg.get("usar_gemini", True)),
        "tema": cfg.get("tema", "Clássico Dark"),
        "temaIdx": tema_idx,
        "gemini": _tem_chave(cfg.get("api_key", "")),
        "gemini_reserva": _tem_chave(cfg.get("api_key_reserva", "")),
        "servicos": servicos,
    }


def _cfg_tela_demo():
    """Configurações de exemplo (usado no modo DEMO, para a tela ter
    o mesmo aspecto mesmo sem ler nada do Wolf)."""
    return {
        "modo_pesquisa": "auto",
        "usar_contexto": True,
        "aprender": True,
        "web_corretor": True,
        "voz_enviar": True,
        "usar_plano_b": True,
        "usar_gemini": True,
        "tema": "Clássico Dark",
        "temaIdx": 0,
        "gemini": {"definida": True, "final": "a1b2"},
        "gemini_reserva": {"definida": False, "final": ""},
        "servicos": [{
            "nome": s["nome"],
            "campo": s["campo_chave"],
            "resumo": s.get("resumo", ""),
            "passos": s.get("passos", ""),
            "pagina": s.get("pagina", ""),
            "definida": False,
            "final": "",
        } for s in p.SERVICOS_RESERVA],
    }


def _conversas_para_a_tela():
    """A lista da barra esquerda, da mais nova para a mais antiga.

    Mesmo criterio do programa antigo: o arquivo guarda as conversas na
    ordem em que foram salvas (a mais antiga primeiro) e a lista mostra
    ao contrario. Nao ordenar pelo texto do horario de propósito: ele so
    tem minuto de precisao, e duas conversas no mesmo minuto ficariam em
    ordem aleatoria.

    Quem o Wolf **fixou no topo** vem antes de todas, mas entre as
    fixadas e entre as soltas a ordem continua sendo a mesma (a mais nova
    primeiro) — senao a lista inteira mudaria de lugar a cada conversa
    nova. A conversa fixada continua valendo no programa antigo: ele
    apenas ignora o campo a mais (ver `fixar_conversa`).
    """
    if DEMO:
        return list(CONVERSAS_DEMO)
    lista = list(reversed(p.carregar_conversas()))
    fixadas = [c for c in lista if c.get("fixada")]
    soltas = [c for c in lista if not c.get("fixada")]
    return fixadas + soltas


def _mensagens_de(conversa):
    return list(conversa.get("mensagens", [])) if conversa else []


def _ler_json_da_ia(texto):
    """Le o JSON que a IA devolveu, mesmo que venha com sujeira em volta.

    Reaproveita o leitor do `roteador`, que ja foi testado para JSON
    limpo, JSON dentro de ``` e texto solto. Se o `roteador` sumir do
    projeto, cai no `json.loads` simples em vez de quebrar a tela.
    """
    try:
        import roteador
        return roteador._ler_json(texto)
    except Exception:
        try:
            return json.loads(texto)
        except Exception:
            return None


# --- a ponte: o que o JavaScript chama -------------------------------------

class Ponte:
    """Tudo que a tela nova pode pedir ao Python.

    A conversa aberta mora AQUI (em `self.mensagens` e `self.id_atual`),
    igual ao programa antigo, que tambem guarda a conversa aberta dentro
    dele e so grava no arquivo quando ha mensagem nova.

    O `self.ocupado` e o "trava" do envio: enquanto a IA responde, a tela
    nao aceita outra pergunta (e o botao fica apagado, la no JavaScript).
    """

    def __init__(self, janela=None):
        # O nome da janela tem underscore DE PROPOSITO (16/10/2026).
        #
        # O pywebview monta a ponte andando por `dir(ponte)` e, quando acha
        # um objeto que nao e' funcao, ele ENTRA dentro dele para ver se ha
        # mais funcoes la. A janela do WebView2 tem `native` ->
        # `AccessibilityObject` -> `Bounds` -> `Empty` -> `Empty` -> ... e
        # nunca acaba: o pywebview estoura "maximum recursion depth
        # exceeded" depois de milhares de atributos.
        #
        # Enquanto ele se perde nisso, a ponte fica VAZIA, e a tela
        # (que ja estava pronta) pergunta e leva
        # "TypeError: api[nome] is not a function" — foi assim que o Wolf
        # perdeu a tela no primeiro teste em 16/10/2026. Tudo que comeca
        # com underscore o pywebview pula, entao aqui nao entra naco.
        self._janela = janela
        self.id_atual = None        # conversa aberta (igual ao app antigo)
        self.mensagens = []
        self.ocupado = False
        # microfone (passo 4): o gravador e' o mesmo do programa antigo
        self.gravador = None
        self.gravando = False
        # A chave principal do Google parou de ser recusada? Este dicionario
        # e' o que FAZ LEMBRAR. Precisa ser o mesmo a cada pergunta, senao o
        # programa esqueceria que ja trocou e voltaria a insistir na chave
        # morta a cada mensagem.
        self.chaves = {"falhou": False}
        # CONVERSA PRIVADA (ideia 3 da IDEIAS.md): enquanto estiver ligada,
        # a conversa NAO e' gravada e a IA nao aprende nada sobre o que
        # foi dito. serve para assunto que o Wolf nao quer deixar
        # registrado. Ver `definir_privada`.
        self.privada = False

        # As fotos da ultima busca de imagens. Ficam aqui (e nao vao para
        # a conversa salva) porque sao bytes de imagem: guardar isso em
        # arquivo nenhum, e a tela so precisa delas enquanto a conversa
        # esta aberta na tela.
        self._ultimas_fotos = []

        # Pedacos de PDF recebidos da tela (base64), por id. Vazio na
        # maior parte do tempo; some quando `pdf_extrair` junta tudo.
        self._pdf_recebendo = {}

    # --- 1. o que a tela precisa para comecar ---

    def iniciar(self):
        """Primeira coisa que a tela chama: devolve o estado inicial."""
        conversas = _conversas_para_a_tela()
        atual = conversas[0] if conversas else None
        cfg = p._ler_json(p.ARQUIVO_CONFIG, {})
        self.id_atual = (atual or {}).get("id")
        self.mensagens = _mensagens_de(atual)
        return {
            # Usa a mesma configuração resumida das ações de atualização,
            # incluindo tema/temaIdx para a interface aplicar o tema salvo
            # na abertura (sem isso, ela voltava ao tema padrão).
            "cfg": self._cfg_curta(),
            "conversas": conversas,
            "mensagens": list(self.mensagens),
            "atual": self.id_atual,
            # No modo exemplo a chave e' lida (so ler nao mexe em nada) para
            # o aviso ser honesto: sem chave, a IA realmente nao responde.
            "tem_chave": bool(cfg.get("api_key")),
        }

    def abrir_conversa(self, identificador):
        """Clique numa conversa da barra esquerda."""
        for c in _conversas_para_a_tela():
            if str(c.get("id")) == str(identificador):
                self.id_atual = c.get("id")
                self.mensagens = _mensagens_de(c)
                return {
                    "mensagens": list(self.mensagens),
                    "atual": self.id_atual,
                }
        return {"erro": "Não achei essa conversa."}

    def conversas_buscar(self, termo):
        """Procura um texto dentro das conversas (titulo e mensagens).

        Devolve, para cada conversa que tem o termo, um pedaco do texto
        com o trecho achado no meio (para o Wolf ver onde era) e o
        indice da mensagem. A tela usa isso para mostrar o resultado e
        pular direto para a conversa.

        Regra de procura: sem acento e sem diferenciar maiuscula de
        minuscula, porque o Wolf digita do jeito que lembra. `unicodedata`
        e' a mesma coisa que o programa antigo usa para comparar
        palavras Parecidas na Memoria.
        """
        termo = (termo or "").strip()
        if len(termo) < 2:
            # Uma letra sozinha acha conversa demais e polui a tela.
            return {"achados": [], "vazio": True}
        alvo = p._sem_acento(termo).lower()
        achados = []
        for conversa in _conversas_para_a_tela():
            cid = conversa.get("id")
            titulo = str(conversa.get("titulo") or "")
            mensagens = conversa.get("mensagens") or []
            melhor = None
            for indice, mensagem in enumerate(mensagens):
                texto = str(mensagem.get("text") or "")
                if alvo in p._sem_acento(texto).lower():
                    if melhor is None or indice < melhor[0]:
                        melhor = (indice, texto)
            if melhor is None and alvo not in p._sem_acento(titulo).lower():
                continue
            if melhor is None:
                pedaco = "O título dessa conversa tem o que você procurou."
            else:
                pedaco = _trecho_em_torno(melhor[1], alvo)
            achados.append({
                "id": cid,
                "titulo": titulo or "Conversa sem título",
                "quando": conversa.get("quando", ""),
                "indice": melhor[0] if melhor else -1,
                "trecho": pedaco,
            })
            if len(achados) >= 30:
                break
        return {"achados": achados}

    def config_ler(self):
        """Abre as Configurações (so leitura neste passo)."""
        if DEMO:
            return _cfg_tela_demo()
        return _cfg_tela()

    def _memoria_para_a_tela(self):
        """Fatos + datas, sempre juntos (a aba Memoria mostra os dois).

        Tudo que muda a memoria passa por aqui, para a data nunca ficar
        velha na tela depois de adicionar, apagar ou editar um item.
        """
        return {"fatos": p.carregar_memoria(),
                "datas": p.carregar_memoria_datas()}

    def sugerir_correcao(self, palavra):
        """Correções de uma palavra digitada (botão direito).

        WebView2 em produção DESLIGA o menu de contexto do navegador
        (`AreDefaultContextMenusEnabled = _state['debug']`), entao o
        botão direito não abre nada. A tela monta o menu dela com esta
        lista — e a lógica da sugestão é a mesma do programa antigo, que
        está no motor (`pesquisa_ia.sugerir_correcao`).
        """
        try:
            return {"sugestoes": p.sugerir_correcao(palavra)}
        except Exception as erro:
            p.registrar_erro("sugerir_correcao", erro)
            return {"sugestoes": []}

    def memoria_listar(self):
        """Aba Memória, com a data em que cada fato foi aprendido.

        As datas vem do arquivo ao lado (`memoria_datas.json`), nunca de
        dentro do `memoria.json`: esse arquivo e' lido pelos dois
        programas e tem regra de ouro (nunca perder uma palavra), entao
        nao se mexe nele. Fato antigo, que ja estava guardado antes das
        datas existirem, vem sem data.
        """
        if DEMO:
            return {"fatos": [
                "Nome: Igor (pode ser chamado de Wolf)",
                "Natural de Santa Maria, Rio Grande do Sul",
                "Gosta muito de jogar videogames",
            ], "datas": {}}
        fatos = p.carregar_memoria()
        return {"fatos": fatos, "datas": p.carregar_memoria_datas(),
                "gavetas": p.carregar_memoria_gavetas(),
                "assuntos": p.carregar_memoria_por_assunto()}

    # --- 2. as conversas de verdade (este passo) ---

    def nova_conversa(self):
        """Botão 'Nova conversa' (também F5 no programa antigo).

        NAO grava nada: conversa sem pergunta nao tem o que salvar. O
        arquivo só é escrito quando houver mensagem nova (passo 3).
        Funciona tambem no modo exemplo (lá nada e gravado mesmo).
        """
        self.id_atual = None
        self.mensagens = []
        return {"atual": None, "conversas": _conversas_para_a_tela()}

    def fixar_conversa(self, identificador):
        """Fixa a conversa no topo da lista, ou solta se ja estiver fixada.

        Grava um campo a mais na conversa ("fixada": true). O programa
        antigo NAO conhece esse campo, mas tambem nao se incomoda com ele
        (ele ignora o que nao usa) — por isso a conversa continua
        aparecendo la como sempre, so que sem a fixacao.

        Este e' o unico jeito de mexer em uma conversa sem passar pelo
        caminho de excluir e recriar: o arquivo inteiro e' reescrito com
        a conversa trocada de lugar, e as mensagens dela vao junto,
        intactas.
        """
        if DEMO:
            return self._demo_nada()
        alvo = str(identificador)
        conversas = p.carregar_conversas()
        achou = None
        for conversa in conversas:
            if str(conversa.get("id")) == alvo:
                achou = conversa
                break
        if achou is None:
            return {"erro": "Não achei essa conversa."}
        mensagens_antes = len(achou.get("mensagens") or [])
        if achou.get("fixada"):
            achou.pop("fixada", None)
            fixada = False
        else:
            achou["fixada"] = True
            fixada = True
        p.salvar_conversas(conversas)
        # confere que nada se perdeu no caminho
        depois = [c for c in p.carregar_conversas()
                  if str(c.get("id")) == alvo]
        if not depois or len(depois[0].get("mensagens") or []) != mensagens_antes:
            return {"erro": "A conversa ficou esquisita ao ser fixada; "
                            "melhor não arriscar."}
        return {
            "fixada": fixada,
            "conversas": _conversas_para_a_tela(),
        }

    def fazer_backup(self):
        """Copia as conversas, a memoria e as chaves para um .zip.

        O mesmo que o `9 - Fazer backup dos meus dados.bat` faz, e com
        a mesma funcao do motor (`pesquisa_ia.fazer_backup_dados`), para
        nao existir dois jeitos de fazer a mesma coisa.
        """
        try:
            caminho, nomes = p.fazer_backup_dados()
            return {"caminho": str(caminho), "arquivos": len(nomes)}
        except Exception as erro:
            return {"erro": "Não consegui fazer a cópia: %s" % erro}

    def sugerir(self, pergunta, resposta):
        """Sugere 3 perguntas para continuar a conversa (ideia 4).

        E' um BOTAO, e nao automatico de proposito: cada pergunta aqui
        gasta uma chamada de IA, e fazer isso sozinho a cada resposta
        dobraria o custo do programa sem o Wolf pedir. Com o botao, ele so
        paga quando quer.

        Usa o modelo rapido (o mesmo do roteador): sao tres frases
        curtas, nao precisa pensar muito.
        """
        if DEMO:
            return self._demo_nada()
        cfg = p._ler_json(p.ARQUIVO_CONFIG, {})
        chave = (cfg.get("api_key") or "").strip()
        _servicos_ok = p._servicos_prontos(cfg)
        _usar_gemini = bool(cfg.get("usar_gemini", True))
        if _usar_gemini and not chave and not _servicos_ok:
            return {"erro": "sem_chave"}
        if not _usar_gemini and not _servicos_ok:
            return {"erro": "sem_servico"}
        if self.ocupado:
            return {"erro": "Aguarde a resposta terminar."}
        try:
            from google import genai
            from google.genai import types

            http = types.HttpOptions(timeout=20000)
            cliente = genai.Client(api_key=chave, http_options=http)
            pedido = (
                "Voce sugere perguntas de continuacao para um chat.\n"
                "Responda S\u00d3 com JSON, sem texto em volta:\n"
                '{"perguntas": ["...", "...", "..."]}\n\n'
                "A pergunta foi:\n%s\n\n"
                "E a resposta foi:\n%s\n\n"
                "Escreva 3 perguntas curtas que a pessoa poderia fazer em "
                "seguir sobre o MESMO assunto. Nada de 'como posso ajudar' "
                "nem de perguntas sobre a propria conversa. Portugues do "
                "Brasil, no maximo 90 letras cada."
                % (str(pergunta or "")[:600], str(resposta or "")[:1800])
            )
            r = cliente.models.generate_content(
                model=cfg.get("modelo_memoria") or p.MODELO_MEMORIA,
                contents=pedido,
                config=types.GenerateContentConfig(
                    temperature=0.7, response_mime_type="application/json"),
            )
            dados = _ler_json_da_ia(getattr(r, "text", "") or "")
            itens = (dados or {}).get("perguntas")
            if not isinstance(itens, list):
                return {"erro": "Não consegui sugerir perguntas agora."}
            limpas = [str(x).strip() for x in itens if str(x).strip()][:3]
            if not limpas:
                return {"erro": "Não consegui sugerir perguntas agora."}
            return {"perguntas": limpas}
        except Exception as erro:
            return {"erro": p.traduzir_erro(erro)}

    def definir_privada(self, ligada):
        """Liga ou desliga a conversa privada.

        Ligada, a conversa **nao e' gravada** e a IA **nao aprende nada**
        do que for dito nela (nada vai parar na memoria do Wolf).

        Detalhe de seguranca, e' o mais importante aqui: **ligar OU
        DESLIGAR comeca uma conversa nova**, jogando fora o que estava na
        tela. Sem isso haveria um vazamento: o Wolf faria uma pergunta
        privada, desligaria o modo e a pergunta seguinte gravaria a
        conversa INTEIRA, incluindo a parte privada. Verificamos isso no
        `verificar.py`.
        """
        ligada = bool(ligada)
        self.privada = ligada
        self.id_atual = None
        self.mensagens = []
        return {"privada": ligada, "atual": None, "mensagens": [],
                "conversas": _conversas_para_a_tela()}


    def excluir_conversa(self, identificador):
        """Apaga uma conversa da lista.

        Faz exatamente o que o programa antigo faz: tira a conversa do
        arquivo e, se era a que estava aberta, abre a tela inicial. O
        que a IA aprendeu sobre o Wolf continua guardado de proposito
        (apagar a conversa nao e apagar o que ele ensinou).

        No modo exemplo NÃO apaga: as conversas mostradas ali são de
        mentira, e o arquivo de verdade é do Wolf.
        """
        if DEMO:
            return {"erro": "No modo exemplo nada é apagado (as conversas "
                            "aí são de mentira). Use o programa de sempre "
                            "para excluir de verdade."}
        alvo = str(identificador)
        restantes = [c for c in p.carregar_conversas()
                     if str(c.get("id")) != alvo]
        apagada = len(restantes) != len(p.carregar_conversas())
        if not apagada:
            return {"erro": "Não achei essa conversa."}
        p.salvar_conversas(restantes)
        era_atual = str(self.id_atual) == alvo
        if era_atual:
            self.id_atual = None
            self.mensagens = []
        return {
            "conversas": _conversas_para_a_tela(),
            "era_atual": era_atual,
            "atual": self.id_atual,
        }

    # --- o que já dá para usar de verdade (desde o passo 1) ---

    def _gravar_conversa(self):
        """Guarda a conversa aberta no arquivo (usado no passo 3).

        Mesma regra do programa antigo: a conversa só ganha id (e só vai
        para o arquivo) quando tem mensagem de verdade.

        Na **conversa privada** nada é gravado — é exatamente esse o
        combinado (ver `definir_privada`).
        """
        if DEMO:
            return None
        if self.privada:
            return None
        if not self.mensagens:
            return None
        if self.id_atual is None:
            self.id_atual = str(time.time())
        return p.guardar_conversa(self.id_atual, self.mensagens)

    def salvar_texto(self, texto):
        """Salvar a resposta num .txt usando o diálogo nativo do pywebview."""
        if not texto or not str(texto).strip():
            return {"erro": "Não tem resposta para salvar."}
        if self._janela is None:
            return {"erro": "A janela ainda não está pronta para salvar arquivos."}
        nome = p._nome_de_resposta(texto)
        try:
            # Use o diálogo pertencente à janela principal. Criar um Tk()
            # aqui abre outra raiz em uma thread da ponte e pode deixar a
            # interface inteira esperando sem mostrar a janela de Salvar.
            tipo_salvar = webview.FileDialog.SAVE
            caminhos = self._janela.create_file_dialog(
                tipo_salvar,
                save_filename=nome,
                file_types=("Arquivo de texto (*.txt)",),
            )
        except Exception as erro:
            return {"erro": "Não consegui abrir a janela de salvar: %s" % erro}
        if not caminhos:
            return {}                      # cancelou: nao e erro
        caminho = caminhos[0] if isinstance(caminhos, (list, tuple)) else caminhos
        caminho = str(caminho)
        if not caminho.lower().endswith(".txt"):
            caminho += ".txt"
        try:
            with open(caminho, "w", encoding="utf-8-sig") as arquivo:
                arquivo.write(str(texto).rstrip() + "\n")
        except Exception as erro:
            return {"erro": "Não consegui salvar: %s" % erro}
        return {"caminho": caminho}

    def abrir_link(self, url):
        """Clique num link da resposta (vai abrir o navegador de sempre)."""
        try:
            if url and str(url).startswith(("http://", "https://")):
                webbrowser.open(str(url))
        except Exception:
            pass
        return {}

    # --- leitura de PDF (arrastar para a conversa) ---
    #
    # O arquivo NAO chega por caminho: a tela le os bytes e manda em
    # pedacos base64 (para nao travar a ponte com um texto gigante de
    # uma vez). `pdf_extrair` junta tudo, tira o texto com o modulo
    # `pdf_leitor` (local, sem internet) e devolve para a tela revisar.

    _documento = None      # documento aberto (documento.py), so na memoria

    def pdf_iniciar(self, id):
        """Comeca a receber um PDF. Devolve o id para os pedacos."""
        if not hasattr(self, "_pdf_recebendo"):
            self._pdf_recebendo = {}
        # Nao deixa pedaco antigo preso na memoria (se a tela recarregar).
        if len(self._pdf_recebendo) > 3:
            self._pdf_recebendo.clear()
        self._pdf_recebendo[str(id)] = []
        return {}

    def pdf_parte(self, id, parte):
        """Guarda um pedaco base64 do PDF."""
        recebendo = getattr(self, "_pdf_recebendo", None)
        if not recebendo or str(id) not in recebendo:
            return {"erro": "O envio do PDF expirou. Solte o arquivo de novo."}
        pedaco = str(parte or "")
        # Limite duro: ~25 MB de arquivo => ~34 MB de base64. Se passar
        # disso, corta o envio (evita encher a memoria).
        if sum(len(x) for x in recebendo[str(id)]) + len(pedaco) > 34_000_000:
            recebendo.pop(str(id), None)
            return {"erro": "Esse PDF e' grande demais (limite de 25 MB)."}
        recebendo[str(id)].append(pedaco)
        return {}

    def pdf_extrair(self, id, nome=""):
        """Junta os pedacos e devolve o texto do PDF (ou um erro claro).

        PDF longo nao vira texto na caixa: abre como "documento" e devolve
        {"documento": info} (ver documento.py).
        """
        recebendo = getattr(self, "_pdf_recebendo", None)
        pedacos = recebendo.pop(str(id), None) if recebendo else None
        if pedacos is None:
            return {"erro": "O envio do PDF expirou. Solte o arquivo de novo."}
        try:
            dados = base64.b64decode("".join(pedacos))
        except Exception as erro:
            p.registrar_erro("pdf_extrair (base64)", erro)
            return {"erro": "Não consegui ler esse arquivo (parece corrompido)."}
        try:
            import pdf_leitor
        except ImportError:
            return {"erro": "Falta o módulo de leitura de PDF neste programa."}
        paginas, erro = pdf_leitor.paginas_de_pdf(dados)
        if erro:
            return {"erro": erro}
        try:
            import documento
        except ImportError:
            return {"texto": "\n".join(paginas).strip()}
        if documento.eh_longo(paginas):
            self._documento = documento.Documento(nome, paginas)
            return {"documento": self._documento.info()}
        return {"texto": "\n".join(paginas).strip()}

    def documento_info(self):
        """Documento aberto agora (ou {} se nao ha)."""
        doc = getattr(self, "_documento", None)
        return doc.info() if doc is not None else {}

    def documento_fechar(self):
        """Fecha o documento: as perguntas voltam ao normal."""
        self._documento = None
        return {}

    # --- 3. a IA de verdade (este passo) ---

    def _evento(self, dados):
        """Fala com a tela: `window.PIA.evento({...})` (ver web/app.js).

        O `json.dumps` com `ensure_ascii=False` e' obrigatorio: sem ele o
        acento e o emoji viram "\\u00e7" na tela.

        Aqui nunca estoura nada: se o Wolf fechou a janela no meio da
        resposta, o erro e' engolido (a thread morre em silencio).
        """
        if self._janela is None:
            return                    # teste sem janela: nao ha para quem falar
        try:
            self._janela.evaluate_js(
                "window.PIA.evento("
                + json.dumps(dados, ensure_ascii=False) + ")"
            )
        except Exception:
            pass

    def enviar(self, texto, profundo=False):
        """O Wolf aperta Enter (ou o botao): a IA responde.

        DEVOLVE NA HORA. Quem trabalha e' a thread `_responder`; o que ela
        descobre volta para a tela por `_evento` ("etapa" enquanto pesquisa,
        "resposta" no fim, "erro" se deu ruim). Fazer o trabalho aqui
        mesmo travaria a janela por varios segundos.

        Os dois unicos erros que saem daqui sao os que a tela precisa saber
        AGORA, antes de mostrar a pergunta: pergunta vazia e falta de
        chave ("sem_chave", que o app.js reconhece e abre as Configuracoes).
        """
        texto = str(texto or "").strip()
        if not texto:
            return {"erro": "Escreva a pergunta antes de enviar."}
        if self.ocupado:
            return {"erro": "Aguarde a resposta terminar."}

        if DEMO:
            # Modo exemplo: NAO chama o Google de verdade (gastaria token
            # do Wolf a cada rascunho). Repete o mesmo caminho da tela —
            # "etapa", espera, "resposta" — para dar para ver o desenho
            # funcionando antes de gastar.
            self.ocupado = True
            self.mensagens.append({"role": "user", "text": texto})
            threading.Thread(target=self._responder_exemplo, args=(texto,),
                             daemon=True).start()
            return {}

        # Lembretes ("me lembra amanhã às 9h de pagar a conta"): quem
        # responde é o módulo `lembretes`, tudo local, sem IA e SEM precisar
        # de chave (ver lembretes.py e PLANO-LEMBRETES.md). Se a frase não
        # for sobre lembretes, `responder` devolve None e o caminho normal
        # continua logo abaixo. No modo exemplo nem chega aqui (a resposta
        # de exemplo saiu logo acima), então nada é gravado.
        resposta_lembrete = None
        try:
            import lembretes
            resposta_lembrete = lembretes.responder(texto)
        except Exception as erro:
            p.registrar_erro("lembretes.responder", erro)
        if resposta_lembrete:
            self.ocupado = True
            self.mensagens.append({"role": "user", "text": texto})
            threading.Thread(target=self._responder_lembrete,
                             args=(resposta_lembrete,), daemon=True).start()
            return {}

        cfg = p._ler_json(p.ARQUIVO_CONFIG, {})
        chave = (cfg.get("api_key") or "").strip()

        # "imagens de lobos" NAO vai para a IA: vai para a busca de
        # imagens (o mesmo caminho do programa antigo, e a MESMA funcao
        # do motor). Sem chave de API a busca de imagens funciona igual,
        # porque nao usa o Google.
        if p.TEM_PIL and p._quer_imagens(texto):
            termo = p._termo_imagens(texto)
            if not termo:
                self.mensagens.append({"role": "user", "text": texto})
                self.mensagens.append({
                    "role": "erro",
                    "text": "Escreva o que você quer ver, por exemplo: "
                            "imagens de lobos.",
                })
                return {}
            self.ocupado = True
            self.mensagens.append({"role": "user", "text": texto})
            threading.Thread(target=self._responder_imagens, args=(termo,),
                             daemon=True).start()
            return {}

        # Documento aberto (PLANO-DOCUMENTOS-LONGOS.md): a pergunta vira
        # "trechos relevantes + pergunta" so na chamada da IA. Indice e
        # "nao achei" respondem aqui mesmo, sem gastar token.
        texto_ia = None
        doc = getattr(self, "_documento", None)
        if doc is not None:
            resposta_doc = None
            try:
                import documento
                if documento.eh_pedido_de_indice(texto):
                    resposta_doc = doc.indice_texto()
                elif documento.eh_pedido_de_resumo(texto):
                    texto_ia = doc.montar_resumo()
                else:
                    texto_ia = doc.montar_pergunta(texto)
                    if texto_ia is None:
                        resposta_doc = (
                            "Não achei nada sobre isso em \"%s\". Tente outras "
                            "palavras, peça o \"índice do documento\" ou feche o "
                            "documento (botão acima da caixa) para conversar "
                            "normalmente." % doc.nome)
            except Exception as erro:
                p.registrar_erro("documento.pergunta", erro)
                texto_ia = None
            if resposta_doc:
                self.ocupado = True
                self.mensagens.append({"role": "user", "text": texto})
                threading.Thread(target=self._responder_lembrete,
                                 args=(resposta_doc,), daemon=True).start()
                return {}

        if not chave:
            return {"erro": "sem_chave"}

        # A pergunta entra no espelho da conversa antes da thread comecar,
        # para ela ja fazer parte do historico que a IA vai ler.
        self.ocupado = True
        self.mensagens.append({"role": "user", "text": texto})
        threading.Thread(
            target=self._responder, args=(texto, cfg, chave, bool(profundo), texto_ia),
            daemon=True
        ).start()
        return {}

    # ---------------- galeria de imagens --------------------------------
    def _responder_imagens(self, termo):
        """Busca as fotos e manda para a tela, uma a uma não: junta.

        As miniaturas viajam em base64 dentro do evento (são pequenas).
        As grandes ficam guardadas aqui e a tela pede uma por vez, com
        `imagem_ampliada` — mandar todas de uma vez travaria a janela.
        """
        try:
            self._evento({"tipo": "etapa", "texto": "Buscando imagens..."})
            itens = p._buscar_imagens(termo)
            if not itens:
                self._evento({
                    "tipo": "resposta",
                    "texto": "Não achei nenhuma imagem para "
                              "“%s”." % termo,
                })
            else:
                self._ultimas_fotos = itens
                fotos = []
                for item in itens:
                    fotos.append({
                        "miniatura": _para_base64(item.get("thumb")),
                        "titulo": item.get("titulo") or "",
                        "pagina": item.get("pagina") or "",
                    })
                self._evento({
                    "tipo": "imagens",
                    "termo": termo,
                    "fotos": fotos,
                    "texto": "Imagens de “%s”" % termo,
                })
            self.ocupado = False
            self._gravar_conversa()
            self._evento({"tipo": "conversas"})
        except Exception as erro:
            p.registrar_erro("_responder_imagens", erro)
            self._evento({"tipo": "erro",
                          "texto": p.traduzir_erro(erro)})
        finally:
            self.ocupado = False

    def imagem_ampliada(self, indice):
        """A foto grande, quando o Wolf clica numa miniatura.

        Já foi baixada em segundo plano enquanto ele lia a resposta, então
        costuma vir na hora. Se ainda não chegou, baixa agora.
        """
        if DEMO:
            return {"erro": "No modo exemplo as fotos são de mentira. "
                            "Abra sem --demo para ver as de verdade."}
        try:
            itens = getattr(self, "_ultimas_fotos", None) or []
            if not isinstance(indice, int) or not (0 <= indice < len(itens)):
                return {"erro": "Foto não encontrada."}
            item = itens[indice]
            grande = item.get("_grande")
            if grande is None:
                dados = p._baixar_bytes(
                    item.get("imagem") or item.get("thumb_url"),
                    tempo=15.0, limite=8_000_000)
                grande = p._imagem_de_bytes(dados)
                if grande is not None:
                    item["_grande"] = grande
            if grande is None:
                return {"erro": "Não consegui abrir essa foto."}
            return {"base64": _imagem_para_base64(grande),
                    "titulo": item.get("titulo") or "",
                    "pagina": item.get("pagina") or ""}
        except Exception as erro:
            p.registrar_erro("imagem_ampliada", erro)
            return {"erro": "Não consegui abrir essa foto."}

    def _responder(self, texto, cfg, chave, profundo=False, texto_ia=None):
        """A thread que trabalha enquanto a janela continua viva.

        Reaproveita o caminho do programa antigo: `pesquisa_ia.perguntar`
        (com busca na web) ou `pesquisa_ia.conversar` (papo normal),
        escolhidos pelo mesmo roteador, com a mesma chave reserva e o
        mesmo tradutor de erro. Nenhum disso foi reescrito aqui.
        """
        def avisar(mensagem):
            """`progresso` das funcoes acima: o que a IA esta fazendo."""
            self._evento({"tipo": "etapa", "texto": str(mensagem or "")})

        try:
            modelo = cfg.get("modelo", p.MODELO_PADRAO)
            usar_contexto = bool(cfg.get("usar_contexto", True))
            modo_cfg = cfg.get("modo_pesquisa", "auto")
            if texto_ia:
                modo_cfg = "nunca"    # pergunta sobre o documento: nao pesquisa na web
            if modo_cfg not in ("auto", "sempre", "nunca"):
                modo_cfg = "auto"

            # Historico que a IA entende: so "user" e "model" (o erro de
            # uma tentativa anterior nao entra, e o Gemini nao aceita).
            historico = [{"role": m["role"], "text": m["text"]}
                         for m in self.mensagens[:-1]
                         if m.get("role") in ("user", "model")
                         and str(m.get("text") or "").strip()]

            # "lembra que ...": guarda direto, sem gastar chamada de IA
            # (igual ao programa antigo). No modo exemplo nao guarda nada,
            # e NEM NA CONVERSA PRIVADA — senao a memoria do Wolf
            # receberia o que ele pediu para nao registrar.
            if not DEMO and not self.privada:
                try:
                    fato = p.roteador.fato_pedido(texto)
                    if fato:
                        p._mesclar_memoria([fato])
                except Exception:
                    pass

            decisao = p._decidir_modo(chave, texto, historico, modo_cfg)
            modo = decisao.get("modo", "amigo")
            consulta = decisao.get("consulta") or texto
            # Noticia explicita continua pesquisando, como antes.
            if p._quer_noticias(texto):
                modo = "pesquisa"
                consulta = texto
            if profundo:
                modo = "pesquisa"
                consulta = (consulta or texto).strip()

            # Com documento aberto, a IA recebe os trechos + a pergunta (texto_ia);
            # o roteador e a memoria continuam vendo so o que o Wolf escreveu.
            texto_modelo = texto_ia or texto

            def chamar_a_ia(qual_chave):
                if modo == "amigo":
                    return p.conversar(
                        qual_chave, modelo, historico, texto_modelo, usar_contexto,
                        progresso=avisar, cfg=cfg, id_atual=self.id_atual,
                    )
                return p.perguntar(
                    qual_chave, modelo, historico, texto_modelo, usar_contexto,
                    progresso=avisar, cfg=cfg, id_atual=self.id_atual,
                    consulta=consulta, profundo=profundo,
                )

            # Mesma troca automatica de chave do programa antigo. O
            # dicionario `self.chaves` e' o mesmo sempre, para a troca
            # durar a sessao toda (e nao recomecar a cada pergunta).
            resposta, fontes, _buscas, _origem = p.tentar_com_reserva(
                chamar_a_ia, cfg, self.chaves)
            resposta = (resposta or "").strip() or "(sem resposta)"
            if self.chaves.get("falhou"):
                self._evento({"tipo": "etapa",
                              "texto": "A chave principal parou de valer; "
                                       "estou usando a chave reserva."})
            resposta = (resposta or "").strip() or "(sem resposta)"

            # Os sites consultados vaoguardados junto da mensagem (o programa
            # antigo ignora o campo a mais, entao nao muda nada pra ele).
            # Sem isso, fechar e reabrir a conversa faria a resposta ficar
            # sem a lista de onde veio.
            fontes = fontes or []
            self.ultimaPergunta = texto
            self.ultimaResposta = resposta
            self.mensagens.append({"role": "model", "text": resposta,
                                   "fontes": fontes})
            if not DEMO:
                self._gravar_conversa()
            self._evento({"tipo": "resposta", "texto": resposta,
                          "fontes": fontes})
            if not DEMO:
                # A lista da esquerda mostra a conversa nova.
                self._evento({"tipo": "conversas",
                              "conversas": _conversas_para_a_tela(),
                              "atual": self.id_atual})
                self._aprender(texto, resposta, cfg, chave)
        except Exception as erro:
            self.mensagens.append({"role": "erro", "text": p.traduzir_erro(erro)})
            # `chave`: a tela abre as Configuracoes sozinha (como o programa
            # antigo faz quando a chave morre).
            self._evento({"tipo": "erro",
                          "texto": p.traduzir_erro(erro),
                          "chave": bool(p._falha_de_chave(erro))})
        finally:
            self.ocupado = False

    def _responder_exemplo(self, texto):
        """Resposta falsificada, so para o modo exemplo (--demo).

        Serve para ver a tela animando: os tres pontinhos, o texto
        aparecendo aos poucos e a lista de conversas se atualizando,
        sem gastar uma unica chamada de IA.
        """
        partes = [
            "Você está vendo uma resposta de EXEMPLO. 🙂",
            "",
            "- No modo exemplo eu **não** chamo o Google: não gasta token.",
            "- O desenho da tela e' o mesmo de verdade (mesmos eventos).",
            "- Para a IA de verdade, abra sem o modo exemplo.",
        ]
        try:
            for etapa in ("Pensando...", "Conversando com você..."):
                self._evento({"tipo": "etapa", "texto": etapa})
                time.sleep(0.6)
            for parte in partes:
                self._evento({"tipo": "etapa", "texto": "Escrevendo..."})
                time.sleep(0.35)
            resposta = "\n".join(partes)
            self.mensagens.append({"role": "model", "text": resposta})
            self._evento({"tipo": "resposta", "texto": resposta})
        except Exception:
            pass
        finally:
            self.ocupado = False

    def _responder_lembrete(self, resposta):
        """Responde um lembrete na conversa, sem chamar a IA.

        É tudo local (arquivo em %LOCALAPPDATA%), então a resposta sai na
        hora — mas numa thread, como as outras respostas, para não segurar
        a janela enquanto a tela espera. Não gasta token e funciona mesmo
        sem chave.
        """
        try:
            self.mensagens.append({"role": "model", "text": resposta})
            self._gravar_conversa()
            self._evento({"tipo": "resposta", "texto": resposta})
            if not DEMO:
                # A lista da esquerda mostra a conversa nova.
                self._evento({"tipo": "conversas",
                              "conversas": _conversas_para_a_tela(),
                              "atual": self.id_atual})
        except Exception as erro:
            p.registrar_erro("_responder_lembrete", erro)
            self._evento({"tipo": "erro", "texto": p.traduzir_erro(erro)})
        finally:
            self.ocupado = False

    # --- 4. o microfone (este passo) ---

    def mic_alternar(self):
        """Um clique comeca a gravar; o clique seguinte para e transcreve.

        Igual ao programa antigo (Ctrl+M): o mesmo `voz.Gravador`, o mesmo
        `wav_tem_som` e o mesmo `transcrever` com a lista de modelos de
        reserva. O texto falado NAO e' enviado sozinho: ele entra na caixa
        de digitar para o Wolf conferir antes (a menos que ele tenha
        ligado a opcao "enviar sozinho" nas Configuracoes).
        """
        if self.ocupado and not self.gravando:
            return {"erro": "Aguarde a resposta terminar."}
        if self.gravando:
            return self._parar_gravacao()
        return self._comecar_gravacao()

    def _comecar_gravacao(self):
        # Na tela de exemplo o microfone e' de mentira: fingimos que
        # gravou, para o botao poder ser testado sem microfone nenhum
        # (com --voz ele passa a ser o de verdade).
        if VOZ_FALSA:
            self.gravando = True
            self._evento({"tipo": "gravando", "ligado": True})
            return {"gravando": True}
        if not p.voz.TEM_SOM:
            return {"erro": "Este programa foi montado sem a biblioteca de "
                            "som. Rode '1 - Instalar.bat' de novo."}
        try:
            if not p.voz.microfone_disponivel():
                return {"erro": "Não achei nenhum microfone ligado neste "
                                "computador."}
        except Exception as erro:
            return {"erro": p.voz.microfone_erro(erro)}
        if not (p._ler_json(p.ARQUIVO_CONFIG, {}).get("api_key") or "").strip():
            return {"erro": "sem_chave_voz"}

        gravador = p.voz.Gravador()
        try:
            gravador.iniciar()
        except Exception as erro:
            return {"erro": p.voz.microfone_erro(erro)}
        self.gravador = gravador
        self.gravando = True
        self._evento({"tipo": "gravando", "ligado": True})
        return {"gravando": True}

    def _parar_gravacao(self):
        gravador = self.gravador
        self.gravador = None
        self.gravando = False
        self._evento({"tipo": "gravando", "ligado": False})
        if VOZ_FALSA:
            # texto de exemplo, para o Wolf ver o micro funcionando
            self.ocupado = True

            def tarefa_demo():
                self._evento({"tipo": "voz",
                              "texto": "qual foi a primeira frase jogada na Lua?",
                              "enviar": False})
                self.ocupado = False

            threading.Thread(target=tarefa_demo, daemon=True).start()
            return {"gravando": False, "transcrevendo": True}
        if gravador is None:
            return {"gravando": False}
        try:
            wav = gravador.parar()
        except Exception as erro:
            return {"erro": p.voz.microfone_erro(erro)}
        if not p.voz.wav_tem_som(wav):
            return {"erro": "Não ouvi nada. Tente de novo, mais perto do "
                            "microfone."}

        self.ocupado = True
        cfg = p._ler_json(p.ARQUIVO_CONFIG, {})
        modelo = cfg.get("modelo", p.MODELO_PADRAO)
        modelos = [modelo] + [m for m in p.MODELOS_RESERVA if m != modelo]

        def tarefa():
            try:
                texto = p.tentar_com_reserva(
                    lambda qual: p.voz.transcrever(
                        p._criar_cliente(qual), modelos, wav
                    ),
                    cfg, self.chaves,
                )
                self._evento({"tipo": "voz", "texto": str(texto or "").strip(),
                              "enviar": bool(cfg.get("voz_enviar", False))})
            except Exception as erro:
                self._evento({"tipo": "voz_erro", "texto": p.traduzir_erro(erro),
                              "chave": bool(p._falha_de_chave(erro))})
            finally:
                self.ocupado = False

        threading.Thread(target=tarefa, daemon=True).start()
        return {"gravando": False, "transcrevendo": True}

    def _aprender(self, pergunta, resposta, cfg, chave):
        """Deixa a IA aprender sobre o Wolf, em segundo plano e calada.

        Igual ao programa antigo: nada aparece na tela, nada e' perguntado,
        e o proprio `aprender_com_o_usuario` se limita para nao chamar a IA
        a cada mensagem.
        """
        if DEMO or not cfg.get("aprender", True) or not chave:
            return
        # Na conversa privada a IA nao aprende nada: e' o outro lado do
        # combinado (ver `definir_privada`).
        if self.privada:
            return

        def tarefa():
            try:
                p.aprender_com_o_usuario(chave, pergunta, resposta)
            except Exception:
                pass

        threading.Thread(target=tarefa, daemon=True).start()

    # --- 5. Configuracoes e Memoria (passo 5) ---

    def _demo_nada(self):
        return {"erro": "No modo exemplo nada é gravado. Abra sem "
                        "--demo para mudar de verdade."}

    def _cfg_curta(self):
        cfg = p._ler_json(p.ARQUIVO_CONFIG, {})
        tema_idx = cfg.get("temaIdx", 0)
        if not isinstance(tema_idx, int) or isinstance(tema_idx, bool) or not 0 <= tema_idx < len(TEMAS_VALIDOS):
            tema_idx = 0
        return {"modo_pesquisa": cfg.get("modo_pesquisa", "auto"),
                "corretor": bool(cfg.get("corretor", True)),
                "tema": cfg.get("tema", "Clássico Dark"),
                "temaIdx": tema_idx}

    # --- lembretes (PLANO-LEMBRETES.md): a tela pergunta, o Python cuida ---
    #
    # A tela chama `lembretes_vencidos` de tempos em tempos (e ao abrir) e
    # mostra um cartão para cada um; "Feito" e "Adiar 10 min" chamam os
    # outros dois. Nada sai daqui para a internet e nada é gravado no modo
    # exemplo.

    def lembretes_vencidos(self):
        """Lembretes cuja hora já chegou, prontos para a tela mostrar.

        Cada um vai com o `id`, o `texto` e o horário já em português
        ("hoje às 09:00"). No modo exemplo devolve lista vazia: não existe
        lembrete de verdade para avisar.
        """
        if DEMO:
            return {"lembretes": []}
        try:
            import lembretes
            agora = datetime.now()
            return {"lembretes": [
                {"id": i["id"], "texto": i["texto"],
                 "quando": lembretes.descrever(
                     datetime.fromisoformat(i["quando"]), agora)}
                for i in lembretes.vencidos(agora)]}
        except Exception as erro:
            p.registrar_erro("lembretes_vencidos", erro)
            return {"lembretes": []}

    def lembrete_concluir(self, id):
        """O Wolf apertou "Feito": o lembrete sai da lista."""
        if DEMO:
            return {}
        try:
            import lembretes
            lembretes.concluir(str(id))
        except Exception as erro:
            p.registrar_erro("lembrete_concluir", erro)
        return {}

    def lembrete_adiar(self, id, minutos=10):
        """O Wolf apertou "Adiar": o lembrete fica para daqui a pouco."""
        if DEMO:
            return {}
        try:
            import lembretes
            lembretes.adiar(str(id), minutos)
        except Exception as erro:
            p.registrar_erro("lembrete_adiar", erro)
        return {}

    # --- barra de titulo propria: a tela manda, o Python mexe na janela ---

    def _estado_da_janela(self):
        maximizada = _janela_maximizada()
        return {"maximizada": maximizada,
                "borda": _borda_maximizada() if maximizada else 0}

    def janela_estado(self):
        return self._estado_da_janela()

    def janela_minimizar(self):
        try:
            import ctypes
            hwnd = _hwnd_da_janela()
            if hwnd:
                ctypes.windll.user32.ShowWindow(hwnd, 6)            # SW_MINIMIZE
        except Exception as erro:
            p.registrar_erro("janela_minimizar", erro)
        return {}

    def janela_maximizar(self):
        """Alterna maximizar/restaurar e diz como ficou."""
        try:
            import ctypes
            hwnd = _hwnd_da_janela()
            if hwnd:
                ctypes.windll.user32.ShowWindow(
                    hwnd, 9 if _janela_maximizada(hwnd) else 3)     # RESTORE / MAXIMIZE
        except Exception as erro:
            p.registrar_erro("janela_maximizar", erro)
        return self._estado_da_janela()

    def janela_fechar(self):
        # WM_CLOSE: o mesmo que o X nativo (dispara o `closing` que guarda a
        # posicao da janela). Se nao der, cai no destroy do pywebview.
        try:
            import ctypes
            hwnd = _hwnd_da_janela()
            if hwnd:
                ctypes.windll.user32.PostMessageW(hwnd, 0x0010, 0, 0)
                return {}
            if self._janela is not None:
                self._janela.destroy()
        except Exception as erro:
            p.registrar_erro("janela_fechar", erro)
        return {}

    def janela_arrastar(self):
        """Comeca o arrasto da janela como se fosse a barra nativa."""
        try:
            import ctypes
            hwnd = _hwnd_da_janela()
            if hwnd and not _janela_maximizada(hwnd):
                ctypes.windll.user32.ReleaseCapture()
                ctypes.windll.user32.SendMessageW(hwnd, 0x00A1, 2, 0)   # WM_NCLBUTTONDOWN, HTCAPTION
        except Exception as erro:
            p.registrar_erro("janela_arrastar", erro)
        return {}

    _BORDAS_HT = {"esquerda": 10, "direita": 11, "topo": 12, "topo-esq": 13,
                  "topo-dir": 14, "base": 15, "base-esq": 16, "base-dir": 17}

    _ret0 = None

    def janela_redimensionar_ini(self):
        """Guarda o retangulo da janela no inicio do arrasto de uma borda."""
        try:
            import ctypes
            from ctypes import wintypes
            hwnd = _hwnd_da_janela()
            if hwnd and not _janela_maximizada(hwnd):
                r = wintypes.RECT()
                ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(r))
                self._ret0 = (r.left, r.top, r.right, r.bottom)
            else:
                self._ret0 = None
        except Exception as erro:
            self._ret0 = None
            p.registrar_erro("janela_redimensionar_ini", erro)
        return {}

    def janela_redimensionar_mover(self, borda="", dx=0, dy=0):
        """Muda o tamanho da janela: dx/dy = quanto o mouse andou (pixels fisicos)."""
        try:
            import ctypes
            borda = str(borda)
            hwnd = _hwnd_da_janela()
            if not (hwnd and self._ret0 and borda in self._BORDAS_HT):
                return {}
            dx, dy = int(dx), int(dy)
            e, t, d, b = self._ret0
            if "esq" in borda:
                e += dx
            if "dir" in borda:
                d += dx
            if "topo" in borda:
                t += dy
            if "base" in borda:
                b += dy
            minl, mina = 640, 480
            if d - e < minl:
                if "esq" in borda:
                    e = d - minl
                else:
                    d = e + minl
            if b - t < mina:
                if "topo" in borda:
                    t = b - mina
                else:
                    b = t + mina
            # 0x0014 = SWP_NOZORDER | SWP_NOACTIVATE
            ctypes.windll.user32.SetWindowPos(hwnd, 0, e, t, d - e, b - t, 0x0014)
        except Exception as erro:
            p.registrar_erro("janela_redimensionar_mover", erro)
        return {}

    def colar_texto(self):
        """Le o texto da area de transferencia do Windows (para o menu de contexto)."""
        try:
            import ctypes
            CF_UNICODETEXT = 13
            user32 = ctypes.windll.user32
            kernel32 = ctypes.windll.kernel32
            # 64-bit: definir restype para ponteiros de 64 bits
            user32.GetClipboardData.restype = ctypes.c_void_p
            user32.GetClipboardData.argtypes = [ctypes.c_uint]
            kernel32.GlobalLock.restype = ctypes.c_void_p
            kernel32.GlobalLock.argtypes = [ctypes.c_void_p]
            kernel32.GlobalUnlock.argtypes = [ctypes.c_void_p]
            if not user32.OpenClipboard(None):
                return {"texto": "", "erro": "Não foi possível abrir a área de transferência."}
            try:
                handle = user32.GetClipboardData(CF_UNICODETEXT)
                if not handle:
                    return {"texto": "", "erro": "Nenhum texto na área de transferência."}
                ptr = kernel32.GlobalLock(handle)
                if not ptr:
                    return {"texto": "", "erro": "Não foi possível ler a área de transferência."}
                try:
                    texto = ctypes.wstring_at(ptr)
                finally:
                    kernel32.GlobalUnlock(handle)
                return {"texto": texto or ""}
            finally:
                user32.CloseClipboard()
        except Exception as erro:
            p.registrar_erro("colar_texto", erro)
            return {"texto": "", "erro": str(erro)}

    def definir_modo(self, modo):
        if DEMO:
            return {"cfg": {"modo_pesquisa": modo, "corretor": True}}
        if modo not in ("auto", "sempre", "nunca"):
            return {"erro": "Modo desconhecido."}
        cfg = p._ler_json(p.ARQUIVO_CONFIG, {})
        cfg["modo_pesquisa"] = modo
        p.salvar_config(cfg)
        return {"cfg": self._cfg_curta()}

    def config_salvar(self, dados):
        """Grava as opcoes e as chaves coladas (chave vazia = nao mexe)."""
        if DEMO:
            return self._demo_nada()
        cfg = p._ler_json(p.ARQUIVO_CONFIG, {})
        dados = dados or {}
        if dados.get("modo_pesquisa") in ("auto", "sempre", "nunca"):
            cfg["modo_pesquisa"] = dados["modo_pesquisa"]
        for campo in ("usar_contexto", "aprender", "voz_enviar",
                      "usar_plano_b", "usar_gemini"):
            if campo in dados:
                cfg[campo] = bool(dados[campo])
        if "web_corretor" in dados:
            cfg["corretor"] = bool(dados["web_corretor"])
        tema_idx = dados.get("temaIdx")
        if isinstance(tema_idx, int) and not isinstance(tema_idx, bool) and 0 <= tema_idx < len(TEMAS_VALIDOS):
            cfg["temaIdx"] = tema_idx
            cfg["tema"] = TEMAS_VALIDOS[tema_idx]
        permitidos = {"api_key", "api_key_reserva"} | {
            s["campo_chave"] for s in p.SERVICOS_RESERVA}
        for campo, valor in (dados.get("chaves") or {}).items():
            valor = str(valor).strip()
            if campo in permitidos and valor:
                cfg[campo] = valor
                if campo == "api_key":
                    self.chaves["falhou"] = False
        p.salvar_config(cfg)
        return {"cfg": self._cfg_curta()}

    def testar_chave(self, campo, valor):
        """Testa a chave colada (ou a ja salva, se o campo veio vazio)."""
        try:
            cfg = dict(p._ler_json(p.ARQUIVO_CONFIG, {}))
            if valor:
                cfg[campo] = valor
            chave = cfg.get(campo, "")
            if not chave:
                return {"ok": False, "texto": "Cole a chave antes de testar."}
            if campo in ("api_key", "api_key_reserva"):
                p.testar_chave(chave, cfg.get("modelo") or p.MODELO_PADRAO)
            else:
                p.testar_servico(cfg, campo)
            return {"ok": True}
        except Exception as erro:
            try:
                texto = p.traduzir_erro(erro)
            except Exception:
                texto = str(erro)
            return {"ok": False, "texto": texto}

    def memoria_adicionar(self, texto):
        if DEMO:
            return self._demo_nada()
        texto = (texto or "").strip()
        if texto:
            p._mesclar_memoria([texto])
        return self._memoria_para_a_tela()

    def memoria_apagar(self, fato):
        if DEMO:
            return self._demo_nada()
        p.esquecer_memoria(fato)
        return self._memoria_para_a_tela()

    def memoria_apagar_tudo(self):
        if DEMO:
            return self._demo_nada()
        p.esquecer_memoria()
        return self._memoria_para_a_tela()

    def memoria_organizar(self):
        if DEMO:
            return self._demo_nada()
        mudou = p.organizar_memoria()
        _r = self._memoria_para_a_tela()
        _r["mudou"] = bool(mudou)
        return _r

    def memoria_editar(self, antigo, novo):
        """Troca um fato guardado por outro (clicar no texto na lista).

        Nao apaga e regrava: o `esquecer_memoria` e' usado so para tirar o
        item da gaveta, e `mesclar_memoria` para colocar o novo. Assim o
        jeito com que a memoria guarda continua igual ao do programa
        antigo (que e' o que a tela nova e o programa antigo leem).
        """
        if DEMO:
            return self._demo_nada()
        antigo = (antigo or "").strip()
        novo = (novo or "").strip()
        if not antigo:
            return {"erro": "Não achei esse item na memória."}
        if not novo:
            return {"erro": "O item não pode ficar vazio."}
        if novo == antigo:
            return self._memoria_para_a_tela()
        if len(novo) > p.memoria.TAMANHO_MAXIMO:
            return {"erro": "Esse item tem %d letras e o limite é %d. "
                            "Escreva mais curto."
                            % (len(novo), p.memoria.TAMANHO_MAXIMO)}
        antes = p.carregar_memoria()
        restante = [f for f in antes if f != antigo]
        if len(restante) == len(antes):
            return {"erro": "Não achei esse item na memória."}
        p.salvar_memoria(restante)
        p._mesclar_memoria([novo])
        return self._memoria_para_a_tela()

    def memoria_exportar(self):
        """Salva a memória inteira num .txt (o mesmo .txt do Windows)."""
        if DEMO:
            return self._demo_nada()
        fatos = p.carregar_memoria()
        if not fatos:
            return {"erro": "A memória está vazia: não há nada para exportar."}
        data = datetime.now().strftime("%d/%m/%Y %H:%M")
        linhas = ["MEMÓRIA DO EYE OF THUNDERA", "salva em %s" % data,
                  "%d item(ns):" % len(fatos), ""]
        linhas += ["- %s" % f for f in fatos]
        return self.salvar_texto("\n".join(linhas))


# --- montando a janela ------------------------------------------------------

# --- barra de titulo propria (PLANO-BARRA-PROPRIA.md) -----------------------
# A barra branca do Windows e' retirada POR DENTRO: tira o bit WS_CAPTION e
# MANTEM o WS_THICKFRAME, que e' quem da' redimensionar pelas bordas, encaixe
# (Win+setas) e sombra. Quem desenha minimizar/maximizar/fechar e' a tela (HTML).
#
# O WS_THICKFRAME traz junto a area nao-cliente (a moldura). Sem barra de
# titulo, essa moldura aparecia como uma FAIXA PRETA em volta da janela (7 px no
# topo a 100% de escala). Por isso a janela tambem passa a responder
# WM_NCCALCSIZE com 0: a area nao-cliente fica vazia e o conteudo cobre a janela
# inteira. O redimensionar continua porque quem decide as bordas do mouse e' o
# estilo da janela (WS_THICKFRAME), nao a area nao-cliente.

def _hwnd_da_janela(titulo=None):
    """Janela do programa, achada pelo titulo (o mesmo de TITULO_JANELA)."""
    try:
        import ctypes
        return ctypes.windll.user32.FindWindowW(None, titulo or TITULO_JANELA) or None
    except Exception:
        return None


def _estilo_sem_barra(estilo):
    """Estilo novo da janela quando a barra de título do Windows sai.

    Tira só o WS_CAPTION (0x00C00000), que é o que desenha a barra branca,
    e mantém o WS_THICKFRAME (0x00040000): sem ele a janela perde a borda
    redimensionável — não dá mais para arrastar as bordas nem encaixar a
    janela com Win+setas.
    """
    return estilo & ~0x00C00000


WM_NCCALCSIZE = 0x0083
WM_NCHITTEST = 0x0084

# Codigos do Windows para a pergunta "o mouse esta em qual parte da janela?"
# (resposta da WM_NCHITTEST). Os da borda mandam redimensionar.
HT_ESQUERDA = 10
HT_DIREITA = 11
HT_TOPO = 12
HT_CANTO_TOPO_ESQ = 13
HT_CANTO_TOPO_DIR = 14
HT_BASE = 15
HT_CANTO_BASE_ESQ = 16
HT_CANTO_BASE_DIR = 17


def _resposta_area_cliente(msg, wparam):
    """Resposta da janela a uma mensagem. None = deixa o Windows decidir.

    WM_NCCALCSIZE é a mensagem em que o Windows pergunta qual é a área
    não-cliente (a moldura). Responder 0 quer dizer "nenhuma": o conteúdo passa
    a ocupar a janela inteira e não sobra a faixa preta da moldura. Só vale
    quando wparam é verdadeiro — no caso simples quem responde é o Windows.
    """
    if msg == WM_NCCALCSIZE and wparam:
        return 0
    return None


def _borda_de_redimensionar(px, py, esquerda, topo, direita, base, grossura):
    """O que o Windows deve fazer com o mouse no ponto (px, py), em tela.

    Devolve um dos códigos de borda quando o ponto está a menos de "grossura"
    pixels da moldura, ou None quando não está (aí o clique é um clique normal).
    Como a área não-cliente fica vazia (ver _resposta_area_cliente), é esta
    resposta que mantém o redimensionar pelas bordas funcionando.
    """
    if grossura <= 0:
        return None
    na_esquerda = px < esquerda + grossura
    na_direita = px >= direita - grossura
    no_topo = py < topo + grossura
    na_base = py >= base - grossura
    if no_topo and na_esquerda:
        return HT_CANTO_TOPO_ESQ
    if no_topo and na_direita:
        return HT_CANTO_TOPO_DIR
    if na_base and na_esquerda:
        return HT_CANTO_BASE_ESQ
    if na_base and na_direita:
        return HT_CANTO_BASE_DIR
    if na_esquerda:
        return HT_ESQUERDA
    if na_direita:
        return HT_DIREITA
    if no_topo:
        return HT_TOPO
    if na_base:
        return HT_BASE
    return None


def _codigo_borda(hwnd, lparam):
    """Codigo de redimensionar para o ponto da WM_NCHITTEST, ou None.

    Não responde nada quando a janela está maximizada ou minimizada: nesses
    casos não existe borda para arrastar (e a ponto da tela passaria por fora
    da janela).
    """
    try:
        import ctypes
        usuario = ctypes.windll.user32
        if usuario.IsZoomed(hwnd) or usuario.IsIconic(hwnd):
            return None
        grossura = _borda_maximizada()
        if grossura <= 0:
            return None

        class RETANGULO(ctypes.Structure):
            _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long),
                        ("right", ctypes.c_long), ("bottom", ctypes.c_long)]

        r = RETANGULO()
        if not usuario.GetWindowRect(hwnd, ctypes.byref(r)):
            return None
        # O lParam traz a posicao do mouse em tela, em dois numeros com sinal
        # de 16 bits (pode ser negativa em monitor a esquerda).
        x = ctypes.c_short(lparam & 0xFFFF).value
        y = ctypes.c_short((lparam >> 16) & 0xFFFF).value
        return _borda_de_redimensionar(x, y, r.left, r.top, r.right, r.bottom,
                                       grossura)
    except Exception:
        return None


# Os ganchos ficam guardados aqui: se o Python recolher o objeto da função, o
# Windows chama memória livre e o programa cai.
_ganchos_wndproc = {}
_janelas_cobertas = set()


def _cobrir_area_cliente(hwnd):
    """A janela inteira passa a ser conteúdo (sem a moldura preta do Windows).

    Põe um gancho na janela (subclasse do WNDPROC) que responde WM_NCCALCSIZE
    com 0 e devolve as bordas na WM_NCHITTEST — ver PLANO-BARRA-PROPRIA.md.
    Cuida de não instalar duas vezes na mesma janela. Devolve True se o gancho
    está posto.
    """
    if not hwnd:
        return False
    if hwnd in _janelas_cobertas:
        return True
    try:
        import ctypes
        usuario = ctypes.windll.user32
        usuario.GetWindowLongPtrW.restype = ctypes.c_ssize_t
        usuario.GetWindowLongPtrW.argtypes = [ctypes.c_void_p, ctypes.c_int]
        usuario.SetWindowLongPtrW.restype = ctypes.c_ssize_t
        usuario.SetWindowLongPtrW.argtypes = [ctypes.c_void_p, ctypes.c_int,
                                              ctypes.c_ssize_t]
        usuario.CallWindowProcW.restype = ctypes.c_ssize_t
        usuario.CallWindowProcW.argtypes = [ctypes.c_void_p, ctypes.c_void_p,
                                            ctypes.c_uint, ctypes.c_size_t,
                                            ctypes.c_ssize_t]
        anterior = usuario.GetWindowLongPtrW(hwnd, -4)          # GWL_WNDPROC
        if not anterior:
            return False
        tipo_proc = ctypes.WINFUNCTYPE(ctypes.c_ssize_t, ctypes.c_void_p,
                                       ctypes.c_uint, ctypes.c_size_t,
                                       ctypes.c_ssize_t)

        def gancho(h, msg, wparam, lparam):
            resposta = _resposta_area_cliente(msg, wparam)
            if resposta is not None:
                return resposta
            if msg == WM_NCHITTEST:
                borda = _codigo_borda(h, lparam)
                if borda is not None:
                    return borda
            return usuario.CallWindowProcW(ctypes.c_void_p(anterior), h, msg,
                                           wparam, lparam)

        ponte = tipo_proc(gancho)
        usuario.SetWindowLongPtrW(hwnd, -4,
                                  ctypes.cast(ponte, ctypes.c_void_p).value)
        _ganchos_wndproc[hwnd] = ponte
        _janelas_cobertas.add(hwnd)
        return True
    except Exception:
        return False


def _tirar_barra_nativa(titulo=None, tentativas=20, espera=0.1):
    """Tira a barra de titulo do Windows. Devolve True se conseguiu."""
    try:
        import ctypes
        usuario = ctypes.windll.user32
        usuario.GetWindowLongPtrW.restype = ctypes.c_ssize_t
        usuario.GetWindowLongPtrW.argtypes = [ctypes.c_void_p, ctypes.c_int]
        usuario.SetWindowLongPtrW.restype = ctypes.c_ssize_t
        usuario.SetWindowLongPtrW.argtypes = [ctypes.c_void_p, ctypes.c_int,
                                              ctypes.c_ssize_t]
    except Exception:
        return False
    for _ in range(tentativas):
        hwnd = _hwnd_da_janela(titulo)
        if hwnd:
            estilo = usuario.GetWindowLongPtrW(hwnd, -16)           # GWL_STYLE
            # Sem CAPTION, mantendo o redimensionamento (ver _estilo_sem_barra).
            novo = _estilo_sem_barra(estilo)
            usuario.SetWindowLongPtrW(hwnd, -16, novo)
            # Sem area nao-cliente: o conteudo cobre a janela toda e a moldura
            # preta do WS_THICKFRAME nao aparece (ver _cobrir_area_cliente).
            _cobrir_area_cliente(hwnd)
            # Vidro do Windows na janela inteira: e' o que mantem a sombra e os
            # cantos arredondados. O conteudo da tela desenha por cima dele.
            try:
                dwm = ctypes.windll.dwmapi
                class MARGINS(ctypes.Structure):
                    _fields_ = [("cxLeftWidth", ctypes.c_int),
                                ("cxRightWidth", ctypes.c_int),
                                ("cyTopHeight", ctypes.c_int),
                                ("cyBottomHeight", ctypes.c_int)]
                margins = MARGINS(-1, -1, -1, -1)
                dwm.DwmExtendFrameIntoClientArea(hwnd, ctypes.byref(margins))
            except Exception:
                pass
            # SWP_NOSIZE|NOMOVE|NOZORDER|NOACTIVATE|FRAMECHANGED
            usuario.SetWindowPos(hwnd, None, 0, 0, 0, 0, 0x0001 | 0x0002 | 0x0004 | 0x0010 | 0x0020)
            return True
        time.sleep(espera)
    return False


def _janela_maximizada(hwnd=None):
    try:
        import ctypes
        hwnd = hwnd or _hwnd_da_janela()
        return bool(hwnd and ctypes.windll.user32.IsZoomed(hwnd))
    except Exception:
        return False


def _borda_maximizada():
    """Pixels fisicos que a janela maximizada sem barra passa da tela."""
    try:
        import ctypes
        m = ctypes.windll.user32.GetSystemMetrics
        return int(m(32) + m(92))      # SM_CXSIZEFRAME + SM_CXPADDEDBORDER
    except Exception:
        return 0


def _endereco_de(arquivo):
    """webview.create_window nao aceita caminho com acento: usa file://."""
    return arquivo.resolve().as_uri()


def principal():
    faltando = [a for a in (INDEX, ESTILO, SCRIPT) if not a.exists()]
    if faltando:
        msg = "Faltam arquivos da tela nova:\n  " + "\n  ".join(str(a) for a in faltando)
        try:
            p.registrar_erro("principal (arquivos faltantes)", Exception(msg))
        except Exception:
            pass
        raise RuntimeError(msg)

    ponte = Ponte()
    # Onde abrir: no monitor onde o Wolf fechou da ultima vez (16/10).
    # Se esse monitor nao existir mais hoje (levou o notebook para outro
    # lugar), cai no padrao — em vez de abrir fora de qualquer tela.
    abrir_x, abrir_y = _posicao_de_abertura()
    janela = webview.create_window(
        TITULO_JANELA,
        url=_endereco_de(INDEX),
        js_api=ponte,
        x=abrir_x, y=abrir_y,
        width=LARGURA, height=ALTURA,
        min_size=(900, 620),
        background_color="#0e0e13",      # a barra some no fundo escuro
        frameless=False,
        easy_drag=False,
        text_select=True,
    )
    ponte._janela = janela

    # ---- a janela lembra onde foi fechada ----------------------------
    # Pedido do Wolf (16/10/2026): o programa abre no monitor em que foi
    # fechado, e nao sempre no segundo. Guardar e' feito aqui, no
    # `closing` (que dispara ANTES da janela sumir) — depois seria tarde
    # demais, a posicao ja teria virado (0,0).
    def ao_fechar():
        try:
            x = getattr(janela, "x", None)
            y = getattr(janela, "y", None)
            if (isinstance(x, int) and isinstance(y, int) and (x or y)
                    and not _janela_maximizada()):
                _guardar_posicao(x, y)
        except Exception as erro:
            p.registrar_erro("ao_fechar (posicao)", erro)

    janela.events.closing += ao_fechar

    def ao_abrir(instancia):
        # A barra de titulo do Windows e' branca por padrao e destoa de
        # um programa escuro.
        #
        # Aqui NAO da para usar `ativar_barra_escura`: ela espera um
        # widget do tkinter (`update_idletasks` e `winfo_id`), e a janela
        # do pywebview nao tem nenhum dos dois. O erro era engolido e a
        # barra ficava BRANCA. Agora a janela e' procurada pelo titulo
        # (ela pode demorar um pouco para o Windows criar, por isso a
        # repeticao) e a barra e' escurecida de verdade.
        # Uma tarefa de fundo: se ficasse esperando aqui, a janela nao
        # apareceria.
        def escurecer():
            try:
                p.escurecer_janela_por_titulo(TITULO_JANELA)
            except Exception:
                pass

        threading.Thread(target=escurecer, daemon=True).start()
        threading.Thread(target=_tirar_barra_nativa, daemon=True).start()

    # O dicionário do corretor leva quase 4 segundos para carregar na
    # primeira vez (são dois dicionários: português e inglês). Se isso
    # acontecer no meio de um clique direito, a tela ficaria 4 segundos
    # parada com o menu aberto. Melhor carregar aqui, em segundo plano,
    # enquanto o Wolf ainda está lendo o que já abriu.
    def aquecer_corretor():
        try:
            p._obter_corretor("pt")
            p._obter_corretor("en")
        except Exception:
            pass

    threading.Thread(target=aquecer_corretor, daemon=True).start()

    print("Abrindo a tela nova (passo 4: microfone ligado).")
    print("Janela em x=%d y=%d  (%dx%d)"
          % (abrir_x, abrir_y, LARGURA, ALTURA))
    if DEMO:
        print("MODO DEMO: as conversas mostradas sao de EXEMPLO.")
        print("A IA de verdade responde, mas NADA e gravado (nem conversa,")
        print("nem memoria) enquanto a janela estiver no modo exemplo.")
    else:
        print("Suas conversas e memoria podem ser atualizadas ao conversar.")
    try:
        webview.start(ao_abrir, janela, gui="edgechromium",
                      icon=str(RAIZ / "icone.ico"))
    except Exception as erro:
        # O programa de sempre grava tudo no erro.log para podermos ver
        # depois. A tela nova nao gravava NADA: um erro aqui era simplesmente
        # perdido. Escrever o log e' o unico jeito de ter prova do que
        # aconteceu na proxima vez (achado em 16/10/2026, quando o Wolf
        # viu a tela fechar ao arrastar a janela para o outro monitor).
        try:
            p.registrar_erro("tela nova - abrindo a janela", erro)
        except Exception:
            pass
        sys.exit("A janela nao abriu: %r" % (erro,))
    print("Tela nova fechada.")


if __name__ == "__main__":
    principal()
