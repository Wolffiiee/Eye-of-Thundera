import io
p = "D:/Projetos/PesquisaIA/verificar.py"
s = io.open(p, encoding="utf-8").read()
anchor = "# --- resumo -----------------------------------------------------------------\n"
assert anchor in s
block = (
    "\n"
    "# --- gavetas por assunto / memoria evidence ----------------------\n"
    "try:\n"
    "    import memoria as _mem\n"
    "    _f = _mem.gavetas_por_assunto([\n"
    "        \"Gosta de jogar videogame\", \"Mora em Santa Maria\",\n"
    "        \"Prefere ser chamado de Wolf\"])\n"
    "    if isinstance(_f, dict) and len(_f) >= 1:\n"
    "        ok(\"gavetas por assunto: agrupa fatos em dict\")\n"
    "    else:\n"
    "        falha(\"gavetas por assunto: resultado inesperado %r\" % (_f,))\n"
    "    if _mem.assunto_de(\"Gosta de jogar videogame\"):\n"
    "        ok(\"assunto_de: retorna rotulo nao vazio\")\n"
    "    else:\n"
    "        falha(\"assunto_de: retornou vazio\")\n"
    "except Exception as _e:\n"
    "    falha(\"gavetas por assunto quebrou: %r\" % (_e,))\n"
    "\n"
    '_g = Path(PASTA / "web" / "app.js").read_text(encoding="utf-8")\n'
    'if "assuntos" in _g and "gavetas" in _g:\n'
    '    ok("UI: assuntos e gavetas presentes na tela")\n'
    'else:\n'
    '    falha("UI: assuntos/gavetas ausentes")\n'
    "\n"
)
s = s.replace(anchor, block + anchor, 1)
io.open(p, "w", encoding="utf-8", newline="\n").write(s)
print("ok")
