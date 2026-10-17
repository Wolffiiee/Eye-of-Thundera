"use strict";
/* Eye of Thundera - tela nova. Fala com o Python por window.pywebview.api (ver app_web.py). */

const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];
const NS = "http://www.w3.org/2000/svg";
function ico(id) {
  const s = document.createElementNS(NS, "svg");
  const u = document.createElementNS(NS, "use");
  u.setAttribute("href", "#" + id);
  s.appendChild(u);
  return s;
}
function el(tag, cls, texto) {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (texto !== undefined) e.textContent = texto;
  return e;
}

const estado = { mensagens: [], conversas: [], atual: null, ocupado: false, gravando: false, privada: false, profundo: false, sugerindo: false, ultimaPergunta: "", ultimaResposta: "", cfg: {}, aba: "memoria", rascunho: {} };
const ROTULO_WEB = { auto: "Web: automática", sempre: "Web: sempre", nunca: "Web: desligada" };

// Paletas centralizadas para a tela de Personalização e para a abertura do app.
const TEMAS_UI = [
  { nome: "Clássico Dark", cores: { "--bg": "#0e0e13", "--painel": "#13131a", "--superficie": "#1a1a23", "--superficie-2": "#22222d", "--texto": "#ececf3", "--texto-2": "#a6a6bb", "--texto-3": "#70708a", "--borda": "#272735", "--azul": "#3d6bff", "--azul-2": "#5b84ff" } },
  { nome: "Purpurina", cores: { "--bg": "#0d0f1a", "--painel": "#15172a", "--superficie": "#202440", "--superficie-2": "#2a2e50", "--texto": "#e4dcf5", "--texto-2": "#b8acd6", "--texto-3": "#8e82b2", "--borda": "#4b416c", "--azul": "#a94eff", "--azul-2": "#c17aff" } },
  { nome: "Amethyst", cores: { "--bg": "#141222", "--painel": "#211a32", "--superficie": "#2a1f3e", "--superficie-2": "#392950", "--texto": "#eee3ff", "--texto-2": "#c7b4e0", "--texto-3": "#9a83b8", "--borda": "#59416f", "--azul": "#b464e4", "--azul-2": "#cf8cff" } },
  { nome: "Ocean", cores: { "--bg": "#0f2027", "--painel": "#152b35", "--superficie": "#1b3542", "--superficie-2": "#254654", "--texto": "#e0f4ff", "--texto-2": "#a8d0e6", "--texto-3": "#79a8c0", "--borda": "#345968", "--azul": "#36a9d6", "--azul-2": "#63c7ed" } },
  { nome: "Forest", cores: { "--bg": "#0d1b15", "--painel": "#14291f", "--superficie": "#1a3a2e", "--superficie-2": "#24503d", "--texto": "#e0f5e7", "--texto-2": "#a8d5ba", "--texto-3": "#7fb394", "--borda": "#3d6a50", "--azul": "#6d9e4f", "--azul-2": "#8fbd70" } },
  { nome: "Aurora", cores: { "--bg": "#111827", "--painel": "#172235", "--superficie": "#202e44", "--superficie-2": "#2b3c55", "--texto": "#edf4ff", "--texto-2": "#bdcee6", "--texto-3": "#91a6c3", "--borda": "#40546d", "--azul": "#54b7a6", "--azul-2": "#83d5c6" } },
  { nome: "Pôr do Sol", cores: { "--bg": "#1b1412", "--painel": "#291b16", "--superficie": "#38251d", "--superficie-2": "#4b3327", "--texto": "#fff0e6", "--texto-2": "#e2c5b1", "--texto-3": "#ba9680", "--borda": "#634737", "--azul": "#e7925d", "--azul-2": "#ffb67c" } },
  { nome: "Rosa Chá", cores: { "--bg": "#1d1420", "--painel": "#291a2d", "--superficie": "#38233b", "--superficie-2": "#4a3050", "--texto": "#fbf0fc", "--texto-2": "#dec5e3", "--texto-3": "#b69bbd", "--borda": "#604569", "--azul": "#d781bf", "--azul-2": "#efadd8" } },
  { nome: "Grafite Dourado", cores: { "--bg": "#15181c", "--painel": "#1d2228", "--superficie": "#272d34", "--superficie-2": "#333b44", "--texto": "#f1f3f5", "--texto-2": "#c6cdd5", "--texto-3": "#9ba6b1", "--borda": "#49545f", "--azul": "#d0a85c", "--azul-2": "#f1cd7d" } },
  { nome: "Thundera", cores: { "--bg": "#0d0808", "--painel": "#1a0e0e", "--superficie": "#2a1414", "--superficie-2": "#3a1c1c", "--texto": "#f5e8e8", "--texto-2": "#d4b8b8", "--texto-3": "#a88888", "--borda": "#5a2a2a", "--azul": "#c0392b", "--azul-2": "#e74c3c" } },
];

function aplicarTema(indice) {
  const idx = Number.isInteger(Number(indice)) && Number(indice) >= 0 && Number(indice) < TEMAS_UI.length
    ? Number(indice) : 0;
  Object.entries(TEMAS_UI[idx].cores).forEach(([chave, valor]) => {
    document.documentElement.style.setProperty(chave, valor);
  });
  return TEMAS_UI[idx];
}

/* ---------------- a ponte com o programa ----------------
   O pywebview cria a ponte em DUAS etapas: primeiro põe um objeto VAZIO
   (window.pywebview.api = {}) e só depois coloca as funções dentro. Entre
   uma etapa e outra, api[nome] é undefined e a tela estoura um
   "api[nome] is not a function".

   Foi exatamente isso que travou o Wolf em 16/10/2026: a tela perguntou
   nesse intervalo, o erro apareceu, o "pensando" ficou aceso para sempre
   e ele nao conseguia mais perguntar NADA.

   Aqui a tela ESPERA a ponte encher em vez de confiar na ordem. Nao
   importa se ela chega primeiro, depois ou junto: a chamada so acontece
   quando existe pelo menos uma funcao. */
const ESPERA_PONTE_MS = 30000;
let pontePronta = null;

function esperarPonte() {
  if (pontePronta) return pontePronta;
  pontePronta = new Promise((resolve, reject) => {
    const comecou = Date.now();
    const tentar = () => {
      const api = window.pywebview && window.pywebview.api;
      if (api && Object.keys(api).length > 0) return resolve(api);
      if (Date.now() - comecou > ESPERA_PONTE_MS) {
        pontePronta = null; // deixa tentar de novo na proxima chamada
        return reject(new Error(
          "o programa não respondeu em " + ESPERA_PONTE_MS / 1000 +
          " segundos. Fecha e abre de novo."
        ));
      }
      setTimeout(tentar, 40);
    };
    window.addEventListener("pywebviewready", tentar);
    tentar();
  });
  return pontePronta;
}

async function chamar(nome, ...args) {
  try {
    const api = await esperarPonte();
    if (typeof api[nome] !== "function") {
      const disponiveis = Object.keys(api).sort().join(", ");
      throw new Error(
        `a função "${nome}" não existe no programa (o que existe: ${disponiveis})`
      );
    }
    return await api[nome](...args);
  } catch (e) {
    // Se a chamada falhar, a tela NÃO pode ficar travada esperando: quem
    // chama tem que poder seguir em frente.
    if (estado.ocupado) esperar(false);
    aviso("Algo deu errado: " + (e.message || e), true);
    return { erro: String(e.message || e) };
  }
}

let temporizadorAviso = null;
function aviso(texto, erro) {
  const a = $("#aviso");
  a.textContent = texto;
  a.className = erro ? "erro" : "";
  clearTimeout(temporizadorAviso);
  temporizadorAviso = setTimeout(() => a.classList.add("oculto"), 4200);
}

/* ---------------- texto das mensagens ---------------- */
const URL_RE = /https?:\/\/[^\s<>"')\]]+[^\s<>"')\].,;:!?]/g;
const MARCA_LISTA = /^\s*(?:[•\-–*]|\d+[.)])\s+/;

function comLinks(pai, texto) {
  // Processa **negrito** e URLs, em ordem de aparicao.
  const partes = [];
  let resto = String(texto);
  // Primeiro, separa os trechos **negrito**.
  const boldRe = /\*\*([^*]+)\*\*/g;
  let ultimoBold = 0;
  const segmentos = [];
  for (const m of resto.matchAll(boldRe)) {
    if (m.index > ultimoBold) segmentos.push({ tipo: "texto", valor: resto.slice(ultimoBold, m.index) });
    segmentos.push({ tipo: "negrito", valor: m[1] });
    ultimoBold = m.index + m[0].length;
  }
  if (ultimoBold < resto.length) segmentos.push({ tipo: "texto", valor: resto.slice(ultimoBold) });

  for (const seg of segmentos) {
    if (seg.tipo === "negrito") {
      const strong = document.createElement("strong");
      // Dentro do negrito, ainda pode haver URL.
      comLinks(strong, seg.valor);
      pai.append(strong);
    } else {
      // Texto normal: aplica URLs.
      let ultimo = 0;
      for (const m of seg.valor.matchAll(URL_RE)) {
        if (m.index > ultimo) pai.append(seg.valor.slice(ultimo, m.index));
        const a = el("a", "", m[0]);
        a.href = m[0];
        a.dataset.url = m[0];
        pai.append(a);
        ultimo = m.index + m[0].length;
      }
      if (ultimo < seg.valor.length) pai.append(seg.valor.slice(ultimo));
    }
  }
}

function formatar(texto, alvo) {
  const blocos = String(texto).replace(/\r/g, "").trim().split(/\n{2,}/);
  for (const bloco of blocos) {
    const linhas = bloco.split("\n");
    if (linhas.length && linhas.every((l) => MARCA_LISTA.test(l))) {
      const lista = el(/^\s*\d+[.)]/.test(linhas[0]) ? "ol" : "ul");
      for (const l of linhas) {
        const li = el("li");
        comLinks(li, l.replace(MARCA_LISTA, ""));
        lista.append(li);
      }
      alvo.append(lista);
    } else {
      const p = el("p");
      linhas.forEach((l, i) => {
        if (i) p.append(document.createElement("br"));
        comLinks(p, l);
      });
      alvo.append(p);
    }
  }
}

async function escreverClipboard(texto) {
  const valor = String(texto ?? "");
  if (!valor) return false;
  try {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      await navigator.clipboard.writeText(valor);
      return true;
    }
  } catch (_e) { /* tenta a cópia compatível com WebView */ }
  const foco = document.activeElement;
  const temporario = el("textarea");
  temporario.value = valor;
  temporario.setAttribute("readonly", "");
  temporario.setAttribute("aria-hidden", "true");
  temporario.tabIndex = -1;
  temporario.style.cssText = "position:fixed;left:-10000px;top:0;opacity:0;pointer-events:none";
  document.body.append(temporario);
  temporario.focus();
  temporario.select();
  let copiou = false;
  try { copiou = document.execCommand("copy"); } catch (_e) { copiou = false; }
  temporario.remove();
  if (foco && foco !== document.body && foco.isConnected && foco.focus) {
    try { foco.focus({ preventScroll: true }); } catch (_e) { foco.focus(); }
  }
  return copiou;
}

async function copiarTexto(texto) {
  const copiou = await escreverClipboard(texto);
  if (!copiou) aviso("Não consegui copiar. Selecione o texto e use Ctrl+C.", true);
  return copiou;
}

function criarMensagem(m) {
  const tipo = m.role === "user" ? "eu" : m.role === "erro" ? "erro" : "ia";
  const caixa = el("div", "msg " + tipo);
  const corpo = el("div", "corpo");
  if (tipo === "ia") {
    const av = el("span", "avatar");
    av.append(ico("i-lupa"));
    caixa.append(av);
  }
  formatar(m.text || "", corpo);
  if (tipo === "ia") {
    const acoes = el("div", "acoes");
    const bCopiar = el("button");
    bCopiar.title = "Copiar a resposta";
    bCopiar.append(ico("i-copiar"), el("span", "", "Copiar"));
    bCopiar.addEventListener("click", async () => {
      if (!await copiarTexto(m.text)) return;
      bCopiar.lastChild.textContent = "Copiado";
      acoes.classList.add("visivel");
      setTimeout(() => { bCopiar.lastChild.textContent = "Copiar"; acoes.classList.remove("visivel"); }, 1400);
    });
    const bSalvar = el("button");
    bSalvar.title = "Salvar a resposta em um arquivo .txt";
    bSalvar.append(ico("i-salvar"), el("span", "", "Salvar .txt"));
    bSalvar.addEventListener("click", async () => {
      const r = await chamar("salvar_texto", m.text);
      if (r && r.caminho) aviso("Salvo em " + r.caminho);
      else if (r && r.erro) aviso(r.erro, true);
    });
    acoes.append(bCopiar, bSalvar);
    corpo.append(linhaFontes(m.fontes), acoes, botaoSugerir());
    // O texto CRU fica guardado na propria mensagem: e' ele que o
    // Ctrl+S precisa salvar (o que aparece na tela ja vem formatado,
    // com link e negrito).
    caixa.dataset.bruto = m.text;
  }
  caixa.append(corpo);
  return caixa;
}

