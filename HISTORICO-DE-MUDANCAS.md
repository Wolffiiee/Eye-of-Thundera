# Histórico de mudanças

Registre aqui toda mudança relevante (a mais nova em cima): o que foi
baixado/instalado, modificado, adicionado, removido ou movido.

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
  Não é bug do programa: a chave de API do Google **está sendo recusada com
  erro 401 "API key not valid"**, em qualquer chamada (até só para listar
  modelos). A chave funcionava mais cedo no mesmo dia (uma transcrição de
  teste deu certo), então o Google passou a recusá-la. Isso afeta **tudo**
  que usa a IA: perguntar, pesquisar e falar. Enquanto o Wolf não trocar a
  chave em <https://aistudio.google.com/apikey>, nenhuma resposta vai
  aparecer.

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
