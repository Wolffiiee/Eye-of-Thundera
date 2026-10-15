"use strict";
/* Pesquisa IA - tela nova. Fala com o Python por window.pywebview.api (ver app_web.py). */

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

const estado = { mensagens: [], conversas: [], atual: null, ocupado: false, cfg: {}, aba: "chaves", rascunho: {} };
const ROTULO_WEB = { auto: "Web: automática", sempre: "Web: sempre", nunca: "Web: desligada" };

async function chamar(nome, ...args) {
  try {
    const api = window.pywebview && window.pywebview.api;
    if (!api) throw new Error("a ponte com o programa ainda não está pronta");
    return await api[nome](...args);
  } catch (e) {
    aviso("Algo deu errado: " + (e.message || e), true);
    return { erro: String(e) };
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
  let ultimo = 0;
  for (const m of texto.matchAll(URL_RE)) {
    if (m.index > ultimo) pai.append(texto.slice(ultimo, m.index));
    const a = el("a", "", m[0]);
    a.href = m[0];
    a.dataset.url = m[0];
    pai.append(a);
    ultimo = m.index + m[0].length;
  }
  if (ultimo < texto.length) pai.append(texto.slice(ultimo));
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

async function copiarTexto(texto) {
  try {
    await navigator.clipboard.writeText(texto);
  } catch (_e) {
    const t = el("textarea");
    t.value = texto;
    document.body.append(t);
    t.select();
    document.execCommand("copy");
    t.remove();
  }
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
      await copiarTexto(m.text);
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
    corpo.append(acoes);
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
  const primeira = estado.mensagens.find((m) => m.role === "user");
  $("#titulo-conversa").textContent = primeira ? primeira.text.slice(0, 70) : "";
  rolarParaOFim();
}

function anexarMensagem(m) {
  estado.mensagens.push(m);
  $("#vazio").classList.add("oculto");
  $("#mensagens").append(criarMensagem(m));
  if (estado.mensagens.length === 1 && m.role === "user") $("#titulo-conversa").textContent = m.text.slice(0, 70);
  rolarParaOFim();
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
}
function ajustarAltura() {
  const e = $("#entrada");
  e.style.height = "auto";
  e.style.height = Math.min(e.scrollHeight, 200) + "px";
}

async function enviar(texto) {
  texto = (texto !== undefined ? texto : $("#entrada").value).trim();
  if (!texto || estado.ocupado) return;
  const r = await chamar("enviar", texto);
  if (r && r.erro) {
    if (r.erro === "sem_chave") {
      aviso("Cole a sua chave do Google nas Configurações para começar.");
      abrirConfig("chaves");
    } else aviso(r.erro, true);
    return;
  }
  $("#entrada").value = "";
  ajustarAltura();
  anexarMensagem({ role: "user", text: texto });
  esperar(true, "Pensando...");
}

window.PIA = {
  __estado: estado,
  evento(o) {
    if (o.tipo === "etapa") {
      $("#etapa").textContent = o.texto;
    } else if (o.tipo === "resposta") {
      esperar(false);
      anexarMensagem({ role: "model", text: o.texto });
    } else if (o.tipo === "erro") {
      esperar(false);
      anexarMensagem({ role: "erro", text: o.texto });
      if (o.chave) abrirConfig("chaves");
    } else if (o.tipo === "conversas") {
      estado.conversas = o.conversas;
      estado.atual = o.atual;
      desenharConversas();
    }
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
  pop.append(pedir);
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
  }
});
document.addEventListener("click", (e) => {
  const link = e.target.closest("a[data-url]");
  if (link) {
    e.preventDefault();
    chamar("abrir_link", link.dataset.url);
  }
});

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
    linhaToggle("Lembrar o assunto da conversa", "Permite perguntas de acompanhamento.", "usar_contexto"),
    linhaToggle("Aprender sozinho com as conversas", "Guarda gostos e hábitos (sem repetir o que já sabe).", "aprender"),
    linhaToggle("Corretor ortográfico", "Sublinha palavras erradas na caixa de digitar.", "web_corretor"),
    linhaToggle("Enviar sozinho depois de falar", "Para quando o microfone estiver ligado.", "voz_enviar")
  );
  corpo.append(caixa);
}