function rolarParaOFim() {
  const r = $("#rolagem");
  r.scrollTop = r.scrollHeight;
}

function desenharMensagens() {
  const lista = $("#mensagens");
  lista.replaceChildren();
  for (const m of estado.mensagens) lista.append(criarMensagem(m));
  $("#vazio").classList.toggle("oculto", estado.mensagens.length > 0);
  mostrarPrivada();          // escreve o titulo E o aviso de conversa privada
  rolarParaOFim();
}

function anexarMensagem(m) {
  estado.mensagens.push(m);
  $("#vazio").classList.add("oculto");
  const caixa = criarMensagem(m);
  $("#mensagens").append(caixa);
  // A ultima bolha: e' onde a galeria de imagens vai entrar quando o
  // Python mandar as fotos ("imagens de lobos"). Guardar a bolha e'
  // melhor do que a tela procurar por texto: se a conversa tiver varias
  // mensagens, "a ultima" seria ambigua.
  estado.ultimaBolha = caixa;
  if (estado.mensagens.length === 1 && m.role === "user") mostrarPrivada();
  rolarParaOFim();
}

/* ---------------- menu do botão direito ----------------
   No WebView2 de produção o menu de contexto do navegador está DESLIGADO
   (`AreDefaultContextMenusEnabled = _state['debug']`), então o botão
   direito não abre nada — foi o que o Wolf viu em 16/10/2026. Aqui a
   tela faz o menu dela: as correções da palavra sob o cursor (a lógica
   é a do MOTOR, a mesma do programa antigo) e os comandos de edição. */
function palavraNoCursor(campo, pos) {
  const t = campo.value;
  let ini = pos, fim = pos;
  while (ini > 0 && /[^\W\d_]/u.test(t[ini - 1])) ini--;
  while (fim < t.length && /[^\W\d_]/u.test(t[fim])) fim++;
  return { palavra: t.slice(ini, fim), ini, fim };
}

let focoContextoRetorno = null;

function fecharMenuContexto(restaurarFoco = false) {
  $("#menu-contexto").classList.add("oculto");
  $("#menu-contexto").replaceChildren();
  const foco = focoContextoRetorno;
  focoContextoRetorno = null;
  if (restaurarFoco && foco && foco.isConnected && foco.focus) {
    try { foco.focus({ preventScroll: true }); } catch (_e) { foco.focus(); }
  }
}

function itemMenu(texto, aoClicar, ligado = true, atalho = "") {
  const b = el("button", "item-contexto");
  b.type = "button";
  b.setAttribute("role", "menuitem");
  b.append(el("span", "item-contexto-texto", texto));
  if (atalho) b.append(el("kbd", "item-contexto-atalho", atalho));
  b.disabled = !ligado;
  if (ligado) b.addEventListener("click", async () => {
    try { await aoClicar(); }
    catch (_e) { aviso("Não consegui concluir essa ação.", true); }
  });
  return b;
}

function mostrarMenuContexto(x, y) {
  const menu = $("#menu-contexto");
  const campo = $("#entrada");
  menu.replaceChildren();
  menu.setAttribute("role", "menu");
  menu.setAttribute("aria-label", "Ações para editar o texto");
  const { palavra, ini, fim } = palavraNoCursor(campo, campo.selectionStart);
  // Guardamos o intervalo antes do foco ir para o menu, para que Recortar
  // e Colar atuem no trecho que a pessoa escolheu ao abrir o menu.
  const selecaoIni = Math.min(campo.selectionStart, campo.selectionEnd);
  const selecaoFim = Math.max(campo.selectionStart, campo.selectionEnd);
  const trecho = campo.value.slice(selecaoIni, selecaoFim);
  const temSelecao = selecaoIni !== selecaoFim;
  menu.append(
    itemMenu("Recortar", async () => {
      const copiou = await escreverClipboard(trecho);
      if (copiou) {
        campo.focus();
        campo.setRangeText("", selecaoIni, selecaoFim, "start");
        ajustarAltura(); atualizarEnviar();
        aviso("Texto recortado.");
      } else aviso("Não consegui copiar; o texto foi mantido.", true);
      fecharMenuContexto(true);
    }, temSelecao, "Ctrl+X"),
    itemMenu("Copiar", async () => {
      const copiou = await escreverClipboard(trecho);
      aviso(copiou ? "Texto copiado." : "Não consegui copiar o texto.", !copiou);
      fecharMenuContexto(true);
    }, temSelecao, "Ctrl+C"),
    itemMenu("Colar", async () => {
      await colar(selecaoIni, selecaoFim);
      fecharMenuContexto(true);
    }, true, "Ctrl+V"),
    itemMenu("Selecionar tudo", () => {
      campo.focus(); campo.select(); fecharMenuContexto(true);
    }, true, "Ctrl+A")
  );
  if (palavra.length >= 2) {
    // A busca das correções leva quase 4 segundos na PRIMEIRA vez (é o
    // carregamento do dicionário). O título e o "carregando..." saem
    // juntos, no fim da espera: se a busca demorasse e o título já
    // tivesse sumido, aparecia um menu com os comandos e mais nada, e o
    // Wolf pensaria que a correção não funciona.
    const divisoria = el("div", "divisao");
    const tit = el("div", "titulo", "Corrigir");
    const vazio = el("div", "titulo", "carregando...");
    menu.append(divisoria, tit, vazio);
    chamar("sugerir_correcao", palavra).then((r) => {
      // enquanto a tela procura as correções, o Wolf pode ter clicado
      // em outro lugar: nesse caso este menu já foi fechado e as
      // sugestões iriam aparecer num menu que ninguém está vendo.
      if (menu.classList.contains("oculto")) return;
      tit.remove();
      vazio.remove();
      const ss = (r && r.sugestoes) || [];
      if (!ss.length) {
        menu.append(el("div", "titulo", "(nada parecido)"));
        return;
      }
      for (const s of ss) {
        menu.append(itemMenu(s, () => {
          substituirTrecho(ini, fim, s);
          fecharMenuContexto(true);
        }));
      }
      // reajusta a posicao depois que as sugestoes cresceram o menu
      const l2 = Math.min(x, window.innerWidth - menu.offsetWidth - 8);
      const a2 = Math.min(y, window.innerHeight - menu.offsetHeight - 8);
      menu.style.left = Math.max(8, l2) + "px";
      menu.style.top = Math.max(8, a2) + "px";
    }).catch(() => {
      if (menu.classList.contains("oculto")) return;
      vazio.textContent = "(não consegui buscar sugestões)";
    });
  }
  // mostra antes de medir, e CORRIGE A POSIÇÃO se estiver perto da borda
  menu.classList.remove("oculto");
  menu.style.left = "0px"; menu.style.top = "0px";
  const l = Math.min(x, window.innerWidth - menu.offsetWidth - 8);
  const a = Math.min(y, window.innerHeight - menu.offsetHeight - 8);
  menu.style.left = Math.max(8, l) + "px";
  menu.style.top = Math.max(8, a) + "px";
  focoContextoRetorno = campo;
  const primeiro = menu.querySelector("button:not(:disabled)");
  if (primeiro) primeiro.focus({ preventScroll: true });
}

/* Troca um trecho do texto. `ini`/`fim` são índices do texto, não da
   seleção: por isso recuamos se a seleção cobre o trecho. */
function substituirTrecho(ini, fim, novo) {
  const campo = $("#entrada");
  const a = Math.min(ini, campo.selectionStart);
  const b = Math.max(fim, campo.selectionEnd);
  campo.focus();
  campo.setRangeText(novo, a, b, "end");
  ajustarAltura(); atualizarEnviar();
}

function substituirSelecao(novo) {
  const campo = $("#entrada");
  campo.focus();
  campo.setRangeText(novo, campo.selectionStart, campo.selectionEnd, "end");
  ajustarAltura(); atualizarEnviar();
}

async function colar(inicio, fim) {
  if (!navigator.clipboard || !navigator.clipboard.readText) {
    aviso("Para colar, use Ctrl+V.", true);
    return false;
  }
  try {
    const texto = await navigator.clipboard.readText();
    const campo = $("#entrada");
    campo.focus();
    campo.setRangeText(texto, inicio, fim, "end");
    ajustarAltura(); atualizarEnviar();
    return true;
  } catch (_e) {
    aviso("Não consegui acessar a área de transferência. Use Ctrl+V.", true);
    return false;
  }
}

/* O Chromium (e o WebView2) NÃO movem o cursor quando se clica com o
   botão direito. Sem isto, o menu de correção abriria sempre em cima da
   ÚLTIMA letra digitada, e não da palavra que o Wolf clicou — que é
   exatamente o defeito que o programa antigo não tinha. */
function indiceTextareaNoPonto(campo, x, y) {
  const texto = campo.value;
  if (!texto || texto.length > 3000) return campo.selectionStart;
  const ret = campo.getBoundingClientRect();
  const estilo = getComputedStyle(campo);
  const espelho = el("div");
  ["font", "lineHeight", "letterSpacing", "wordSpacing", "textAlign", "textIndent",
    "direction", "padding", "border", "tabSize"].forEach((p) => { espelho.style[p] = estilo[p]; });
  espelho.style.cssText += ";position:fixed;visibility:hidden;pointer-events:none;overflow:hidden;" +
    "white-space:pre-wrap;overflow-wrap:break-word;word-wrap:break-word;box-sizing:border-box;" +
    "margin:0;left:" + (ret.left - campo.scrollLeft) + "px;top:" + (ret.top - campo.scrollTop) +
    "px;width:" + ret.width + "px;height:" + ret.height + "px";
  const noTexto = document.createTextNode(texto);
  espelho.append(noTexto);
  document.body.append(espelho);
  const faixa = document.createRange();
  const alturaLinha = parseFloat(estilo.lineHeight) || parseFloat(estilo.fontSize) * 1.5;
  let melhor = campo.selectionStart, menorDistancia = Infinity;
  for (let i = 0; i <= texto.length; i++) {
    faixa.setStart(noTexto, i);
    faixa.collapse(true);
    const r = faixa.getBoundingClientRect();
    if (!r.height) continue;
    const dy = Math.abs((r.top + r.height / 2) - y);
    const dx = x < r.left ? r.left - x : x > r.left ? x - r.left : 0;
    const distancia = dy * Math.max(2, alturaLinha) + dx;
    if (distancia < menorDistancia) { menorDistancia = distancia; melhor = i; }
  }
  espelho.remove();
  return melhor;
}

function cursorNoClique(campo, x, y) {
  try {
    if (document.caretRangeFromPoint) {
      const r = document.caretRangeFromPoint(x, y);
      if (r && campo.contains(r.startContainer)) return r.startOffset;
    }
  } catch (_e) { /* sem suporte: fica onde estava */ }
  return indiceTextareaNoPonto(campo, x, y);
}

