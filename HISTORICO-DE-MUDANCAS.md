# Histórico de mudanças

Registre aqui toda mudança relevante (a mais nova em cima): o que foi
baixado/instalado, modificado, adicionado, removido ou movido.

---

## 2026-10-15 (noite) - Claude: memória sem repetição (módulo novo), guia dos emojis e conferência

- **Pedido do Wolf:** (1) a memória do app parar de guardar o mesmo tipo de
  informação várias vezes; (2) o menu dos três pontinhos das conversas não
  excluía; (3) orientação para trazer os emojis coloridos de volta; (4)
  conferir se o opencode está indo bem.
- **Conferido às 18:41:** Git limpo, 10 commits do dia (voz, interface,
  chave reserva, backup, salvar .txt) e `verificar.bat` = TUDO CERTO.
- **Corrigido mais cedo (commit 2e31086):** três pontinhos. O mesmo clique
  que abria a caixinha subia até a janela e a fechava na hora; agora o
  `fora()` de `_menu_da_conversa` ignora o clique no próprio botão. Teste
  novo: `testes_lista_de_conversas` (abre, fecha ao clicar fora, exclui a
  conversa certa).
- **Adicionado:** `memoria.py` (funções puras): `mesclar`, `consolidar`,
  `autoteste`. Junta fatos sem repetir: palavras iguais = 1 fato; mais
  completo troca o simples; contradição troca o antigo; nome/apelido, cidade
  e idade têm lugar fixo (o mais novo vence); fato de outra pessoa nunca
  sobrescreve. **NÃO está ligado ainda**: os passos estão em
  `PROXIMOS-PASSOS.md` (ORDEM NOVA, item 1).
- **Documentação:** Tarefa E (emojis coloridos) no `PLANO-NOVAS-FUNCOES.md`,
  armadilha nova no `INSTRUCOES-PARA-IA.md`, lista reorganizada no
  `PROXIMOS-PASSOS.md`.
- **Teste de bancada (arquivo apagado depois):** Pillow 12.3.0 desenha emoji
  colorido da fonte Segoe UI Emoji (`embedded_color=True`); dentro de um
  `tk.Text` a figurinha fica na linha e quebra com a frase. Sem `raqm` e sem
  bandeiras no Windows, 👨‍💻 e 🇧🇷 não saem completos (ver E3).
- **Não mexi no `pesquisa_ia.py`** (o opencode estava trabalhando nele).

---

## 2026-10-15 — Tela em HTML: teste decisivo (funciona aqui) + Configurações sem texto espremido

### 1. A tela em HTML foi testada de verdade (e funciona)

