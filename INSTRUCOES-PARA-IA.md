# Instruções para a IA que programa o Pesquisa IA

Leia este arquivo ANTES de mexer em qualquer coisa. Depois leia
`PASSO-A-PASSO.md` (o método de trabalho) e `HISTORICO-DE-MUDANCAS.md`
(o que já foi mudado e por quê).

Quem pede as mudanças (o Wolf) não programa. O trabalho tem que vir
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
- `roteador.py` — decide se a mensagem é papo ou pesquisa (não importa o programa).
- `voz.py` — grava o microfone e transcreve com o Gemini (não importa o programa).
- `verificar.py` / `verificar.bat` — a conferência automática (obrigatória).
- `3 - Gerar EXE.bat` + `Pesquisa IA.spec` — geram `dist\Pesquisa IA.exe`.
- `1 - Instalar.bat`, `2 - Abrir Pesquisa IA.bat` — instalar e abrir.
- `requirements.txt` (programa) e `requirements-dev.txt` (ferramentas).
- `.venv\` — ambiente Python (não editar, não versionar).
- `_arquivo_morto\` — coisas antigas guardadas; ignorar, não usar.
- `_tmp\` — sobras dos testes (prints, áudios). Ignorada pelo Git; quando
  acabar o trabalho, pode esvaziar.

## Tela de teste: sempre no SEGUNDO monitor
O segundo monitor do Wolf começa em **X=1920** (vai até X=3840). Qualquer
janela de teste ou `.exe` aberto para conferir precisa nascer em `X >= 1950`
(ex.: `+2000+100`), **nunca** no monitor principal, que é onde ele está
trabalhando.
- No `verificar.py` isso já está pronto: `POSICAO_TESTE = "+2000+100"`.
- Para abrir o `.exe`: o PyInstaller sobe um processo filho, então o
  `MainWindowHandle` do processo iniciado fica vazio. procure a janela pelo
  TÍTULO ("Pesquisa IA") em todos os processos e mova com `SetWindowPos`.

## Regras de trabalho (obrigatórias)
0. **Nenhuma janela branca, nunca.** Todo aviso, pergunta, confirmação e
   erro tem que sair pela `_dialogo_escuro(pai, titulo, texto,
   botoes=(...))` — ou pelo `_confirmar(titulo, texto)`, que já usa essa
   função. **Proibidos:** `messagebox`, `simpledialog`, `tk_optionMenu` e
   qualquer outra janela do tkinter/sistema (elas abrem brancas e
   destoam). O `verificar.py` **falha** se qualquer um desses aparecer.
   A única exceção é a janela de "Salvar como...", que é do Windows e não
   dá para trocar as cores — para ela existe
   `_deixar_dialogo_do_sistema_escuro(raiz)`, que pede ao Windows o tema
   escuro (pode não funcionar em toda versão do Windows).
1. **Nunca** tente criar, adivinhar ou "consertar" a chave de API do
   Google por conta própria. O Google não tem API pública para criar
   chaves no AI Studio, e qualquer contorno exigiria a senha do Wolf.
   O que o programa faz é avisar com clareza e oferecer a chave reserva.
1. Leia `git status` e `git log --oneline -5` antes de começar. Se houver
   mudança solta, pergunte ao Wolf ou faça commit dela separado.
2. Mudanças pequenas, uma de cada vez. Nada de reescrever o arquivo inteiro
   nem "aproveitar para melhorar" o que não foi pedido.
3. Depois de TODA alteração: `verificar.bat` (ou
   `.venv\Scripts\python.exe verificar.py`). Só diga que terminou se a
   última linha for `TUDO CERTO` e não houver `[FALHA]`.
4. Bug relatado = primeiro ache a CAUSA no código e diga qual é. Não chute.
5. Bug corrigido de verdade = existe um teste novo no `verificar.py` que
   falharia sem a correção. Se for só visual, explique como o Wolf confere.
6. Se aparecer erro na tela, leia `%LOCALAPPDATA%\PesquisaIA\erro.log`.
7. Depois que `verificar.py` passar, faça commit com mensagem clara.
8. Se a mudança afeta o que o Wolf vê ao abrir o programa pelo atalho
   (a Área de Trabalho usa o .exe!), rode `3 - Gerar EXE.bat` e copie
   `dist\Pesquisa IA.exe` para a Área de Trabalho. Sem isso, a correção só
   existe em `2 - Abrir Pesquisa IA.bat`. Diga ao Wolf qual dos dois ele
   está usando.
9. Nunca apague arquivos do Wolf. Para "remover", mova para `_arquivo_morto`.
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
- **Texto de `Label` sem `anchor` fica CENTRADO:** um `tk.Label` com
  várias linhas e sem `anchor="w"` centraliza o bloco, mesmo com
  `justify="left"` (o `justify` alinha as linhas entre si, não o bloco).
- **Janela com `grab_set`/`wait_window` trava a chamada:** para printar
  uma dessas janelinhas, agende o print com `after()` de dentro — depois
  que a função voltar, a janela já foi destruída.
- **Nome de parâmetro tem que ser igual:** o Python 3 aceita acento em
  identificadores, então um `cor_bolao` escrito `cor_bolão` passa ileso
  na hora de compilar, mas o `pyflakes` acusa "undefined name" e o
  `verificar.py` trava. Confira o nome byte a byte.
- **`PIL.ImageGrab` em tela com dois monitores:** para conferir o desenho
  de um botão, é mais seguro gerar o PNG direto com o Pillow (mesma arte
  da função `_foto_*`) do que tentar capturar a tela — `ImageGrab` no
  segundo monitor devolveu imagem preta. Para capturar a janela de verdade
  use `PrintWindow` (veja `_tmp`/histórico): janela de Tk no Windows ->
  `GetAncestor(winfo_id(), GA_ROOT)` dá o HWND certo.
- **Canto arredondado "por cima" e o que fica embaixo:** as tampinhas de
  canto são `Label` criadas **depois** da entrada e dos botões, então
  ficam na frente. Se o respiro do botão for menor que `RAIO_CANTO`, a
  tampinha come um pedaço do botão. Regra: respiro do botão >= raio.
- **`place` + `anchor`: não some deslocamento.** O `anchor` JÁ põe o canto
  do widget no ponto indicado. Escrever `place(relx=1.0, x=-raio,
  anchor="ne")` empurra a coisa 12 px para dentro (o `x` é do canto da
  âncora, não do centro). Use só `relx/rely` + `anchor`.
- **A curva do canto tem o centro no canto OPOSTO** (`_dentro_do_canto`):
  o bico do canto fica FORA (é o que a tampinha pinta) e o miolo fica
  DENTRO. Invertido, a tampinha come o miolo da caixa em vez de arredondar.
- **`tkinter` NÃO tem widget transparente.** O `bg` de um `Label`
  preenche o retângulo inteiro, então uma imagem com "buraco"
  (alpha=0) não deixa ver o que está embaixo: o buraco sai com a cor do
  `bg`. Por isso `_imagem_canto` pinta a imagem **inteira** (dentro = cor
  da caixa, fora = cor de fundo) e não usa transparência. Tem teste que
  falha se aparecer qualquer pixel transparente.
- **`PrintWindow` engana com antialiasing:** nos meus prints o canto
  "parecia" curva mesmo estando quadrado. **O que vale é a tela de verdade
  do Wolf.** Quando ele reclamar de algo visual, ache o pixel exato no
  print que ele mandou e confira os valores RGB — foi assim que o quadrado
  apareceu.
- **Mudar a altura da caixa de digitar redesenha a conversa:** o `Text`
  encolhe/engrandece, o rodapé muda de tamanho, o Canvas recebe
  `<Configure>` e agenda `_agendar_redesenho`, que **recria todas as
  bolhas**. Nos testes, pegue `app._telas_bolha` de novo depois de mexer
  na caixa, senão o teste vai mexer em widget já destruído.
- **`undo=True` no `tk.Text`:** sem isso `edit_undo()`/`edit_redo()` não
  fazem nada e o Ctrl+Z parece quebrado.
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
- Texto das bolhas: duplo clique (palavra) e triplo clique (texto todo) ja funcionam desde 15/10/2026. Faltam seleção por parágrafo e arrastar mantendo a palavra. Trocar por `tk.Text` somente leitura é o caminho de menor esforço; alternativa maior: interface em HTML com `pywebview` (ver PROXIMOS-PASSOS.md).
- Não há backup do código fora deste computador. Sugerir ao Wolf um
  repositório privado (GitHub) ou cópia periódica da pasta.
- Nomes de modelos Gemini em `MODELOS_RESERVA` não foram conferidos na
  documentação oficial; o programa já tenta o próximo se um falhar.
