"""
Troca o modelo do OpenCode por um modelo GRATIS que esteja respondendo.

QUANDO USAR: quando o limite do modelo atual estiver acabando (ou ja acabou:
erro 429, "rate limit", "quota", "credits", "context length").
Quem roda: o proprio OpenCode (ver AGENTS.md) ou o Wolf, com o arquivo
"10 - Trocar para modelo gratis.bat".

O QUE FAZ
  1. le a lista de ferramentas/modelos-gratis.txt (um modelo por linha, do
     melhor para o pior; linhas com # sao comentario);
  2. pergunta "Responda apenas: OK" a cada um, em ordem, ate um responder;
  3. grava esse modelo em "model" no opencode.json (com copia de seguranca
     opencode.json.bak-antes-de-trocar) e avisa qual foi.
  Funciona na PROXIMA sessao do OpenCode. Dentro de uma sessao aberta,
  use /models e escolha o modelo que este script mostrar.

NAO mexe em chaves nem em nenhuma outra parte do arquivo.
Uso:  python ferramentas/trocar_modelo_gratis.py [--so-testar]
"""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

LISTA = Path(__file__).with_name("modelos-gratis.txt")
CONFIG = Path(os.environ.get("USERPROFILE", str(Path.home()))) / \
    ".config" / "opencode" / "opencode.json"
SO_TESTAR = "--so-testar" in sys.argv


def candidatos():
    for linha in LISTA.read_text(encoding="utf-8-sig").splitlines():
        linha = linha.strip()
        if linha and not linha.startswith("#"):
            yield linha


def responde(modelo, espera=90):
    """True se o modelo respondeu algo em ate `espera` segundos."""
    try:
        r = subprocess.run(
            ["opencode", "run", "-m", modelo, "Responda apenas: OK"],
            capture_output=True, text=True, timeout=espera,
            encoding="utf-8", errors="replace", shell=(os.name == "nt"))
    except Exception:
        return False
    saida = (r.stdout or "").strip()
    ruim = ("rate limit", "quota", "429", "unauthorized", "not found",
            "insufficient", "credit", "ECONNREFUSED", "error")
    return r.returncode == 0 and bool(saida) and \
        not any(x.lower() in saida.lower()[:300] for x in ruim)


def main():
    escolhido = None
    for modelo in candidatos():
        print("Testando %s ..." % modelo, flush=True)
        if responde(modelo):
            escolhido = modelo
            print("  respondeu!")
            break
        print("  nao respondeu, proximo.")
    if not escolhido:
        print("\nNenhum modelo gratis respondeu agora (internet? limite "
              "geral?). Tente de novo em alguns minutos.")
        return 1
    if SO_TESTAR:
        print("\nModelo gratis que funciona: %s (nada foi alterado)" % escolhido)
        return 0
    dados = json.loads(CONFIG.read_text(encoding="utf-8-sig"))
    if dados.get("model") == escolhido:
        print("\nO OpenCode ja esta usando %s." % escolhido)
        return 0
    copia = CONFIG.with_name("opencode.json.bak-antes-de-trocar")
    shutil.copy2(CONFIG, copia)
    dados["model"] = escolhido
    CONFIG.write_text(json.dumps(dados, indent=2, ensure_ascii=False),
                      encoding="utf-8")
    print("\nPronto: o modelo agora e %s" % escolhido)
    print("Vale na proxima sessao. Na sessao aberta: /models e escolha ele.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
