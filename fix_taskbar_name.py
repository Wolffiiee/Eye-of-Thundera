import io
p = "D:/Projetos/PesquisaIA/app_web.py"
s = io.open(p, encoding="utf-8").read()

# Add AppUserModelID setting before webview.start
old = '        webview.start(ao_abrir, janela, gui="edgechromium",\n                      icon=str(RAIZ / "icone.ico"))\n'
new = ('        # Nome do app na barra de tarefas (em vez de "IDLE (Python 3.12)").\n'
       '        try:\n'
       '            import ctypes\n'
       '            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(\n'
       '                "Eye of Thundera")\n'
       '        except Exception:\n'
       '            pass\n'
       '        webview.start(ao_abrir, janela, gui="edgechromium",\n'
       '                      icon=str(RAIZ / "icone.ico"))\n')
assert old in s
s = s.replace(old, new, 1)
io.open(p, "w", encoding="utf-8", newline="\n").write(s)
print("ok")