O Wolf aprovou refazer a tela em HTML ("tudo o que puder ser otimizado, tá
liberado"). Antes de mexer em 6500 linhas, o `web/spike_webview.py` foi
reescrito para responder o que decide a decisão. Resultado na casa do Wolf:

| Pergunta | Resposta |
|---|---|
| a janela abre? | sim |
| abre no 2º monitor (x=2000)? | **sim** (regra do Wolf: nunca no 1º) |
| o Python chama o JavaScript? | sim |
| o JavaScript chama o Python (a ponte)? | sim (`Ola, Wolf! (veio do Python)`) |
| **o emoji sai COLORIDO?** | **sim: 1.855 de 2.937 pixels com cor (63%)** |
| dá para selecionar texto? | sim (`Primeira linha de`) |

Antes disso foi conferido que o WebView2 Runtime está instalado (versão
155.0.4283.45) e que há Edge e Chrome. `pywebview` 6.2.1 já estava
instalado (instalado pelo Claude, **sem** estar no `requirements.txt`).

**Por que o teste conta:** o Tk do Windows só desenha emoji de uma cor.
O navegador desenha colorido sozinho. 63% de pixels coloridos é a prova
de que os emojis coloridos saem de graça na tela nova — e é o motivo de
pular a Tarefa E inteira.

Duas coisas que o teste ensinou (e que o `.exe` vai precisar):
- a ponte do pywebview é **assíncrona**: `window.pywebview.api.algo(...)`
  devolve uma Promise. O JavaScript tem que usar `.then(...)`.
- o `pywebview` precisa entrar no `requirements.txt` **e** no
  `Pesquisa IA.spec` (senão o `.exe` gerado não abre).

### 2. Configurações: o texto estava espremido (corrigido)

O Wolf avisou que na aba Chaves o texto parecia espremido pela janela.
A causa: **15 parágrafos com `wraplength` fixo** e todos diferentes
(380, 490, 540, 560, 600...). Cada um quebrava a linha num ponto
arbitrário, então o texto não preenchia a janela e sobrava vão vazio.

- **Novo:** `_acompanhar_largura(janela)` percorre os `Label` com quebra de
  linha e faz a largura acompanhar a da janela, mudando sozinha quando o
  Wolf redimensiona. Vale para as **quatro** abas de uma vez.
- **Aba Chave:** o título "Chave da API do Google (Gemini)" aparecia
  **duas vezes seguidas** (uma em corpo grande, outra em negrito 10).
  Agora aparece uma vez só.
- **Janela** de 700x780 para **760x800** (mais folga).
- **Teste novo:** abre a aba Chave, mede a largura do texto a 640 px e a
  1300 px de largura e confirma que o texto acompanha (deu 564 px para
  1224 px) e que não estica demais.

---

## 2026-10-15 — Revisão do trabalho do Claude (memória) + 2 defeitos corrigidos

- **Situação encontrada:** o Claude trabalhou até os tokens acabarem. Deixou
  **dois commits** (`46a8fd4`, `cecabef`) com a `memoria.py` ligada ao
  programa, e começou uma experiência nova (`pasta web/`) que ficou
  **pela metade e sem commit**. O `verificar.py` passava (TUDO CERTO).
- **Defeito 1 (grave): organizar a memória APAGAVA informação do Wolf.**
  A regra das "gavetas" (nome, onde mora, idade: um lugar só) **trocava**
  o fato antigo pelo novo. Simulando com a memória real do Wolf:
  - `"Nome: Igor (pode ser chamado de Wolf)"` era **substituído** por
    `"Nome ou apelido: Wolf"` → o programa **esquecia o nome Igor**.
  - `"Fez 30 anos em 2 de outubro de 2026"` era **substituído** por
    `"Idade: mais de 30 anos"` → **perdia a data de nascimento**.
  - Pior: os 4 fatos repetidos de "Dragon's Dogma" **continuavam lá**.
  Ou seja: apagava o que era único e guardava a repetição. Como
  `organizar_memoria()` roda **toda vez que o programa abre**, isso ia
  acontecer no primeiro uso do `.exe` novo.
- **Defeito 2:** o fato `"NADA"` estava guardado na memória. Ele é a
  resposta que o modelo dá quando não há fato novo (o prompt novo manda
  responder "NADA"), ou seja, ia virar "lembre do programa" para sempre.
- **Correção 1 — nunca perder informação** (`memoria.juntar`): quando dois
  fatos são da mesma gaveta, eles agora são **JUNTADOS** num só
  (`"Nome: Igor (...) | Quer ser chamado de Wolf | Nome ou apelido: Wolf"`)
  em vez de um substituir o outro. Se não couberem em 200 caracteres, os
  dois ficam guardados separados — é melhor do que cortar a ponta de um
  deles.
- **Correção 2 — `"NADA"` e afins** (`memoria.tem_informacao`) não entram
  mais na memória, nem quando o modelo devolve isso agora, nem quando a
  memória antiga tem isso guardado.
- **Teste que barra a regressão:** `memoria.autoteste()` ganhou a regra de
  ouro — depois de organizar, **nenhuma palavra da memória antiga pode ter
  desaparecido**. O teste usa exatamente o caso do Wolf (o nome Igor, o
  apelido Wolf, a data de 2 de outubro) e falha se voltar a perder.
- **Resultado da simulação (com a memória real, só leitura, nada gravado):**
  23 fatos → 12, e a única "palavra perdida" foi a do `"NADA"`, que é
  lixo. Ficaram guardados: o nome Igor junto com o apelido Wolf, a data
  de nascimento completa, a cidade e a região.
- **A pasta `web/` foi guardada** (estava sem commit, podia se perder),
  com um `LEIA-ME.md` avisando que é só um protótipo: falta a ponte
  `app_web.py` e falta instalar o `pywebview`. Não é o programa.

---

## 2026-10-15 — Salvar a resposta em arquivo (.txt)

- **Pedido do Wolf:** item 2 da lista ("hoje só dá pra copiar").
- **Adicionado na bolha da IA:** um segundo botão embaixo da resposta, ao
  lado do de copiar — um **disquete** (`_desenhar_salvar` /
  `_icone_salvar`), que salva aquele texto num `.txt`.
- **Atalho:** **Ctrl+S** salva a última resposta (`_salvar_ultima`), no
  mesmo formato do botão de copiar (que já tinha Ctrl+C).
- **Nome do arquivo sugerido** (`_nome_de_resposta`): pega a primeira linha
  que tiver conteúdo, tira a numeração de lista ("1. ", "12) "), apaga
  tudo que o Windows proíbe em nome de arquivo (`\ / : * ? " < > |`),
  reduz espaços repetidos e corta em 48 caracteres. O nome sempre termina
  em `.txt`.
- **Gravação:** `utf-8-sig` (o Bloco de Notas do Windows abre com acentos
  certos; outros programas também entendem). Se a pessoa cancelar a
  janela, **não é erro** e o arquivo que já existia fica intacto — tem
  teste para isso. Se der erro ao gravar, aparece a janelinha escura
  `_dialogo_escuro` (nada de janela branca).
- **Limpeza no caminho:** o botão de copiar e o novo botão de salvar são o
  mesmo desenho, então `_icone_copiar` virou um atalho de
  `_icone_resposta(pai, comando, nome, desenhar, desenhar_no_canvas, ...)`.
  Cada símbolo passa também como ele deve ser desenhado **direto no
  Canvas**, para o botão continuar funcionando (só que serrilhado) se o
  Pillow faltar.
- **O que já existia e foi aproveitado:** a janela de "Salvar como" do
  Windows já era aberta escura por `_deixar_dialogo_do_sistema_escuro`
  (usada para salvar imagem), e todo aviso de erro já é `_dialogo_escuro`.
- **Testado:** nome sugerido em 4 casos + texto gigante; os dois botões
  existem na resposta e respondem ao clique; o arquivo sai com o texto
  certo; cancelar não estraga o que já estava lá.

---

## 2026-10-15 — Backup do código (cópia de segurança)

- **Pedido do Wolf:** "vou deixar isso na tua mão, faz o que tu achar que
  vai ser melhor caso aconteça uma catastrofe".
- **O risco:** o projeto inteiro vivia só neste computador (o Git estava
  dentro dele). Disco queimado, pasta apagada ou Windows reinstalado e ia
  junto todo o trabalho.
- **Adicionado:** `fazer_backup.py` + `4 - Fazer backup.bat`. O script
  grava o projeto num `.zip` com carimbo de data/hora em
  `OneDrive\Backup Pesquisa IA\` (que o OneDrive sincroniza com a nuvem),
  guarda só as 10 cópias mais recentes, e **confere o zip depois de
  escrever** (abre o arquivo, verifica que não está corrompido e que o
  `.git/HEAD` está dentro).
- **O que fica de fora (e por quê):** `.venv` (119 MB), `dist`, `build`,
  `__pycache__`, `_tmp` e `_arquivo_morto` (470 MB de `.exe` antigos).
  Nenhum disso é o programa — só dá para reinstalar/regerar.
- **Limpeza no caminho:** o `.git` tinha **48 MB**, sendo 47 MB num único
  arquivo órfão (um `.exe` que chegou a ser adicionado e nunca entrou em
  commit). `git reflog expire` + `git gc` derrubou para **0,5 MB**, sem
  mexer no histórico (os 30 commits continuam lá e o `verificar.py` segue
  passando).
- **Testado de verdade:** o zip foi **descompactado numa pasta vazia** e
  conferido: todos os arquivos presentes, o `git log` mostrando os 30
  commits, e `pesquisa_ia.py`, `voz.py`, `roteador.py`, `verificar.py` e
  `fazer_backup.py` compilando sem erro de sintaxe. Ou seja: o backup
  restaura de verdade.
- **Ainda dá para melhorar:** um repositório privado no GitHub daria uma
  segunda cópia em outro servidor. Precisa de uma conta do Wolf — por
  isso não foi feito sozinho.
- **Testado:** `verificar.py` = TUDO CERTO (o script novo entra no
  pyflakes junto com o resto).

---

## 2026-10-15 — Botão direito na caixa vazia + menu na tela certa

- **Relato do Wolf:** "o botão direito na caixa de digitar, nada acontece
  quando não há nada escrito; as opções só aparecem quando tem algo
  escrito".
- **Causa 1 (a do relato):** o texto de apoio ("Pergunte qualquer
  coisa...") é um `tk.Label` colocado **por cima** da caixa de digitar.
  Com a caixa vazia ele fica visível e **engolia os cliques** — o botão
  direito batia no Label, que não tinha nenhum clique ligado, e o menu
  nunca abria. De quebra, o clique com o botão esquerdo também não
  focava a caixa.
- **Correção 1:** `_clique_no_apoio` e `_menu_no_apoio` repassam o clique
  para a caixa (`_evento_da_entrada` traduz as coordenadas, porque o
  Label está 15 px deslocado dentro dela).
- **Causa 2 (achada testando):** mesmo com o menu abrindo, ele aparecia
  **na tela errada**. O código usava `raiz.winfo_screenwidth()`, que num
  Windows com dois monitores devolve **só a largura do monitor
  principal** (1920). Com a janela no segundo monitor, o menu era
  "arrumado" para x = 1920 - 133 - 8 = 1779 — ou seja, na primeira tela.
- **Correção 2:** nova função `_tela_virtual()`, que pergunta ao Windows
  pelos "virtual screen metrics" (a união dos monitores: aqui 3840x1080).
  O menu agora é preso dentro dessa área e nunca pula de tela.
- **Testado:** `verificar.py` = TUDO CERTO, com testes novos (clicar no
  texto de apoio foca a caixa; botão direito no texto de apoio abre o
  mesmo menu; a tela virtual inclui o segundo monitor; o menu fica dentro
  da tela toda). E **testado com o mouse de verdade no `.exe` novo**: a
  janela foi para o segundo monitor, o botão direito na caixa vazia
  abriu o menu em (2368, 853) — exatamente embaixo do clique, na tela
  certa — com as quatro opções, e "Recortar/Copiar/Colar" aparecendo
  apagados (correto: com a caixa vazia não há o que recortar, copiar nem
  colar ainda). Print conferido.

---

## 2026-10-15 — Nenhuma janela branca (tudo no darkmode do programa)

- **Pedido do Wolf:** "todas as janelas que abrem, como as de confirmação
  de teste, fossem em darkmode também, para manter o padrão do app... e
  para futuras adições também, sempre em darkmode e sem bordas brancas".
- **O que estava branco:** 13 janelas do `messagebox` do tkinter (que o
  Windows desenha com fundo branco e borda do sistema): "Salvo", "Erro",
  "Falta a chave", "Tudo certo" (chave e plano B), "Problema com a chave",
  "Apagar a memória" e a janela de erro fatal ao abrir o programa.
- **Correção:** nova função única `_dialogo_escuro(pai, titulo, texto,
  botoes=(...), destaque=0, largura_texto=380)`, que monta a janelinha
  com as mesmas cores, a mesma fonte e os mesmos botões do resto do
  programa (sem borda do Windows). Devolve o rótulo do botão clicado.
  - `_confirmar()` virou um chamarão dela (aceita os rótulos "Sim/Não" ou
    "Apagar/Cancelar").
  - `_janela_chave_ruim()` também (os botões abrem a página do Google ou
    as Configurações depois que o diálogo fecha).
  - `messagebox` saiu do import: não existe mais no programa.
- **Janela de "Salvar imagem como...":** essa é do próprio Windows e o
  tkinter não deixa trocar as cores. O que dá para fazer é pedir ao
  Windows que ela abra no tema escuro:
  `_deixar_dialogo_do_sistema_escuro(raiz)` procura a janela da classe
  `#32770` e aplica `SetWindowTheme("DarkMode_Explorer")`. **Honesto:**
  isso depende da versão do Windows e pode não funcionar em todas.
- **Regra para o futuro (o pedido do Wolf):** o `verificar.py` agora
  **FALHA** se `messagebox`, `simpledialog` ou `tk_optionMenu` aparecerem
  no código (a regra ignora comentários e docstrings para não se acusar
  sozinha). Está escrito também no `INSTRUCOES-PARA-IA.md` como regra 0.
- **Testado:** `verificar.py` = TUDO CERTO. Testes novos: (1) a regra das
  janelas brancas; (2) o diálogo tem as cores do programa (conferidas
  widget por widget, não por impressão de tela); (3) a confirmação devolve
  "não" quando fechada; (4) a janela de chave inválida abre e fecha.
  Conferência no print: "Excluir conversa" e "A chave do Google parou de
  valer" saíram escuras (41 e 145 pixels claros, só o texto e o botão
  azul). **O botão direito da caixa de digitar continua sem conferência
  visual** — é o único item ainda pendente dos testes.

