import io
fn = "D:/Projetos/PesquisaIA/web/app.js"
s = io.open(fn, encoding="utf-8").read()

# rascunho include usar_gemini
old = "    modo_pesquisa: r.modo_pesquisa, usar_contexto: r.usar_contexto, aprender: r.aprender,\n    web_corretor: r.web_corretor, voz_enviar: r.voz_enviar, usar_plano_b: r.usar_plano_b,\n"
new = ("    modo_pesquisa: r.modo_pesquisa, usar_contexto: r.usar_contexto, aprender: r.aprender,\n"
       "    web_corretor: r.web_corretor, voz_enviar: r.voz_enviar, usar_plano_b: r.usar_plano_b,\n"
       "    usar_gemini: r.usar_gemini,\n")
assert old in s
s = s.replace(old, new, 1)

# abaChaves: add toggle after plano B card (before servicos loop)
old2 = '  corpo.append(plano);\n  for (const s of cfg.servicos) {'
new2 = ('  corpo.append(plano);\n'
        '  const geminiCard = el("div", "cartao");\n'
        '  geminiCard.append(linhaToggle("Usar o Gemini (principal)",\n'
        '    "Desliga o Gemini e usa so o plano B (ChatGPT/Groq/OpenRouter).",\n'
        '    "usar_gemini"));\n'
        '  corpo.append(geminiCard);\n'
        '  for (const s of cfg.servicos) {')
assert old2 in s
s = s.replace(old2, new2, 1)

io.open(fn, "w", encoding="utf-8", newline="\n").write(s)
print("ok")
