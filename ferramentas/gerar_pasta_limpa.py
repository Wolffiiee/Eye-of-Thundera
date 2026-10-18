"""Refaz a pasta "Eye of Thundera" so com o que o programa precisa para rodar.

Ver PLANO-PASTA-LIMPA.md. E' uma COPIA: a pasta de trabalho (onde fica o
verificar.py, os planos, o .git etc.) nao muda. Rode de novo sempre que o
programa ganhar modulos ou arquivos novos: a lista e' DESCOBERTA aqui, nao
escrita a mao (le os `import` a partir do app_web.py e o que o index.html carrega).

Uso:  python ferramentas/gerar_pasta_limpa.py ["D:/Projetos/Eye of Thundera"]

Regras: so copia (por cima dos mesmos nomes); nunca apaga nada no destino; nao
copia chave, conversas, memoria nem lembretes (ficam em %LOCALAPPDATA%/PesquisaIA);
o LEIA-ME.txt do destino so e' criado se nao existir.
"""
import ast
import re
import shutil
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DESTINO_PADRAO = Path(r"D:\Projetos\Eye of Thundera")
ENTRADA = "app_web.py"
EXTRAS = ["icone.ico", "requirements.txt", "1 - Instalar.bat", "2 - Abrir Eye of Thundera.bat"]

LEIA_ME = """Eye of Thundera - assistente pessoal de pesquisa com IA
=======================================================

Como usar (so na primeira vez):
  1. Instale o Python (https://www.python.org/downloads/) marcando "Add Python to PATH".
  2. De dois cliques em  "1 - Instalar.bat"  (cria o ambiente e baixa as bibliotecas).
  3. De dois cliques em  "2 - Abrir Eye of Thundera.bat"  para abrir o programa.
  4. Em Configuracoes > Chaves, cole a sua chave do Google (Gemini).

Suas conversas, memoria, lembretes e chaves ficam em:
  %LOCALAPPDATA%\\PesquisaIA   (fora desta pasta, de proposito).
"""


def modulos_locais(inicio=ENTRADA):
    """Arquivos .py da raiz que o programa importa (direta ou indiretamente)."""
    achados, fila = [], [inicio]
    while fila:
        nome = fila.pop()
        if nome in achados:
            continue
        achados.append(nome)
        arvore = ast.parse((RAIZ / nome).read_text(encoding="utf-8"))
        for no in ast.walk(arvore):
            nomes = []
            if isinstance(no, ast.Import):
                nomes = [a.name.split(".")[0] for a in no.names]
            elif isinstance(no, ast.ImportFrom) and no.module and no.level == 0:
                nomes = [no.module.split(".")[0]]
            for n in nomes:
                if (RAIZ / (n + ".py")).exists():
                    fila.append(n + ".py")
    return sorted(achados)


def arquivos_da_tela():
    """O que o index.html carrega (css, js, imagens locais)."""
    html = (RAIZ / "web" / "index.html").read_text(encoding="utf-8")
    refs = re.findall(r'(?:src|href)="([^"#?:]+)"', html)
    return sorted({"web/" + r for r in refs if (RAIZ / "web" / r).is_file()} | {"web/index.html"})


def lista():
    return modulos_locais() + arquivos_da_tela() + EXTRAS


def main():
    destino = Path(sys.argv[1]) if len(sys.argv) > 1 else DESTINO_PADRAO
    if destino.resolve() == RAIZ:
        print("O destino nao pode ser a propria pasta de trabalho.")
        return 1
    copiados = []
    for rel in lista():
        origem = RAIZ / rel
        if not origem.is_file():
            print("FALTA na origem:", rel)
            return 1
        alvo = destino / rel
        alvo.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(origem, alvo)
        copiados.append(rel)
    leia = destino / "LEIA-ME.txt"
    if not leia.exists():
        leia.write_text(LEIA_ME, encoding="utf-8")
    total = sum((destino / r).stat().st_size for r in copiados)
    print("Copiados %d arquivos (%.0f KB) para %s" % (len(copiados), total / 1024, destino))
    for r in copiados:
        print("  ", r)
    # Confere: o programa tem que importar usando SO os arquivos da pasta nova.
    r = subprocess.run(
        [sys.executable, "-B", "-c",       # -B: nao deixa __pycache__ na pasta nova
         "import app_web, pdf_leitor, lembretes, documento; print(app_web.__file__)"],
        cwd=str(destino), capture_output=True, text=True, encoding="utf-8", errors="replace")
    saida = (r.stdout or "").strip()
    if r.returncode != 0 or str(destino).lower() not in saida.lower():
        print("CONFERENCIA FALHOU:", saida, (r.stderr or "")[-500:])
        return 1
    print("Conferencia: o programa importa direto da pasta nova (%s)." % saida)
    return 0


if __name__ == "__main__":
    sys.exit(main())