---

## 2026-10-15 — Chave reserva com troca automática + aviso com botão

- **Pedido do Wolf:** "consegue atualizar a chave sempre que acontecer
  algo parecido? criar uma nova e atualizar no app?"
- **Resposta honesta (registrada aqui para não repetir):** **não dá para
  criar a chave sozinho.** O Google não oferece nenhuma API pública para o
  AI Studio criar chaves; só dá pela página, logado na conta. Um programa
  que fizesse isso teria que guardar a senha do Google do Wolf — o que
  ninguém, nem uma IA, deve fazer. O que dá para fazer é evitar o susto.
- **O que foi feito:**
  - **Chave reserva** (nova opção `cfg["api_key_reserva"]`) com campo
    próprio na aba Chave das Configurações.
  - **Troca automática**: `_falha_de_chave()` reconhece recusa de chave
    (401 / "API key not valid" / "unauthenticated" etc.) e
    `_tentar_com_reserva()` repete a chamada **uma vez** com a reserva.
    Erros que NÃO são de chave (cota do dia, internet caída) não trocam
    nada, e já na reserva ele não fica tentando trocar de novo.
  - aviso discreto embaixo da conversa: "A chave principal do Google parou
    de valer. Estou usando a chave reserva."
  - **janela de chave inválida** (`_janela_chave_ruim`) com dois botões:
    "Criar chave nova" (abre a página do Google) e "Colar chave nova"
    (abre as Configurações). Só aparece quando **não há** chave reserva.
  - a ajuda e o `LEIA-ME.txt` explicam o mecanismo.
