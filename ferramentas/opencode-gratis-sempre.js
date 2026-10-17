// gratis-sempre v2: fallback apenas para modelos gratuitos do provedor OpenCode.
// Feito para OpenCode 2.0.x. Mantém a sessão e reenvia o último pedido do usuário.
// Uma troca é uma nova geração: chamadas de ferramenta parcialmente executadas não são retomadas.
import fs from "node:fs"
import path from "node:path"

const DESCANSO_MS = 15 * 60 * 1000
const MAX_TROCAS_POR_PEDIDO = 9
const JANELA_DUPLICADO_MS = 2500

// Lista conferida com `opencode models` em 16/10/2026.
// Somente IDs gratuitos do provedor OpenCode que estavam disponíveis na máquina.
const MODELOS_GRATUITOS_VALIDOS = [
  "opencode/deepseek-v4.1-flash-free",
  "opencode/glm-5.3-flash-free",
  "opencode/nemotron-3-ultra-free",
  "opencode/nemotron-3.5-lightning-free",
  "opencode/nemotron-3.5-super-vl-free",
  "opencode/mimo-v2.6-flash-free",
  "opencode/longcat-2.5-preview-free",
  "opencode/space-bunny-free",
  "opencode/beam-free",
]

const PADROES_LIMITE = [
  /\b429\b/i,
  /rate.?limit/i,
  /too many requests/i,
  /quota(?:\s|_)?(?:exceeded|exhausted|limit)?/i,
  /credit balance|credits? exhausted|insufficient credits/i,
  /usage limit|free tier limit|limit reached/i,
  /resource.?exhausted/i,
  /overloaded|capacity exceeded|temporarily unavailable/i,
  /\b(?:503|529)\b/i,
  /try again (?:later|in \d+)/i,
]

export function ehLimite(texto) {
  const t = String(texto || "")
  return PADROES_LIMITE.some((p) => p.test(t))
}

function textoDoErro(e) {
  if (!e) return ""
  const partes = []
  const vistos = new Set()
  let atual = e
  for (let i = 0; atual && i < 4 && !vistos.has(atual); i++) {
    if (typeof atual === "string" || typeof atual === "number") {
      partes.push(String(atual))
      break
    }
    vistos.add(atual)
    if (atual.name) partes.push(atual.name)
    if (atual.message) partes.push(atual.message)
    if (atual.statusCode) partes.push(String(atual.statusCode))
    if (atual.data) {
      try { partes.push(JSON.stringify(atual.data)) } catch {}
    }
    if (atual.responseBody) {
      try { partes.push(typeof atual.responseBody === "string" ? atual.responseBody : JSON.stringify(atual.responseBody)) } catch {}
    }
    atual = atual.cause || atual.data?.cause
  }
  try { partes.push(JSON.stringify(e)) } catch {}
  return partes.filter(Boolean).join(" ")
}

function separar(modelo) {
  const i = modelo.indexOf("/")
  return { providerID: modelo.slice(0, i), modelID: modelo.slice(i + 1) }
}

function lerLista(directory) {
  // O arquivo do projeto só define a preferência. IDs obsoletos ou de outros
  // provedores nunca entram na rotação.
  try {
    const arq = path.join(directory || "", "ferramentas", "modelos-gratis.txt")
    const linhas = fs.readFileSync(arq, "utf8").replace(/^\uFEFF/, "").split(/\r?\n/)
      .map((l) => l.trim()).filter((l) => l && !l.startsWith("#"))
    const preferidos = linhas.filter((l) => MODELOS_GRATUITOS_VALIDOS.includes(l))
    return [...preferidos, ...MODELOS_GRATUITOS_VALIDOS.filter((m) => !preferidos.includes(m))]
  } catch {
    return MODELOS_GRATUITOS_VALIDOS.slice()
  }
}

function textoDaMensagem(msg) {
  return (msg?.parts || [])
    .filter((p) => p?.type === "text" && typeof p.text === "string")
    .map((p) => p.text)
    .join("\n")
    .trim()
}