function ligarMenuContexto() {
  const campo = $("#entrada");
  campo.addEventListener("contextmenu", (e) => {
    e.preventDefault();
    if (campo.selectionStart === campo.selectionEnd) {
      const pos = Math.min(cursorNoClique(campo, e.clientX, e.clientY),
                           campo.value.length);
      campo.setSelectionRange(pos, pos);
    }
    mostrarMenuContexto(e.clientX, e.clientY);
  });
  document.addEventListener("mousedown", (e) => {
    if (!e.target.closest("#menu-contexto")) fecharMenuContexto(false);
  });
  window.addEventListener("blur", () => fecharMenuContexto(false));
  const menu = $("#menu-contexto");
  menu.addEventListener("keydown", (e) => {
    const itens = [...menu.querySelectorAll("button:not(:disabled)")];
    if (e.key === "Escape") {
      e.preventDefault(); fecharMenuContexto(true); return;
    }
    if (!itens.length || !["ArrowDown", "ArrowUp", "Home", "End"].includes(e.key)) return;
    e.preventDefault();
    let idx = itens.indexOf(document.activeElement);
    if (e.key === "Home") idx = 0;
    else if (e.key === "End") idx = itens.length - 1;
    else idx = (idx + (e.key === "ArrowDown" ? 1 : -1) + itens.length) % itens.length;
    itens[idx].focus();
  });
  // copiar texto selecionado na RESPOSTA da IA (botao direito)
  document.addEventListener("contextmenu", (e) => {
    const sel = (window.getSelection() || "").toString();
    if (sel.trim() && e.target && e.target.closest && e.target.closest(".corpo")) {
      e.preventDefault();
      escreverClipboard(sel).then((copiou) => {
        aviso(copiou ? "Texto copiado." : "Não consegui copiar o texto.", !copiou);
      });
    }
  });
}

/* ---------------- resumo do dia ----------------
   Um clique e a tela já pergunta as notícias de hoje. Existe como botão e
   como atalho (Ctrl+D) porque é o que se pergunta TODO dia — não faz
   sentido obrigar a digitar a mesma frase sempre. */
const PERGUNTA_RESUMO =
  "Me faz um resumo das notícias mais importantes de hoje no Brasil e no mundo. " +
  "Em tópicos curtos, e no fim diga de onde você tirou.";

function resumoDoDia() {
  if (estado.ocupado) return aviso("Espere a resposta terminar.", true);
  $("#entrada").value = PERGUNTA_RESUMO;
  ajustarAltura();
  atualizarEnviar();
  enviar(PERGUNTA_RESUMO);
}

/* ---------------- perguntas para continuar ----------------
   Um BOTAO, e nao automatico: cada sugestao gasta uma chamada de IA
   (ver `sugerir` no Python). Clicando, aparecem 3 perguntas curtinhas
   sobre o mesmo assunto; clicar em uma manda a pergunta. */
function botaoSugerir() {
  const b = el("button", "sugerir-btn");
  b.setAttribute("aria-label", "Sugerir perguntas para continuar a conversa");
  b.append(ico("i-brilho"), el("span", "", "outras perguntas"));
  const caixa = el("div", "sugestoes oculto");
  b.addEventListener("click", async (e) => {
    e.stopPropagation();
    if (!caixa.classList.contains("oculto")) {
      caixa.classList.add("oculto");
      return;
    }
    if (estado.sugerindo) return;
    estado.sugerindo = true;
    b.classList.add("carregando");
    const r = await chamar("sugerir", estado.ultimaPergunta || "",
                           estado.ultimaResposta || "");
    estado.sugerindo = false;
    b.classList.remove("carregando");
    if (r.erro) return aviso(r.erro === "sem_chave"
      ? "Cole a sua chave de API antes de pedir sugestões." : r.erro, true);
    caixa.replaceChildren();
    for (const p of r.perguntas || []) {
      const chip = el("button", "sugestao", p);
      chip.setAttribute("role", "button");
      chip.setAttribute("aria-label", "Pergunta sugerida: " + p);
      chip.addEventListener("click", () => {
        caixa.classList.add("oculto");
        $("#entrada").value = p;
        ajustarAltura();
        atualizarEnviar();
        enviar(p);
      });
      chip.addEventListener("keydown", (e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          chip.click();
        }
      });
      caixa.append(chip);
    }
    caixa.classList.remove("oculto");
  });
  const li = el("div", "linha-sugerir");
  li.append(b, caixa);
  return li;
}

/* ---------------- sites consultados ----------------
   A letra discreta embaixo da resposta (ideia 1 da IDEIAS.md). Clicar
   abre a lista, e cada site abre no navegador.

   IMPORTANTE: estes sao os resultados da BUSCA, nao citacoes. O
   programa nao confere se o que o site diz e' verdade - por isso o
   texto e' "sites consultados" e o link esta ali para o Wolf conferir
   com os proprios olhos. */
function linhaFontes(fontes) {
  const lista = (fontes || []).filter((f) => f && f.url);
  if (!lista.length) return el("span");
  const caixa = el("div", "fontes");
  const botao = el("button", "ver-fontes");
  botao.append(ico("i-globo"), el("span", "", `sites consultados: ${lista.length}`));
  const ul = el("div", "lista-fontes oculto");
  for (const f of lista) {
    const a = el("a", "", f.titulo || f.url);
    a.href = f.url;
    a.target = "_blank";
    a.rel = "noopener noreferrer";
    a.title = f.url;
    a.addEventListener("click", (e) => {
      e.preventDefault();
      e.stopPropagation();
      chamar("abrir_link", f.url);
    });
    ul.append(a);
  }
  botao.addEventListener("click", (e) => {
    e.stopPropagation();
    ul.classList.toggle("oculto");
  });
  caixa.append(botao, ul);
  return caixa;
}

/* ---------------- espera / envio ---------------- */
function esperar(ligado, texto) {
  estado.ocupado = ligado;
  $("#digitando").classList.toggle("oculto", !ligado);
  if (ligado) $("#etapa").textContent = texto || "Pensando...";
  atualizarEnviar();
  if (ligado) rolarParaOFim();
}
function atualizarEnviar() {
  $("#btn-enviar").disabled = estado.ocupado || !$("#entrada").value.trim();
  $("#btn-serio").disabled = estado.ocupado || !$("#entrada").value.trim();
}
function ajustarAltura() {
  const e = $("#entrada");
  e.style.height = "auto";
  e.style.height = Math.min(e.scrollHeight, 200) + "px";
}

/* O Python devolve a chamada de `enviar` e manda os eventos logo depois.
   A promise normalmente volta antes do primeiro evento, mas nao e
   garantido: se a IA falhar na hora (chave invalida, internet caiu), o
   evento de erro pode chegar antes. Guardar os eventos ate a pergunta
   entrar na tela garante a ordem - pergunta, depois resposta/erro. Sem
   isso o "pensando" ficaria aceso para sempre quando o erro chegasse
   primeiro. */
let eventosSegurados = null;

function segurarEventos(ligado) {
  if (ligado) {
    eventosSegurados = [];
    return;
  }
  const guardados = eventosSegurados || [];
  eventosSegurados = null;
  for (const o of guardados) aplicarEvento(o);
}

function aplicarEvento(o) {
  if (o.tipo === "etapa") {
    $("#etapa").textContent = o.texto;
  } else if (o.tipo === "resposta") {
    esperar(false);
    estado.ultimaResposta = o.texto;
    anexarMensagem({ role: "model", text: o.texto, fontes: o.fontes });
  } else if (o.tipo === "erro") {
    esperar(false);
    anexarMensagem({ role: "erro", text: o.texto });
    if (o.chave) abrirConfig("chaves");
  } else if (o.tipo === "conversas") {
    estado.conversas = o.conversas;
    estado.atual = o.atual;
    desenharConversas();
  } else if (o.tipo === "gravando") {
    mostrarGravando(o.ligado);
  } else if (o.tipo === "voz") {
    // o texto falado NAO e' enviado sozinho: entra na caixa de digitar
    // para o Wolf conferir antes (igual ao programa antigo)
    esperar(false);
    const caixa = $("#entrada");
    if (o.texto) {
      caixa.value = caixa.value ? caixa.value + " " + o.texto : o.texto;
      ajustarAltura();
      atualizarEnviar();
      caixa.focus();
      const fim = caixa.value.length;
      caixa.setSelectionRange(fim, fim);
      aviso("Pronto! Confira o texto e aperte Enter para enviar.");
      if (o.enviar) setTimeout(() => enviar(), 400);
    } else {
      aviso("Não consegui entender o áudio. Tente falar mais perto do microfone.", true);
    }
  } else if (o.tipo === "voz_erro") {
    esperar(false);
    aviso(o.texto || "Não consegui transcrever o áudio.", true);
    if (o.chave) abrirConfig("chaves");
  } else if (o.tipo === "imagens") {
    // "imagens de lobos" NAO vai para a IA: o Python busca as fotos e
    // manda aqui, ja com as miniaturas em base64.
    esperar(false);
    desenharGaleria(o);
  }
}

/* ---------------- galeria de imagens ----------------
   A grade de miniaturas fica dentro da conversa, embaixo da resposta,
   como no programa antigo. Clicar em uma abre a foto grande numa janela
   propria (a grande NAO vem junto: viria em megabytes e travaria a tela,
   entao a tela pede uma por vez com `imagem_ampliada`).
   A foto grande ja foi baixada em segundo plano enquanto o Wolf lia a
   resposta, entao aparece quase na hora. */
function desenharGaleria(o) {
  const fotos = (o && o.fotos) || [];
  if (!fotos.length) return;
  // Sem bolha onde colocar (a tela recarregou no meio da busca): cria
  // uma, para as fotos nao sumirem.
  if (!estado.ultimaBolha || !document.body.contains(estado.ultimaBolha)) {
    anexarMensagem({ role: "model", text: o.texto || "Imagens" });
  }
  const corpo = estado.ultimaBolha.querySelector(".corpo") ||
                estado.ultimaBolha;

  const tit = el("div", "galeria-titulo", o.texto || "Imagens");
  const grade = el("div", "galeria");
  fotos.forEach((f, i) => {
    const b = el("button", "foto");
    b.title = f.titulo || "Abrir a foto";
    const img = document.createElement("img");
    img.src = f.miniatura;
    img.alt = f.titulo || "Foto " + (i + 1);
    img.loading = "lazy";
    b.append(img);
    b.addEventListener("click", () => ampliarFoto(i, f, fotos));
    grade.append(b);
  });
  // antes das acoes ("copiar / salvar / outras perguntas"): as fotos
  // fazem parte da RESPOSTA, e as acoes ficam por ultimo.
  const acoes = corpo.querySelector(".acoes");
  if (acoes) corpo.insertBefore(tit, acoes);
  else corpo.append(tit);
  if (acoes) corpo.insertBefore(grade, acoes);
  else corpo.append(grade);
  rolarParaOFim();
}

/* ---------------- ver as fotos uma a uma ----------------
   O Wolf pediu para passar para a foto seguinte sem ter que diminuir e
   clicar na outra. A tela de foto aberta e' entao um VISOR com varias
   fotos: nao fecha a cada troca, so troca o que esta aparecendo.

   Tres jeitos de passar para a outra, porque nao ha um jeito certo:
   - as setas do teclado (← →), que o Wolf ja usa para tudo;
   - um botao embaixo, com "3 de 9" para saber onde se esta;
   - arrastar a foto com o mouse, que e' o gesto mais natural.

   Arrastar e' implementado "de proprio": com tres fotos (pouco mais que
   o celular mostra), dois programinhas de posicao resolvem em
   milissegundos, sem clicar. Com muita foto, simular o arrasto no
   mouse arrancaria e soltaria a imagem do servidor — por isso acima de
   12 some o arrasto e ficam as setas e o botao. */
const FOTOS_COM_ARRASTO = 12;

let fotoAberta = null;   // {indice, total, fotos, mostrar, fechar}

