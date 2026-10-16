# ONDE A GENTE PAROU (leia isto primeiro)

> Escrito em 16/10/2026. Se você é uma IA lendo isto: o Wolf não programa.
> Fale com ele em português simples, sem jargão, e chame-o de Wolf.

## Uma linha de resumo
O Pesquisa IA tem UMA tela só: a **tela nova** (HTML/JS/pywebview).
O programa antigo (tkinter) foi aposentado. O projeto agora foca
100% na versão nova.

## Como ver o programa
- **.**`Pesquisa IA Tela Nova.exe`** na Área de Trabalho (o .exe pronto).
- **.**`2 - Abrir Pesquisa IA.bat`** abre pelo código-fonte (para desenvolvimento).
- **.**`Gerar o EXE.bat`** gera o .exe (só precisa rodar se mexer no código).

## Leia nesta ordem antes de mexer em qualquer coisa
1. `INSTRUCOES-PARA-IA.md` — as regras e as armadilhas já descobertas
2. `PASSO-A-PASSO.md` — o método (achar a causa, mudar o mínimo, testar)
3. `HISTORICO-DE-MUDANCAS.md` — tudo que foi feito, com a causa de cada bug
4. `PROXIMOS-PASSOS.md` — o plano de desenvolvimento
5. `web/LEIA-ME.md` — como a tela nova conversa com o Python

Depois rode `verificar.bat`. **Só diga que terminou se a última linha for
"TUDO CERTO"**.

## Estado atual (confie, foi conferido)
- `verificar.bat` = **TUDO CERTO**, com **120 verificações** (7 segundos).
- O `.exe` da Área de Trabalho está atualizado (gerado em 16/10/2026).
- O `.git` está limpo; último commit `ada7e8b` (simplificação dos scripts .bat).
- O programa antigo (tkinter) está em `_arquivo_morto` — não é mais usado.

## Regras que não podem ser quebradas
1. **Nenhuma janela branca.** Todo aviso/erro/pergunta é
   `_dialogo_escuro(...)` (ou `_confirmar`). `messagebox`, `simpledialog`
   e `tk_optionMenu` são PROIBIDOS — o `verificar.py` reprova.
2. **Janela de teste (PREVIA) sempre no segundo monitor** (X >= 1950).
   O programa de verdade abre onde o Wolf fechou da última vez.
3. **Nada de `unbind_all("<Button-1>")`.** Menus usam
   `_registrar_clique_global` / `_remover_clique_global`.
4. **Nunca mexer nos dados do Wolf** (`%LOCALAPPDATA%\PesquisaIA`) nos
   testes: aponte `p.ARQUIVO_HISTORICO`, `p.ARQUIVO_MEMORIA` e
   `p.ARQUIVO_CONFIG` para uma pasta em `_tmp` e restaure no fim.
5. **Nunca apagar nem renomear o `pesquisa_ia.py`.** É o motor do programa.
6. Nada de API key escrita no projeto; nada de mexer no histórico/git do
   usuário.
7. Depois de mexer: `verificar.bat` verde, commit, e atualizar
   `HISTORICO-DE-MUDANCAS.md` + este arquivo + `PROXIMOS-PASSOS.md`.

## Armadilhas já descobertas (não repetidas)
- O Tk desenha emoji de **uma cor só**. Na tela HTML sai colorido.
- A ponte do pywebview é **assíncrona**: `window.pywebview.api.algo(...)`
  devolve uma Promise (o `app.js` já usa `await`).
- O `pywebview` precisa estar no `requirements.txt` **e** no spec, senão o
  `.exe` gerado não abre.
- O horário da conversa (`%d/%m/%Y as %H:%M`) só tem minuto: **não
  ordenar a lista por ele**. Use `list(reversed(carregar_conversas()))`.
- A memória não pode perder informação: `memoria.py` tem a regra de ouro
  "organizar nunca pode apagar palavra" e o `autoteste()` barra a volta do
  defeito.
- `ctypes.wintypes` **NAO vem junto com `import ctypes`**: sem o
  `from ctypes import wintypes`, a função de contar telas levanta
  `AttributeError`.
