import io

fn = "D:/Projetos/PesquisaIA/web/app.js"
s = io.open(fn, encoding="utf-8").read()
L = s.splitlines()

print("=== mostrarAba ===")
for i, line in enumerate(L):
    if 'function mostrarAba' in line:
        for j in range(i, min(len(L), i+40)):
            print(f"{j+1}: {L[j][:200]}")
        break

print("\n=== fecharConfig ===")
for i, line in enumerate(L):
    if 'function fecharConfig' in line:
        for j in range(i, min(len(L), i+20)):
            print(f"{j+1}: {L[j][:200]}")
        break