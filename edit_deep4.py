import io
p = "D:/Projetos/PesquisaIA/pesquisa_ia.py"
L = io.open(p, encoding="utf-8").read().splitlines(keepends=True)

# Find start line (comment) and end (pass before blank)
start = None
for i,l in enumerate(L):
    if l.strip().startswith("# Pesquisa profunda: fonte extra"):
        start = i
        break
assert start is not None
# find the 'pass' after start
end = None
for j in range(start, len(L)):
    if L[j].strip() == "pass" and j > start:
        end = j
        break
assert end is not None
# include through end
new_block = (
    '    # Pesquisa profunda: varias queries (sem gastar IA) para cobrir\n'
    '    # mais fontes. As variacoes sao simples e baratas.\n'
    '    if profundo:\n'
    '        _variacoes = (\n'
    '            (busca or ""),\n'
    '            (busca or "") + " principais",\n'
    '            (busca or "") + " atual",\n'
    '            (busca or "") + " detalhes",\n'
    '        )\n'
    '        for _q in _variacoes:\n'
    '            try:\n'
    '                _extra = _buscar_texto(_q)\n'
    '                vistos = {(i.get("href") or i.get("url") or "").strip()\n'
    '                          for i in (resultados or [])}\n'
    '                for item in (_extra or []):\n'
    '                    u = (item.get("href") or item.get("url") or "").strip()\n'
    '                    if u and u not in vistos:\n'
    '                        vistos.add(u)\n'
    '                        (resultados or []).append(item)\n'
    '            except Exception:\n'
    '                pass\n'
    "\n"
)
L[start:end+1] = [new_block]

# Increase page reading
for i,l in enumerate(L):
    if "_conteudo_das_paginas(resultados, quantidade=(8 if profundo else 4))" in l:
        L[i] = l.replace("_conteudo_das_paginas(resultados, quantidade=(8 if profundo else 4))",
                          "_conteudo_das_paginas(resultados, quantidade=(12 if profundo else 4))")
        print("quantity updated")

# Improve prompt emphasis
for i,l in enumerate(L):
    if "MODO PESQUISA PROFUNDA: organize a resposta em topicos curtos," in l:
        L[i] = '            "\\n\\nMODO PESQUISA PROFUNDA: organize a resposta em topicos curtos, "\n'
        # replace next 3 lines
        L[i+1] = '            "cite site(s) fonte por paragrafo, crie secao \'fontes\' final. "\n'
        L[i+2] = '            "Seja mais detalhada (3-5 paragrafos)."\n'
        print("prompt updated line", i+1)
        break

io.open(p, "w", encoding="utf-8", newline="\n").write("".join(L))
print("done")