function abrirVisorFotos(indice, fotos) {
  estado._visorTrigger = document.activeElement;
  if (fotoAberta) fotoAberta.fechar();
  const total = fotos.length;
  const tampa = el("div", "foto-aberta");
  tampa.setAttribute("role", "dialog");
  tampa.setAttribute("aria-modal", "true");
  tampa.setAttribute("aria-label", "Visualizador de fotos");
  const img = document.createElement("img");
  img.alt = "Foto ampliada";
  const carregando = el("div", "foto-carregando", "Abrindo a foto...");
  const fechar = el("button", "foto-fechar", "✕");
  fechar.title = "Fechar (Esc)";
  fechar.setAttribute("aria-label", "Fechar visualizador de fotos");
  const pagina = el("a", "foto-pagina", "ver a página da foto");
  pagina.target = "_blank";
  pagina.rel = "noopener noreferrer";

  // --- a barra de baixo: anterior, contagem, proxima, arrastar
  const barra = el("div", "foto-barra");
  const anterior = el("button", "foto-seta", "‹");
  anterior.title = "Foto anterior (seta para a esquerda)";
  anterior.setAttribute("aria-label", "Foto anterior");
  const proximo = el("button", "foto-seta", "›");
  proximo.title = "Próxima foto (seta para a direita)";
  proximo.setAttribute("aria-label", "Próxima foto");
  const conta = el("span", "foto-conta", "");
  const dica = el("span", "foto-dica", "");
  barra.append(anterior, conta, proximo, dica);

  function mostrar(novo) {
    if (novo < 0 || novo >= total) return;
    fotoAberta.indice = novo;
    const info = fotos[novo];
    conta.textContent = (novo + 1) + " de " + total;
    anterior.disabled = novo === 0;
    proximo.disabled = novo === total - 1;
    pagina.href = info.pagina || "#";
    pagina.classList.toggle("oculto", !info.pagina);
    img.alt = info.titulo || ("Foto " + (novo + 1));
    img.style.opacity = "0";
    mostrarAviso("Abrindo a foto...");
    chamar("imagem_ampliada", novo).then((r) => {
      if (!document.body.contains(tampa)) return;   // o Wolf ja fechou
      if (r && r.erro) {
        mostrarAviso(r.erro);
        return;
      }
      // some com o aviso AQUI. Sem esta linha, "Abrindo a foto..."
      // ficava escrito no meio da imagem para sempre (16/10/2026) —
      // o aviso e' tirado em mostrar(), mas nao quando a foto chega.
      esconderAviso();
      img.src = r.base64;
      img.style.opacity = "1";
      if (r.pagina) {
        pagina.href = r.pagina;
        pagina.classList.remove("oculto");
      }
    });
  }

  function mostrarAviso(texto) {
    carregando.textContent = texto;
    carregando.classList.remove("oculto");
    if (!carregando.isConnected) tampa.append(carregando);
  }

  function esconderAviso() {
    carregando.classList.add("oculto");
    if (carregando.parentElement) carregando.remove();
  }

  function terminar() {
    document.removeEventListener("keydown", teclas);
    document.removeEventListener("mousedown", mouseBaixo);
    document.removeEventListener("mousemove", arrastando);
    document.removeEventListener("mouseup", soltarMouse);
    if (foto) { foto.style.transform = ""; foto = null; }
    if (tampa.parentElement) tampa.remove();
    fotoAberta = null;
    if (estado._visorTrigger && typeof estado._visorTrigger.focus === "function") {
      try { estado._visorTrigger.focus(); } catch (_e) { /* elemento removido */ }
    }
    estado._visorTrigger = null;
  }

  anterior.addEventListener("click", () => mostrar(fotoAberta.indice - 1));
  proximo.addEventListener("click", () => mostrar(fotoAberta.indice + 1));
  fechar.addEventListener("click", terminar);
  tampa.addEventListener("click", (e) => {
    // clique no fundo (fora da foto e dos botoes) fecha; na foto,
    // avanca — que e' o que se espera ao clicar numa foto grande.
    if (e.target === tampa || e.target === img) {
      if (e.target === img && proximaExiste()) mostrar(fotoAberta.indice + 1);
      else terminar();
    }
  });

  function proximaExiste() {
    return fotoAberta && fotoAberta.indice < total - 1;
  }

  function teclas(e) {
    if (!document.body.contains(tampa)) return;
    if (e.key === "Escape") { terminar(); return; }
    if (e.key === "ArrowRight" || e.key === "ArrowDown") {
      e.preventDefault();
      mostrar(fotoAberta.indice + 1);
    } else if (e.key === "ArrowLeft" || e.key === "ArrowUp") {
      e.preventDefault();
      mostrar(fotoAberta.indice - 1);
    }
  }
  document.addEventListener("keydown", teclas);

  // --- arrastar com o mouse
  let arrasta = false;
  let x0 = 0, y0 = 0, terceiro = false, ultimo = null;
  let foto = null;
  let saiuPeloLado = false;

  function mouseBaixo(e) {
    if (!document.body.contains(tampa)) return;
    if (e.button !== 0) return;
    if (e.target.closest("button, a")) return;
    arrasta = true;
    terceiro = false;
    saiuPeloLado = false;
    ultimo = null;
    x0 = e.clientX;
    y0 = e.clientY;
    foto = img;
  }

  function arrastando(e) {
    if (!arrasta || !foto) return;
    const dx = e.clientX - x0;
    const dy = e.clientY - y0;
    foto.style.transition = "none";
    foto.style.transform = "translate(" + dx + "px," + dy * 0.22 + "px)";
    if (ultimo === null) ultimo = e.clientX;
    if (Math.abs(e.clientX - ultimo) > 18) {
      terceiro = true;
      ultimo = e.clientX;
    }
    saiuPeloLado = Math.abs(dx) > 130;
  }

  function soltarMouse() {
    if (!arrasta || !foto) return;
    arrasta = false;
    // 3 criterios, do mais forte para o mais fraco:
    // 1) andou de lado varias vezes -> vai para onde veio andando;
    // 2) puxou longe para o lado -> vai para la;
    // 3) so um arrasto curtinho -> proxima.
    let passo;
    if (terceiro) passo = (ultimo || x0) > x0 ? 1 : -1;
    else if (saiuPeloLado) passo = dxAtual() > 0 ? -1 : 1;
    else passo = 1;
    foto.style.transition = "transform .16s ease";
    if (passo < 0 && fotoAberta.indice > 0) mostrar(fotoAberta.indice - 1);
    else if (passo > 0 && fotoAberta.indice < total - 1) mostrar(fotoAberta.indice + 1);
    // volta pro lugar: e' o que faz a foto parecer que passou voando
    setTimeout(() => {
      if (foto) { foto.style.transform = ""; foto = null; }
    }, 20);
  }

  function dxAtual() {
    return foto ? foto.getBoundingClientRect().left -
        (tampa.getBoundingClientRect().left +
         (tampa.clientWidth - foto.offsetWidth) / 2) : 0;
  }

  if (total <= FOTOS_COM_ARRASTO) {
    document.addEventListener("mousedown", mouseBaixo);
    document.addEventListener("mousemove", arrastando);
    document.addEventListener("mouseup", soltarMouse);
    dica.textContent = "arraste ou use as setas para passar";
  } else {
    dica.textContent = "use as setas do teclado";
  }

  tampa.append(fechar, carregando, img, pagina, barra);
  document.body.append(tampa);
  fotoAberta = { indice, total, fotos, mostrar, fechar: terminar };
  mostrar(indice);
}

function ampliarFoto(indice, info, todas) {
  // chamada antiga (so uma foto): abre o visor com uma foto so
  if (!todas || !todas.length) return;
  abrirVisorFotos(indice, todas);
}

async function enviar(texto, profundo = estado.profundo) {
  texto = (texto !== undefined ? texto : $("#entrada").value).trim();
  if (!texto || estado.ocupado) return;
  // guardada para o botao "outras perguntas" (que pergunta a IA a partir
  // da ultima pergunta e da ultima resposta)
  estado.ultimaPergunta = texto;
  segurarEventos(true);
  let r = {};
  try {
    // O botão/atalho de pesquisa profunda pode forçar `true`; envios
    // comuns continuam respeitando o estado do botão de alternância.
    r = (await chamar("enviar", texto, !!profundo)) || {};
  } finally {
    // A pergunta entra na tela ANTES de soltar os eventos da IA.
    $("#entrada").value = "";
    ajustarAltura();
    anexarMensagem({ role: "user", text: texto });
    // Se ja veio erro, nao fica esperando resposta que nao vem.
    esperar(!r.erro, "Pensando...");
    segurarEventos(false);
  }
  if (r.erro) {
    if (r.erro === "sem_chave") {
      aviso("Cole a sua chave do Google nas Configurações para começar.");
      abrirConfig("chaves");
    } else aviso(r.erro, true);
  }
}

window.PIA = {
  __estado: estado,
  evento(o) {
    if (eventosSegurados) return eventosSegurados.push(o);
    aplicarEvento(o);
  },
};

/* ---------------- barra lateral ---------------- */
let menuAberto = null;
function fecharMenu() {
  if (!menuAberto) return;
  menuAberto.pop.remove();
  menuAberto.botao.classList.remove("aberto");
  menuAberto = null;
}

function abrirMenuConversa(botao, c) {
  const mesmo = menuAberto && menuAberto.botao === botao;
  fecharMenu();
  if (mesmo) return;
  const pop = el("div", "pop");
  // Fixar no topo: a conversa vai para o comeco da lista e fica la.
  const fixar = el("button", c.fixada ? "" : "");
  fixar.append(ico(c.fixada ? "i-soltar" : "i-fixar"),
               el("span", "", c.fixada ? "Soltar do topo" : "Fixar no topo"));
  fixar.addEventListener("click", async () => {
    fecharMenu();
    const r = await chamar("fixar_conversa", c.id);
    if (r.erro) return aviso(r.erro, true);
    estado.conversas = r.conversas || estado.conversas;
    desenharConversas();
    aviso(r.fixada ? "Conversa fixada no topo." : "Conversa solta.");
  });
  const pedir = el("button", "perigo");
  pedir.append(ico("i-lixo"), el("span", "", "Excluir"));
  pedir.addEventListener("click", () => {
    pop.replaceChildren(el("div", "texto", "Excluir esta conversa?"));
    pop.append(el("div", "nota", "O que o assistente aprendeu sobre você continua guardado."));
    const linha = el("div", "linha");
    const nao = el("button", "", "Cancelar");
    const sim = el("button", "perigo", "Excluir");
    nao.addEventListener("click", fecharMenu);
    sim.addEventListener("click", async () => {
      fecharMenu();
      await excluirConversa(c.id);
    });
    linha.append(nao, sim);
    pop.append(linha);
  });
  pop.append(fixar, pedir);
  document.body.append(pop);
  const r = botao.getBoundingClientRect();
  pop.style.left = Math.max(8, r.right - pop.offsetWidth) + "px";
  pop.style.top = r.bottom + 4 + "px";
  botao.classList.add("aberto");
  menuAberto = { pop, botao };
}
document.addEventListener("mousedown", (e) => {
  if (menuAberto && !menuAberto.pop.contains(e.target) && e.target.closest(".mais") !== menuAberto.botao) fecharMenu();
});
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") {
    fecharMenu();
    if (!$("#modal").classList.contains("oculto")) fecharConfig();
    return;
  }
  // Ctrl+M: microfone sem tirar a mao do teclado (como no programa antigo).
  // Nao enquanto a pessoa esta digitando um texto com Ctrl grudado, nem
  // se ja ha uma conversa rodando.
  if ((e.ctrlKey || e.metaKey) && (e.key === "m" || e.key === "M")) {
    e.preventDefault();
    alternarMicrofone();
    return;
  }
  // Ctrl+S: salva a ultima resposta em .txt (igual ao programa antigo).
  // Sem isso, o navegador abriria a janelinha de "Salvar pagina", que
  // e' branca e nao tem nada a ver com o programa.
  if ((e.ctrlKey || e.metaKey) && (e.key === "s" || e.key === "S")) {
    e.preventDefault();
    const ultima = [...document.querySelectorAll("#mensagens .msg.ia")].pop();
    if (!ultima) return aviso("Ainda não tem resposta para salvar.");
    const bruto = ultima.dataset.bruto || "";
    chamar("salvar_texto", bruto).then((r) => {
      if (r && r.caminho) aviso("Salvo em " + r.caminho);
      else if (r && r.erro) aviso(r.erro, true);
    });
    return;
  }
  // Ctrl+N: conversa nova. Ctrl+F: ir para a busca (o padrao do
  // navegador abriria a barra de endereco, que nao existe aqui).
  if ((e.ctrlKey || e.metaKey) && (e.key === "n" || e.key === "N")) {
    e.preventDefault();
    novaConversa();
    return;
  }
  if ((e.ctrlKey || e.metaKey) && (e.key === "f" || e.key === "F")) {
    e.preventDefault();
    // com a barra recolhida a busca nao aparece: mostrar ela primeiro
    if ($("#lateral").classList.contains("recolhida")) {
      $("#btn-abrir-lateral").click();
    }
    const campo = $("#campo-busca");
    campo.focus();
    campo.select();
    return;
  }
  // Ctrl +, / Ctrl - / Ctrl 0: tamanho da letra.
  if ((e.ctrlKey || e.metaKey) && (e.key === "=" || e.key === "+")) {
    e.preventDefault();
    mudarLetra(1);
    return;
  }
  if ((e.ctrlKey || e.metaKey) && (e.key === "-" || e.key === "_")) {
    e.preventDefault();
    mudarLetra(-1);
    return;
  }
  if ((e.ctrlKey || e.metaKey) && e.key === "0") {
    e.preventDefault();
    aplicarTamanho(15);
    return;
  }
  // Ctrl+D: resumo das notícias de hoje.
  if ((e.ctrlKey || e.metaKey) && (e.key === "d" || e.key === "D")) {
    e.preventDefault();
    resumoDoDia();
  }
});
document.addEventListener("click", (e) => {
  const link = e.target.closest("a[data-url]");
  if (link) {
    e.preventDefault();
    chamar("abrir_link", link.dataset.url);
  }
});

