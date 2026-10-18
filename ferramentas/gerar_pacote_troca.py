import subprocess
from pathlib import Path
raiz = Path(".")
tr = raiz / "_troca"
def git(*a):
    return subprocess.run(["git", *a], capture_output=True, text=True, encoding="utf-8").stdout
log = git("log", "--format=%h  %ad  %s", "--date=format:%d/%m %H:%M", "-15")
arq = git("ls-files")
(tr / "arvore-de-arquivos.txt").write_text(arq, encoding="utf-8")
(tr / "ultimos-commits.txt").write_text(log, encoding="utf-8")
texto = f"""# Pacote de troca para o ChatGPT - Eye of Thundera

Gerado em 16/10/2026 pelo Claude, a pedido do Wolf. LEIA ISTO PRIMEIRO.

## Quem e o dono
O Wolf (usuario do Windows: Igor) NAO programa. Fale com ele em portugues simples,
sem jargao. Ele usa varias IAs para programar (OpenCode, Codex, Claude, ChatGPT).

## O que e o programa
Um assistente pessoal com IA para Windows. Responde como um amigo e so pesquisa na web
quando precisa. Tela escura estilo Claude, em HTML dentro de uma janela do Windows
(pywebview + WebView2). Motor em Python (Gemini + busca DuckDuckGo), com memoria do que
aprende sobre o Wolf, microfone (voz para texto via Gemini), 5 temas de cor, conversa
privada, pesquisa profunda, resumo do dia, galeria de imagens e fontes citadas.

- Pasta do projeto: D:\\Projetos\\Eye of Thundera
- Entrada do programa: app_web.py  |  telas: web\\index.html, estilo.css, app.js
- Motor: eye_of_thundera.py (ainda carrega codigo velho de tela Tk, que esta MORTO),
  roteador.py (chat x pesquisa), memoria.py, voz.py
- Programa antigo (tkinter) esta APOSENTADO. Nao mexer nele.
- Testes: verificar.py e verificar_motor.py (rodar com verificar.bat; ambos TUDO CERTO)
- Regras para IAs: GUIA-DO-OPENCODE.md, INSTRUCOES-PARA-IA.md, ONDE-PARAMOS.md

## Estado em 16/10/2026 (noite)
- Todos os testes passam (136 + 171 verificacoes).
- Feito: conversas, memoria (com data e por assunto), configuracoes em 5 abas,
  microfone, temas, pesquisa profunda, resumo do dia, galeria, fontes citadas,
  atalhos (Ctrl+M, Ctrl+N, Ctrl+F, Ctrl+D, Ctrl+/-), backup dos dados.
- Pendente: conferir visual das Configuracoes em janela pequena / escala do Windows >100%;
  arrastar PDF e imagem para a conversa (hoje so .txt .md .csv .json);
  separar o motor do codigo antigo de tela Tk (nucleo.py) em passos pequenos;
  rever o plugin gratis-sempre do OpenCode (troca de modelo gratis no limite).
- Problema recente: um commit do OpenCode apagou ~220 testes; o Claude os restaurou
  em verificar_motor.py. REGRA: nunca apagar teste.

## Possivel defeito visual visto nos prints
Na conversa de exemplo, o negrito aparece com asteriscos literais dentro de listas
("**Modelos de IA menores**"). Pode ser so o texto de exemplo ou o renderizador de
markdown nao tratar negrito dentro de topicos. Vale conferir.

## Prints (pasta prints\\), todos em MODO EXEMPLO (nada pessoal do Wolf)
01-tela-inicial, 02-conversa-aberta, 03-config-memoria / conversa / chaves / ajuda /
personalizacao, 04-voltou-ao-chat.

## Limites desta troca
O ChatGPT NAO controla o PC do Wolf: so le este pacote. Nao ha chaves de API, conversas
nem memoria do Wolf aqui. Para atualizar: rodar "12 - Atualizar pacote do ChatGPT.bat".
"""
(tr / "LEIA-ME-PARA-O-CHATGPT.md").write_text(texto, encoding="utf-8")
gi = raiz / ".gitignore"
g = gi.read_text(encoding="utf-8") if gi.exists() else ""
if "_troca" not in g:
    gi.write_text(g.rstrip("\n") + "\n_troca/\n", encoding="utf-8")
