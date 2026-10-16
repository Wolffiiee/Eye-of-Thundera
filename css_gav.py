import io
p = "D:/Projetos/PesquisaIA/web/estilo.css"
s = io.open(p, encoding="utf-8").read()

# Add CSS for gavetas at the end of the file
css = '''
/* ---- gavetas de memoria (chips e secoes) ---- */
.gavetas { display: flex; flex-wrap: wrap; gap: 6px; margin: 8px 0 12px; }
.gavetas-filtro { padding: 6px; background: var(--superficie); border: 1px solid var(--borda);
  border-radius: 12px; }
.badge-gaveta { padding: 4px 10px; border-radius: 999px; font-size: 12px;
  background: var(--superficie-2); color: var(--texto-2); border: 1px solid var(--borda);
  cursor: pointer; transition: background .15s, color .15s, border-color .15s; }
.badge-gaveta:hover { background: var(--superficie-3, #2a2a3a); color: var(--texto); }
.badge-gaveta.ativo { background: #1c2447; color: #b8c8ff; border-color: #34458f; }
.gaveta-secao { margin: 10px 0; border: 1px solid var(--borda); border-radius: 12px;
  background: var(--superficie); overflow: hidden; }
.gaveta-secao summary { cursor: pointer; padding: 8px 12px; font-size: 13px;
  font-weight: 600; color: var(--texto); background: var(--superficie-2);
  border-bottom: 1px solid var(--borda); }
.gaveta-secao summary:hover { background: var(--superficie-3, #2a2a3a); }
.gaveta-lista { padding: 8px 10px; display: flex; flex-direction: column; gap: 6px; }
.fato-compacto { font-size: 13px; }
.gaveta-secao .btn { margin: 8px 10px 10px; font-size: 12px; }
'''

if ".gavetas {" not in s:
    s = s.rstrip() + "\n" + css
    io.open(p, "w", encoding="utf-8", newline="\n").write(s)
    print("css patched")
else:
    print("already has .gavetas")
