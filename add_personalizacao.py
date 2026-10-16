import io

fn = "D:/Projetos/PesquisaIA/web/app.js"
s = io.open(fn, encoding="utf-8").read()

# Step 1: Add personalizacao to the mostrarAba dispatcher
old_dispatcher = '({ memoria: abaMemoria, conversa: abaConversa, chaves: abaChaves, ajuda: abaAjuda })[aba](corpo);'
new_dispatcher = '({ memoria: abaMemoria, conversa: abaConversa, chaves: abaChaves, ajuda: abaAjuda, personalizacao: abaPersonalizacao })[aba](corpo);'
assert old_dispatcher in s, "old_dispatcher not found"
s = s.replace(old_dispatcher, new_dispatcher, 1)
print("Added personalizacao to dispatcher")

# Step 2: Define the new abaPersonalizacao function content
new_func_text = \n\nfunction abaPersonalizacao(corpo) {\n  const cfg = estado.cfgTela;\n  const temaAtual = cfg.tema || \"dark\";\n  corpo.append(\n    el(\"h3\", \"\", \"Personalizacao\"),\n    el(\"p\", \"sub\", \"Escolha o visual da interface:\")\n  );\n  const temas = [\n    { nome: \"Clássico Dark\", cores: {\"--bg\": \"#0e0e13\", \"--painel\": \"#1a1a24\", \"--texto\": \"#e0e0e0\", \"--borda\": \"#3a3a4f\", \"--accent\": \"#6c5ce7\"}},\n    { nome: \"Purpurina\", cores: {\"--bg\": \"#0d0f1a\", \"--painel\": \"#161d3a\", \"--texto\": \"#c0d6e8\", \"--borda\": \"#5a7a9d\", \"--accent\": \"#a94eff\"}},\n    { nome: \"Amethyst\", cores: {\"--bg\": \"#141222\", \"--painel\": \"#2a1a3e\", \"--texto\": \"#d0c0e8\", \"--borda\": \"#6a4a7e\", \"--accent\": \"#b464e4\"}},\n    { nome: \"Ocean\", cores: {\"--bg\": \"#0f2027\", \"--painel\": \"#1b2e3a\", \"--texto\": \"#a8d0e6\", \"--borda\": \"#3d5a7f\", \"--accent\": \"#e05d5d\"}},\n    { nome: \"Forest\", cores: {\"--bg\": \"#0d1b15\", \"--painel\": \"#1a3a2e\", \"--texto\": \"#a8d5ba\", \"--borda\": \"#5a7a5e\", \"--accent\": \"#6d9e4f\"}},\n  ];\n  const sel = el(\"select\");\n  temas.forEach((t, i) => {\n    const o = el(\"option\", \"\", t.nome);\n    o.value = i;\n    sel.append(o);\n  });\n  sel.value = (cfg.temaIdx !== undefined ? cfg.temaIdx : 0);\n  sel.addEventListener(\"change\", async (e) => {\n    const idx = parseInt(e.target.value);\n    const t = temas[idx];\n    // Aplica variáveis CSS imediatamente\n    Object.entries(t.cores).forEach(([k, v]) => document.documentElement.style.setProperty(k, v));\n    // Salva a configuração\n    await chamar(\"config_salvar\", { ...estado.rascunho, chaves: { tema: t.nome, temaIdx: idx } });\n    aviso(\"Tema alterado para \" + t.nome);\n  });\n  corpo.append(sel, el(\"p\", \"sub\", \"Após selecionar, a interface atualizará com o novo tema.\"));\n}\n'''

# Step 3: Insert the new function after the dispatcher line
dispatcher_pos = s.find(new_dispatcher) + len(new_dispatcher)
s = s[:dispatcher_pos] + new_func_text + s[dispatcher_pos:]

# Write back
io.open(fn, "w", encoding="utf-8", newline="\n").write(s)
print("App.js updated successfully")