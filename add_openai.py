import io

p = "D:/Projetos/PesquisaIA/pesquisa_ia.py"
s = io.open(p, encoding="utf-8").read()

# Insert ChatGPT/OpenAI first in SERVICOS_RESERVA
old = "SERVICOS_RESERVA = [\n"
new = (
    "SERVICOS_RESERVA = [\n"
    "    {\n"
    '        "nome": "ChatGPT (OpenAI)",\n'
    '        "endereco": "https://api.openai.com/v1/chat/completions",\n'
    '        "modelo": "gpt-4o-mini",\n'
    '        "campo_chave": "chave_openai",\n'
    '        "campo_modelo": "modelo_openai",\n'
    '        "pagina": "https://platform.openai.com/api-keys",\n'
    '        "prefixo": "sk-",\n'
    '        "resumo": "OpenAI (ChatGPT), pago por uso, chave comeca com sk-",\n'
    '        "passos": (\n'
    '            "Como conseguir: 1) clique em \\"Como conseguir a chave\\"; "\n'
    '            "2) entre com sua conta OpenAI; 3) clique em Create new secret key; "\n'
    '            "4) copie o codigo (comeca com sk-) e cole aqui."\n'
    '        ),\n'
    "    },\n"
)
assert old in s
s = s.replace(old, new, 1)

# Add prefix field to Groq and OpenRouter entries
s = s.replace('"resumo": "gr\u00e1tis, sem cart\u00e3o (cerca de 1.000 pedidos por dia)",',
              '"prefixo": "gsk_",\n        "resumo": "gr\u00e1tis, sem cart\u00e3o (cerca de 1.000 pedidos por dia)",')
s = s.replace('"resumo": "gr\u00e1tis, sem cart\u00e3o (cerca de 50 pedidos por dia)",',
              '"prefixo": "sk-or-",\n        "resumo": "gr\u00e1tis, sem cart\u00e3o (cerca de 50 pedidos por dia)",')

# Update _erro_do_servico 401 prefix logic via line replace
lines = s.splitlines(keepends=True)
for i, l in enumerate(lines):
    if '            % (nome, "gsk_" if nome == "Groq" else "sk-or-")' in l:
        lines[i] = ('            % (nome, "sk-" if nome.startswith("ChatGPT") else (\n'
                    '                "gsk_" if nome == "Groq" else "sk-or-"))\n')
        print("patched 401 prefix line", i+1)
        break

io.open(p, "w", encoding="utf-8", newline="\n").write("".join(lines))
print("ok")
