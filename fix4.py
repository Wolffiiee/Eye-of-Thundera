import io

# Fix 4: Reposition context menu after async suggestions load (app.js)
fn = "D:/Projetos/PesquisaIA/web/app.js"
s = io.open(fn, encoding="utf-8").read()
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
        '      // reajusta a posicao depois que as sugestoes cresceram o menu\n'
        '      const l2 = Math.min(x, window.innerWidth - menu.offsetWidth - 8);\n'
        '      const a2 = Math.min(y, window.innerHeight - menu.offsetHeight - 8);\n'
        '      menu.style.left = Math.max(8, l2) + "px";\n'
        '      menu.style.top = Math.max(8, a2) + "px";\n'
        '    });\n')
assert old4 in s, "old4 not found"
s = s.replace(old4, new4, 1)
io.open(fn, "w", encoding="utf-8", newline="\n").write(s)
print("app.js fix4 patched")

# Fix 3: text_select=True in create_window (app_web.py)
fn2 = "D:/Projetos/PesquisaIA/app_web.py"
s2 = io.open(fn2, encoding="utf-8").read()
old3 = '        easy_drag=False,\n    )\n'
new3 = '        easy_drag=False,\n        text_select=True,\n    )\n'
assert old3 in s2, "old3 not found"
s2 = s2.replace(old3, new3, 1)
io.open(fn2, "w", encoding="utf-8", newline="\n").write(s2)
print("app_web.py fix3 patched")