- **Bug achado no caminho:** `_abrir_config(aba)` chamava
  `_mostrar_aba_config(aba)` **antes** das abas serem montadas, então
  `_abrir_config("chave")` numa janela nova abria na aba Memória e o botão
  "Colar chave nova" não levaria o Wolf ao campo da chave. Agora a aba pedida
  é mostrada depois que tudo existe. Tem teste.
- **Testado:** 9 testes novos no `verificar.py` (reconhece erro de chave,
  troca para a reserva na ordem certa, não entra em laço, cota não troca,
  janela de aviso abre sem erro, Configurações abre na aba pedida).
  A janelinha de aviso e a aba Chave com o campo da reserva foram
  conferidas no print (segundo monitor). O `.exe` novo foi gerado, aberto
  no segundo monitor (microfone vermelho -> cinza, cantos da caixa
  certos), sem `erro.log`, e copiado para a Área de Trabalho.
  `verificar.py` = TUDO CERTO.

---

## 2026-10-15 — Cantos da caixa: conserto do quadrado (relato do Wolf)

- **Relato do Wolf:** "os cantos da caixa de pergunta não estão
  arredondados mas sim com quadrados pretos", com print.
- **Causa:** a imagem do canto era pintada com a parte de FORA da curva em
  COR_FUNDO e o resto **transparente**, contando que o que está embaixo
  (a caixa) apareceria por baixo. Só que o `tkinter` não tem widget
  transparente: o `bg` de um `Label` preenche o quadrado INTEIRO. Então o
  "transparente" da curva virava COR_FUNDO também, e o canto saía como um
  quadrado de 12x12 em vez de uma curva. Nos prints que eu tirei com
  `PrintWindow` o antialiasing fazia parecer curva; na tela do Wolf
  apareceu o quadrado.
- **Correção:** `_foto_canto` virou `_imagem_canto` (devolve a imagem PIL,
  para o `verificar.py` poder conferir os pixels) + `_foto_canto` (a
  transforma em foto do Tk). A imagem agora é **inteiramente pintada**:
  dentro da curva fica a cor da caixa e fora a cor de fundo. Sem
  transparência, sem quadrado, sem depender do que está embaixo.
