import io
fn = "D:/Projetos/PesquisaIA/web/app.js"
s = io.open(fn, encoding="utf-8").read()

old1 = ('  corpo.append(\n'
        '    cartaoChave("Google Gemini (principal)", "\ufffd% ela que pesquisa e escreve as respostas.", "api_key", cfg.gemini, {\n'
        '      testar: true,\n'
        '      pagina: "https://aistudio.google.com/apikey",\n'
        '    }),\n'
        '    cartaoChave("Google Gemini (reserva, opcional)", "Se a principal parar de funcionar, o programa troca sozinho para esta.", "api_key_reserva", cfg.gemini_reserva, { testar: true\n'
        '  );\n'
        '  const plano = el("div", "cartao");\n'
        '  plano.append(linhaToggle("Usar o plano B", "Se o Gemini n\u00fbo responder, tenta estes servi\u00e7os de reserva.", "usar_plano_b"));\n'
        '  corpo.append(plano);\n'
        '  const geminiCard = el("div", "cartao");\n'
        '  geminiCard.append(linhaToggle("Usar o Gemini (principal)",\n'
        '    "Desliga o Gemini e usa so o plano B (ChatGPT/Groq/OpenRouter).",\n'
        '    "usar_gemini"));\n'
        '  corpo.append(geminiCard);\n'
        '  for (const s of cfg.servicos) {')
# That's too fragile with encoding. Use line-based instead.
"placeholder"
""

# Use line-based approach instead
lines = s.splitlines(keepends=True)
# Find the abaChaves function
start_idx = None
for i, l in enumerate(lines):
    if 'function abaChaves(corpo)' in l:
        start_idx = i
        break
assert start_idx is not None
# Find end of function (closing brace at column 0)
end_idx = None
for j in range(start_idx + 1, len(lines)):
    if lines[j].strip() == '}':
        end_idx = j
        break
assert end_idx is not None

# Rebuild the function body with geminiCard at top
new_func = '''function abaChaves(corpo) {
  const cfg = estado.cfgTela;
  const geminiCard = el("div", "cartao");
  geminiCard.append(linhaToggle("Usar o Gemini (principal)",
    "Desliga o Gemini e usa so o plano B (ChatGPT/Groq/OpenRouter).",
    "usar_gemini"));
  corpo.append(geminiCard);
  corpo.append(
    cartaoChave("Google Gemini (principal)", "% ela que pesquisa e escreve as respostas.", "api_key", cfg.gemini, {
      testar: true,
      pagina: "https://aistudio.google.com/apikey",
    }),
    cartaoChave("Google Gemini (reserva, opcional)", "Se a principal parar de funcionar, o programa troca sozinho para esta.", "api_key_reserva", cfg.gemini_reserva, { testar: true })
  );
  const plano = el("div", "cartao");
  plano.append(linhaToggle("Usar o plano B", "Se o Gemini nao responder, tenta estes servicos de reserva.", "usar_plano_b"));
  corpo.append(plano);
  for (const s of cfg.servicos) {
    corpo.append(cartaoChave(s.nome, s.resumo ? "Gratis: " + s.resumo : "", s.campo, s, { passos: s.passos, pagina: s.pagina }));
  }
}
'''
lines[start_idx:end_idx+1] = [new_func + "\n"]

# ===== Fix 4: Reposition context menu after async suggestions load =====
s2 = "".join(lines)
old4 = ('      for (const s of ss) {\n'
        '        menu.append(itemMenu(s, () => {\n'
        '          substituirTrecho(ini, fim, s);\n'
        '          fecharMenuContexto();\n'
        '        }));\n'
        '      }\n')
new4 = ('      for (const s of ss) {\n'
        '        menu.append(itemMenu(s, () => {\n'
        '          substituirTrecho(ini, fim, s);\n'
        '          fecharMenuContexto();\n'
        '        }));\n'
        '      }\n'
        '      // reajusta a posicao depois que as sugestoes cresceram o menu\n'
        '      const l2 = Math.min(x, window.innerWidth - menu.offsetWidth - 8);\n'
        '      const a2 = Math.min(y, window.innerHeight - menu.offsetHeight - 8);\n'
        '      menu.style.left = Math.max(8, l2) + "px";\n'
        '      menu.style.top = Math.max(8, a2) + "px";\n')
assert old4 in s2, "old4 not found"
s2 = s2.replace(old4, new4, 1)

# ===== Fix 3: text_select=True in create_window =====
fn2 = "D:/Projetos/PesquisaIA/app_web.py"
s3 = io.open(fn2, encoding="utf-8").read()
old3 = '         easy_drag=False,\n     )\n'
new3 = '         easy_drag=False,\n         text_select=True,\n     )\n'
assert old3 in s3, "old3 not found"
s3 = s3.replace(old3, new3, 1)
io.open(fn2, "w", encoding="utf-8", newline="\n").write(s3)

io.open(fn, "w", encoding="utf-8", newline="\n").write(s2)
print("patched all")
