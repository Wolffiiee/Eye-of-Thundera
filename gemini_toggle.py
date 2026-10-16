import io

# ---- pesquisa_ia.py ----
p = "D:/Projetos/PesquisaIA/pesquisa_ia.py"
s = io.open(p, encoding="utf-8").read()

# 1) cfg.setdefault usar_gemini
old = '    cfg.setdefault("usar_plano_b", True)\n'
new = '    cfg.setdefault("usar_plano_b", True)\n    cfg.setdefault("usar_gemini", True)\n'
assert old in s
s = s.replace(old, new, 1)

# 2) _gerar_texto: skip Gemini if usar_gemini False
old2 = '    amigo = (modo == "amigo")\n    cliente = _criar_cliente(api_key)\n    ordem = [modelo] + [m for m in MODELOS_RESERVA if m != modelo]\n    ultimo_erro = None\n'
new2 = ('    amigo = (modo == "amigo")\n'
        '    usar_gemini = True if not cfg else bool(cfg.get("usar_gemini", True))\n'
        '    cliente = _criar_cliente(api_key) if usar_gemini else None\n'
        '    ordem = [modelo] + [m for m in MODELOS_RESERVA if m != modelo]\n'
        '    ultimo_erro = None\n')
assert old2 in s
s = s.replace(old2, new2, 1)

# Wrap the Gemini for-loop in if usar_gemini
old3 = '    for _rodada in range(2):\n        for nome in ordem:\n'
new3 = '    if usar_gemini:\n        for _rodada in range(2):\n            for nome in ordem:\n'
assert old3 in s
s = s.replace(old3, new3, 1)

# Need to fix indentation of the Gemini loop body (add 4 spaces). This is tricky.
# Instead, let's do a different approach: keep the loop but guard with if.
# Actually the above replacement breaks indentation. Let me revert and use a simpler guard.
# Revert
s = s.replace(new3, old3, 1)

# Simpler: add early return to plano B if not usar_gemini, before Gemini loop
# Insert before "for _rodada in range(2):"
guard = ('    if not usar_gemini:\n'
         '        ultimo_erro = RuntimeError("Gemini desligado pelo usuario.")\n'
         '    else:\n')
# We need to indent the for-loop. Too complex. Instead, wrap differently:
# Use a flag: if not usar_gemini, skip the entire Gemini block.
# Let's just patch the condition at the loop start with a guard that breaks out.
# Simplest: replace "    for _rodada in range(2):" with guard + indented loop is hard.
# Alternative: add "if not usar_gemini: pass" won't skip.
# Let's instead modify _gerar_texto to early-try plano B when usar_gemini False.

# Approach: before the for loop, if not usar_gemini, jump to plano B section.
# We can't easily jump. Instead, let's make the loop condition include usar_gemini.
old4 = '    for _rodada in range(2):\n        for nome in ordem:\n'
new4 = '    if usar_gemini:\n        for _rodada in range(2):\n            for nome in ordem:\n'
assert old4 in s
s = s.replace(old4, new4, 1)

# Now indent the body of the for loop (lines until "time.sleep(1.5)") by 4 spaces.
# Find the range
lines = s.splitlines(keepends=True)
start = None
for i, l in enumerate(lines):
    if '    if usar_gemini:' in l and i > 0:
        start = i + 2  # first line inside (for _rodada)
        break
# find end: the line with "time.sleep(1.5)" 
end = None
for j in range(start, len(lines)):
    if 'time.sleep(1.5)' in lines[j]:
        end = j
        break
assert start is not None and end is not None
# Indent lines from start to end (inclusive) by 4 spaces
for k in range(start, end + 1):
    if lines[k].strip():
        lines[k] = "    " + lines[k]
s = "".join(lines)

# Now the plano B section: guard with "if com_plano_b or not usar_gemini:"
# Already has "if com_plano_b:". Change to "if com_plano_b or not usar_gemini:"
old5 = '    if com_plano_b:\n        servicos = _servicos_prontos(cfg)\n'
new5 = '    if com_plano_b or not usar_gemini:\n        servicos = _servicos_prontos(cfg)\n'
assert old5 in s
s = s.replace(old5, new5, 1)

# 3) _gerar_texto_rapido: skip Gemini if usar_gemini False
old6 = '    servicos = _servicos_prontos(cfg) if cfg else []\n'
new6 = ('    usar_gemini = True if not cfg else bool(cfg.get("usar_gemini", True))\n'
        '    servicos = _servicos_prontos(cfg) if cfg else []\n')
assert old6 in s
s = s.replace(old6, new6, 1)

# andamento init
old7 = '    andamento = {"gemini": True, "plano_b": True}\n'
new7 = '    andamento = {"gemini": usar_gemini, "plano_b": bool(servicos)}\n'
assert old7 in s
s = s.replace(old7, new7, 1)

# correr_gemini guard: only start if usar_gemini and api_key
old8 = '    def correr_gemini():\n'
# We'll guard the thread start instead
old9 = '    threading.Thread(target=correr_gemini, daemon=True).start()\n'
new9 = ('    if usar_gemini and api_key:\n'
        '        threading.Thread(target=correr_gemini, daemon=True).start()\n')
assert old9 in s
s = s.replace(old9, new9, 1)

# If neither gemini nor servicos, raise early
old10 = '    if not servicos:\n        # sem plano B nao ha corrida: e so o Gemini mesmo\n        return _gerar_texto(api_key, modelo, prompt, historico, cfg)\n'
new10 = ('    if not servicos and not usar_gemini:\n'
         '        raise RuntimeError("Gemini desligado e nenhum servico de plano B ativo.")\n'
         '    if not servicos:\n'
         '        # sem plano B nao ha corrida: e so o Gemini mesmo\n'
         '        return _gerar_texto(api_key, modelo, prompt, historico, cfg)\n')
assert old10 in s
s = s.replace(old10, new10, 1)

io.open(p, "w", encoding="utf-8", newline="\n").write(s)
print("pesquisa_ia.py patched")
