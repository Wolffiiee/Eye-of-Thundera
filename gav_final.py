import io
fn = "D:/Projetos/PesquisaIA/web/app.js"
s = io.open(fn, encoding="utf-8").read()

old = '      const texto = el("span", "editavel", f);\n'
new = (
 '      const gavetaTag = el("span", "gaveta-tag", (gavetas && Object.keys(gavetas).find((g) => (gavetas[g] || []).includes(f))) || "outros");\n'
 '      const texto = el("span", "editavel", f);\n'
)
assert old in s, "old not found"
s = s.replace(old, new, 1)

old2 = '      linha.append(texto, x);'
new2 = '      linha.append(gavetaTag, texto, x);'
assert old2 in s, "old2 not found"
s = s.replace(old2, new2, 1)

io.open(fn, "w", encoding="utf-8", newline="\n").write(s)
print("ok")
"