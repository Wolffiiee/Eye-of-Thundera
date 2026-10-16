import io

fn = "D:/Projetos/PesquisaIA/web/app.js"
s = io.open(fn, encoding="utf-8").read()
L = s.splitlines()

# Show abaMemoria and abaConversa structure
print("=== abaMemoria (line 1278) ===")
for i in range(1277, min(len(L), 1350)):
    print(f"{i+1}: {L[i][:150]}")

print("\n=== abaConversa (line 1142) ===")
# Need to find it - let me search
for i, line in enumerate(L):
    if 'function abaConversa' in line:
        for j in range(i, min(len(L), i+30)):
            print(f"{j+1}: {L[j][:150]}")
        break

print("\n=== abaAjuda (line 1557) ===")
for i in range(1556, min(len(L), 1620)):
    print(f"{i+1}: {L[i][:150]}")

print("\n=== mostrarAba (line 1591) ===")
for i in range(1590, min(len(L), 1620)):
    print(f"{i+1}: {L[i][:150]}")

print("\n=== fecharConfig (line 1614) ===")
for i in range(1613, min(len(L), 1640)):
    print(f"{i+1}: {L[i][:150]}")