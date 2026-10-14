# Instruções para a IA que programa o Pesquisa IA

Leia este arquivo ANTES de mexer em qualquer coisa. Depois leia
`PASSO-A-PASSO.md` (o método de trabalho) e `HISTORICO-DE-MUDANCAS.md`
(o que já foi mudado e por quê).

Quem pede as mudanças (o Igor) não programa. O trabalho tem que vir
pronto, testado e explicado em português simples.

## Onde fica o projeto
`C:\Projetos\PesquisaIA`  (desde 14/10/2026; antes ficava no OneDrive).
Não trabalhe na pasta antiga "Projeto Padrão (ANTIGO - pode apagar)".

## O projeto em uma frase
Programa de janela (Python 3.12 + tkinter) que pesquisa na web, manda os
trechos para o Gemini e mostra a resposta num chat. Todo o código está em
`pesquisa_ia.py` (classe `Aplicativo`). Cada mensagem é uma "bolha"
desenhada num Canvas (`_criar_bolha`). Dados do usuário (conversas, memória,
chaves) ficam em `%LOCALAPPDATA%\PesquisaIA\` e NUNCA entram no projeto.

## Mapa dos arquivos
- `pesquisa_ia.py` — o programa inteiro.
- `verificar.py` / `verificar.bat` — a conferência automática (obrigatória).
- `3 - Gerar EXE.bat` + `Pesquisa IA.spec` — geram `dist\Pesquisa IA.exe`.
- `1 - Instalar.bat`, `2 - Abrir Pesquisa IA.bat` — instalar e abrir.
- `requirements.txt` (programa) e `requirements-dev.txt` (ferramentas).
- `.venv\` — ambiente Python (não editar, não versionar).
- `_arquivo_morto\` — coisas antigas guardadas; ignorar, não usar.

## Regras de trabalho (obrigatórias)
1. Leia `git status` e `git log --oneline -5` antes de começar. Se houver
   mudança solta, pergunte ao Igor ou faça commit dela separado.
2. Mudanças pequenas, uma de cada vez. Nada de reescrever o arquivo inteiro
   nem "aproveitar para melhorar" o que não foi pedido.
3. Depois de TODA alteração: `verificar.bat` (ou
   `.venv\Scripts\python.exe verificar.py`). Só diga que terminou se a
   última linha for `TUDO CERTO` e não houver `[FALHA]`.
4. Bug relatado = primeiro ache a CAUSA no código e diga qual é. Não chute.
5. Bug corrigido de verdade = existe um teste novo no `verificar.py` que
   falharia sem a correção. Se for só visual, explique como o Igor confere.
6. Se aparecer erro na tela, leia `%LOCALAPPDATA%\PesquisaIA\erro.log`.
7. Depois que `verificar.py` passar, faça commit com mensagem clara.
8. Se a mudança afeta o que o Igor vê ao abrir o programa pelo atalho
   (a Área de Trabalho usa o .exe!), rode `3 - Gerar EXE.bat` e copie
   `dist\Pesquisa IA.exe` para a Área de Trabalho. Sem isso, a correção só
   existe em `2 - Abrir Pesquisa IA.bat`. Diga ao Igor qual dos dois ele
   está usando.
9. Nunca apague arquivos do Igor. Para "remover", mova para `_arquivo_morto`.
10. Instalou ou removeu biblioteca? Atualize `requirements.txt` (ou
    `-dev`) com a versão exata (`==`) e registre no
    `HISTORICO-DE-MUDANCAS.md`.
11. Termine sempre com um relato curto em português simples: o que estava
    errado, o que mudou, como conferir, e o que NÃO foi testado.

## Armadilhas já encontradas (não repita)
- **Seleção de texto (Canvas):** `select_from` só move o ponto de partida,
  não apaga a seleção antiga. Todo clique chama `_limpar_selecoes()`;
  clique fora das bolhas cai em `_ao_clicar_fora` (ligado com
  `raiz.bind(..., add="+")`).
- **Cliques globais / menus que fecham ao clicar fora:** existe UM
  `bind_all("<Button-1>")` (o `_despachar_clique`). Menu novo usa
  `_registrar_clique_global(fn)` ao abrir e `_remover_clique_global(fn)` ao
  fechar. **Proibido** `unbind_all("<Button-1>")` (apagava o atalho de todos
  os outros menus). O `verificar.py` falha se isso aparecer.
- **Widgets que devolvem "break":** as bolhas devolvem `"break"` no clique,
  então o clique não chega ao `bind_all`. Por isso `_on_click` chama
  `_despachar_clique(event)` à mão.
- **Opção `fg` em Canvas:** Canvas não aceita `fg` (`unknown option "-fg"`
  já aconteceu). Em Canvas use `itemconfigure`.
- **Erros escondidos:** erro dentro de botão/evento não derruba o programa;
  vai para o `erro.log`. O `verificar.py` captura esses erros durante o
  teste (`report_callback_exception`).
- **Corrida de redesenho:** a janela redesenha as bolhas logo depois de
  abrir. Em testes, espere ~1 s antes de pegar referências às bolhas.
- **Emojis:** as bolhas removem emojis de propósito (`_remover_emojis`).
- **Chaves de API:** só em `%LOCALAPPDATA%\PesquisaIA\config.json`. Nunca no
  código nem em arquivo da pasta do projeto.
- **Avatar no .exe:** `avatar_usuario.png` e `icone.ico` são embutidos no
  .exe pelo `Pesquisa IA.spec`. Trocou a imagem? Gere o .exe de novo.

## Ainda não resolvido / ideias
- Texto das bolhas é item de Canvas: só seleção simples (sem duplo clique
  para palavra, sem triplo para linha). Trocar por `tk.Text` somente leitura
  é o caminho de menor esforço. Alternativa maior: interface em HTML com
  `pywebview` (ver conversa sobre alternativas ao tkinter).
- Não há backup do código fora deste computador. Sugerir ao Igor um
  repositório privado (GitHub) ou cópia periódica da pasta.
- Nomes de modelos Gemini em `MODELOS_RESERVA` não foram conferidos na
  documentação oficial; o programa já tenta o próximo se um falhar.
