import io
p = "D:/Projetos/PesquisaIA/pesquisa_ia.py"
s = io.open(p, encoding="utf-8").read()

# 1) Replace profundo extra-search block with multi-query (4 variations)
old = ("    # Pesquisa profunda: fonte extra com varia��ǜo da busca, sem gastar IA.\n"
       "    if profundo:\n"
       "        for _q in ((busca or \"\") + \" noticias\",\n"
       "                   (busca or \"\") + \" informacoes\"):\n"
       "            try:\n"
       "                _extra = _buscar_texto(_q)\n"
       "                vistos = {(i.get(\"href\") or i.get(\"url\") or \"\").strip()\n"
       "                          for i in (resultados or [])}\n"
       "                for item in (_extra or []):\n"
       "                    u = (item.get(\"href\") or item.get(\"url\") or \"\").strip()\n"
       "                    if u and u not in vistos:\n"
       "                        vistos.add(u)\n"
       "                        (resultados or []).append(item)\n"
       "            except Exception:\n"
       "                pass\n")
new = ("    # Pesquisa profunda: varias queries (sem gastar IA) para cobrir\n"
       "    # mais fontes. As variacoes sao simples e baratas.\n"
       "    if profundo:\n"
       "        _variacoes = (\n"
       "            (busca or \"\"),\n"
       "            (busca or \"\") + \" principais\",\n"
       "            (busca or \"\") + \" atual\",\n"
       "            (busca or \"\") + \" detalhes\",\n"
       "        )\n"
       "        for _q in _variacoes:\n"
       "            try:\n"
       "                _extra = _buscar_texto(_q)\n"
       "                vistos = {(i.get(\"href\") or i.get(\"url\") or \"\").strip()\n"
       "                          for i in (resultados or [])}\n"
       "                for item in (_extra or []):\n"
       "                    u = (item.get(\"href\") or item.get(\"url\") or \"\").strip()\n"
       "                    if u and u not in vistos:\n"
       "                        vistos.add(u)\n"
       "                        (resultados or []).append(item)\n"
       "            except Exception:\n"
       "                pass\n")
assert old in s, "old block not found"
s = s.replace(old, new, 1)

# 2) Increase page reading to 12 in deep mode
old2 = "    conteudos = _conteudo_das_paginas(resultados, quantidade=(8 if profundo else 4))\n"
new2 = "    conteudos = _conteudo_das_paginas(resultados, quantidade=(12 if profundo else 4))\n"
assert old2 in s, "old2 not found"
s = s.replace(old2, new2, 1)

# 3) Improve prompt emphasis for deep research
old3 = ("    if profundo:\n"
        "        prompt += (\n"
        "            \"\\n\\nMODO PESQUISA PROFUNDA: organize a resposta em topicos curtos, \"\n"
        "            \"cite site(s) fonte por paragrafo, crie secao 'fontes' final. \"\n"
        "            \"Seja mais detalhada (3-5 paragrafos).\"\n"
        "        )\n")
new3 = ("    if profundo:\n"
        "        prompt += (\n"
        "            \"\\n\\nMODO PESQUISA PROFUNDA: a resposta deve ser detalhada e \"\n"
        "            \"organizada em topico(s) com titulo, cada topico com 2-4 \"\n"
        "            \"paragrafos, citando a fonte (URL) de cada afirmacao. \"\n"
        "            \"Ao final, crie uma secao 'FONTES CONSULTADAS' listando \"\n"
        "            \"todas as URLs usadas. Nao invente fontes.\"\n"
        "        )\n")
assert old3 in s, "old3 not found"
s = s.replace(old3, new3, 1)

io.open(p, "w", encoding="utf-8", newline="\n").write(s)
print("pesquisa_ia.py patched (multi-query deep)")
