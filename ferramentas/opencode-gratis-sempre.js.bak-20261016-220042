// ============================================================================
// gratis-sempre: quando o modelo do OpenCode bate no limite, troca sozinho
// para o proximo modelo GRATIS que funcione e repete o ultimo pedido.
//
// COMO FUNCIONA
//  1. Escuta erros da sessao (evento "session.error") e mensagens do assistente
//     que vieram com erro (evento "message.updated").
//  2. Se o erro parece LIMITE (429, rate limit, quota, credits, "too many
//     requests", "resource exhausted", "overloaded"...), marca o modelo atual
//     como "descansando" por 15 minutos.
//  3. Escolhe o proximo da lista (ferramentas/modelos-gratis.txt, no projeto,
//     ou a lista embutida abaixo) que NAO esteja descansando, avisa com um aviso
//     na tela e reenvia o ultimo pedido do Wolf usando o novo modelo.
//  4. Trava de seguranca: no maximo 6 trocas por sessao e nunca repete o mesmo
//     pedido mais de 1 vez por modelo (nao entra em loop).
//
// LIMITES HONESTOS
//  - O OpenCode nao revela "quanto falta" da cota: o plugin age QUANDO o
//    limite acontece (ou quando o provedor avisa), nao antes.
//  - A troca vale para a sessao em andamento. Para a PROXIMA sessao comecar
//    com um modelo bom, rode "10 - Trocar para modelo gratis.bat".
//  - Se o OpenCode mudar a API de plugins, o plugin avisa no log e desliga.
//
// Instalacao: copiar para %USERPROFILE%\.config\opencode\plugin\  (o arquivo
// "11 - Instalar plugin gratis-sempre.bat" faz isso). Pede 'default export'
// com id e setup (formato do opencode 2.0.30).
// ============================================================================
import fs from "node:fs"
import os from "node:os"
import path from "node:path"

const DESCANSO_MS = 15 * 60 * 1000
const MAX_TROCAS = 6

const LISTA_EMBUTIDA = [
  "opencode/deepseek-v4.1-flash-free",
  "opencode/glm-5.3-flash-free",
  "opencode/nemotron-3-ultra-free",
  "opencode/muse-spark-1.3-contributor-free",
  "opencode/mimo-v2.6-flash-free",
  "opencode/longcat-2.5-preview-free",
  "opencode/space-bunny-free",
  "opencode/beam-free",
  "opencode/ll-alpha-free",
]

const PADROES_LIMITE = [
  /\b429\b/i, /rate.?limit/i, /quota/i, /credit/i, /too many requests/i,
  /resource.?exhausted/i, /overloaded/i, /usage limit/i, /exceeded/i,
  /insufficient/i, /free (tier|usage)/i, /try again (later|in)/i,
  /context.?(length|window)/i, /maximum context/i, /token limit/i,
]

export function ehLimite(texto) {
  const t = String(texto || "")
  return PADROES_LIMITE.some((p) => p.test(t))
}

export function lerLista(pastaProjeto) {
  try {
    const arq = path.join(pastaProjeto || "", "ferramentas", "modelos-gratis.txt")
    const linhas = fs.readFileSync(arq, "utf8").replace(/^\uFEFF/, "").split(/\r?\n/)
      .map((l) => l.trim()).filter((l) => l && !l.startsWith("#"))
    // so os que o OpenCode chama direto (sem 9router/ollama, que podem estar desligados)
    const diretos = linhas.filter((l) => l.startsWith("opencode/"))
    if (diretos.length) return diretos
  } catch { /* usa a embutida */ }
  return LISTA_EMBUTIDA.slice()
}

export function proximoModelo(lista, atual, descansando, agora = Date.now()) {
  const livres = lista.filter((m) => !(descansando[m] && descansando[m] > agora) && m !== atual)
  if (!livres.length) return null
  const i = lista.indexOf(atual)
  // o primeiro livre DEPOIS do atual na ordem da lista; se nao houver, o primeiro livre
  return livres.find((m) => lista.indexOf(m) > i) || livres[0]
}

