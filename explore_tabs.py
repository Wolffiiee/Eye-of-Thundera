import io

fn = "D:/Projetos/PesquisaIA/web/app.js"
s = io.open(fn, encoding="utf-8").read()
L = s.splitlines()

# Find abaChaves and surrounding functions to understand tab structure
for i, line in enumerate(L):
    if 'function abaChaves' in line:
        print(f"=== abaChaves at line {i+1} ===")
        for j in range(i, min(len(L), i+30)):
            print(f"{j+1}: {L[j][:150]}")
        print("---")

# Find all function definitions that might be tabs
print("\n=== All function starts ===")
for i, line in enumerate(L):
    stripped = line.strip()
    if stripped.startswith('function ') and ('aba' in stripped.lower() or 'config' in stripped.lower() or 'tela' in stripped.lower()):
        print(f"{i+1}: {stripped[:150]}")