- **Testes novos no `verificar.py`:** a imagem do canto não pode ter
  nenhum pixel transparente, e tem que ter as duas cores.
- **Conferido no `.exe`:** pixel a pixel, a curva do canto agora é uma
  curva de verdade (a borda da caixa vai entrando 1 px por linha, até
  completar 12 px, dos dois lados).
- **JUNTO VEIO:** o Wolf avisou que **a voz para texto não funcionou**.
  Não é bug do programa: a chave de API do Google **estava sendo recusada
  com erro 401 "API key not valid"**, em qualquer chamada (até só para
  listar modelos). A chave funcionava mais cedo no mesmo dia (uma
  transcrição de teste deu certo), então o Google passou a recusá-la no
  meio do caminho. Isso afetava **tudo** que usa a IA: perguntar,
  pesquisar e falar.
- **RESOLVIDO no mesmo dia:** o Wolf criou uma chave nova em
  <https://aistudio.google.com/apikey>, colou em Configurações e
  **testou: o reconhecimento de voz funcionou**. Confirmei daqui também
  (transcrição de um áudio de teste com a chave nova deu certo). A Tarefa
  B está agora testada de ponta a ponta pela voz do Wolf.

---

## 2026-10-15 — Tarefa C: interface mais limpa (estilo Claude)

- **Pedido do Wolf:** executar a `PLANO-NOVAS-FUNCOES.md`, Tarefa C.
- **Modificado:** `pesquisa_ia.py`:
  - **caixa de digitar com cantos arredondados.** O tkinter não sabe
    arredondar um `tk.Text`, então foram desenhadas quatro "tampinhas"
    (uma por canto) com o Pillow, que pintam de fundo o que sobrou fora da
    curva: `_dentro_do_canto()` (a conta da curva, testável) e
    `_foto_canto()` (a imagem). Elas acompanham a caixa quando a janela
    muda de tamanho (`_cantos_da_caixa`).
  - **texto de apoio** "Pergunte qualquer coisa..." dentro da caixa, que
    some assim que a pessoa digita, cola ou fala (`_atualizar_apoio`).
  - a borda reta da caixa foi tirada (`highlightthickness=0`), porque
    quadrado por cima de canto redondo ficava torto.
  - **botão direito completo** na caixa de digitar: Recortar, Copiar, Colar
    e Selecionar tudo, com as correções de ortografia no topo quando a
    palavra sob o cursor está errada. O que não pode ser usado naquele
    momento (Recortar/Copiar sem seleção, Colar sem nada na área de
    transferência) fica apagado e sem clique. O clique direito também
    coloca o cursor onde foi clicado, para o "Colar" entrar no lugar certo.
  - a lógica das sugestões saiu de `_menu_ortografia` para
    `_sugestoes_no_ponto(x, y)`, que o `verificar.py` consegue testar sem
    clicar.
  - **Ctrl+A, Ctrl+Z e Ctrl+Y** funcionando na caixa. Foi preciso criar o
    `tk.Text` com `undo=True` (o Tk deixa o histórico desligado por
    padrão, então o `edit_undo()` não fazia nada).
  - **coluna centralizada**: a conversa (e a caixa de digitar) passam a ter
    largura máxima de 820 px e ficam no meio da janela; em janela normal
    continua igual, usando a tela toda (`_margem_da_coluna`,
    `_alinhar_rodape`, `LARGURA_MAX_COLUNA`).
- **Modificado:** `verificar.py`: 20 testes novos da Tarefa C (texto de
  apoio, cantos, Ctrl+A/Z/Y, o menu do botão direito com os quatro
  comandos, ordem das correções, comandos apagados, recortar/copiar/colar de
  verdade, coluna e caixa centralizadas).
- **Bugs encontrados no caminho (e corrigidos):**
  - `_foto_canto` pintava uma cor de 5 valores e o Pillow recusava
    (`_rgba` já devolve RGBA inteiro);
  - **o mais chato:** `_dentro_do_canto` punha o centro da curva no canto
    errado (estava girado 90°). Aí a tampinha comia um pedaço do botão de
    enviar em vez de arredondar o canto. Só apareceu olhando os pixels do
    print. Agora a função tem um teste que confere, para os quatro cantos,
    que o bico fica FORA da caixa e o miolo fica DENTRO, e que os quatro
    juntos só cortam uns 20% (a curvatura);
  - **e depois:** no `place`, o `anchor` JÁ põe o canto do widget no ponto
    indicado. Somar `-raio` empurrava as tampinhas 12 px para dentro da
    caixa, e elas cobriam o botão de enviar — inclusive o microfone, que
    parou de responder ao clique no `.exe`. Agora é só `anchor` + `relx`/
    `rely`. Tem teste conferindo que cada tampinha encosta na borda da
    sua quina e que nenhuma cobre o botão de enviar;
  - o `padx` do botão de enviar era menor que o raio do canto, e a
    tampinha do canto passava por cima do botão. Agora o respiro é
    `RAIO_CANTO` (12 px);
  - `linha_modo` (o "Web: automática") nunca foi salva como atributo, então
    a linha não acompanhava a coluna — e o erro era engolido pelo
    `except: pass`.