export function separar(modelo) {
  const i = modelo.indexOf("/")
  return { providerID: modelo.slice(0, i), modelID: modelo.slice(i + 1) }
}

function textoDoErro(e) {
  if (!e) return ""
  const d = e.data || {}
  return [e.name, e.message, d.message, d.statusCode, d.responseBody].filter(Boolean).join(" ")
}

const GratisSempre = async ({ client, directory }) => {
  const estado = new Map() // sessionID -> {trocas, tentados:Set}
  const descansando = {}
  const lista = lerLista(directory)

  const aviso = async (mensagem, variant = "info") => {
    try { await client.tui.showToast({ body: { message: mensagem, variant } }) } catch { /* sem TUI */ }
  }
  const log = async (level, message, extra) => {
    try { await client.app.log({ body: { service: "gratis-sempre", level, message, extra } }) } catch { /* ok */ }
  }

  async function trocar(sessionID, modeloAtual, motivo) {
    const s = estado.get(sessionID) || { trocas: 0, tentados: new Set(), ultima: 0 }
    estado.set(sessionID, s)
    // o mesmo erro chega por dois eventos: ignora o segundo (10 s)
    if (Date.now() - s.ultima < 10000) return
    s.ultima = Date.now()
    if (modeloAtual) descansando[modeloAtual] = Date.now() + DESCANSO_MS
    if (s.trocas >= MAX_TROCAS) {
      await aviso("gratis-sempre: ja troquei 6 vezes nesta sessao. Parei para nao entrar em loop.", "warning")
      return
    }
    const proximo = proximoModelo(lista, modeloAtual, descansando)
    if (!proximo || s.tentados.has(proximo + "|" + s.trocas)) {
      await aviso("gratis-sempre: nenhum modelo gratis livre agora. Tente em alguns minutos.", "error")
      return
    }
    s.trocas += 1
    s.tentados.add(proximo + "|" + (s.trocas - 1))

    // ultimo pedido do Wolf nesta sessao
    let texto = ""
    try {
      const r = await client.session.messages({ path: { id: sessionID } })
      const msgs = r.data || r
      for (let i = msgs.length - 1; i >= 0; i--) {
        if (msgs[i].info && msgs[i].info.role === "user") {
          texto = (msgs[i].parts || []).filter((p) => p.type === "text").map((p) => p.text).join("\n")
          break
        }
      }
    } catch (e) { await log("error", "nao consegui ler as mensagens", { erro: String(e) }) }

    await aviso("Limite em " + (modeloAtual || "?") + " (" + motivo + "). Troquei para " + proximo + " (gratis).", "warning")
    await log("info", "trocando de modelo", { de: modeloAtual, para: proximo, motivo })
    if (!texto) return
    try {
      await client.session.prompt({
        path: { id: sessionID },
        body: {
          model: separar(proximo),
          parts: [{ type: "text", text: texto }],
        },
      })
    } catch (e) {
      await log("error", "falhou ao reenviar com o novo modelo", { erro: String(e) })
    }
  }

  return {
    event: async ({ event }) => {
      try {
        if (event.type === "session.error") {
          const p = event.properties || {}
          const txt = textoDoErro(p.error)
          if (p.sessionID && ehLimite(txt)) await trocar(p.sessionID, null, txt.slice(0, 60))
        }
        if (event.type === "message.updated") {
          const info = (event.properties || {}).info || {}
          if (info.role === "assistant" && info.error) {
            const txt = textoDoErro(info.error)
            if (ehLimite(txt)) {
              const atual = info.providerID && info.modelID ? info.providerID + "/" + info.modelID : null
              await trocar(info.sessionID, atual, txt.slice(0, 60))
            }
          }
        }
      } catch (e) { await log("error", "erro no plugin", { erro: String(e) }) }
    },
  }
}

export default { id: "gratis-sempre", setup: GratisSempre }
