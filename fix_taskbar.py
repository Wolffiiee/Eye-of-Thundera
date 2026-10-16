import io
p = "D:/Projetos/PesquisaIA/app_web.py"
s = io.open(p, encoding="utf-8").read()
old = '        webview.start(ao_abrir, janela, gui="edgechromium")\n'
new = '        webview.start(ao_abrir, janela, gui="edgechromium",\n                      icon=str(RAIZ / "icone.ico"))\n'
assert old in s
s = s.replace(old, new, 1)
io.open(p, "w", encoding="utf-8", newline="\n").write(s)
print("ok")