- **Testado com os olhos:** janela normal e janela de 1700 px, com a
  caixa vazia (texto de apoio + cantos), com texto escrito, com palavra
  errada sublinhada e com a coluna centralizada. Print tirado com
  `PrintWindow` na janela do segundo monitor (o `ImageGrab` no segundo
  monitor devolve preto). Também conferido pixel por pixel: sem o
  `_dentro_do_canto` e o `anchor` certainos, o canto comia o botão.
- **Testado no `.exe` novo:** janela no segundo monitor, microfone fica
  vermelho e volta ao cinza (clicando nele), e a coluna centraliza na
  janela de 1700 px. `erro.log` não apareceu.
- **Não testado:** o visual do menu do botão direito na tela (é uma janela
  separada e o `PrintWindow` não a pega; os itens foram conferidos pelos
  testes) e o canto arredondado com o mouse passando em cima.
- **Testado:** `verificar.py` = TUDO CERTO (110 linhas de conferência).
  `.exe` novo gerado e copiado para a Área de Trabalho.

---

## 2026-10-15 — Tarefa B: falar a pergunta (botão de microfone)

- **Pedido do Wolf:** executar a `PLANO-NOVAS-FUNCOES.md`, Tarefa B.
- **Baixado:** `sounddevice==0.5.6` (traz o PortAudio junto, sem instalar
  nada à mão). Versão fixada em `requirements.txt`; `requirements-lock.txt`
  refeito com `pip freeze`.
- **Adicionado:** `voz.py` (funções puras, não importa o programa):
  `microfone_disponivel()`, `microfone_erro()`, `Gravador` (grava 16 kHz
  mono, monta o WAV, mede o nível, limite de 120 s), `wav_tem_som()`,
  `segundos_do_wav()` e `transcrever()` (manda o WAV ao Gemini e tenta o
  próximo modelo se um falhar).
- **Modificado:** `pesquisa_ia.py`:
  - novo botão de microfone ao lado do de enviar (mesma arte, feita com
    Pillow), que fica vermelho pulsando enquanto grava; atalho `Ctrl+M`;
  - `_comecar_gravacao` / `_parar_gravacao`: avisam em português quando
    falta a biblioteca, falta microfone, falta a chave ou o Windows
    bloqueou o acesso; se a gravação não tiver voz, diz "Não ouvi nada"
    sem gastar chamada da IA;
  - o texto falado entra na caixa de digitar na posição do cursor e
    **não** é enviado sozinho (opção `cfg["voz_enviar"]`, padrão
    desligada, na aba Chave das Configurações);
  - novos itens de fila `voz` e `voz_erro` tratados em `_tratar_item`;
  - `_definir_ocupado` cuida também do cursor do microfone, e `F5`
    (nova conversa) desliga a gravação;
  - `cfg["voz_enviar"]` com padrão em `carregar_config`;
  - ajuda atualizada com a nova forma de falar e o atalho `Ctrl+M`.
- **Modificado:** `Pesquisa IA.spec`: entra `sounddevice` e
  `_sounddevice_data` (as DLLs do PortAudio), senão o `.exe` abriria sem
  microfone.
- **Modificado:** `verificar.py`: 22 testes novos da voz (gravador com
  fluxo falso, cabeçalho do WAV, "tem voz?" com voz fraca e só ruído,
  `transcrever` com cliente falso e modelos em queda) e 6 testes de tela
  (botão existe, fica vermelho, `Ctrl+M` para, texto entra na caixa sem
  espaço, erro não trava). A janela de teste passou a nascer no **segundo
  monitor** (`POSICAO_TESTE = "+2000+100"`), para não cobrir a tela do Wolf.
- **Testado de verdade:** microfone gravado por 4 s (o `sounddevice` achou
  o aparelho) e um WAV gerado pelo Windows foi transcrito pelo Gemini:
  "Qual e o melhor jogo de God of War?" virou "Qual é o melhor jogo de
  God of War?".
- **Medido no microfone do Wolf:** parado o volume fica em 5 a 20; por
  isso `wav_tem_som` exige volume acima de 60 **e** um trecho pelo menos
  8x mais forte que o mais fraco (senão um fone ligado perto do
  microfone seria confundido com voz).
- **Não testado:** ouvir a sua voz de verdade e ver o texto transcrito
  aparecer na caixa (precisa de alguém falando; num teste anterior o
  microfone do Wolf quase não pegou o áudio do alto-falante, então o
  volume medido foi baixo). O botão com o mouse passando em cima só foi
  conferido no desenho, não na tela.
