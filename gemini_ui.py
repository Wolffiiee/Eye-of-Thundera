import io

p = "D:/Projetos/PesquisaIA/app_web.py"
s = io.open(p, encoding="utf-8").read()

# _cfg_tela: add usar_gemini
old = '        "usar_plano_b": bool(cfg.get("usar_plano_b", True)),\n'
new = '        "usar_plano_b": bool(cfg.get("usar_plano_b", True)),\n        "usar_gemini": bool(cfg.get("usar_gemini", True)),\n'
assert old in s
s = s.replace(old, new, 1)

# _cfg_tela_demo: add usar_gemini
old2 = '        "usar_plano_b": True,\n        "gemini": {"definida": True, "final": "a1b2"},\n'
new2 = '        "usar_plano_b": True,\n        "usar_gemini": True,\n        "gemini": {"definida": True, "final": "a1b2"},\n'
assert old2 in s
s = s.replace(old2, new2, 1)

# config_salvar: handle usar_gemini
old3 = '        for campo in ("usar_contexto", "aprender", "voz_enviar",\n'
old3b = '                      "usar_plano_b"):\n'
assert old3 in s and old3b in s
s = s.replace('                      "usar_plano_b"):\n',
              '                      "usar_plano_b", "usar_gemini"):\n', 1)

# _responder: allow without gemini key if usar_gemini False and servicos available
old4 = '        if not chave:\n            return {"erro": "sem_chave"}\n'
new4 = ('        _servicos_ok = p._servicos_prontos(cfg)\n'
        '        _usar_gemini = bool(cfg.get("usar_gemini", True))\n'
        '        if _usar_gemini and not chave and not _servicos_ok:\n'
        '            return {"erro": "sem_chave"}\n'
        '        if not _usar_gemini and not _servicos_ok:\n'
        '            return {"erro": "sem_servico"}\n')
assert old4 in s
s = s.replace(old4, new4, 1)

io.open(p, "w", encoding="utf-8", newline="\n").write(s)
print("app_web patched")
