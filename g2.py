import io, re

# ---- memoria.py: add public gavetator de fatos
p = "D:/Projetos/PesquisaIA/memoria.py"
s = io.open(p, encoding="utf-8").read()
# Add gavetas_de after _gaveta function
needle = "    for nome, rx in _GAVETAS:\n        if rx.search(t):\n            return nome\n    return None\n"
add = needle + "\n\ndef gavetas_de(fatos):\n    \"\"\"Devolve {nome: [...], mora: [...], idade: [...], outros: [...]}.\n\n    Fatos sem gaveta reconhecida (ou de terceiros) caem no 'outros'.\n    Nao remove nada, serve para a tela agrupar/exibir chests.\n    \"\"\"\n    saida = {\n        \"nome\": [], \"mora\": [], \"idade\": [], \"outros\": [],\n    }\n    for fato in fatos or []:\n        g = _gaveta(fato)\n        if g in saida and g is not None:\n            saida[g].append(fato)\n        else:\n            saida[\"outros\"].append(fato)\n    # tira gavetas vazias\n    return {k: v for k, v in saida.items() if v}\n\ndef gavetas_nomes():\n    \"\"\"Labels disponiveis (para ordenar a tela).\"\"\"\n    return [\"nome\", \"mora\", \"idade\", \"outros\"]\n"
assert needle in s
s = s.replace(needle, add, 1)
io.open(p, "w", encoding="utf-8", newline="\n").write(s)
print("memoria.py patched")

# ---- pesquisa_ia.py: add helper
p2 = "D:/Projetos/PesquisaIA/pesquisa_ia.py"
s2 = io.open(p2, encoding="utf-8").read()
if "import memoria" not in s2:
    raise Exception("memoria import check manual")
# insert helper right after organizar_memoria
needle2 = "def organizar_memoria():\n"
ins = (
    "def carregar_memoria_gavetas():\n"
    "    \"\"\"Memoria agrupada por gaveta (read-only).\"\"\"\n"
    "    return memoria.gavetas_de(carregar_memoria())\n"
    "\n\n"
)
assert needle2 in s2
s2 = s2.replace(needle2, ins + needle2, 1)
io.open(p2, "w", encoding="utf-8", newline="\n").write(s2)
print("pesquisa_ia.py patched")

# ---- app_web.py: memoria_listar include gavetas
p3 = "D:/Projetos/PesquisaIA/app_web.py"
s3 = io.open(p3, encoding="utf-8").read()
old = "        fatos = p.carregar_memoria()\n        return {\"fatos\": fatos, \"datas\": p.carregar_memoria_datas()}\n"
new = ("        fatos = p.carregar_memoria()\n"
       "        return {\"fatos\": fatos, \"datas\": p.carregar_memoria_datas(),\n"
       "                \"gavetas\": p.carregar_memoria_gavetas()}\n")
assert old in s3
s3 = s3.replace(old, new, 1)
io.open(p3, "w", encoding="utf-8", newline="\n").write(s3)
print("app_web.py patched")