- **Limpeza:** sobras da Tarefa A (`_tmp\capturar.py`, `_tmp\patch1.py`)
  foram para `_arquivo_morto\_tmp_sobras\`, e a `_tmp\` agora é ignorada
  pelo Git.
- **Testado de verdade no `.exe`:** janela aberta no segundo monitor,
  clique no microfone -> botão fica vermelho e aparece "Ouvindo... clique
  de novo no microfone (ou Ctrl+M) para parar"; segundo clique -> botão
  volta ao cinza e, como ninguém falou, aparece "Não ouvi nada. Tente de
  novo, mais perto do microfone." (exatamente o comportamento combinado).
  `erro.log` não apareceu.
- **Testado:** `verificar.py` = TUDO CERTO. `.exe` novo gerado e copiado
  para a Área de Trabalho.

---

## 2026-10-15 — .exe atualizado (Tarefa A e correção dos três pontinhos)

- **O que era:** o atalho da Área de Trabalho era de 15/10 03:30, sem a
  Tarefa A (roteador) e sem a correção dos três pontinhos da lista de
  conversas.
- **O que foi feito:** `3 - Gerar EXE.bat` (verificar + PyInstaller),
  `.exe` aberto por 13 s no segundo monitor sem criar `erro.log`, e o
  antigo foi para `_arquivo_morto\Pesquisa IA - antes da Tarefa B
  (15-10 03-30).exe`.

---

## 2026-10-15 — Tarefa A: amigo que só pesquisa quando precisa

- **Pedido do Wolf:** executar o `PLANO-NOVAS-FUNCOES.md`, Tarefa A.
- **Adicionado:** `roteador.py` (funções puras, só biblioteca padrão, sem
  importar o programa): `regra_local` (cumprimento e comandos `/web` e
  `/papo` decidem na hora, sem gastar IA), `decidir` (regra -> modelo com
  JSON -> heurística de reserva, nunca trava), `heuristica_pesquisa` (só
  pesquisa com palavras de "agora"), `fato_pedido` ("lembra que..." vira
  fato) e `prompt_roteador`.
- **Adicionado:** `PLANO-NOVAS-FUNCOES.md` (plano escrito pelo Claude,
  colocado na pasta pelo Wolf).
- **Modificado:** `pesquisa_ia.py`:
  - `INSTRUCOES` agora abre com "amigo bem informado"; novo
    `INSTRUCOES_AMIGO` (tom de amigo, sem web, sem inventar fatos).
  - `instrucoes_da_ia(modo="pesquisa")`, e o `modo` passa por
    `_gerar_texto`, `_chamar_servico` e `_gerar_texto_rapido` (amigo usa
    temperatura 0.7 e 12 falas; pesquisa continua 0.3 e 6).
  - `perguntar(..., consulta=None)`: a busca usa a consulta do roteador; o
    prompt final continua com a pergunta original.
  - `conversar`: prompt curto (data + pergunta + conversas); bloco de
    memória duplicado removido (a memória já vai no `instrucoes_da_ia`).
  - `_enviar`: a decisão sai da thread da tela e vai para a thread de
    fundo (`_decidir_modo` com o modelo rápido e 8 s de limite); status
    "Pensando..." e depois "Pesquisando na web..." ou "Conversando...".
    Imagens e notícias explícitas continuam pesquisando como antes.
    "Lembra que..." grava direto na memória, sem gastar IA.
  - Novo `cfg["modo_pesquisa"]` (auto|sempre|nunca) com botão pequeno
    ("Web: automática", clique alterna) sob a caixa de digitar, e novo
    `cfg["aprender"]` (padrão ligado). Aprendizado agora roda quando a
    fala tem 12+ caracteres OU a resposta 120+.
  - `_quer_pesquisa` ficou sem uso (o roteador assumiu); mantida no código
    por enquanto.
- **Modificado:** `verificar.py`: 20 testes novos do roteador (regras,
  JSON limpo/cercado/lixo/erro, frases reais, fato pedido, prompts).
- **Não testado:** pergunta real à IA nem uso longo (precisa da chave e do
  Wolf). Os controles de modo na aba Conversa das Configurações ficam
  para a Tarefa D (a aba ainda não existe).
- **Testado:** `verificar.py` = TUDO CERTO. Sem .exe novo (o plano só pede
  .exe ao final de B, C e D).

---

## 2026-10-15 — Duplo/triplo clique, .exe novo e pasta antiga apagada

- **Pedido do Wolf:** fazer tudo que desse, trabalhar só com a pasta nova,
  apagar a antiga e deixar instruções para outra IA continuar.
- **Modificado:** `pesquisa_ia.py` (`_criar_bolha`): duplo clique seleciona
  a palavra, triplo clique seleciona o texto todo da bolha. Ambos limpam as
  outras seleções e avisam os menus abertos (`_despachar_clique`).
- **Modificado:** `verificar.py`: dois testes novos (duplo e triplo clique).
- **Adicionado:** `PROXIMOS-PASSOS.md` (o que falta e o que não foi
  testado) e `requirements-lock.txt` (`pip freeze` completo do .venv).
- **Reescrito:** `PROMPT-PARA-A-IA.md` (estado atual, sem a pasta antiga).
- **Textos:** o usuário agora é chamado de Wolf (apelido) nos guias; o nome de
  usuário do Windows continua Igor (aparece em caminhos).
- **Gerado:** `dist\Pesquisa IA.exe` de novo (PyInstaller 6.22.3), copiado
  para a Área de Trabalho. O anterior foi movido para
  `_arquivo_morto\Pesquisa IA (Area de Trabalho, antes de 15-10).exe.antigo`.
  O .exe novo abriu e ficou 12 s aberto sem criar `erro.log`.
- **Apagado:** o conteúdo da pasta antiga
  `C:\Users\Igor\OneDrive\Documentos\Projeto Padrão` (autorizado pelo
  Wolf). Só havia de exclusivo um `erro.log` antigo, sem valor. Uma pasta
  vazia pode ter sobrado (travada por outro programa); ignorar.
- **Corrigido neste histórico:** a entrada de 14/10 dizia que a pasta antiga
  tinha sido renomeada para "(ANTIGO - pode apagar)"; na verdade nunca foi
  renomeada. Agora foi apagada.
- **Não testado:** pergunta real à IA e uso longo do .exe.

---
## 2026-10-14 — Mudança de pasta, correção de cliques e organização

### Local do projeto
- **Movido** de `C:\Users\Igor\OneDrive\Documentos\Projeto Padrão`
  para `C:\Projetos\PesquisaIA`.
  Motivos: o OneDrive sincronizava a pasta `.venv` (centenas de arquivos,
  lento e pode corromper) e o nome antigo tinha acento (`ã`), que já
  causava texto quebrado em scripts.
- A pasta antiga ficou como cópia de segurança até 15/10/2026, quando foi apagada (ver a entrada de 15/10 acima). Não existe mais.
- O Git veio junto (histórico completo preservado).
- O ambiente `.venv` foi **recriado** do zero no local novo (venv não é
  movível), com Python 3.12.10.

### Baixado / instalado (no `.venv` novo)
Programa (`requirements.txt`, agora com versões fixas):
- google-genai 2.30.1, ddgs 9.16.0, pyspellchecker 0.9.1, pillow 12.3.0
- **httpx 0.28.1** — adicionado ao arquivo porque o código usa `import httpx`
  direto (antes só vinha de carona).
Ferramentas (`requirements-dev.txt`, novo):
- pyinstaller 6.22.3 (gera o .exe), pyflakes 4.0.3 (analisa o código — novo)
- pip atualizado de 25.0.1 para 26.2.1
Dependências automáticas dessas bibliotecas (pydantic, requests, etc.)
foram instaladas junto; não precisam ser listadas.

### Modificado
- `pesquisa_ia.py`:
  - Seleção de texto: `_limpar_selecoes`, `_ao_clicar_fora`,
    `_selecao_propria`, lista `_telas_bolha`; clique novo apaga a seleção
    anterior; Ctrl+C e menu Copiar só usam a seleção da própria bolha.
  - Cliques globais: criados `_despachar_clique`,
    `_registrar_clique_global`, `_remover_clique_global`. Os 3 usos de
    `bind_all`/`unbind_all("<Button-1>")` (menu de ortografia, menu Copiar,
    menu "Excluir" da conversa) agora usam esse sistema.
  - Removida a função morta `_rolar_ajuda` (citava `tela_ajuda`, nome que
    não existe); `_preencher_aba_ajuda(self, pai, ao_rolar=None)` com
    parâmetro opcional.
  - Limpezas do pyflakes: `except ... as erro` sem uso e `global
    _memoria_cache` sem uso.
- `requirements.txt`: versões fixadas (`==`), `httpx` incluído, comentário.
- `Pesquisa IA.spec`: agora também embute `avatar_usuario.png` no .exe
  (antes só o ícone; o .exe da Área de Trabalho ficava sem o avatar).
- `.gitignore`: `*.spec` deixou de ser ignorado (a receita do .exe agora é
  versionada); `_arquivo_morto/` passou a ser ignorado.

### Adicionado
- `verificar.py` + `verificar.bat` — conferência automática com testes de
  tela (seleção, menus, Configurações, erros escondidos), pyflakes e regras
  do projeto. Obrigatória após qualquer alteração.
- `3 - Gerar EXE.bat` — roda o verificador e gera `dist\Pesquisa IA.exe`.
- `requirements-dev.txt`.
- `INSTRUCOES-PARA-IA.md`, `PASSO-A-PASSO.md`, este arquivo e
  `PROMPT-PARA-A-IA.md`.

### Removido do projeto (não copiado para o local novo)
- `cairosvg` e scripts `svg2pdf` — estavam no `.venv` antigo, mas o código
  não os usa.
- Pastas geradas `build/`, `dist/` (antigas) e `__pycache__/`; `.exe` antigo
  da raiz. O `dist\Pesquisa IA.exe` foi regenerado.

### Movido para `_arquivo_morto\` (não apagado)
- `_run41.py`, `_run_debug.py`, `_run_debug2.py` (testes soltos antigos,
  usavam o caminho antigo com acento).
- `pesquisa_ia.backup-antes-da-selecao.py` (versão antes da correção de
  seleção), `erro-antigo-2026-10-14.log`, `Pesquisa IA.spec.antigo`,
  `Pesquisa IA.exe.antigo` e a cópia do .exe que estava na Área de Trabalho.

### Substituído fora do projeto
- `Pesquisa IA.exe` na Área de Trabalho (em
  `C:\Users\Igor\OneDrive\Área de Trabalho`) pelo novo, gerado em
  `C:\Projetos\PesquisaIA\dist`.

### Não mexido
- `%LOCALAPPDATA%\PesquisaIA\` (conversas, memória, chaves do Wolf).
- `IDEIAS.md`, `PLANO-B.txt`, `avatar_usuario.png`, `icone.ico`.

### Testado
- `verificar.py`: TUDO CERTO (3 rodadas seguidas, sem avisos).
- O .exe novo abriu e ficou aberto 9 s sem criar `erro.log`.
- NÃO testado: perguntas reais à IA (precisa de internet e da chave do
  Wolf) e o uso do .exe por um período mais longo.
