import io

# 1) memoria.py: add assunto_de + gavetas_por_assunto
p = "D:/Projetos/PesquisaIA/memoria.py"
s = io.open(p, encoding="utf-8").read()

# Add _STOP_ASSUNTO after _TERCEIROS block (before _SEM_INFORMACAO)
needle_stop = '# Respostas vazias do modelo quando nao ha fato novo. NAO sao informacao\n'
assert needle_stop in s
stop_block = (
    "# Palavras que nao servem de assunto (verbos comuns, gavetas fixas).\n"
    "_STOP_ASSUNTO = _PARADAS | frozenset(\n"
    '    "nome mora idade tem gosta prefere chamado apelido natural nasceu "\n'
    '    "faz completa anos gosta de jogar videogame".split()\n'
    ")\n\n"
)
s = s.replace(needle_stop, stop_block + needle_stop, 1)

# Add functions before autoteste()
needle_func = "def autoteste():\n"
assert needle_func in s
funcs = (
    "def assunto_de(fato):\n"
    '    """Rotulo curto de assunto do fato (primeira palavra significativa)."""\n'
    "    texto = _sem_acento(fato)\n"
    "    for p in re.findall(r\"[a-z0-9]+\", texto):\n"
    "        if p in _STOP_ASSUNTO:\n"
    "            continue\n"
    "        if len(p) < 3:\n"
    "            continue\n"
    "        return p[:12]\n"
    "    return \"outros\"\n"
    "\n\n"
    "def gavetas_por_assunto(fatos):\n"
    '    """Agrupa fatos por assunto (rotulo curto)."""\n'
    "    saida = {}\n"
    "    for fato in (fatos or []):\n"
    "        a = assunto_de(fato)\n"
    "        saida.setdefault(a, []).append(fato)\n"
    "    # ordena pelas gavetas com mais fatos primeiro\n"
    "    return dict(sorted(saida.items(), key=lambda kv: -len(kv[1])))\n"
    "\n\n"
)
s = s.replace(needle_func, funcs + needle_func, 1)
io.open(p, "w", encoding="utf-8", newline="\n").write(s)
print("memoria.py patched")

# 2) pesquisa_ia.py: add carregar_memoria_por_assunto
p2 = "D:/Projetos/PesquisaIA/pesquisa_ia.py"
s2 = io.open(p2, encoding="utf-8").read()
needle2 = "def organizar_memoria():\n"
assert needle2 in s2
helper = (
    "def carregar_memoria_por_assunto():\n"
    '    """Memoria agrupada por assunto (read-only)."""\n'
    "    return memoria.gavetas_por_assunto(carregar_memoria())\n"
    "\n\n"
)
s2 = s2.replace(needle2, helper + needle2, 1)
io.open(p2, "w", encoding="utf-8", newline="\n").write(s2)
print("pesquisa_ia.py patched")

# 3) app_web.py: memoria_listar include assuntos
p3 = "D:/Projetos/PesquisaIA/app_web.py"
s3 = io.open(p3, encoding="utf-8").read()
old = ('        return {"fatos": fatos, "datas": p.carregar_memoria_datas(),\n'
       '                "gavetas": p.carregar_memoria_gavetas()}\n')
new = ('        return {"fatos": fatos, "datas": p.carregar_memoria_datas(),\n'
       '                "gavetas": p.carregar_memoria_gavetas(),\n'
       '                "assuntos": p.carregar_memoria_por_assunto()}\n')
assert old in s3
s3 = s3.replace(old, new, 1)
io.open(p3, "w", encoding="utf-8", newline="\n").write(s3)
print("app_web.py patched")
