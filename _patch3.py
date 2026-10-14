p="pesquisa_ia.py"
lines=open(p,encoding="utf-8").read().split("\n")
for i,l in enumerate(lines):
    strip=l.strip()
    if strip.startswith("# Se nao sobrou"):
        lines[i]="         "+strip if len(l)-len(l.lstrip()) <8 else "         "+strip
    # no-op
open(p,"w",encoding="utf-8").write("\n".join(lines))
print("ok")