/* ---------------- conversa privada ----------------
   Ligada, o que for dito NAO e' salvo e a IA nao aprende nada. Quando
   liga ou desliga, comeca uma conversa nova de proposito: sem isso a
   pergunta seguinte gravaria a conversa inteira, incluindo a parte
   que o Wolf mandou nao guardar (ver `definir_privada` no Python). */
async function alternarPrivada() {
  const ligando = !estado.privada;
  const r = await chamar("definir_privada", ligando);
  if (r.erro) return aviso(r.erro, true);
  estado.privada = !!r.privada;
  estado.atual = r.atual ?? null;
  estado.mensagens = r.mensagens || [];
  estado.conversas = r.conversas || estado.conversas;
  mostrarPrivada();
  desenharConversas();
  desenharMensagens();
  $("#entrada").focus();
  aviso(ligando
    ? "Conversa privada ligada: isto não será salvo nem entra na memória."
    : "Conversa privada desligada: a partir de agora tudo é salvo de novo.");
}

function atualizarMenuModos() {
  const ativos = Number(!!estado.profundo) + Number(!!estado.privada);
  const menu = $("#menu-modos");
  const rotulo = $("#rotulo-modos");
  if (!menu || !rotulo) return;
  rotulo.textContent = ativos ? "Mais · " + ativos + " ativo(s)" : "Mais";
  menu.classList.toggle("tem-ativo", ativos > 0);
}

function mostrarPrivada() {
  const b = $("#btn-privada");
  b.classList.toggle("ligada", !!estado.privada);
  atualizarMenuModos();
  b.title = estado.privada
    ? "Conversa privada LIGADA: nada é salvo nem entra na memória (clique para desligar)"
    : "Conversa privada: o que for dito aqui não é salvo nem entra na sua memória (clique para ligar)";
  // marca a conversa na tela, para nunca ficar na duvida
  $("#titulo-conversa").classList.toggle("privada", !!estado.privada);
  $("#titulo-conversa").textContent = estado.privada
    ? "Conversa privada (não será salva)"
    : (() => {
        const primeira = estado.mensagens.find((m) => m.role === "user");
        return primeira ? primeira.text.slice(0, 70) : "";
      })();
}

/* ---------------- tamanho da letra ----------------
   Ctrl + (ou =) aumenta, Ctrl - diminui, Ctrl 0 volta ao normal. O
   tamanho fica guardado neste computador (localStorage), entao a tela
   ja abre do jeito que o Wolf deixou. Nao mexe em nada do Python nem
   dos arquivos: e' so aparencia. */
const TAMANHOS = [13, 14, 15, 16, 18, 20, 23, 26];

function tamanhoAtual() {
  const lido = parseInt(localStorage.getItem("pia_letra") || "15", 10);
  return TAMANHOS.includes(lido) ? lido : 15;
}

function aplicarTamanho(px) {
  if (!TAMANHOS.includes(px)) px = 15;
  document.body.style.fontSize = px + "px";
  document.documentElement.style.setProperty("--tamanho", px + "px");
  try { localStorage.setItem("pia_letra", String(px)); } catch (_e) { /* sem armazenamento */ }
  const rotulo = $("#rotulo-letra");
  if (rotulo) rotulo.textContent = px + "px";
}

function mudarLetra(passo) {
  let i = TAMANHOS.indexOf(tamanhoAtual());
  if (i < 0) i = TAMANHOS.indexOf(15);
  aplicarTamanho(TAMANHOS[Math.max(0, Math.min(TAMANHOS.length - 1, i + passo))]);
}

/* ---------------- procurar nas conversas ----------------
   O Python procura (sem acento e sem diferenciar maiuscula, porque o
   Wolf digita do jeito que lembra) e devolve onde achou. Aqui a tela
   mostra os resultados e, ao clicar, abre a conversa. */
function pintarTrecho(texto, termo) {
  const alvo = termo.trim().toLowerCase();
  if (alvo.length < 2) return document.createTextNode(texto);
  const i = texto.toLowerCase().indexOf(alvo);
  if (i < 0) return document.createTextNode(texto);
  const frag = document.createDocumentFragment();
  frag.append(document.createTextNode(texto.slice(0, i)));
  const m = el("mark", "", texto.slice(i, i + alvo.length));
  frag.append(m);
  frag.append(document.createTextNode(texto.slice(i + alvo.length)));
  return frag;
}

async function buscar(termo) {
  termo = termo.trim();
  const caixa = $("#resultados-busca");
  $("#btn-limpar-busca").classList.toggle("oculto", !termo);
  if (!termo) return caixa.replaceChildren();
  const r = await chamar("conversas_buscar", termo);
  // se o Wolf digitou mais coisa enquanto a busca rodava, esta resposta
  // ja nao interessa
  if ($("#campo-busca").value.trim() !== termo) return;
  caixa.replaceChildren();
  const achados = r.achados || [];
  if (!achados.length) {
    caixa.append(el("div", "nada", 'Nada encontrado com "' + termo + '".'));
    return;
  }
  for (const a of achados) {
    const b = el("button", "resultado");
    b.append(el("span", "rt", a.titulo));
    const p = el("span", "rp");
    p.append(pintarTrecho(a.trecho, termo));
    b.append(p);
    b.addEventListener("click", async () => {
      await abrirConversa(a.id);
      $("#campo-busca").value = "";
      $("#resultados-busca").replaceChildren();
      $("#btn-limpar-busca").classList.add("oculto");
      rolarParaOFim();
    });
    caixa.append(b);
  }
}

function desenharConversas() {
  const lista = $("#lista-conversas");
  lista.replaceChildren();
  if (!estado.conversas.length) {
    lista.append(el("div", "vazio-lista", "Nenhuma conversa ainda."));
    return;
  }
  for (const c of estado.conversas) {
    const item = el("div", "conv" + (c.id === estado.atual ? " ativa" : ""));
    const textos = el("div", "textos");
    textos.append(el("span", "t", c.titulo), el("span", "q", c.quando));
    const mais = el("button", "mais");
    mais.title = "Mais opções";
    mais.append(ico("i-pontos"));
    mais.addEventListener("click", (ev) => {
      ev.stopPropagation();
      abrirMenuConversa(mais, c);
    });
    item.append(textos, mais);
    item.addEventListener("click", () => abrirConversa(c.id));
    lista.append(item);
  }
}

async function abrirConversa(id) {
  if (estado.ocupado) return aviso("Espere a resposta terminar.", true);
  const r = await chamar("abrir_conversa", id);
  if (r.erro) return aviso(r.erro, true);
  estado.mensagens = r.mensagens;
  estado.atual = r.atual;
  desenharConversas();
  desenharMensagens();
}
async function novaConversa() {
  if (estado.ocupado) return aviso("Espere a resposta terminar.", true);
  const r = await chamar("nova_conversa");
  if (r.erro) return aviso(r.erro, true);
  estado.mensagens = [];
  estado.atual = r.atual;
  desenharConversas();
  desenharMensagens();
  $("#entrada").focus();
}
async function excluirConversa(id) {
  const r = await chamar("excluir_conversa", id);
  if (r.erro) return aviso(r.erro, true);
  estado.conversas = r.conversas;
  if (r.era_atual) {
    estado.mensagens = [];
    estado.atual = r.atual;
    desenharMensagens();
  }
  desenharConversas();
  aviso("Conversa excluída.");
}

/* ---------------- configurações ---------------- */
function linhaToggle(titulo, desc, chave) {
  const l = el("div", "linha-opcao");
  const t = el("div");
  t.append(el("b", "", titulo), el("span", "", desc));
  const sw = el("label", "chave-liga");
  const i = el("input");
  i.type = "checkbox";
  i.checked = !!estado.rascunho[chave];
  i.addEventListener("change", () => (estado.rascunho[chave] = i.checked));
  sw.append(i, el("i"));
  l.append(t, sw);
  return l;
}

function abaConversa(corpo) {
  corpo.append(el("h3", "", "Conversa"), el("p", "sub", "Como o assistente conversa com você."));
  const caixa = el("div", "cartao");
  const sel = el("select");
  for (const [v, rot] of [["auto", "Automática (recomendado)"], ["sempre", "Sempre pesquisar"], ["nunca", "Nunca pesquisar"]]) {
    const o = el("option", "", rot);
    o.value = v;
    sel.append(o);
  }
  sel.value = estado.rascunho.modo_pesquisa;
  sel.addEventListener("change", () => (estado.rascunho.modo_pesquisa = sel.value));
  const l = el("div", "linha-opcao");
  const t = el("div");
  t.append(el("b", "", "Pesquisa na web"), el("span", "", "No automático, ele decide sozinho: papo normal não vira pesquisa."));
  l.append(t, sel);
  caixa.append(
    l,
    linhaTamalho(),
    linhaToggle("Lembrar o assunto da conversa", "Permite perguntas de acompanhamento.", "usar_contexto"),
    linhaToggle("Aprender sozinho com as conversas", "Guarda gostos e hábitos (sem repetir o que já sabe).", "aprender"),
    linhaToggle("Corretor ortográfico", "Sublinha palavras erradas na caixa de digitar.", "web_corretor"),
    linhaToggle("Enviar sozinho depois de falar", "Para quando o microfone estiver ligado.", "voz_enviar")
  );
  corpo.append(caixa, cartaoBackup());
}

/* Cópia de segurança dos dados, dentro do próprio programa: e' o mesmo
   que o `9 - Fazer backup dos meus dados.bat`, so que com um clique e
   sem sair da tela. */
function cartaoBackup() {
  const c = el("div", "cartao");
  c.append(el("h4", "", "Cópia de segurança dos seus dados"));
  c.append(el("p", "desc", "Guarda as conversas, a memória e as chaves num arquivo .zip dentro do OneDrive. Só lê e copia: não muda nada."));
  const b = el("button", "btn", "Fazer cópia agora");
  const onde = el("p", "nota-backup");
  b.addEventListener("click", async () => {
    b.disabled = true;
    b.textContent = "Copiando...";
    onde.textContent = "";
    const r = await chamar("fazer_backup");
    b.disabled = false;
    b.textContent = "Fazer cópia agora";
    if (r.erro) return aviso(r.erro, true);
    onde.textContent = "Cópia feita: " + r.arquivos + " arquivo(s).";
    aviso("Cópia de segurança feita.");
  });
  c.append(b, onde);
  return c;
}

/* A letra da tela. Tem botão aqui E atalho (Ctrl +, Ctrl - e Ctrl 0),
   para ninguem ter que decorar atalho para aumentar a letra. */
function linhaTamalho() {
  const l = el("div", "linha-opcao");
  const t = el("div");
  t.append(el("b", "", "Tamanho da letra"),
           el("span", "", "Deixa a conversa mais fácil de ler."));
  const grupo = el("div", "grupo-letra");
  const menos = el("button", "btn letra", "A−");
  menos.title = "Diminuir a letra (Ctrl -)";
  menos.addEventListener("click", () => mudarLetra(-1));
  const rotulo = el("span", "rotulo-letra");
  rotulo.id = "rotulo-letra";
  const mais = el("button", "btn letra", "A+");
  mais.title = "Aumentar a letra (Ctrl +)";
  mais.addEventListener("click", () => mudarLetra(1));
  const normal = el("button", "btn", "Normal");
  normal.title = "Voltar ao tamanho normal (Ctrl 0)";
  normal.addEventListener("click", () => aplicarTamanho(15));
  grupo.append(menos, rotulo, mais, normal);
  l.append(t, grupo);
  return l;
}