function cartaoChave(titulo, desc, campo, info, opc) {
  const c = el("div", "cartao");
  c.append(el("h4", "", titulo), el("p", "desc", desc));
  const linha = el("div", "campo");
  const inp = el("input");
  inp.type = "password";
  inp.autocomplete = "off";
  inp.spellcheck = false;
  inp.dataset.campo = campo;
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
  corpo.append(el("h3", "", "Chaves de acesso"), el("p", "sub", "As chaves ficam só neste computador. Todas são gratuitas e não pedem cartão."));
  corpo.append(
    cartaoChave("Google Gemini (principal)", "É ela que pesquisa e escreve as respostas.", "api_key", cfg.gemini, {
      testar: true,
      pagina: "https://aistudio.google.com/apikey",
    }),
    cartaoChave("Google Gemini (reserva, opcional)", "Se a principal parar de funcionar, o programa troca sozinho para esta.", "api_key_reserva", cfg.gemini_reserva, { testar: true })
  );
  const plano = el("div", "cartao");
  plano.append(linhaToggle("Usar o plano B", "Se o Gemini não responder, tenta estes serviços de reserva.", "usar_plano_b"));
  corpo.append(plano);
  for (const s of cfg.servicos) {
    corpo.append(cartaoChave(s.nome, s.resumo ? "Grátis — " + s.resumo : "", s.campo, s, { passos: s.passos, pagina: s.pagina }));
  }
}

async function abaMemoria(corpo) {
  corpo.append(el("h3", "", "Memória"), el("p", "sub", "O que o assistente aprendeu sobre você. Ele usa isso sozinho e nunca comenta que guardou."));
  const r = await chamar("memoria_listar");
  if (estado.aba !== "memoria") return;
  let fatos = r.fatos || [];
  const topo = el("div", "memoria-topo");
  const busca = el("input", "busca");
  busca.placeholder = "Buscar na memória...";
  busca.spellcheck = false;
  const organizar = el("button", "btn", "Organizar");
  organizar.title = "Junta fatos repetidos";
  const apagarTudo = el("button", "btn perigo", "Apagar tudo");
  topo.append(busca, organizar, apagarTudo);
  const novo = el("div", "adicionar");
  const campo = el("input");
  campo.placeholder = "Adicionar algo que ele deve saber sobre você...";
  const add = el("button", "btn primario", "Adicionar");
  novo.append(campo, add);
  const contador = el("div", "contador");
  const lista = el("div");
  const desenhar = () => {
    lista.replaceChildren();
    const termo = busca.value.trim().toLowerCase();
    const vistos = fatos.filter((f) => !termo || f.toLowerCase().includes(termo));
    contador.textContent = fatos.length + (fatos.length === 1 ? " item guardado" : " itens guardados");
    if (!vistos.length) lista.append(el("div", "vazio-lista", fatos.length ? "Nada encontrado." : "Ainda não guardou nada."));
    for (const f of vistos) {
      const linha = el("div", "fato");
      const x = el("button", "icone");
      x.title = "Apagar este item";
      x.append(ico("i-fechar"));
      x.addEventListener("click", async () => {
        const rr = await chamar("memoria_apagar", f);
        if (rr.fatos) { fatos = rr.fatos; desenhar(); }
      });
      linha.append(el("span", "", f), x);
      lista.append(linha);
    }
  };
  busca.addEventListener("input", desenhar);
  const adicionar = async () => {
    if (!campo.value.trim()) return;
    const rr = await chamar("memoria_adicionar", campo.value.trim());
    if (rr.fatos) { fatos = rr.fatos; campo.value = ""; desenhar(); }
  };
  add.addEventListener("click", adicionar);
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
    if (rr.fatos) { fatos = rr.fatos; desenhar(); }
  });
  corpo.append(topo, novo, contador, lista);
  desenhar();
}

