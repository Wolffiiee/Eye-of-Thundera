# Passo a passo: como corrigir coisas neste projeto

Este arquivo ensina o MÉTODO. Foi escrito a partir de uma correção real
(14/10/2026, bug da seleção de texto). Siga na mesma ordem.

## O método (sempre igual)

1. **Entender o relato.** O que o Igor viu, em qual tela, o que esperava.
   Se faltar informação essencial, faça UMA pergunta curta.
2. **Achar a causa no código.** Busque palavras-chave no `pesquisa_ia.py`
   (ex.: `select_from`, `bind_all`, `_criar_bolha`). Leia o trecho inteiro.
   Escreva a causa em 1 ou 2 frases. Sem causa, não corrija.
3. **Proteger o que existe.** `git status`; se estiver sujo, commit à parte.
   O Git é o backup (não precisa copiar arquivos).
4. **Escrever o teste que falha** em `verificar.py` (simule cliques com
   `event_generate`). Se não der para testar (algo só visual), anote como o
   Igor confere com os olhos.
5. **Corrigir com a menor mudança possível.** Sem refatorar o resto.
6. **Rodar `verificar.bat`** até a última linha ser `TUDO CERTO`.
7. **Se o Igor usa o atalho da Área de Trabalho:** `3 - Gerar EXE.bat` e
   copiar `dist\Pesquisa IA.exe` para a Área de Trabalho.
8. **Commit** com mensagem clara em português (o quê e por quê).
9. **Relatar** em português simples: o que estava errado, o que mudou,
   como conferir, o que não foi testado.

## O exemplo real (bug da seleção de texto)

- **Relato:** "seleciono um pedaço do texto, mas ao clicar fora a seleção
  não some".
- **Causa (passo 2):** cada bolha é um Canvas. O clique só chamava
  `select_from`, que move o ponto de partida mas NÃO apaga a seleção antiga.
  E clicar fora das bolhas (caixa de digitar, fundo) não tinha tratamento.
- **Correção (passo 5):** `_limpar_selecoes()` em todo clique na bolha, e
  `_ao_clicar_fora` ligado com `raiz.bind(..., add="+")` para o resto da
  janela. O Ctrl+C e o menu Copiar passaram a usar só a seleção da própria
  bolha (`_selecao_propria`).
- **Problema vizinho achado no caminho:** três menus usavam
  `unbind_all("<Button-1>")`, que apaga o atalho de TODOS os menus. Troquei
  por um único `bind_all` (o `_despachar_clique`) e uma lista de ouvintes
  (`_registrar_clique_global` / `_remover_clique_global`).
- **Testes criados (passo 4):** 5 jeitos de clicar que têm que apagar a
  seleção, arrastar para selecionar, menus que fecham ao clicar fora,
  um menu não desligar o outro, janela de Configurações abrir e trocar de
  aba sem erro escondido.
- **Auditoria automática:** o `pyflakes` achou uma função morta que
  citava um nome inexistente (`tela_ajuda`); removi.

## Como agir em pedidos comuns

**"Apareceu um erro / o programa fechou"**
Leia `%LOCALAPPDATA%\PesquisaIA\erro.log` (a última entrada). Procure o nome
da função no traceback, leia o trecho, siga o método acima.

**"Quero uma função nova"**
Confirme em 1 frase o que ele quer. Veja `IDEIAS.md` (talvez já esteja
descrita). Faça em pedaços pequenos; a cada pedaço, `verificar.bat`. Adicione
um teste que use a função nova.

**"Atualizar/instalar uma biblioteca"**
Instale no `.venv` com `.venv\Scripts\python.exe -m pip install ...`, fixe a
versão exata em `requirements.txt` (ou `requirements-dev.txt` se for só
ferramenta), rode `verificar.bat`, registre no `HISTORICO-DE-MUDANCAS.md`.

**"Está lento / estranho depois de mexer"**
Compare com o último commit bom (`git diff`, `git log`). Volte só o trecho
problemático. Nunca reescreva o arquivo todo.

**"Mexeu e quebrou"**
`git stash` ou `git checkout -- pesquisa_ia.py` volta ao último commit.
Explique ao Igor o que foi desfeito.

## Comandos úteis (PowerShell, na pasta do projeto)

    .venv\Scripts\python.exe verificar.py         # conferência completa
    .venv\Scripts\python.exe -m pyflakes pesquisa_ia.py   # só análise
    .venv\Scripts\python.exe pesquisa_ia.py       # abrir o programa
    git status ; git log --oneline -5             # estado do projeto
    git diff                                      # o que mudou

## O que NUNCA fazer

- Mexer em `%LOCALAPPDATA%\PesquisaIA\` (conversas, memória e chaves dele).
- Escrever chave de API em qualquer arquivo do projeto.
- Apagar arquivos (mova para `_arquivo_morto`).
- Dizer "pronto" sem rodar `verificar.bat`.
- Usar `unbind_all("<Button-1>")`.