function cartaoChave(titulo, desc, campo, info, opc) {
  const c = el("div", "cartao" + (opc.destaque ? " cartao-destaque" : ""));
  c.append(el("h4", "", titulo), el("p", "desc", desc));
  if (opc.controle) {
    c.append(linhaToggle(opc.controle.titulo, opc.controle.desc, opc.controle.chave));
  }
  const linha = el("div", "campo");
  const inp = el("input");
  inp.type = "password";
  inp.autocomplete = "off";
  inp.spellcheck = false;
  inp.dataset.campo = campo;
  inp.value = (estado.rascunho.chaves && estado.rascunho.chaves[campo]) || "";
  inp.addEventListener("input", () => {
    if (!estado.rascunho.chaves) estado.rascunho.chaves = {};
    if (inp.value.trim()) estado.rascunho.chaves[campo] = inp.value;
    else delete estado.rascunho.chaves[campo];
  });
  inp.placeholder = info.definida ? "Salva (termina em " + info.final + "). Cole outra para trocar." : "Cole a chave aqui";
  const ver = el("button", "btn", "Mostrar");
  ver.addEventListener("click", () => {
    inp.type = inp.type === "password" ? "text" : "password";
    ver.textContent = inp.type === "password" ? "Mostrar" : "Ocultar";
  });
  linha.append(inp, ver);
  const st = el("div", "estado-chave", info.definida ? "Chave salva neste computador." : "Sem chave ainda.");
  if (info.definida) st.classList.add("ok");
  if (opc.testar) {
    const t = el("button", "btn", "Testar");
    t.addEventListener("click", async () => {
      st.className = "estado-chave";
      st.textContent = "Testando...";
      const r = await chamar("testar_chave", campo, inp.value.trim());
      st.className = "estado-chave " + (r.ok ? "ok" : "ruim");
      st.textContent = r.ok ? "Funcionou!" : r.texto || "A chave não funcionou.";
    });
    linha.append(t);
  }
  c.append(linha, st);
  if (opc.passos) c.append(el("div", "passos", opc.passos));
  if (opc.pagina) {
    const b = el("button", "btn", "Como conseguir a chave");
    b.style.marginTop = "10px";
    b.addEventListener("click", () => chamar("abrir_link", opc.pagina));
    c.append(b);
  }
  return c;
}

function abaChaves(corpo) {
  const cfg = estado.cfgTela;
  corpo.append(
    cartaoChave("Google Gemini (principal)", "Modelo principal: responde às perguntas e faz pesquisas. A chave fica guardada neste computador.", "api_key", cfg.gemini, {
      destaque: true,
      testar: true,
      pagina: "https://aistudio.google.com/apikey",
      controle: {
        titulo: "Usar o Gemini (principal)",
        desc: "Desliga o Gemini e usa só o plano B (ChatGPT/Groq/OpenRouter).",
        chave: "usar_gemini",
      },
    }),
    cartaoChave("Google Gemini (reserva, opcional)", "Alternativa automática caso o Gemini principal falhe. Não é obrigatório configurar.", "api_key_reserva", cfg.gemini_reserva, { testar: true })
  );
  const plano = el("div", "cartao");
  plano.append(linhaToggle("Usar o plano B", "Se o Gemini não responder, tenta estes serviços de reserva.", "usar_plano_b"));
  corpo.append(plano);
  for (const s of cfg.servicos) {
    corpo.append(cartaoChave(s.nome, s.resumo ? "Grátis: " + s.resumo : "", s.campo, s, { passos: s.passos, pagina: s.pagina }));
  }
}

async function abaMemoria(corpo) {
  corpo.append(el("h3", "", "Memória"), el("p", "sub", "O que o assistente aprendeu sobre você. Ele usa isso sozinho e nunca comenta que guardou."));
  const r = await chamar("memoria_listar");
  if (estado.aba !== "memoria") return;
  let fatos = r.fatos || [];
  let datas = r.datas || {};
  // Toda mudanca na memoria traz as datas junto, senao a data da tela
  // ficaria velha depois de adicionar ou apagar um item.
  const pegar = (rr) => {
    if (rr.fatos) fatos = rr.fatos;
    if (rr.datas) datas = rr.datas;
  };
  const gavetas = r.gavetas || {};
  let filtroGaveta = ""; // "" = todos
  let filtroAssunto = ""; // "" = todos
  const gavetasEl = el("div", "gavetas gavetas-filtro");
  const allBtn = el("button", "badge-gaveta ativo", "todos · " + fatos.length);
  allBtn.title = "Mostrar todas as gavetas";
  allBtn.addEventListener("click", () => { filtroGaveta = ""; pintarativo(); desenhar(); });
  gavetasEl.append(allBtn);
  for (const k of ["nome", "mora", "idade", "outros"]) {
    if (gavetas[k] && gavetas[k].length) {
      const b = el("button", "badge-gaveta", k + " · " + gavetas[k].length);
      b.dataset.gaveta = k;
      b.addEventListener("click", () => {
        filtroGaveta = (filtroGaveta === k ? "" : k);
        pintarativo(); desenhar();
      });
      gavetasEl.append(b);
    }
  }
  const pintarativo = () => {
    gavetasEl.querySelectorAll(".badge-gaveta").forEach((b) => {
      if (b.dataset.gaveta === undefined) {
        b.classList.toggle("ativo", filtroGaveta === "");
      } else {
        b.classList.toggle("ativo", filtroGaveta === b.dataset.gaveta);
      }
    });
  };
  const assuntos = r.assuntos || {};
  const assuntosEl = el("div", "gavetas gavetas-filtro");
  const allAss = el("button", "badge-gaveta ativo", "todos (assunto) · " + fatos.length);
  allAss.title = "Mostrar todos os assuntos";
  allAss.addEventListener("click", () => { filtroAssunto = ""; pintarAss(); desenhar(); });
  assuntosEl.append(allAss);
  for (const k of Object.keys(assuntos)) {
    const b = el("button", "badge-gaveta", k + " · " + assuntos[k].length);
    b.dataset.assunto = k;
    b.addEventListener("click", () => {
      filtroAssunto = (filtroAssunto === k ? "" : k);
      pintarAss(); desenhar();
    });
    assuntosEl.append(b);
  }
  const pintarAss = () => {
    assuntosEl.querySelectorAll(".badge-gaveta").forEach((b) => {
      if (b.dataset.assunto === undefined) {
        b.classList.toggle("ativo", filtroAssunto === "");
      } else {
        b.classList.toggle("ativo", filtroAssunto === b.dataset.assunto);
      }
    });
  };
  // --- visualizacao agrupada por gaveta (secoes recolhiveis) ---
  const agruparBtn = el("button", "btn", "Agrupar");
  agruparBtn.title = "Mostra as gavetas como secoes recolhiveis";
  let modoAgrupado = false;
  agruparBtn.addEventListener("click", () => {
    modoAgrupado = !modoAgrupado;
    agruparBtn.textContent = modoAgrupado ? "Lista" : "Agrupar";
    agruparBtn.title = modoAgrupado
      ? "Volta para a lista simples"
      : "Mostra as gavetas como secoes recolhiveis";
    desenhar();
  });

  const secoes = el("div", "gavetas-secoes");
  const desenharSecoes = () => {
    secoes.replaceChildren();
    if (!modoAgrupado) { secoes.classList.add("oculto"); return; }
    secoes.classList.remove("oculto");
    const termo = busca.value.trim().toLowerCase();
    const nomes = ["nome", "mora", "idade", "outros"];
    for (const g of nomes) {
      const fatosG = (gavetas[g] || []).filter((f) =>
        !termo || f.toLowerCase().includes(termo));
      if (!fatosG.length) continue;
      const det = el("details", "gaveta-secao");
      det.open = true;
      const sum = el("summary", "gaveta-titulo");
      sum.append(el("span", "", g + " (" + fatosG.length + ")"));
      det.append(sum);
      const listaG = el("div", "gaveta-lista");
      for (const f of fatosG) {
        const linha = el("div", "fato fato-compacto");
        const texto = el("span", "editavel", f);
        texto.title = "Clique para editar";
        texto.addEventListener("click", () => {
          if (linha.classList.contains("editando")) return;
          linha.classList.add("editando");
          const caixa = el("input", "edicao");
          caixa.value = f;
          const ok = el("button", "btn primario", "Salvar");
          const cancelar = el("button", "btn", "Cancelar");
          ok.addEventListener("click", async () => {
            const novoTexto = caixa.value.trim();
            if (!novoTexto) return aviso("O item não pode ficar vazio.", true);
            const rr = await chamar("memoria_editar", f, novoTexto);
            if (rr.erro) return aviso(rr.erro, true);
            pegar(rr);
            aviso("Item editado.");
            desenhar();
          });
          cancelar.addEventListener("click", () => desenhar());
          caixa.addEventListener("keydown", (e) => {
            if (e.key === "Enter") { e.preventDefault(); ok.click(); }
            if (e.key === "Escape") { e.preventDefault(); desenhar(); }
          });
          linha.replaceChildren(caixa, ok, cancelar);
          caixa.focus();
          caixa.setSelectionRange(caixa.value.length, caixa.value.length);
        });
        const x = el("button", "icone");
        x.title = "Apagar este item";
        x.append(ico("i-fechar"));
        x.addEventListener("click", async () => {
          const rr = await chamar("memoria_apagar", f);
          pegar(rr); desenhar();
        });
        const quando = (datas || {})[f];
        if (quando) linha.append(el("span", "quando", "aprendeu em " + quando));
        linha.append(texto, x);
        listaG.append(linha);
      }
      const addG = el("button", "btn", "+ Adicionar em " + g);
      addG.addEventListener("click", () => {
        const val = prompt("Novo fato para a gaveta " + g + ":");
        if (val && val.trim()) {
          chamar("memoria_adicionar", val.trim()).then((rr) => {
            if (rr.fatos) { fatos = rr.fatos; }
            if (rr.datas) datas = rr.datas;
            desenhar();
          });
        }
      });
      det.append(listaG, addG);
      secoes.append(det);
    }
  };

  const topo = el("div", "memoria-topo");
  const busca = el("input", "busca");
  busca.placeholder = "Buscar na memória...";
  busca.spellcheck = false;
  const organizar = el("button", "btn", "Organizar");
  organizar.title = "Junta fatos repetidos";
  const exportar = el("button", "btn", "Exportar");
  exportar.title = "Salva a memória num .txt";
  const apagarTudo = el("button", "btn perigo", "Apagar tudo");
  topo.append(busca, organizar, exportar, apagarTudo, agruparBtn);
  exportar.addEventListener("click", async () => {
    const rr = await chamar("memoria_exportar");
    if (rr.erro) aviso(rr.erro, true);
  });
  const novo = el("div", "adicionar");
  const campo = el("input");
  // O limite e' de verdade (o memoria.py corta em 200). Avisar ANTES
  // e' melhor do que o item ser cortado pela metade sem ninguem ver.
  const LIMITE = 200;
  campo.placeholder = "Adicionar algo que ele deve saber sobre você...";
  const restam = el("span", "restam");
  restam.title = `Cada item pode ter até ${LIMITE} letras`;
  const add = el("button", "btn primario", "Adicionar");
  novo.append(campo, add, restam);
  const avisarResto = () => {
    const n = LIMITE - campo.value.trim().length;
    restam.textContent = campo.value.trim() ? (n >= 0 ? n + " letras restantes" : "passou " + -n + " do limite") : "";
    restam.classList.toggle("ruim", n < 0);
  };
  const contador = el("div", "contador");
  const lista = el("div");
  const desenhar = () => {
    lista.replaceChildren();
    const termo = busca.value.trim().toLowerCase();
    const daGaveta = filtroGaveta ? (gavetas[filtroGaveta] || []) : fatos;
    const daAssunto = filtroAssunto ? (assuntos[filtroAssunto] || []) : daGaveta;
    const vistos = daAssunto.filter((f) => !termo || f.toLowerCase().includes(termo));    contador.textContent = fatos.length + (fatos.length === 1 ? " item guardado" : " itens guardados");
    if (!vistos.length) lista.append(el("div", "vazio-lista", fatos.length ? "Nada encontrado." : "Ainda não guardou nada."));
    for (const f of vistos) {
      const linha = el("div", "fato");
      const x = el("button", "icone");
      x.title = "Apagar este item";
      x.append(ico("i-fechar"));
      x.addEventListener("click", async () => {
        const rr = await chamar("memoria_apagar", f);
        pegar(rr); desenhar();
      });
      // A data em que o fato foi aprendido. Fato antigo (guardado antes
      // das datas existirem) fica sem data — e a tela mostra isso, em vez
      // de inventar um dia.
      const quando = (datas || {})[f];
      if (quando) linha.append(el("span", "quando", "aprendeu em " + quando));
      // Clicar no TEXTO edita na hora (a Tarefa D pede "editar: clique no
      // texto"). Nao abro uma janelinha: edita-se aqui mesmo, e so grava
      // quando o Wolf confirmar.
      const texto = el("span", "editavel", f);
      texto.title = "Clique para editar";
      texto.addEventListener("click", () => {
        if (linha.classList.contains("editando")) return;
        linha.classList.add("editando");
        const caixa = el("input", "edicao");
        caixa.value = f;
        const ok = el("button", "btn primario", "Salvar");
        const cancelar = el("button", "btn", "Cancelar");
        ok.addEventListener("click", async () => {
          const novoTexto = caixa.value.trim();
          if (!novoTexto) return aviso("O item não pode ficar vazio.", true);
          const rr = await chamar("memoria_editar", f, novoTexto);
          if (rr.erro) return aviso(rr.erro, true);
          pegar(rr);
          aviso("Item editado.");
          desenhar();
        });
        cancelar.addEventListener("click", () => desenhar());
        caixa.addEventListener("keydown", (e) => {
          if (e.key === "Enter") { e.preventDefault(); ok.click(); }
          if (e.key === "Escape") { e.preventDefault(); desenhar(); }
        });
        const alerta = el("span", "alerta-edicao");
        const ver = () => {
          const n = LIMITE - caixa.value.trim().length;
          alerta.textContent = caixa.value.trim() && n < 0 ? "passou " + -n + " do limite" : "";
        };
        caixa.addEventListener("input", ver);
        linha.replaceChildren(caixa, ok, cancelar, alerta);
        caixa.focus();
        caixa.setSelectionRange(caixa.value.length, caixa.value.length);
      });
      linha.append(texto, x);
      lista.append(linha);
    }
  };
  busca.addEventListener("input", () => { desenhar(); desenharSecoes(); });
  const adicionar = async () => {
    if (!campo.value.trim()) return;
    const rr = await chamar("memoria_adicionar", campo.value.trim());
    if (rr.fatos) { fatos = rr.fatos; campo.value = ""; }
    if (rr.datas) datas = rr.datas;
    desenhar();
  };
  add.addEventListener("click", adicionar);
  campo.addEventListener("input", avisarResto);
  campo.addEventListener("keydown", (e) => { if (e.key === "Enter") adicionar(); });
  organizar.addEventListener("click", async () => {
    const rr = await chamar("memoria_organizar");
    if (rr.fatos) {
      aviso(rr.mudou ? "Memória organizada: repetidos foram juntados." : "Já estava tudo organizado.");
      fatos = rr.fatos;
      desenhar();
    }
  });
  apagarTudo.addEventListener("click", async () => {
    if (apagarTudo.dataset.pedido !== "1") {
      apagarTudo.dataset.pedido = "1";
      apagarTudo.textContent = "Tem certeza? Clique de novo";
      setTimeout(() => { apagarTudo.dataset.pedido = ""; apagarTudo.textContent = "Apagar tudo"; }, 3500);
      return;
    }
    const rr = await chamar("memoria_apagar_tudo");
    pegar(rr); desenhar();
  });
  if (gavetasEl.children && gavetasEl.children.length) corpo.append(gavetasEl);
if (assuntosEl.children && assuntosEl.children.length) corpo.append(assuntosEl);
if (modoAgrupado) { desenharSecoes(); } else { secoes.classList.add("oculto"); }
corpo.append(topo, novo, contador, lista, secoes);
  desenhar();
}