const GratisSempre = async ({ client, directory }) => {
  const estados = new Map()
  const modeloPorSessao = new Map()
  const emCooldown = new Map()
  const ultimosErros = new Map()
  const lista = lerLista(directory)

  const estadoDe = (id) => {
    if (!estados.has(id)) estados.set(id, {
      trocas: 0, tentados: new Set(), ocupado: false, preparando: false, erroPendente: null,
      ultimoPedido: "", pedidoAutomatico: false,
    })
    return estados.get(id)
  }

  const aviso = async (message, variant = "info") => {
    try { await client.tui.showToast({ body: { message, variant } }) } catch {}
  }
  const log = async (level, message, extra = {}) => {
    try { await client.app.log({ body: { service: "gratis-sempre", level, message, extra } }) } catch {}
  }

  async function ultimoPedido(sessionID) {
    try {
      const r = await client.session.messages({ path: { id: sessionID } })
      const msgs = Array.isArray(r?.data) ? r.data : (Array.isArray(r) ? r : [])
      let texto = ""
      let modelo = ""
      for (let i = msgs.length - 1; i >= 0; i--) {
        const info = msgs[i]?.info || msgs[i]
        if (!modelo && info?.role === "assistant" && info.providerID && info.modelID) {
          modelo = info.providerID + "/" + info.modelID
        }
        if (!texto && info?.role === "user") texto = textoDaMensagem(msgs[i])
        if (texto && modelo) break
      }
      return { texto, modelo }
    } catch (e) {
      await log("error", "não consegui ler o histórico da sessão", { erro: textoDoErro(e) })
      return { texto: "", modelo: "" }
    }
  }

  function proximoModelo(s, atual) {
    const agora = Date.now()
    return lista.find((m) =>
      m !== atual &&
      !s.tentados.has(m) &&
      !(emCooldown.get(m) > agora)
    ) || null
  }

  async function trocar(sessionID, modeloComFalha, motivo) {
    if (!sessionID) return
    const s = estadoDe(sessionID)
    const modeloConhecido = modeloComFalha || modeloPorSessao.get(sessionID) || ""
    const assinatura = sessionID + "|" + modeloConhecido + "|" + String(motivo).slice(0, 100)
    const ultimo = ultimosErros.get(assinatura) || 0
    if (Date.now() - ultimo < JANELA_DUPLICADO_MS) return
    ultimosErros.set(assinatura, Date.now())

    if (s.ocupado || s.preparando) {
      // Deduplica antes desta trava: o mesmo erro pode chegar por dois eventos.
      s.erroPendente = { modelo: modeloConhecido, motivo }
      return
    }
    // A trava começa antes de qualquer await para impedir duas trocas simultâneas.
    s.preparando = true
    const hist = await ultimoPedido(sessionID)
    s.preparando = false
    const atual = modeloConhecido || hist.modelo || ""
    if (atual) modeloPorSessao.set(sessionID, atual)
    if (!s.ultimoPedido && hist.texto) s.ultimoPedido = hist.texto
    const texto = hist.texto || s.ultimoPedido
    if (!texto) {
      s.preparando = false
      await aviso("Fallback: não consegui recuperar o último pedido; não reenviei nada.", "error")
      await log("error", "pedido vazio; fallback cancelado", { sessionID, modelo: atual })
      return
    }

    if (atual) {
      s.tentados.add(atual)
      emCooldown.set(atual, Date.now() + DESCANSO_MS)
    }
    s.ocupado = true
    s.trocas = 0

    try {
      let modeloFalho = atual
      let motivoFalha = motivo
      while (s.trocas < MAX_TROCAS_POR_PEDIDO) {
        const proximo = proximoModelo(s, modeloFalho)
        if (!proximo) {
          await aviso("Fallback: todos os modelos gratuitos disponíveis já foram tentados ou estão em espera.", "error")
          await log("warn", "sem modelos gratuitos restantes", { sessionID, tentados: [...s.tentados] })
          return
        }

        s.trocas += 1
        s.tentados.add(proximo)
        modeloPorSessao.set(sessionID, proximo)
        s.erroPendente = null
        await aviso("Limite/indisponibilidade em " + (modeloFalho || "modelo atual") + ". Tentando " + proximo + " (grátis, tentativa " + s.trocas + "/" + MAX_TROCAS_POR_PEDIDO + ").", "warning")
        await log("info", "fallback iniciado", { sessionID, de: modeloFalho, para: proximo, motivo: motivoFalha, tentativa: s.trocas })

        let erroDireto = null
        try {
          s.pedidoAutomatico = true
          await client.session.prompt({
            path: { id: sessionID },
            body: { model: separar(proximo), parts: [{ type: "text", text: texto }] },
          })
        } catch (e) {
          erroDireto = e
        } finally {
          s.pedidoAutomatico = false
        }

        const pendente = s.erroPendente
        s.erroPendente = null
        if (!pendente && !erroDireto) {
          await log("info", "prompt de fallback enviado", { sessionID, modelo: proximo })
          return
        }

        const erro = pendente || (erroDireto ? { modelo: proximo, motivo: textoDoErro(erroDireto) } : null)
        const txt = erro?.motivo || textoDoErro(erroDireto)
        if (txt && !ehLimite(txt)) {
          await log("error", "a tentativa falhou por um erro que não parece limite; parei para evitar repetição", { sessionID, modelo: proximo, erro: txt.slice(0, 240) })
          await aviso("O modelo alternativo falhou por um erro diferente de limite. Parei para evitar um loop.", "error")
          return
        }

        modeloFalho = erro?.modelo || proximo
        motivoFalha = txt || "limite/indisponibilidade no modelo alternativo"
        if (modeloFalho) emCooldown.set(modeloFalho, Date.now() + DESCANSO_MS)
        await log("warn", "modelo alternativo também falhou", { sessionID, modelo: modeloFalho, motivo: motivoFalha.slice(0, 180) })
      }

      await aviso("Fallback interrompido após " + MAX_TROCAS_POR_PEDIDO + " tentativas.", "error")
    } finally {
      s.ocupado = false
      s.erroPendente = null
    }
  }

  await log("info", "plugin carregado", { directory, modelos: lista, versao: "2.0.0" })

  return {
    event: async ({ event }) => {
      try {
        const p = event?.properties || {}
        if (event.type === "message.updated") {
          const info = p.info || {}
          const sessionID = info.sessionID
          if (!sessionID) return
          const s = estadoDe(sessionID)

          if (info.role === "assistant" && info.providerID && info.modelID) {
            modeloPorSessao.set(sessionID, info.providerID + "/" + info.modelID)
          }

          if (info.role === "user") {
            const texto = textoDaMensagem({ parts: info.parts })
            if (texto && !s.pedidoAutomatico && texto !== s.ultimoPedido) {
              s.ultimoPedido = texto
              s.tentados = new Set()
              s.trocas = 0
              s.erroPendente = null
            }
          }

          if (info.role === "assistant" && info.error) {
            const txt = textoDoErro(info.error)
            if (ehLimite(txt)) {
              const atual = info.providerID && info.modelID ? info.providerID + "/" + info.modelID : modeloPorSessao.get(sessionID)
              await trocar(sessionID, atual, txt.slice(0, 180))
            }
          }
        }

        if (event.type === "session.error") {
          const sessionID = p.sessionID
          const txt = textoDoErro(p.error)
          if (sessionID && ehLimite(txt)) {
            await trocar(sessionID, modeloPorSessao.get(sessionID) || "", txt.slice(0, 180))
          }
        }
      } catch (e) {
        await log("error", "erro inesperado no plugin", { erro: textoDoErro(e) })
      }
    },
  }
}

export default { id: "gratis-sempre", setup: GratisSempre }
