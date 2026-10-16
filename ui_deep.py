import io
fn = "D:/Projetos/PesquisaIA/web/index.html"
L = io.open(fn, encoding="utf-8").read().splitlines()
# line index 78 context (0-based 77)
for i, l in enumerate(L):
    if l.strip().startswith('<button id="btn-deep"'):
        L[i] = '          <button id="btn-deep" class="pilula" title="Pesquisa profunda (clique para ligar)"><svg style="width:15px;height:15px"><use href="#i-brilho"/></svg><span>Pesquisa sera</span></button>'
        # remove next line (svg-ish) by combining
        print("patched line", i+1)
        break
# remove the now-orphan line
for i, l in enumerate(L):
    if 'Pesquisa sera</span></button>' in l and l.startswith('            <svg'):
        del L[i]
        print("removed orphan", i+1)
        break
io.open(fn, "w", encoding="utf-8", newline="\n").write("\n".join(L) + "\n")
print("html done")

# JS toggle
fn2 = "D:/Projetos/PesquisaIA/web/app.js"
s2 = io.open(fn2, encoding="utf-8").read()
s2 = s2.replace('$$("#btn-deep").classList.toggle("ativo", estado.profundo);',
                '$$("#btn-deep").classList.toggle("ligada", !!estado.profundo);')
old3 = '  aviso(estado.profundo ? "Pesquisa profunda LIGADA: modulo resposta mais longa." : "Pesquisa profunda desligada.");'
new3 = ('  b.title = estado.profundo\n    ? "Pesquisa profunda LIGADA (clique para desligar)"\n'
        '    : "Pesquisa profunda: mais sites, resposta em topicos com fontes (clique para ligar)";\n'
        '  aviso(estado.profundo ? "Pesquisa profunda LIGADA." : "Pesquisa profunda desligada.");')
assert old3 in s2, "old3"
s2 = s2.replace(old3, new3, 1)
io.open(fn2, "w", encoding="utf-8", newline="\n").write(s2)
print("js patched")