function abaAjuda(corpo) {
  corpo.classList.add("ajuda");
  corpo.append(
    el("h3", "", "Ajuda"),
    el("p", "sub", "O básico para usar o assistente."),
    el("p", "", "Escreva do seu jeito: papo normal ele responde na hora. Quando a pergunta precisa de informação atual (preço, notícia, clima...), ele pesquisa na web sozinho."),
    el("p", "", "Para forçar: comece com “pesquise …”. Para impedir: comece com “sem pesquisar, …”. O botão “Web” abaixo da caixa muda o modo para toda a conversa."),
    el("p", "", "Enter envia. Shift+Enter quebra a linha. Em cada resposta, passe o mouse para copiar ou salvar em .txt."),
    el("p", "", "Para ele lembrar de algo, diga “lembra que …”. Os itens ficam na aba Memória, onde você pode buscar, apagar ou organizar.")
  );
}

function mostrarAba(aba) {
  estado.aba = aba;
  $$(".aba").forEach((b) => b.classList.toggle("ativa", b.dataset.aba === aba));
  const corpo = $("#corpo-config");
  corpo.replaceChildren();
  corpo.className = "janela-corpo";
  $("#config-aviso").textContent = "";
  $("#btn-salvar-config").classList.toggle("oculto", aba === "memoria" || aba === "ajuda");
  ({ memoria: abaMemoria, conversa: abaConversa, chaves: abaChaves, ajuda: abaAjuda })[aba](corpo);
}

async function abrirConfig(aba) {
  const r = await chamar("config_ler");
  if (r.erro) return;
  estado.cfgTela = r;
  estado.rascunho = {
    modo_pesquisa: r.modo_pesquisa, usar_contexto: r.usar_contexto, aprender: r.aprender,
    web_corretor: r.web_corretor, voz_enviar: r.voz_enviar, usar_plano_b: r.usar_plano_b,
  };
  $("#modal").classList.remove("oculto");
  mostrarAba(aba || estado.aba);
}
function fecharConfig() {
  $("#modal").classList.add("oculto");
}

async function salvarConfig() {
  const chaves = {};
  $$("#corpo-config input[data-campo]").forEach((i) => {
    if (i.value.trim()) chaves[i.dataset.campo] = i.value.trim();
  });
  const r = await chamar("config_salvar", { ...estado.rascunho, chaves });
  if (r.erro) return;
  estado.cfg = r.cfg;
  aplicarCfg();
  const av = $("#config-aviso");
  av.textContent = "Salvo.";
  av.className = "ok";
  estado.cfgTela = await chamar("config_ler");
  mostrarAba(estado.aba);
  $("#config-aviso").textContent = "Salvo.";
  $("#config-aviso").className = "ok";
}

/* ---------------- início ---------------- */
function aplicarCfg() {
  const modo = estado.cfg.modo_pesquisa || "auto";
  $("#rotulo-web").textContent = ROTULO_WEB[modo] || ROTULO_WEB.auto;
  $("#btn-web").classList.toggle("ligada", modo === "sempre");
  $("#entrada").spellcheck = estado.cfg.web_corretor !== false;
}

function ligarEventos() {
  const entrada = $("#entrada");
  entrada.addEventListener("input", () => { ajustarAltura(); atualizarEnviar(); });
  entrada.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey && !e.isComposing) {
      e.preventDefault();
      enviar();
    }
  });
  $("#btn-enviar").addEventListener("click", () => enviar());
  $("#btn-nova").addEventListener("click", novaConversa);
  $("#btn-config").addEventListener("click", () => abrirConfig());
  $("#btn-fechar-config").addEventListener("click", fecharConfig);
  $("#btn-salvar-config").addEventListener("click", salvarConfig);
  $("#modal").addEventListener("mousedown", (e) => { if (e.target.id === "modal") fecharConfig(); });
  $$("#abas .aba").forEach((b) => b.addEventListener("click", () => mostrarAba(b.dataset.aba)));
  $$(".sugestao").forEach((b) => b.addEventListener("click", () => enviar(b.textContent)));
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

ligarEventos();
window.addEventListener("pywebviewready", iniciar);