function abaAjuda(corpo) {
  corpo.classList.add("ajuda");
  corpo.append(
    el("h3", "", "Ajuda"),
    el("p", "sub", "O básico para usar o assistente."),
    el("p", "", "Escreva do seu jeito: papo normal ele responde na hora. Quando a pergunta precisa de informação atual (preço, notícia, clima...), ele pesquisa na web sozinho."),
    el("p", "", "Para forçar: comece com “pesquise …”. Para impedir: comece com “sem pesquisar, …”. O botão “Web” abaixo da caixa muda o modo para toda a conversa."),
    el("p", "", "Para ele lembrar de algo, diga “lembra que …”. Os itens ficam na aba Memória, onde você pode buscar, clicar no texto para editar, apagar ou organizar."),
    el("h4", "", "Falar"),
    el("p", "", "O botão do microfone grava; o clique seguinte para e o que você falou aparece na caixa para conferir. Se a opção “enviar sozinho” estiver ligada, ele manda sem você precisar apertar Enter.")
  );
  const atalhos = el("div", "cartao atalhos");
  atalhos.append(el("h4", "", "Atalhos do teclado"));
  const lista = el("div", "lista-atalhos");
  for (const [teclas, oque] of [
    ["Enter", "envia a pergunta"],
    ["Shift + Enter", "quebra a linha"],
    ["Ctrl + M", "liga e desliga o microfone"],
    ["Ctrl + S", "salva a última resposta em .txt"],
    ["Ctrl + N", "começa uma conversa nova"],
    ["Ctrl + F", "procura nas conversas"],
    ["Ctrl + D", "pede o resumo das notícias de hoje"],
    ["Ctrl + Shift + S", "envia com pesquisa profunda"],
    ["Ctrl + e Ctrl −", "aumenta ou diminui a letra"],
    ["Ctrl + 0", "volta a letra ao tamanho normal"],
    ["Esc", "fecha esta janela"],
  ]) {
    const l = el("div", "linha-atalho");
    l.append(el("kbd", "", teclas), el("span", "", oque));
    lista.append(l);
  }
  atalhos.append(lista);
  corpo.append(atalhos);
}

function mostrarAba(aba) {
  estado.aba = aba;
  $$(".aba").forEach((b) => b.classList.toggle("ativa", b.dataset.aba === aba));
  const corpo = $("#corpo-config");
  corpo.replaceChildren();
  corpo.className = "janela-corpo";
  $("#config-aviso").textContent = "";
  $("#btn-salvar-config").classList.toggle(
    "oculto", aba === "memoria" || aba === "ajuda" || aba === "personalizacao"
  );
  ({ memoria: abaMemoria, conversa: abaConversa, chaves: abaChaves, ajuda: abaAjuda, personalizacao: abaPersonalizacao })[aba](corpo);
}

async function abrirConfig(aba) {
  estado._configTrigger = document.activeElement;
  const r = await chamar("config_ler");
  if (r.erro) return;
  estado.cfgTela = r;
  estado.rascunho = {
    modo_pesquisa: r.modo_pesquisa, usar_contexto: r.usar_contexto, aprender: r.aprender,
    web_corretor: r.web_corretor, voz_enviar: r.voz_enviar, usar_plano_b: r.usar_plano_b,
    usar_gemini: r.usar_gemini, chaves: {},
  };
  $("#modal").classList.remove("oculto");
  mostrarAba(aba || estado.aba);
}
function fecharConfig() {
  $("#modal").classList.add("oculto");
  // Devolve o foco ao elemento que abriu as Configurações.
  if (estado._configTrigger && typeof estado._configTrigger.focus === "function") {
    try { estado._configTrigger.focus(); } catch (_e) { /* elemento removido */ }
  }
  estado._configTrigger = null;
}

function abaPersonalizacao(corpo) {
  const cfg = estado.cfgTela;
  corpo.append(
    el("h3", "", "Personalização"),
    el("p", "sub", "Ajuste a aparência do Eye of Thundera. A escolha é aplicada na hora e continua salva quando você abrir o app novamente.")
  );
  const cartao = el("div", "cartao cartao-tema");
  cartao.append(el("h4", "", "Tema da interface"), el("p", "desc", "Escolha a paleta que deixa a leitura mais confortável. Isso não altera suas conversas nem as outras configurações."));
  // Grade de cartoes: cada um mostra uma MINIATURA do app com as cores do tema
  // (lidas de TEMAS_UI, a unica fonte) e o nome embaixo. Padrao radiogroup.
  const grade = el("div", "grade-temas");
  grade.setAttribute("role", "radiogroup");
  grade.setAttribute("aria-label", "Tema da interface");
  let ativo = Number(cfg.temaIdx ?? estado.cfg.temaIdx ?? 0);
  if (!(ativo >= 0 && ativo < TEMAS_UI.length)) ativo = 0;
  const botoes = [];

  const marcar = (idx) => {
    botoes.forEach((b, i) => {
      b.classList.toggle("ativo", i === idx);
      b.setAttribute("aria-checked", i === idx ? "true" : "false");
      b.tabIndex = i === idx ? 0 : -1;
    });
  };

  const escolher = async (idx) => {
    if (idx === ativo) return;
    const anterior = ativo;
    const tema = aplicarTema(idx);
    ativo = idx;
    marcar(idx);
    // Trocar o tema salva somente o tema; nao confirma opcoes de conversa
    // que o usuario ainda pode estar editando em outra aba.
    const r = await chamar("config_salvar", { tema: tema.nome, temaIdx: idx, chaves: {} });
    if (r.erro) {
      aplicarTema(anterior);
      ativo = anterior;
      marcar(anterior);
      aviso("Não foi possível salvar o tema: " + r.erro, true);
      return;
    }
    estado.cfg.tema = tema.nome;
    estado.cfg.temaIdx = idx;
    estado.cfgTela.tema = tema.nome;
    estado.cfgTela.temaIdx = idx;
    aviso("Tema alterado para " + tema.nome);
  };

  TEMAS_UI.forEach((tema, i) => {
    const c = tema.cores;
    const b = el("button", "cartao-amostra");
    b.type = "button";
    b.setAttribute("role", "radio");
    b.setAttribute("aria-label", tema.nome);
    b.style.cssText = ["--m-bg", "--m-painel", "--m-sup", "--m-sup2", "--m-texto", "--m-texto2", "--m-borda", "--m-azul", "--m-azul2"]
      .map((v, k) => v + ":" + c[["--bg", "--painel", "--superficie", "--superficie-2", "--texto", "--texto-2", "--borda", "--azul", "--azul-2"][k]])
      .join(";");
    const mini = el("div", "amostra-tema");
    const lateral = el("div", "amostra-lateral");
    lateral.append(el("i", "amostra-item ativo"), el("i", "amostra-item"), el("i", "amostra-item"));
    const chat = el("div", "amostra-chat");
    chat.append(el("i", "amostra-balao eu"), el("i", "amostra-balao ia"), el("i", "amostra-balao ia curto"));
    const caixa = el("div", "amostra-caixa");
    caixa.append(el("i", "amostra-linha"), el("i", "amostra-envia"));
    chat.append(caixa);
    mini.append(lateral, chat);
    const bolinhas = el("div", "bolinhas-tema");
    ["--bg", "--superficie", "--texto", "--azul", "--azul-2"].forEach((v) => {
      const bo = el("i", "bolinha");
      bo.style.background = c[v];
      bolinhas.append(bo);
    });
    const rodape = el("div", "nome-tema");
    rodape.append(el("span", "", tema.nome), el("span", "marca-ativo", "✓"));
    b.append(mini, bolinhas, rodape);
    b.addEventListener("click", () => escolher(i));
    b.addEventListener("keydown", (e) => {
      const passos = { ArrowRight: 1, ArrowDown: 1, ArrowLeft: -1, ArrowUp: -1 };
      if (!(e.key in passos)) return;
      e.preventDefault();
      const prox = (i + passos[e.key] + TEMAS_UI.length) % TEMAS_UI.length;
      botoes[prox].focus();
      escolher(prox);
    });
    botoes.push(b);
    grade.append(b);
  });
  marcar(ativo);
  cartao.append(grade, el("p", "nota-tema", "A alteração é aplicada imediatamente e salva automaticamente."));
  corpo.append(cartao);
}

