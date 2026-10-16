import io
p = "D:/Projetos/PesquisaIA/pesquisa_ia.py"
L = io.open(p, encoding="utf-8").read().splitlines(keepends=True)

# Fix lines 1393..1411 (1-based) to proper indentation
# We'll replace the block from 'if usar_gemini:' through 'time.sleep(1.5)'
start = None
for i,l in enumerate(L):
    if l.strip() == "if usar_gemini:" and i > 1380:
        start = i
        break
assert start is not None
end = None
for j in range(start, len(L)):
    if "time.sleep(1.5)" in L[j]:
        end = j
        break
assert end is not None

# Rebuild block with correct indentation
block = (
    "    if usar_gemini:\n"
    "        for _rodada in range(2):\n"
    "            for nome in ordem:\n"
    "                try:\n"
    "                    config = types.GenerateContentConfig(\n"
    "                        temperature=0.7 if amigo else 0.3,\n"
    "                        system_instruction=instrucoes_da_ia(modo),\n"
    "                    )\n"
    "                    resposta = cliente.models.generate_content(\n"
    "                        model=nome, contents=conteudo, config=config\n"
    "                    )\n"
    "                    texto = (getattr(resposta, \"text\", \"\") or \"\").strip()\n"
    "                    if not texto:\n"
    "                        texto = _juntar_partes(resposta)\n"
    "                    if texto:\n"
    "                        return texto, \"Gemini\"\n"
    "                    ultimo_erro = RuntimeError(\"a IA nao devolveu texto\")\n"
    "                except Exception as erro:\n"
    "                    ultimo_erro = erro\n"
    "                    continue\n"
    "            time.sleep(1.5)\n"
)
L[start:end+1] = [block]
io.open(p, "w", encoding="utf-8", newline="\n").write("".join(L))
print("fixed")
