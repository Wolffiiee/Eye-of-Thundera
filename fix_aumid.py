import io
p = "D:/Projetos/PesquisaIA/app_web.py"
s = io.open(p, encoding="utf-8").read()

# 1) Remove the late call (before webview.start)
old_late = ('        # Nome do app na barra de tarefas (em vez de "IDLE (Python 3.12)").\n'
            '        try:\n'
            '            import ctypes\n'
            '            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(\n'
            '                "Eye of Thundera")\n'
            '        except Exception:\n'
            '            pass\n'
            '        webview.start(ao_abrir, janela, gui="edgechromium",\n'
            '                      icon=str(RAIZ / "icone.ico"))\n')
new_late = ('        webview.start(ao_abrir, janela, gui="edgechromium",\n'
            '                      icon=str(RAIZ / "icone.ico"))\n')
assert old_late in s, "late block not found"
s = s.replace(old_late, new_late, 1)

# 2) Add early call at module level (after RAIZ definition, before WEB)
old_early = 'WEB = RAIZ / "web"\n'
new_early = ('# Nome do app na barra de tarefas (em vez de "pythonw"/"IDLE").\n'
             'try:\n'
             '    import ctypes\n'
             '    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(\n'
             '        "Eye of Thundera")\n'
             'except Exception:\n'
             '    pass\n'
             '\n'
             'WEB = RAIZ / "web"\n')
assert old_early in s
s = s.replace(old_early, new_early, 1)

io.open(p, "w", encoding="utf-8", newline="\n").write(s)
print("ok")
