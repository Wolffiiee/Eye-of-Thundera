import io

# 1) index.html: add "Serio" button next to send
fn = "D:/Projetos/PesquisaIA/web/index.html"
s = io.open(fn, encoding="utf-8").read()
old = '          <button id="btn-enviar" class="enviar" title="Enviar (Enter)" disabled><svg><use href="#i-enviar"/></svg></button>'
new = ('          <button id="btn-serio" class="enviar serio" title="Pesquisa profunda: organiza em topicos e cita fontes (Ctrl+Shift+S)" disabled><svg><use href="#i-brilho"/></svg></button>\n'
       '          <button id="btn-enviar" class="enviar" title="Enviar (Enter)" disabled><svg><use href="#i-enviar"/></svg></button>')
assert old in s, "html old"
s = s.replace(old, new, 1)
io.open(fn, "w", encoding="utf-8", newline="\n").write(s)

# 2) app.js: wire btn-serio to send with profundo=True
fn2 = "D:/Projetos/PesquisaIA/web/app.js"
s2 = io.open(fn2, encoding="utf-8").read()

# add to atualizarEnviar: enable/disable btn-serio alongside btn-enviar
old2 = '  $("#btn-enviar").disabled = estado.ocupado || !$("#entrada").value.trim();'
new2 = ('  $("#btn-enviar").disabled = estado.ocupado || !$("#entrada").value.trim();\n'
        '  $("#btn-serio").disabled = estado.ocupado || !$("#entrada").value.trim();')
assert old2 in s2
s2 = s2.replace(old2, new2, 1)

# wire click
old3 = '$("#btn-enviar").addEventListener("click", () => enviar());'
new3 = ('$("#btn-enviar").addEventListener("click", () => enviar());\n'
        '$("#btn-serio").addEventListener("click", () => enviar(undefined, true));')
assert old3 in s2
s2 = s2.replace(old3, new3, 1)

# Ctrl+Shift+S shortcut for deep
old4 = '  if (e.key === "Enter" && !e.shiftKey && !e.isComposing) {'
new4 = ('  if (e.key === "S" && e.ctrlKey && e.shiftKey) { e.preventDefault(); enviar(undefined, true); return; }\n'
        '  if (e.key === "Enter" && !e.shiftKey && !e.isComposing) {')
assert old4 in s2
s2 = s2.replace(old4, new4, 1)

io.open(fn2, "w", encoding="utf-8", newline="\n").write(s2)
print("patched")
