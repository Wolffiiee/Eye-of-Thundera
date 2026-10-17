import io

# Fix 1: Update colar messages to use accented characters
fn = "D:/Projetos/PesquisaIA/web/app.js"
s = io.open(fn, encoding="utf-8").read()

# Replace unaccented messages with accented ones
s = s.replace('aviso(r.erro + " Use Ctrl+V.", true);',
              'aviso(r.erro + " Use Ctrl+V.", true);')
s = s.replace('aviso("Nao consegui acessar a area de transferencia. Use Ctrl+V.", true);',
              'aviso("N\u00e3o consegui acessar a \u00e1rea de transfer\u00eancia. Use Ctrl+V.", true);')

io.open(fn, "w", encoding="utf-8", newline="\n").write(s)
print("app.js: updated colar messages with accents")

# Fix 2: Remove unused ctypes.wintypes import
fn2 = "D:/Projetos/PesquisaIA/app_web.py"
s2 = io.open(fn2, encoding="utf-8").read()
old = '''            try:
                import ctypes
                from ctypes import wintypes
                CF_UNICODETEXT = 13'''
new = '''            try:
                import ctypes
                CF_UNICODETEXT = 13'''
assert old in s2, "import not found"
s2 = s2.replace(old, new, 1)
io.open(fn2, "w", encoding="utf-8", newline="\n").write(s2)
print("app_web.py: removed unused ctypes.wintypes import")