async function salvarConfig() {
  const botao = $("#btn-salvar-config");
  if (botao.disabled) return;
  const textoOriginal = botao.textContent;
  const controles = $$("#corpo-config input, #corpo-config select, #corpo-config button");
  const bloqueiosOriginais = controles.map((controle) => controle.disabled);
  botao.disabled = true;
  botao.textContent = "Salvando...";
  controles.forEach((controle) => { controle.disabled = true; });

  const liberarControles = () => controles.forEach((controle, i) => {
    if (controle.isConnected) controle.disabled = bloqueiosOriginais[i];
  });
  const chaves = { ...(estado.rascunho.chaves || {}) };
  $$("#corpo-config input[data-campo]").forEach((i) => {
    if (i.value.trim()) chaves[i.dataset.campo] = i.value.trim();
    else delete chaves[i.dataset.campo];
  });

  try {
    const r = await chamar("config_salvar", { ...estado.rascunho, chaves });
    if (r.erro) {
      const av = $("#config-aviso");
      av.textContent = "Não foi possível salvar: " + r.erro;
      av.className = "erro";
      return;
    }

    estado.cfg = r.cfg;
    aplicarCfg();
    const atual = await chamar("config_ler");
    if (atual.erro || !Array.isArray(atual.servicos)) {
      const av = $("#config-aviso");
      av.textContent = "Alterações salvas, mas não consegui atualizar a tela. Feche e abra Configurações novamente.";
      av.className = "erro";
      return;
    }

    estado.cfgTela = atual;
    estado.rascunho.chaves = {};
    mostrarAba(estado.aba);
    $("#config-aviso").textContent = "Salvo.";
    $("#config-aviso").className = "ok";
  } catch (erro) {
    const av = $("#config-aviso");
    av.textContent = "Ocorreu um erro inesperado ao salvar. Tente novamente.";
    av.className = "erro";
    console.error("Falha ao salvar configurações:", erro);
  } finally {
    liberarControles();
    botao.disabled = false;
    botao.textContent = textoOriginal;
  }
}

/* ---------------- microfone ----------------
   Um clique comeca a gravar; o clique seguinte para. O Python cuida do
   audio (grava, confere se tem som e transcreve) e avisa a tela com os
   eventos "gravando" e "voz". O texto falado entra na caixa de digitar
   para o Wolf conferir antes - igual ao programa antigo. */
let relogioGravacao = null;

function mostrarGravando(ligado) {
  estado.gravando = !!ligado;
  const botao = $("#btn-mic");
  botao.classList.toggle("gravando", estado.gravando);
  botao.title = estado.gravando
    ? "Parar de gravar"
    : "Falar: clique para gravar, clique de novo para parar (Ctrl+M)";
  clearInterval(relogioGravacao);
  relogioGravacao = null;
  if (estado.gravando) {
    $("#digitando").classList.remove("oculto");
    let segundos = 0;
    $("#etapa").textContent = "Gravando... aperte de novo para parar";
    relogioGravacao = setInterval(() => {
      segundos += 1;
      $("#etapa").textContent = "Gravando... " + segundos + "s";
    }, 1000);
  } else {
    $("#etapa").textContent = "Transcrevendo o que você falou...";
  }
}

async function alternarMicrofone() {
  if (estado.ocupado && !estado.gravando) {
    return aviso("Aguarde a resposta terminar.", true);
  }
  const r = await chamar("mic_alternar");
  if (r.erro) {
    if (r.erro === "sem_chave_voz") {
      aviso("Cole a sua chave de API antes de falar a pergunta.", true);
      abrirConfig("chaves");
    } else {
      mostrarGravando(false);
      aviso(r.erro, true);
    }
    return;
  }
  if (r.gravando) mostrarGravando(true);
  else if (r.transcrevendo) {
    esperar(true, "Transcrevendo o que você falou...");
    $("#digitando").classList.remove("oculto");
  }
}

/* ---------------- início ---------------- */
function aplicarCfg() {
  const modo = estado.cfg.modo_pesquisa || "auto";
  $("#rotulo-web").textContent = ROTULO_WEB[modo] || ROTULO_WEB.auto;
  $("#btn-web").classList.toggle("ligada", modo === "sempre");
  $("#entrada").spellcheck = estado.cfg.web_corretor !== false;
  aplicarTema(estado.cfg.temaIdx ?? 0);
}

function lerArquivoTexto(arquivo) {
  return new Promise((resolve) => {
    const r = new FileReader();
    r.onload = () => resolve(String(r.result || ""));
    r.onerror = () => resolve("");
    try { r.readAsText(arquivo); } catch (e) { resolve(""); }
  });
}
async function tratarArquivoSolto(arquivo) {
  if (!arquivo) return;
  const ext = String(arquivo.name.split('.').pop() || "").toLowerCase();
  if (["txt","md","csv","json"].indexOf(ext) === -1) {
    aviso("Formato " + ext + " ainda não suportado. Solte .txt/.md/.csv/.json.", true);
    return;
  }
  const texto = (await lerArquivoTexto(arquivo)).slice(0, 30000);
  if (!texto.trim()) { aviso("Arquivo vazio.", true); return; }
  const entrada = $("#entrada");
  entrada.value = (entrada.value ? entrada.value.trim() + "\n\n" : "") + texto;
  ajustarAltura(); atualizarEnviar();
  aviso("Arquivo carregado: " + arquivo.name + ". Aperte Enter para enviar.");
}
function ligarArrasto() {
  ["dragenter", "dragover", "dragleave", "drop"].forEach((ev) =>
    window.addEventListener(ev, (e) => { e.preventDefault(); e.stopPropagation(); }));
  window.addEventListener("drop", async (e) => {
    const arqs = e.dataTransfer && e.dataTransfer.files;
    if (arqs && arqs.length) {
      for (const a of arqs) await tratarArquivoSolto(a);
    }
  });
}

function ligarEventos() {
  const entrada = $("#entrada");
  entrada.addEventListener("input", () => { ajustarAltura(); atualizarEnviar(); });
  entrada.addEventListener("keydown", (e) => {
    if (e.key === "S" && e.ctrlKey && e.shiftKey) {
      e.preventDefault();
      enviar(undefined, true);
      return;
    }
    if (e.key === "Enter" && !e.shiftKey && !e.isComposing) {
      e.preventDefault();
      enviar();
    }
  });
  $("#btn-enviar").addEventListener("click", () => enviar());
  $("#btn-serio").addEventListener("click", () => {
    $("#menu-modos").open = false;
    enviar(undefined, true);
  });
  $("#btn-deep").addEventListener("click", () => {
    estado.profundo = !estado.profundo;
    const b = $("#btn-deep");
    b.classList.toggle("ligada", !!estado.profundo);
    b.title = estado.profundo
      ? "Pesquisa profunda LIGADA (clique para desligar)"
      : "Modo de pesquisa profunda: mais sites e resposta em tópicos com fontes (clique para ligar)";
    atualizarMenuModos();
    $("#menu-modos").open = false;
    aviso(estado.profundo ? "Pesquisa profunda LIGADA." : "Pesquisa profunda desligada.");
  });
  $("#btn-mic").addEventListener("click", () => alternarMicrofone());
  $("#btn-privada").addEventListener("click", () => {
    $("#menu-modos").open = false;
    alternarPrivada();
  });
  $("#btn-resumo").addEventListener("click", () => {
    $("#menu-modos").open = false;
    resumoDoDia();
  });
  $("#btn-nova").addEventListener("click", novaConversa);
  $("#btn-config").addEventListener("click", () => abrirConfig());
  $("#btn-fechar-config").addEventListener("click", fecharConfig);
  $("#btn-salvar-config").addEventListener("click", salvarConfig);
  $("#modal").addEventListener("mousedown", (e) => { if (e.target.id === "modal") fecharConfig(); });
  $$("#abas .aba").forEach((b) => b.addEventListener("click", () => mostrarAba(b.dataset.aba)));
  $("#campo-busca").addEventListener("input", (e) => buscar(e.target.value));
  $("#campo-busca").addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      e.target.value = "";
      buscar("");
    }
  });
  $("#btn-limpar-busca").addEventListener("click", () => {
    $("#campo-busca").value = "";
    buscar("");
    $("#campo-busca").focus();
  });
  $$(".sugestao").forEach((b) => {
    b.setAttribute("role", "button");
    b.setAttribute("aria-label", "Sugestão: " + b.textContent);
    b.addEventListener("click", () => enviar(b.textContent));
    b.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") { e.preventDefault(); b.click(); }
    });
  });
  $("#btn-web").addEventListener("click", async () => {
    const ordem = ["auto", "sempre", "nunca"];
    const novo = ordem[(ordem.indexOf(estado.cfg.modo_pesquisa || "auto") + 1) % 3];
    const r = await chamar("definir_modo", novo);
    if (r.cfg) { estado.cfg = r.cfg; aplicarCfg(); aviso(ROTULO_WEB[novo]); }
  });
  const recolher = (sim) => {
    $("#lateral").classList.toggle("recolhida", sim);
    $("#btn-abrir-lateral").classList.toggle("oculto", !sim);
    try { localStorage.setItem("pia_lateral", sim ? "1" : "0"); } catch (_e) { /* sem armazenamento */ }
  };
  $("#btn-recolher").addEventListener("click", () => recolher(true));
  $("#btn-abrir-lateral").addEventListener("click", () => recolher(false));
  try { if (localStorage.getItem("pia_lateral") === "1") recolher(true); } catch (_e) { /* ok */ }
  // A letra que o Wolf deixou da ultima vez: aplicar logo no inicio, e
  // nao so quando ele aperta o atalho. Sem isto a tela abriria sempre no
  // tamanho normal e so mudaria depois do primeiro Ctrl +.
  try { aplicarTamanho(tamanhoAtual()); } catch (_e) { /* sem armazenamento */ }
  mostrarPrivada();
  ligarArrasto();
}

async function iniciar() {
  const r = await chamar("iniciar");
  if (r.erro) return;
  estado.cfg = r.cfg;
  estado.conversas = r.conversas;
  estado.mensagens = r.mensagens;
  estado.atual = r.atual;
  aplicarCfg();
  desenharConversas();
  desenharMensagens();
  $("#entrada").focus();
  if (!r.tem_chave) aviso("Cole a sua chave do Google em Configurações > Chaves para começar.");
}

/* ---- barra de titulo propria (PLANO-BARRA-PROPRIA.md) ---- */
function ligarBarraTitulo() {
  const barra = $("#barra-titulo");
  const btnMax = $("#jan-max");
  if (!barra || !btnMax) return;
  const marcar = (r) => {
    if (!r || typeof r.maximizada !== "boolean") return;
    document.body.classList.toggle("maximizada", r.maximizada);
    btnMax.title = r.maximizada ? "Restaurar" : "Maximizar";
    btnMax.setAttribute("aria-label", btnMax.title);
    // A janela maximizada sem moldura passa uns pixels da tela; o Python diz
    // quantos (em pixels fisicos) e a tela recua esse tanto.
    const px = r.maximizada && r.borda ? r.borda / (window.devicePixelRatio || 1) : 0;
    document.documentElement.style.setProperty("--borda-max", px + "px");
  };
  $("#jan-min").addEventListener("click", () => chamar("janela_minimizar"));
  btnMax.addEventListener("click", async () => marcar(await chamar("janela_maximizar")));
  $("#jan-fechar").addEventListener("click", () => chamar("janela_fechar"));
  barra.addEventListener("mousedown", (e) => {
    if (e.button !== 0 || e.target.closest(".botoes-janela")) return;
    if (e.detail === 2) { btnMax.click(); return; }
    // Arrasto nativo: chama o Python que usa ReleaseCapture + SendMessageW.
    // Chama direto pela API do pywebview (mais rapido que chamar()).
    try {
      const api = window.pywebview && window.pywebview.api;
      if (api && typeof api.janela_arrastar === "function") {
        api.janela_arrastar();
      } else {
        chamar("janela_arrastar");
      }
    } catch (_e) {
      chamar("janela_arrastar");
    }
  });
  window.addEventListener("resize", async () => marcar(await chamar("janela_estado")));
}

ligarBarraTitulo();
ligarEventos();
ligarMenuContexto();
window.addEventListener("pywebviewready", iniciar);
