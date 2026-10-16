import io
p = "D:/Projetos/PesquisaIA/web/app.js"
L = io.open(p, encoding="utf-8").read().splitlines(keepends=True)
# find the extra lone brace after pintarativo definition
needle = "  };\n  }\n  const topo = el(\"div\", \"memoria-topo\");"
assert needle in "".join(L), "needle"
s = "".join(L)
s = s.replace(needle, "  };\n  const topo = el(\"div\", \"memoria-topo\");", 1)
io.open(p, "w", encoding="utf-8", newline="\n").write(s)
print("ok")
