import io
fn = "D:/Projetos/PesquisaIA/web/app.js"
s = io.open(fn, encoding="utf-8").read()

# 1) add filtroAssunto var
old = 'let filtroGaveta = ""; // "" = todos\n'
new = 'let filtroGaveta = ""; // "" = todos\nlet filtroAssunto = ""; // "" = todos\n'
assert old in s
s = s.replace(old, new, 1)

# 2) insert assuntos chip row right before const topo
needle = '  const topo = el("div", "memoria-topo");'
assert needle in s
block = (
 '  const assuntos = r.assuntos || {};\n'
 '  const assuntosEl = el("div", "gavetas gavetas-filtro");\n'
 '  const allAss = el("button", "badge-gaveta ativo", "todos (assunto) · " + fatos.length);\n'
 '  allAss.title = "Mostrar todos os assuntos";\n'
 '  allAss.addEventListener("click", () => { filtroAssunto = ""; pintarAss(); desenhar(); });\n'
 '  assuntosEl.append(allAss);\n'
 '  for (const k of Object.keys(assuntos)) {\n'
 '    const b = el("button", "badge-gaveta", k + " · " + assuntos[k].length);\n'
 '    b.dataset.assunto = k;\n'
 '    b.addEventListener("click", () => {\n'
 '      filtroAssunto = (filtroAssunto === k ? "" : k);\n'
 '      pintarAss(); desenhar();\n'
 '    });\n'
 '    assuntosEl.append(b);\n'
 '  }\n'
 '  const pintarAss = () => {\n'
 '    assuntosEl.querySelectorAll(".badge-gaveta").forEach((b) => {\n'
 '      if (b.dataset.assunto === undefined) {\n'
 '        b.classList.toggle("ativo", filtroAssunto === "");\n'
 '      } else {\n'
 '        b.classList.toggle("ativo", filtroAssunto === b.dataset.assunto);\n'
 '      }\n'
 '    });\n'
 '  };\n'
)
s = s.replace(needle, block + needle, 1)

# 3) filter in desenhar
old2 = ('    const daGaveta = filtroGaveta ? (gavetas[filtroGaveta] || []) : fatos;\n'
        '    const vistos = daGaveta.filter((f) => !termo || f.toLowerCase().includes(termo));')
new2 = ('    const daGaveta = filtroGaveta ? (gavetas[filtroGaveta] || []) : fatos;\n'
        '    const daAssunto = filtroAssunto ? (assuntos[filtroAssunto] || []) : daGaveta;\n'
        '    const vistos = daAssunto.filter((f) => !termo || f.toLowerCase().includes(termo));')
assert old2 in s
s = s.replace(old2, new2, 1)

# 4) append assuntosEl to corpo before gavetasEl
old3 = 'if (gavetasEl.children && gavetasEl.children.length) corpo.append(gavetasEl);'
new3 = ('if (gavetasEl.children && gavetasEl.children.length) corpo.append(gavetasEl);\n'
        'if (assuntosEl.children && assuntosEl.children.length) corpo.append(assuntosEl);')
assert old3 in s
s = s.replace(old3, new3, 1)

io.open(fn, "w", encoding="utf-8", newline="\n").write(s)
print("ok")
