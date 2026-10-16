import io
p = "D:/Projetos/PesquisaIA/pesquisa_ia.py"
s = io.open(p, encoding="utf-8").read()
old = ("    if profundo:\n"
       "        try:\n"
       "            _extra = _buscar_texto((busca or \"\") + \" noticias\")\n"
       "            vistos = {(i.get(\"href\") or i.get(\"url\") or \"\").strip()\n"
       "                      for i in (resultados or [])}\n"
       "            for item in (_extra or []):\n"
       "                u = (item.get(\"href\") or item.get(\"url\") or \"\").strip()\n"
       "                if u and u not in vistos:\n"
       "                    vistos.add(u)\n"
       "                    (resultados or []).append(item)\n"
       "        except Exception:\n"
       "            pass\n")
new = ("    if profundo:\n"
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
assert old in s
s = s.replace(old, new, 1)
io.open(p, "w", encoding="utf-8", newline="\n").write(s)
print("ok")
