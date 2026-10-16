import io
p = "D:/Projetos/PesquisaIA/web/estilo.css"
s = io.open(p, encoding="utf-8").read()
needle = ".enviar:disabled { background: var(--superficie-2); color: var(--texto-3); opacity: 1; }"
assert needle in s
add = needle + "\n.enviar.serio { background: #5b3fa0; }\n.enviar.serio:hover:not(:disabled) { background: #6d4db8; }\n"
s = s.replace(needle, add, 1)
io.open(p, "w", encoding="utf-8", newline="\n").write(s)
print("ok")
