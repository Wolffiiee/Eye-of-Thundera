import io
fn = "D:/Projetos/PesquisaIA/web/app.js"
L = io.open(fn, encoding="utf-8").read().splitlines(keepends=True)

# Locate abaChaves
start = next(i for i, l in enumerate(L) if "function abaChaves(corpo)" in l)
end = next(j for j in range(start+1, len(L)) if L[j].strip() == "}")
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
L[start:end+1] = [new_func + "\n"]

# Add right-click copy handler in ligarMenuContexto (after the contextmenu listener for campo)
s = "".join(L)
old = '  window.addEventListener("blur", fecharMenuContexto);\n'
new = ('  window.addEventListener("blur", fecharMenuContexto);\n'
       '  // copiar texto selecionado na RESPOSTA da IA (botao direito)\n'
       '  document.addEventListener("contextmenu", (e) => {\n'
       '    const sel = (window.getSelection() || "").toString().trim();\n'
       '    if (sel && e.target && e.target.closest && e.target.closest(".corpo")) {\n'
       '      e.preventDefault();\n'
       '      try { navigator.clipboard.writeText(sel); } catch (_e) {\n'
       '        const ta = document.createElement("textarea");\n'
       '        ta.value = sel; document.body.appendChild(ta);\n'
       '        ta.select(); document.execCommand("copy"); ta.remove();\n'
       '      }\n'
       '      aviso("Copiado.");\n'
       '    }\n'
       '  });\n')
assert old in s
s = s.replace(old, new, 1)

# Fix 4 reposition (if not already)
old4 = ('      for (const s of ss) {\n'
        '        menu.append(itemMenu(s, () => {\n'
        '          substituirTrecho(ini, fim, s);\n'
        '          fecharMenuContexto();\n'
        '        }));\n'
        '      }\n'
        '    });\n')
new4 = ('      for (const s of ss) {\n'
        '        menu.append(itemMenu(s, () => {\n'
        '          substituirTrecho(ini, fim, s);\n'
        '          fecharMenuContexto();\n'
        '        }));\n'
        '      }\n'
        '      const l2 = Math.min(x, window.innerWidth - menu.offsetWidth - 8);\n'
        '      const a2 = Math.min(y, window.innerHeight - menu.offsetHeight - 8);\n'
        '      menu.style.left = Math.max(8, l2) + "px";\n'
        '      menu.style.top = Math.max(8, a2) + "px";\n'
        '    });\n')
if old4 in s:
    s = s.replace(old4, new4, 1)

io.open(fn, "w", encoding="utf-8", newline="\n").write(s)
print("patched")
