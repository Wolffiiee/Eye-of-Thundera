# Histórico de mudanças

Registre aqui toda mudança relevante (a mais nova em cima): o que foi
baixado/instalado, modificado, adicionado, removido ou movido.

---

## 2026-10-18 - Varredura final: fim dos resquicios de "PesquisaIA"

- **Bug achado e corrigido:** `fazer_backup.py` ainda salvava o backup do codigo em `OneDrive\Backup Pesquisa IA\` com o nome `pesquisa-ia_*.zip`. Agora usa `OneDrive\Backup Eye of Thundera\` e `eye-of-thundera_*.zip`.
- **Backup antigo MOVIDO (nada apagado):** os 2 `.zip` do codigo e os 7 `dados_*.zip` foram da pasta `OneDrive\Backup Pesquisa IA` para `OneDrive\Backup Eye of Thundera`. A pasta antiga foi removida vazia.
- **Documentos ativos arrumados:** `IDEIAS.md`, `PLANO-B.txt`, `PROMPT-PARA-A-IA.md`, `verificar_motor.py`, `web/spike_webview.py`, `ferramentas/gerar_pasta_limpa.py` e `ferramentas/gerar_pacote_troca.py` (inclusive a referencia ao modulo, que agora e `eye_of_thundera.py`).
- **O que ficou com o nome antigo de proposito:**
  - `eye_of_thundera.py`, `lembretes.py`, `plugins.py` e `sincronizar.py` guardam `PASTA_*_ANTIGA = ... / "PesquisaIA"`. E a migration one-time: se o programa rodar num computador que so tem a pasta velha, ela copia os dados para a nova. e precisa ficar.
  - `HISTORICO-DE-MUDANCAS.md` e os planos marcados como "historico" citam o nome antigo porque registram o que aconteceu. Isso e arquivo de memoria do projeto, nao esta rodando.
- **Pasta `%LOCALAPPDATA%\PesquisaIA` mantida** como copia de seguranca dos dados. A pasta nova `%LOCALAPPDATA%\Eye of Thundera` tem tudo e mais atualizado.
- **Pasta `D:\Projetos\PesquisaIA`:** ficou vazia; o Windows so libera o apagamento no proximo reinicio.
- **Verificacao:** `verificar.py` com 177 verificacoes e `verificar_motor.py`, ambos TUDO CERTO. EXE recompilado e atalho atualizado.

---

## 2026-10-18 - Pasta do programa renomeada: `Eye of Thundera`

- **O que mudou:** a pasta de trabalho saiu de `D:\Projetos\PesquisaIA` e passou a se chamar `D:\Projetos\Eye of Thundera`. Nenhum arquivo foi perdido; o repositório git, o ambiente virtual (`.venv`), a pasta `dist` e todo o código vieram junto.
- **Nome da pasta de dados:** `%LOCALAPPDATA%\PesquisaIA` passou a ser `%LOCALAPPDATA%\Eye of Thundera`. Os arquivos do usuário (config, histórico, memória, lembretes, janela, dicionário) foram copiados automaticamente para a pasta nova na primeira execução. **A pasta antiga não foi apagada** — pode ser removida à vontade depois, quando o usuário confirmar que está tudo certo.
- **Pasta de plugins:** o plugin de exemplo (`/tempo`) foi copiado para `%LOCALAPPDATA%\Eye of Thundera\plugins`.
- **Ambiente virtual corrigido:** `pyvenv.cfg` e o `activate.bat` apontavam para o caminho antigo e foram atualizados para a pasta nova.
- **Atalho da Área de Trabalho:** continua apontando para `D:\Projetos\Eye of Thundera\dist\Eye of Thundera\Eye of Thundera.exe` (EXE recompilado após a mudança).
- **Documentação:** `LEIA-ME.txt`, `README.md` e demais arquivos `.md` passaram a citar `D:\Projetos\Eye of Thundera` e `%LOCALAPPDATA%\Eye of Thundera`.
- **Verificação:** suíte com 177 verificações, 0 falhas, 0 avisos.

---

## 2026-10-18 - Modo onedir: um único processo no Gerenciador de Tarefas

- **Problema:** o EXE compilado pelo PyInstaller estava em modo "onefile" (um único arquivo). Ao abrir, o PyInstaller extrai os arquivos para uma pasta temporária e executa um segundo processo — por isso apareciam **dois** "Eye of Thundera.exe" no Gerenciador de Tarefas (aba Detalhes).
- **Solução:** mudou para modo "onedir" (pasta com o executável e as dependências). Agora existe apenas **um processo** ao abrir o programa. O atalho aponta para `dist/Eye of Thundera/Eye of Thundera.exe`.
- **Verificação:** suíte com 177 verificações, 0 falhas, 0 avisos. Confirmado pelo usuário: um único processo no Gerenciador de Tarefas, com ícone correto.

## 2026-10-18 - Plugins e Sincronização entre computadores (Prioridades 5 e 6)

- **O que o usuário ganha:** (1) **Plugins** — comandos locais em Python que respondem sem IA e sem chave, como os lembretes; o Wolf cria um arquivo `.py` na pasta de plugins e liga/desliga pela aba Plugins. (2) **Sincronização** — conversas, memória, configurações e chaves iguais em dois computadores por uma pasta que o Windows sincroniza (OneDrive, Drive, Dropbox); importa ao abrir e exporta ao fechar.
- **Novo `sincronizar.py`:** última escrita vence por arquivo (sem mesclagem), cópia atômica (escreve `.tmp` e renomeia), nunca apaga nada do outro lado, erro nunca derruba o programa. `arquivos_de_dados()` lista os `.json` da pasta de dados (menos `erro.log`). `sincronizar_tudo()` importa e exporta.
- **Novo `plugins.py`:** pasta `plugins` em `%LOCALAPPDATA%\Eye of Thundera`; contrato mínimo `responder(texto)` devolve `None` (não é com ele) ou string (resposta); `NOME`/`DESCRICAO` opcionais para a interface. Plugin com erro **não derruba**: erro vai ao log e o próximo plugin é tentado. Plugin de exemplo (`/tempo`) criado na primeira vez.
- **Interface:** duas abas novas em Configurações — **Sincronização** (escolher pasta pelo diálogo nativo, botão Sincronizar agora, estado com carimbo) e **Plugins** (lista com interruptor ligar/desligar, descrição, aviso de erro, botão abrir a pasta). CSS: `.estado-info`, `.plugin-nome`, `.plugin-desc`, `.aviso-erro`, `.linha-campo`.
- **Ponte (`app_web.py`):** `sincronizar_importar` no arranque do `principal()` (antes de carregar dados) e `sincronizar_exportar` no `ao_fechar`; `sincronizar_config`, `sincronizar_agora`, `sincronizar_config_salvar`, `plugins_listar`, `plugins_salvar`, `escolher_pasta`, `abrir_pasta`; plugins respondem no `enviar()` logo após os lembretes (antes da chave).
- **`verificar.py`:** 2 testes novos (sincronização: importa/exporta/iguala/avisos/erro sem exceção; plugins: descobrir/responder/erro isolado/exemplo). Suíte: **176 verificações, 0 falhas, 0 avisos**.

## 2026-10-18 - Documento longo testado e aprovado com PDF de 12 paginas

- Gerado um PDF de teste (`_tmp/gerar_pdf_longo.py`, apagado da Área de Trabalho depois do teste) com 12 capítulos de um guia de caminhada fictício — PDF de texto puro com acentos (mapa ToUnicode, extraível pelo pypdf sem OCR), um fato único por página para conferir a citação.
- **Resultado do teste manual (aprovado pelo usuário):** as 4 perguntas ("resistência da corda", "graus de queda indicam tempestade", "canal de rádio", "ponto de encontro") citaram a página exata (5, 7, 11 e 12); o "índice do documento" listou os 12 capítulos com a página de cada; o "resumir documento" cobriu os 10 trechos com o aviso honesto de que não cobre o documento inteiro. O modo "documento" foi ativado corretamente (12 > 10 páginas).
- Pendência de teste manual do Prioridade 7 concluída; sobram só validações visuais (escala do Windows >100%, persistência de tema, disposição do menu).

## 2026-10-18 — Termos da busca pintados na Memória

- **O que o usuário ganha:** ao buscar na aba Memória, os termos que casaram com a busca aparecem **pintados** no item ("conta dluz" pinta "conta" e "luz" em "Pagar a conta de luz"), usando a mesma tolerância a erro de digitação e acentos do `busca.js` — dá para ver **por quê** o item apareceu nos resultados.
- **Como funciona:** nova função `destacarTexto()` no `web/app.js` quebra o item palavra por palavra, normaliza cada palavra (mesmo caminho do `busca.js`) e envolve em `<span class="destaque-busca">` o que casou por prefixo ou por razão de Levenshtein (limiares 0.72/0.84 iguais aos da busca). O texto passa por `escaparHtml()` antes do `innerHTML` (o item guardado pode ter `<` ou `&`); os acentos e a capitalização originais ficam intactos — só ganha a marcação. Sem termo na caixa, o texto sai igual a `textContent`.
- **CSS:** `.destaque-busca` usa `var(--azul)` e `var(--btn-texto)`, então acompanha os dez temas.
- **`verificar.py`:** dois testes novos (estrutura: funções no `app.js`, classe no CSS, uso no desenhar; e lógica via Node.js: destaque correto, escape de `<`/`&`, acento preservado e nenhum destaque quando nada casou). Resultado: **174 verificações, 0 falhas, 0 avisos**.
- **Avatar da IA removido** (pedido do usuário de 18/10): o bloco que criava `.avatar` com a lupa à esquerda das respostas foi retirado de `criarMensagem()` e **commitado nesta rodada** — antes, a remoção estava só no working tree e um `git checkout` tinha restaurado sem querer; agora está preservada no código. O indicador "digitando" e os demais ícones seguem intactos.

## 2026-10-17 — Busca na Memória tolerante a erro de digitação e sem acentos (Prioridade 2 das sugestões)

- **O que o usuário ganha:** na aba Memória, o campo de busca agora acha "conta de luz" quando o Wolf digita "conta dluz" (erro de digitação), "cafe" quando está escrito "café" (sem acento), "CONTA DE LUZ" (maiúsculas), e "casa" quando está escrito "casas" (plural/prefixo). A lista também ordena os resultados por relevância (o mais provável vem primeiro). Antes, a busca era `f.toLowerCase().includes(termo)` — texto exato, sem tolerância a nada.
- **Tudo na tela, sem Python e sem dependência:** o novo `web/busca.js` tem 4 funções (`busca_normalizar`, `busca_distancia`, `busca_razao`, `busca_pontos`) — normalização NFD para acentos, Levenshtein iterativo para distância, e pontuação de 0 a 1 com limiar de 0.72 (ou 0.84 para palavras de 1-2 letras). A Memória guarda no máximo 200 itens, então cada tecla custa poucos milissegundos.
- **Regra corrigida durante a validação:** a primeira versão usava `q.includes(p) || p.includes(q)` — a direção `p.includes(q)` fazia com que **qualquer letra** do termo casasse com qualquer palavra do texto: "chocolate" achava "a", "rato" achava "gato" (rato é substring de gato), "bolo de chocolate" achava "A receita de bolo" (porque "chocolate".includes("a")). A regra foi corrigida para **`q.startsWith(p)`** — a palavra do texto começa com o termo (prefixo), não contém como substring intermediária.
- **Limitação conhecida e documentada:** "rato" ainda acha "gato" (75% parecido — só 1 letra de diferença), a **mesma conta** que faz "gatu" achar "gato". É matematicamente impossível aceitar o erro de digitação em palavra curta e recusar palavras diferentes de 1 letra: a decisão foi manter a tolerância (propósito do recurso) e documentar a limitação. O teste de Node.js (`_tmp/testar_busca_memoria.js`) tem 18 casos, incluindo a limitação como `true` com comentário explicando.
- **`verificar.py`:** dois testes novos (existência e regra do `busca.js`, ligação no HTML e no `app.js`; e execução dos testes de Node.js com os 18 casos). Resultado: **172 verificações, 0 falhas, 0 avisos**.

## 18/10/2026 - Perguntar sobre documento longo (Prioridade 7) - plano em PLANO-DOCUMENTOS-LONGOS.md
- Novo `documento.py`: PDF com mais de 10 paginas (ou 30.000 caracteres) abre como "documento" em vez de virar texto na caixa. O texto fica so na memoria, por pagina; cada pergunta manda para a IA apenas os trechos que combinam (busca local, sem acento) com "[pag. N]", e a IA cita "(pag. N)". Nada vai para a IA antes de perguntar.
- Comandos locais (sem gastar token): "indice do documento" (titulos provaveis; sem titulos, a primeira linha de cada pagina) e "resumir documento" (trechos espalhados). Pergunta sem nada parecido no texto responde "Nao achei" sem chamar a IA.
- Defeito corrigido nesta rodada: a busca cortava toda palavra em 6 letras, entao "clausula7" virava "clausu" e todas as clausulas empatavam (a pagina certa ficava de fora). Palavra com numero agora fica inteira; numero sozinho ("artigo 7") tambem vale.
- Tela: cartao "documento aberto" com botao Fechar acima da caixa. `pdf_leitor.paginas_de_pdf` entrega o texto por pagina; o caminho de PDF curto e dos .txt/.md/.csv nao mudou.
- Modo offline com Ollama (Prioridade 4 das sugestoes): CANCELADO pelo Wolf; o programa segue so com as APIs.
- `verificar.py`: 170 verificacoes, 0 falhas, 0 avisos; `verificar_motor.py` TUDO CERTO.
- Nao testado: arrastar um PDF longo de verdade pela tela e perguntar com a chave real.

## 2026-10-17 — PDF digitalizado agora é lido: OCR local do Windows (Prioridade 1 das sugestões)

- **O que o usuário ganha:** arrastar um PDF **digitalizado** (uma foto da página, sem camada de texto) para a conversa não para mais no aviso "não encontrei texto" — o programa **lê as páginas** e coloca o texto na caixa para revisar antes de enviar, como já acontece com PDF com texto. Tudo **no próprio computador**: a página é renderizada na memória e lida pelo **OCR do próprio Windows**, em português. Nada vai para a internet.
- **Viabilidade medida antes de implementar** (como o documento de sugestões pede): o `pytesseract` precisaria do Tesseract instalado no sistema (não é só `pip`), então o caminho escolhido foi o OCR do Windows, que já vem com o sistema. Testes com um PDF sintético (imagem com texto salva como PDF): render de 0,21 s por página e leitura de **0,05 s por página**, com as 4 frases reconhecidas. Entraram no `requirements.txt` e nos dois `.spec`: `pypdfium2` (renderização, só `pip`, sem instalar nada no sistema) e `winsdk` (OCR do Windows).
- **O que mudou no código:** `pdf_leitor.py` ganhou `_texto_por_ocr()` — renderiza até **20 páginas** (cada uma leva ~0,1 s) e avisa no texto quando o PDF passa disso. Se faltar qualquer uma das duas bibliotecas, o aviso antigo continua valendo ("pode ser digitalizado"). O texto do OCR entra na caixa para revisão, como manda o fluxo existente.
- **Achado importante no meio do caminho:** o OCR é assíncrono e depende do loop de eventos da thread. **Na thread principal, depois do pywebview, o `await` do OCR nunca volta** — a chamada travava para sempre (o `verificar.py` ficou preso nisso até o problema ser achado). A tela, que chama o Python em **thread separada**, funcionava; mas para não depender disso, o OCR agora roda em **thread própria**, com seu próprio loop e **limite de 60 s** antes de desistir com aviso claro.
- **Verificação:** `verificar.py`: **166 verificações, 0 falhas, 0 avisos** — dois testes novos (OCR de 1 e 2 páginas, aviso do limite de 20 páginas, e o aviso antigo quando as bibliotecas faltam), além das duas checagens de biblioteca que passaram a disparar. Conferido na tela com dados isolados em `_tmp`: o PDF digitalizado foi "soltado" na conversa e o texto apareceu na caixa ("Conteúdo do arquivo digitalizado.pdf: ..."). O `.exe` foi **recompilado** (64,5 MB) e conferido por dentro: `pypdfium2` (49 entradas, com a DLL do PDFium) e `winsdk` (196 módulos) estão no pacote; aberto com dados isolados, abriu sem `erro.log`.

## 2026-10-17 — Contraste dos temas corrigido: nada mais abaixo do mínimo de leitura (Prioridade 3.6)

- **O que o usuário ganha:** o **texto do botão** (Enviar e os botões de destaque, como Feito e Salvar) era branco sobre um acento claro em **9 dos 10 temas** — no Grafite Dourado ficava **1,53:1**, quase invisível; no Ocean, 2,69:1. Agora o **pior caso é 4,63:1** em todos os temas. O **texto apagado** (`--texto-3`: horário da conversa, notas, de 11,5 a 13 px) fica em **4,60:1 ou mais** (antes chegava a 3,28:1 em 7 temas). O `--azul` como borda de foco/borda de cartão saiu de 2,83:1 (Thundera) e 2,91:1 (Forest) para 3,06:1 e 3,07:1.
- **Nenhuma cor escolhida foi trocada de verdade:** os fundos, painéis e acentos continuam os mesmos (as diferenças são imperceptíveis: `--azul` clareou em Forest `#6d9e4f` → `#73a256` e em Thundera `#c0392b` → `#c34336`, e escureceu 3% no Clássico Dark `#3d6bff` → `#3b68f9`). A mudança visual maior é o **texto do botão ficar escuro nos 8 temas de acento claro**.
- **Duas chaves novas por tema:** `--btn-texto` (a cor do texto do botão — branco no Clássico Dark e no Thundera, escuro nos outros 8, onde o acento é claro) e `--btn-hover` (o fundo do botão no hover; nos 8 temas claros continua sendo o `--azul-2` de antes, e nos 2 escuros virou um tom um pouco mais fundo, porque clarear o fundo apagaria o texto branco). As paletas passaram de 10 para **12 chaves** e o `verificar.py` confere as duas.
- **Medido, não chutado:** um script novo (`_tmp/planejar_cores.py`) leu as dez paletas do `web/app.js`, calculou luminância relativa e contraste (WCAG) e buscou, **tema por tema, o menor ajuste** que resolve cada par: `--texto-3` clareado em 9 dos 10 temas (o Thundera já passava), de 1% a 20% na mistura com o branco; `--azul` ajustado apenas onde a borda ou o texto branco pediam; e a escolha entre texto claro/escuro pelo lado que dá mais folga.
- **Achado do teste novo — o interruptor:** a bolinha do interruptor era **branca fixa** (`#fff`) e o trilho desligado um cinza fixo (`#2c2c3a`). Sobre o acento claro dos 8 temas a bolinha caía para 2,2 a 3,0:1; e trocar a bolinha para escura a faria sumir no trilho escuro. Agora a bolinha usa `--btn-texto` e o trilho desligado usa `--texto-3`: a bolinha fica **visível nos dois estados e nos dez temas** (pior caso 3,21:1). É o tipo de defeito que só aparece quando se mede a combinação certa.
- **O aviso virou falha:** o teste de contraste deixou de acumular avisos e agora **falha** listando cada par abaixo do mínimo com o valor medido. O `verificar.py` foi de **161 verificações, 0 falhas, 1 aviso** para **162 verificações, 0 falhas, 0 avisos**.
- **Conferido na tela (dados isolados em `_tmp`):** capturas nos três casos extremos — Grafite Dourado (acento claro, texto escuro no botão), Thundera (acento escuro, texto branco) e Clássico Dark — mostram o botão **Enviar** ligado e desligado, o botão **Feito** do cartão de lembrete, o **Salvar** das Configurações e os **interruptores** ligado/desligado. O `.exe` distribuível foi **recompilado** e aberto com o tema Grafite Dourado: o botão Enviar saiu dourado com a seta escura **dentro do pacote**, sem `erro.log`. Nesta rodada as duas janelas do teste do `.exe` ficaram órfãs (o roteiro encerrava o bootloader *antes* de matar a árvore de processos) e foram fechadas; o roteiro foi corrigido para matar a árvore primeiro.

## 2026-10-17 — Lembretes ligados no programa ("me lembra amanhã às 9h de ...")

- **O que o usuário ganha:** escrevendo na conversa, em português normal, "me lembra amanhã às 9h de pagar a conta", o programa guarda o lembrete. Na hora marcada (com o programa aberto) aparece um cartão no canto superior direito com **Feito** e **Adiar 10 min**. Se o programa estava fechado, o cartão aparece assim que abrir. Também entende "daqui a 30 minutos", "segunda às 14h30", "dia 25", "20/10 às 7h", "hoje às 18h" e "depois de amanhã às 10 da noite"; lista com "meus lembretes" e cancela com "cancelar lembrete 2". **Nada sai para a internet, a IA não é chamada e funciona sem chave** (nenhum token gasto).
- **O que faltava:** o módulo `lembretes.py` já existia, com plano em `PLANO-LEMBRETES.md`, guardando os lembretes em `%LOCALAPPDATA%/Eye of Thundera/lembretes.json`. Mas **nenhum arquivo o chamava** — era código órfão: para o usuário, o recurso não existia.
- **Ligação no Python (`app_web.py`):** em `Ponte.enviar`, logo depois do bloco do modo exemplo e **antes** da checagem de chave, a frase passa por `lembretes.responder()`. Se ela for sobre lembrete, a resposta sai como mensagem normal da conversa (numa thread, como as outras respostas) e o caminho da IA nem é tocado; se não for, `responder()` devolve `None` e tudo segue como antes. Três métodos novos na ponte: `lembretes_vencidos` (devolve o que já venceu, com o horário em português), `lembrete_concluir` e `lembrete_adiar`. No modo exemplo nada é lido nem gravado.
- **Ligação na tela (`web/`):** contêiner `#lembretes` novo no `index.html`; em `app.js`, a tela pergunta `lembretes_vencidos` ao abrir e **de 30 em 30 segundos**, e desenha um cartão com `role="alert"` para cada lembrete vencido (cada um aparece **uma vez por sessão**, até ser marcado como Feito ou adiado). O visual usa as cores do tema.
- **Defeito achado e corrigido antes do commit:** a primeira versão punha os cartões no **canto inferior direito** — e as capturas mostraram que eles cobriam os botões de **microfone e enviar**, que ficam na direita do compositor. Os cartões passaram para o canto **superior direito**, logo abaixo da barra de título (32 px). Também foi ajustado o fundo do cartão (`--superficie`, em vez de `--superficie-2`) porque o botão "Adiar 10 min" ficava da mesma cor do cartão e não aparecia.
- **Pacote:** `lembretes` entrou nos dois `.spec` do PyInstaller (junto de `pdf_leitor`) e o **`.exe` distribuível foi recompilado** (`dist/Eye of Thundera.exe`). O pacote foi aberto com dados isolados em `_tmp` e um lembrete já vencido: a janela abriu, o **cartão apareceu dentro do `.exe`** e nenhum `erro.log` foi criado. (O `.exe` é *onefile*: quem abre a janela é um processo **filho** do bootloader — ao automatizar, fechar a árvore com `taskkill /T`, senão a janela fica aberta.)
- **Verificação:** `verificar.py`: **161 verificações, 0 falhas, 1 aviso** (o aviso é a pendência de contraste, Prioridade 3.6 — não é defeito desta rodada). Cinco testes novos: o interpretador com datas fixas (4 frases + 3 filtros que devem ir para a IA), o armazenamento (criar, vencer, adiar, concluir, listar, cancelar e sobreviver a arquivo estragado), a ponte (existe, fica quieta no modo exemplo e devolve só o vencido), o **caminho de verdade** do `enviar` (a frase responde **sem chave** e grava o lembrete; uma pergunta normal continua indo à IA) e a ligação na tela/pacote. Tudo com arquivos sintéticos em `_tmp` — nenhum dado real é lido ou alterado.
- **Conferido na tela:** o app foi aberto com uma pasta de dados isolada (em `_tmp`) e dois lembretes já vencidos; as capturas mostram os dois cartões no canto superior direito e confirmam que os botões de enviar e microfone ficaram livres.

## 17/10/2026 - faixas de redimensionar na tela
O redimensionar pelas bordas nao funcionava (o WebView2 cobre a janela e engole o mouse). Agora 8 faixas em HTML chamam Ponte.janela_redimensionar (WM_NCLBUTTONDOWN com HT_*). Plano: PLANO-BORDAS-REDIMENSIONAR.md. Teste novo no verificar.py (156 verificacoes).

## 2026-10-17 — Janela redimensionável de novo e contraste medido nos 10 temas

- **Redimensionamento (patch recebido):** `_tirar_barra_nativa` tirava o `WS_CAPTION` **e o `WS_THICKFRAME`** (`& ~0x00C00000 & ~0x00040000`), então a janela perdia a borda que se arrasta para redimensionar — e também o encaixe com Win+setas. Vale notar: o comentário de topo do bloco já dizia que era para *manter* o `WS_THICKFRAME`; o código não fazia o que o comentário dizia. A lógica saiu para uma função própria, `_estilo_sem_barra(estilo)`, que remove só o `WS_CAPTION`. Correção proposta em `PATCH_redimensionamento.md` e `_tirar_barra_nativa_CORRIGIDA.py`.
- **Teste da janela:** `verificar.py` ganhou um teste comportamental (não de texto): estilo sintético com CAPTION + THICKFRAME + SYSMENU + minimizar/maximizar passa pela função e o teste confirma que o CAPTION sai e **todo o resto permanece**; ainda confirma que nenhum outro ponto do arquivo volta a tirar o `WS_THICKFRAME`. O teste foi validado rodando contra a expressão antiga, que ele acusa.
- **Contraste dos temas (Prioridade 3 do documento de sugestões):** o teste passou a varrer **os 10 temas e os 4 fundos de cada um** (`--bg`, `--painel`, `--superficie`, `--superficie-2`) — antes comparava só `--texto` e `--texto-2` contra `--bg`. Texto principal, secundário e link passam em todos os temas, sobre todos os fundos.
- **Achado do contraste:** os pares que o teste antigo não cobria estão abaixo da norma em **32 casos**. O mais grave é visível: o **texto branco do botão** (Enviar e botão primário, que no hover vira `--azul-2`) **falha em 9 dos 10 temas** — pior caso Grafite Dourado, 1,53:1. O texto apagado (`--texto-3`, de 11,5 a 13 px) fica entre 3,28 e 4,49:1 em 7 temas, e o `--azul` como borda de foco fica abaixo de 3,0 em Thundera e Forest. A viabilidade foi medida antes de decidir: **8 dos 10 temas resolvem só trocando a cor do texto do botão**, sem alterar nenhuma cor escolhida; Clássico Dark e Thundera precisariam escurecer o acento ~15%, e 7 temas precisariam clarear o `--texto-3` de 2% a 14%.
- **Pendência:** como corrigir muda a aparência escolhida, ficou registrado em `PROXIMOS-PASSOS.md` (Prioridade 3.6) aguardando decisão. O `verificar.py` passou a emitir um aviso a cada execução com a contagem, para isso não ser esquecido.
- **Verificação:** `verificar.py`: **155 verificações, 0 falhas, 1 aviso** (o contraste pendente). Nenhum dado real é lido ou alterado.

## 2026-10-17 — Teclado nas conversas, menus acessíveis e textos padronizados

- **Teclado na lista de conversas:** a área do título de cada conversa virou um controle de verdade — abre a conversa com Enter ou Espaço. Antes, quem não usava o mouse não conseguia abrir uma conversa; a área clicável não recebia foco e não respondia ao teclado. O menu “…“ fica fora desse controle, para não aninhar dois botões dentro de um só.
- **Menu “...“ da conversa:** agora tem papel de menu, os itens recebem o foco ao abrir, as setas (e Home/End) andam entre eles, Tab fecha o menu e Esc fecha **devolvendo o foco** ao botão que o abriu. A confirmação de exclusão põe o foco em “Cancelar” (a escolha segura: apertar Enter por engano não apaga nada).
- **Menu “Mais”:** Esc agora fecha o menu de `details/summary` (que não fecha sozinho no navegador) e devolve o foco ao resumo.
- **Rótulos acessíveis:** o botão “…“ ganhou nome acessível com o título da conversa; o campo de busca e a lista de conversas ganharam `aria-label`.
- **Visibilidade por teclado:** o botão “…“ só aparecia ao passar o mouse; agora aparece também quando recebe o foco pelo teclado (senão quem usa teclado nem enxergava o botão).
- **Textos padronizados:** a frase de “ocupado” ficou uma só (“Aguarde a resposta terminar.” — antes misturava “Espere” e “Aguarde”), e a frase de “sem chave” também (“Cole a sua chave do Google em Configurações > Chaves para começar.”). Corrigidos acentos que faltavam em mensagens que aparecem na tela: sugestões de perguntas, leitura de PDF, área de transferência, modo exemplo e transcrição de voz.
- **Verificação:** `verificar.py`: 153 verificações, 0 falhas e 0 avisos. Dois testes novos: navegação por teclado (conversas e menus) e padrão de texto/acentuação. Nenhum documento pessoal é lido e nenhum dado real é alterado.

## 2026-10-17 — Leitura de PDF, foco no diálogo e avisos de erro

- **PDF arrastado:** agora dá para arrastar um `.pdf` para a conversa. O texto é extraído **no computador** (biblioteca `pypdf`, no módulo novo `pdf_leitor.py`) e entra na caixa de digitar para o usuário conferir antes de enviar — nada sai para a internet antes do Enter. O arquivo vai da tela para o Python em pedaços base64 (512 KB) para não travar a ponte. PDF com senha, arquivo corrompido, grande demais (limite de 25 MB) e PDF digitalizado (sem texto) recebem mensagem clara, sem travar a janela. `pypdf==6.1.1` entrou no `requirements.txt`, nos dois `.spec` do PyInstaller e no `verificar.py`.
- **Ajuda:** nova seção “Arquivos e PDF” explica os formatos aceitos e o aviso de PDF digitalizado.
- **Foco no diálogo:** com as Configurações abertas, o Tab fica preso dentro da janela; ao abrir, o foco entra no diálogo; ao fechar (ou apertar Esc), o foco volta ao botão que abriu.
- **Recuperação de falhas:** regressão nova confirma que a resposta da IA, a galeria de imagens e a transcrição de voz liberam `ocupado` no `finally` (nenhum controle fica preso).
- **Avisos de erro:** erros ficam 8 s na tela (avisos normais, 4,2 s) e podem ser fechados com um clique.
- **Acessibilidade:** botões e links de “sites consultados” e o campo de pergunta ganharam rótulos acessíveis e navegação por teclado.
- **Verificação:** `verificar.py`: 151 verificações, 0 falhas e 0 avisos. Os testes de PDF usam arquivos sintéticos em `_tmp`; nenhum documento pessoal é lido e nenhum dado real é alterado.

## 2026-10-17 — Acrescenta paletas e melhora a seleção de texto

- **Plano:** criado `PLANO-RODADA-2026-10-17.md` antes das alterações, conforme pedido do usuário.
- **Temas:** adicionados Aurora, Pôr do Sol, Rosa Chá e Grafite Dourado. `app_web.py` agora valida a lista `TEMAS_VALIDOS` sem limites numéricos duplicados; a suíte compara a lista com `TEMAS_UI`, valida contraste e testa persistência isolada dos nove temas, inclusive rejeição de índices inválidos.
- **Seleção e menu:** corrigido Recortar para só remover texto após confirmar a cópia. Copiar e recortar agora compartilham fallback para WebView; mensagens indicam sucesso/falha. O menu exibe Ctrl+X/C/V/A, permite navegação com setas, Home/End e Escape e restaura o foco. O clique direito posiciona o cursor medindo o texto em vez de usar pixels como índice. A cópia da seleção nas respostas também informa o resultado.
- **Verificação:** a captura em modo demonstração mostrou as quatro novas paletas, o menu e os nove cartões em 900 px. Simulação sintética confirmou que falha de cópia mantém o texto e que o fallback de sucesso é aceito, sem tocar na área de transferência real.
- **Resultado:** `verificar.py`: 143 verificações, 0 falhas e 0 avisos. Ainda falta conferir a persistência escolhendo tema pelo atalho real e a escala do Windows acima de 100%; nenhum dado pessoal foi alterado.
- **Capturas:** `_troca/prints/rodada-2026-10-17-cores-selecao-v3/` (pasta de demonstração; o roteiro agora gera uma pasta exclusiva por execução).

## 2026-10-17 — Cartões de temas com amostras de cores

- **Personalização:** a lista de temas virou uma grade de cinco cartões. Cada um mostra uma miniatura da interface pintada com sua paleta, cinco bolinhas de cor, o nome e uma marca no tema selecionado. As cores vêm de `TEMAS_UI`, sem duplicar a fonte das paletas.
- **Acessibilidade:** os cartões formam um grupo de opções de rádio; somente o tema ativo recebe Tab, as setas navegam e selecionam, e Enter/Espaço ativam o cartão focado. O salvamento continua imediato e isolado das demais opções; se falhar, a interface restaura o tema anterior.
- **Verificação visual:** roteiro de capturas em modo de demonstração executado e a aba conferida em 1180 px e 900 px. Os cartões quebram em nova linha sem rolagem horizontal; a imagem de Ocean também marca Ocean como selecionado. Nenhuma configuração real foi alterada.
- **Regressão:** `verificar.py` atualiza a checagem visual da aba e confirma grupo acessível, grade e fluxo de gravação existente; CSS antigo do seletor foi removido.
- **Verificação:** `verificar.py` passou com 137 verificações, 0 falhas e 0 avisos. Ainda falta testar a troca persistida pelo atalho real e a apresentação em escala do Windows acima de 100%.

## 2026-10-16 — Melhora a hierarquia visual das configurações no app desktop

- **Cartões:** aumentamos levemente o espaçamento e melhoramos a leitura das descrições, usando as cores do tema ativo em vez de tons fixos.
- **Prioridade:** o cartão do Gemini principal agora tem um destaque discreto na borda, sem alterar sua função nem o estado da chave.
- **Personalização:** o seletor de tema passou para um cartão próprio, com explicação clara de que a mudança é imediata e não altera conversas nem outras configurações.
- **Controles:** as linhas de opções têm mais área de respiro e realce suave ao passar o mouse. O tema Ocean foi preservado; os destaques usam as variáveis de cor do tema escolhido.
- **Regressão:** verificar.py confere o cartão destacado, o cartão de tema, o rótulo acessível e as regras visuais.
- **Verificação:** verificar.py: 136 verificações, 0 falhas e 0 avisos; node --check web/app.js, compilação Python e git diff --check aprovados. A validação visual final precisa ser conferida com a janela reaberta.

---

## 2026-10-16 — Evita perder rascunhos nas configurações e limpa a barra de escrita

- **Chaves:** o que for digitado em um campo de chave fica no rascunho enquanto o usuário troca de aba; ao salvar com sucesso, o rascunho temporário é limpo. Chaves já salvas continuam protegidas: campo vazio não as apaga.
- **Tema:** trocar a paleta agora envia apenas `temaIdx` ao backend, sem confirmar opções da conversa que ainda estejam em rascunho.
- **Barra de escrita:** o botão de envio com pesquisa profunda foi movido para “Mais”; o atalho `Ctrl+Shift+S` continua funcionando e foi listado na Ajuda. O envio normal e o alternador de modo profundo não mudaram.
- **Regressão:** `verificar.py` ganhou dois testes para rascunhos das chaves e salvamento isolado do tema; o teste da pesquisa profunda também garante que o botão aparece uma única vez dentro do menu.
- **Verificação:** 135 verificações, 0 falhas, 0 avisos; compilação Python, `node --check web/app.js`, `git diff --check` e IDs HTML únicos aprovados. Falta a confirmação visual desta nova disposição no aplicativo reaberto.

---

## 2026-10-16 — Redige credenciais antes de gravar erros no log

- **Risco encontrado:** `registrar_erro()` gravava mensagens de exceção diretamente em `erro.log`; algumas respostas HTTP podem incluir tokens ou campos de autenticação.
- **Correção:** antes de registrar a origem e a mensagem, `_sanitizar_erro_log()` mascara formatos conhecidos de chaves Google/Gemini, OpenRouter, Groq e OpenAI, tokens Bearer e valores em campos como `api_key`, `authorization`, `access_token` e `client_secret`.
- **Teste seguro:** `verificar.py` valida a sanitização com valores sintéticos; não usa credenciais reais, não chama APIs e não escreve no log real.
- **Limite conhecido:** a sanitização é baseada em padrões e não garante remover todo segredo ou dado pessoal de mensagens inesperadas. Evitar incluir credenciais em exceções continua sendo necessário.
- **Verificação:** `verificar.py`: 133 verificações, 0 falhas, 0 avisos; `py_compile`, `node --check web/app.js` e `git diff --check` aprovados.

---

## 2026-10-16 — Reforça o salvamento e a validação das configurações

- **Salvamento:** o botão indica “Salvando...” e fica desativado durante a gravação para impedir cliques duplicados. Os controles da aba também ficam temporariamente desativados, evitando que mudanças feitas durante a espera sejam perdidas quando a aba é redesenhada.
- **Recuperação:** um `finally` restaura os controles mesmo se a gravação ou a atualização da tela falhar; erros inesperados deixam uma mensagem no rodapé e são registrados no console sem incluir dados secretos.
- **Arquivo protegido:** `eye_of_thundera.salvar_config()` grava primeiro em um temporário no mesmo diretório e só então substitui `config.json` com `os.replace`. Se a escrita ou a troca falhar, o arquivo anterior é preservado e o temporário é limpo. Teste isolado simula a falha e confirma isso sem tocar na configuração real.
- **Regressão:** teste estático verifica o bloqueio e a recuperação dos controles. O teste isolado de persistência confirma preservação da chave principal quando o campo fica vazio, atualização da chave reserva, manutenção de campos existentes e rejeição de campos não permitidos; usa diretório temporário, sem tocar nas chaves reais.
- **Verificação final:** `verificar.py`: 132 verificações, 0 falhas, 0 avisos; `node --check web/app.js`, compilação Python e `git diff --check` aprovados.

---

## 2026-10-16 — Organiza os modos secundários e as configurações do Gemini

- **Interface:** Pesquisa séria, Privada e Resumo do dia agora ficam sob “Mais”, reduzindo a quantidade de botões sempre visíveis na barra de escrita.
- **Estados:** o menu mostra quantos modos estão ativos e fica destacado quando Pesquisa séria ou Privada está ligada; a gaveta abre para cima e preserva os IDs e os atalhos já existentes.
- **Configurações:** o controle “Usar o Gemini (principal)” foi agrupado no cartão da própria chave.
- **Verificação:** adicionados testes estáticos para o menu, os estados ativos e o cartão do Gemini. A conferência visual dessas mudanças ainda está pendente.

---

## 2026-10-16 — Corrige o estilo das sugestões da página inicial

- **Defeito:** a regra visual `.sugestoes` para perguntas sugeridas depois de uma resposta também atingia o bloco `#sugestoes` da página inicial, substituindo os cartões em duas colunas por chips compactos.
- **Correção:** os estilos de chips agora se aplicam apenas às sugestões dinâmicas; a página inicial mantém os cartões em grade e usa uma coluna em janelas estreitas.
- **Verificação:** `git diff --check`, `node --check web/app.js`, compilação Python e `verificar.py`: 127 verificações, 0 falhas e 0 avisos. A correção de CSS não altera a lógica dos botões.

---

## 2026-10-16 — Corrige o envio pela Pesquisa séria

- **Defeito:** o botão dedicado “Pesquisa séria” e Ctrl+Shift+S chamavam `enviar(undefined, true)`, mas `enviar` aceitava só um argumento e ignorava o `true`. O pedido só entrava em pesquisa profunda quando o alternador separado já estava ligado.
- **Correção:** `enviar(texto, profundo = estado.profundo)` agora passa a escolha efetiva à ponte Python; os envios normais continuam respeitando o alternador, enquanto o botão e o atalho forçam pesquisa profunda.
- **Prevenção:** adicionado teste de regressão para assinatura, encaminhamento do argumento, botão e atalho.
- **Verificação:** `node --check web/app.js`, compilação Python, `git diff --check` e `verificar.py`: 127 verificações, 0 falhas, 0 avisos.

---

## 2026-10-16 — Corrige tema que voltava ao padrão ao reabrir

- **Causa:** `Ponte.iniciar()` devolvia apenas `modo_pesquisa` e `corretor` em `cfg`. Como `web/app.js` aplica o tema usando `estado.cfg.temaIdx`, a ausência do campo fazia a interface cair no índice 0 (Clássico Dark), apesar de o tema escolhido estar salvo corretamente.
- **Correção:** `iniciar()` agora usa `self._cfg_curta()`, que devolve também `tema` e `temaIdx` validados, mantendo uma única fonte para a configuração inicial e para as atualizações.
- **Prevenção:** o teste de personalização agora valida os cinco temas em três etapas: arquivo gravado, leitura das configurações e payload real retornado por `iniciar()` — sempre com `config.json` temporário.
- **Verificação:** `node --check web/app.js`, compilação Python e `verificar.py`: 126 verificações, 0 falhas, 0 avisos.

---

## 2026-10-16 — Correção do diálogo Salvar resposta

- **Defeito:** `Salvar resposta` criava uma nova raiz Tkinter dentro da thread da ponte pywebview, podendo deixar a interface esperando enquanto a janela do sistema não aparecia.
- **Correção:** a função agora usa `self._janela.create_file_dialog(webview.FileDialog.SAVE, ...)`, o diálogo da própria janela principal; cancelamento continua sendo uma operação normal, e a extensão `.txt` é garantida.
- **Prevenção:** adicionado teste isolado com uma janela falsa e arquivo temporário para verificar o tipo de diálogo, o filtro `.txt` e o conteúdo gravado, sem abrir uma janela real nem tocar nos dados pessoais.
- **Verificação:** compilação Python e `verificar.py` passaram com 126 verificações, 0 falhas e 0 avisos; ainda falta confirmar manualmente o diálogo nativo na aplicação real.

---

## 2026-10-16 — Revisão da Personalização e persistência dos temas

- **Defeitos encontrados:** a aba Personalização estava implementada em web/app.js, mas não existia como botão em web/index.html; o backend ignorava tema/temaIdx; as paletas alteravam --accent, que não é consumida pelo CSS, e não atualizavam todas as variáveis usadas pela interface; o tema escolhido não era aplicado ao iniciar.
- **Correção:** adicionada a aba no HTML; centralizadas as cinco paletas com as variáveis CSS reais; seleção aplicada imediatamente e no início da aplicação; backend valida e salva o índice/nome do tema; botão Salvar oculto nessa aba porque a escolha é automática.
- **Prevenção:** verificar.py agora verifica a existência da aba e aplica uma rodada isolada por cada um dos cinco temas, usando um diretório temporário dentro de _tmp e restaurando os caminhos originais.
- **Documentação:** atualizados README.md, ONDE-PARAMOS.md e PROXIMOS-PASSOS.md.
- **Verificação:** `node --check web/app.js`, compilação Python e `verificar.py`: 128 verificações, 0 falhas e 0 avisos. Ainda falta conferir visualmente a aba e a persistência no aplicativo real.

---

## 2026-10-16 — Correção: janela abria, mas nenhum botão respondia

- **Causa:** um commit adicionou uma chave `}` extra em `web/app.js`, logo após `abaChaves`. O navegador apontava `SyntaxError: Unexpected token '}'` na linha 1278 e não executava nenhum JavaScript do arquivo; por isso os eventos dos botões nunca eram registrados.
- **Correção:** removida a chave extra. Corrigidos também um texto quebrado na descrição do Gemini e uma linha duplicada na atualização das datas da memória.
- **Prevenção:** `verificar.py` agora roda `node --check web/app.js` quando Node.js está disponível. O teste falha se houver erro de sintaxe no JavaScript.
- **Relatório:** corrigido o contador final que mostrava `TESTES: 0` apesar das verificações executadas; agora conta as verificações reportadas por `ok`, `falha` e `aviso`.
- **Documentação:** criado `README.md` como entrada principal e alinhados `ONDE-PARAMOS.md`, `PROXIMOS-PASSOS.md`, `ROADMAP.md`, `AGENTS.md`, `INSTRUCOES-PARA-IA.md`, `PASSO-A-PASSO.md`, `GUIA-DO-OPENCODE.md`, `LEIA-ME.txt` e `web/LEIA-ME.md` ao atalho real, que executa `app_web.py` pelo ambiente `.venv`. Os comentários e mensagens de `Gerar o EXE.bat` agora distinguem o pacote distribuível do atalho de desenvolvimento; removida também uma função `foo()` sem uso no atualizador do atalho.
- **Verificação:** `verificar.py` passou com 126 verificações reportadas, 0 falhas e 0 avisos. O comando do atalho foi iniciado de novo, a janela `Eye of Thundera` apareceu no Windows e não surgiu `erro.log`; ainda falta confirmar manualmente os cliques.

---

## 2026-10-16 — A janela lembra onde foi fechada (e dois defeitos)

Tres coisas que o Wolf pediu ou viu com o programa na mao.

### 1. A janela lembra onde foi fechada

Ele pediu para acabar com a regra de abrir sempre no segundo monitor.
Agora o programa:

- **guarda a posicao ao fechar** (no evento `closing`, que dispara ANTES
  da janela sumir — depois seria tarde demais);
- **abre no mesmo monitor** onde foi fechado;
- se esse monitor **nao existir mais hoje** (levou o notebook para outro
  lugar), cai no **meio da tela principal**;
- se o Windows nao souber dizer quantas telas tem, cai no padrao.

A posicao vai para `janela.json` — **separado do `config.json`**, que e'
onde fica a chave da API. A janela de "Salvar" passou a usar a mesma
posicao (antes usava um ponto fixo, que com o programa no segundo
monitor punha a janelinha no primeiro — o mesmo defeito de 16/10).

### 2. "Abrindo a foto..." ficava escrito no meio da imagem

O aviso era escondido em `mostrar()`, mas **nao quando a foto chegava** —
e e' quando a foto chega que ele tem de sair. Corrigido com
`esconderAviso()`.

### 3. O .exe abria uma janela preta (CMD) atras do programa

O spec tinha `console=True` "porque a tela nova ainda era um teste". Agora
e' a tela de verdade: `console=False`. Sem a janela preta, os erros vao
para o `erro.log` (que a tela ja grava sozinha).

### O detalque que quase passou batido

`ctypes.wintypes` **NAO vem junto com `import ctypes`**. Sem o
`from ctypes import wintypes`, a funcao de contar telas levantava
`AttributeError` — que o `except` engolia e devolvia "nao tem monitor"
para **qualquer** posicao. O programa nunca mais abriria no monitor
certo, e o sintoma seria "volta a abrir sempre no mesmo lugar".

O `except` agora grava no `erro.log` e devolve `True` (na duvida, abre
onde estava).

### Os testes

Secao 4c11 (11 verificacoes de posicao: 2 monitores, 1 so, notebook,
ordem invertida, monitor que sumiu, arquivo estragado) e 4c10 (o aviso
some + o .exe sem console). O teste 4b foi reescrito: ele copiava um
trecho do codigo e rodava com `exec`, e esse trecho cresceu ate usar
`ctypes` — passou a verificar o compromisso no codigo.

Verificacao: `TUDO CERTO`, **376 testes, 0 falhas, 0 avisos** (49 s).

## 2026-10-16 — O programa antigo foi aposentado (o Wolf mandou)

O Wolf perguntou se ainda era preciso fazer os testes no programa antigo.
**Não era** — e era uma pergunta que eu devia ter feito a ele antes, em
vez de continuar gerando os dois `.exe` por hábito. Custava **uns 90
segundos por build** para uma coisa que ele não usava mais.

**O que foi feito:** o `Pesquisa IA.exe` saiu da Área de Trabalho e foi
para `_arquivo_morto` (com "ANTIGO (tkinter)" no nome). **Não foi
apagado** — se algum dia der vontade de voltar, é só copiar de lá.

### O que NÃO mudou: os testes continuam todos

Aqui é preciso ser claro, porque é tentador "limpar" os testes do
antigo e isso seria um erro.

O `eye_of_thundera.py` é o **motor dos dois programas**. Se eu parasse de
testar o motor junto com a tela antiga, estaria **desligando o alarme do
programa novo também** — a memória, o corretor, a busca na web e a
conversa que ele usa TODO dia são exatamente as mesmas funções.

O que muda é só isto:

| O que os testes cobrem | Para quem serve |
|---|---|
| Memória, corretor, busca, conversa, factual | **Os dois** — é o motor |
| Desenho da tela, cantos da caixa, posição da janela | **Só o antigo** |

Então os testes ficam (são a rede de segurança do novo). O que parou foi
**gerar e testar o `.exe` do antigo** — ~90 segundos por build.

**A lição:** "aposentar uma parte" não significa "jogar fora o que ela
construiu". A tela velha foi embora; o motor que ela ajudou a fazer, não.

Verificacao: `TUDO CERTO`, **355 testes, 0 falhas, 0 avisos** (61 s).

## 2026-10-16 — Ver as fotos uma a uma, e português de verdade

Duas coisas que o Wolf pediu depois de testar a galeria.

### 1. Passar para a foto seguinte sem diminuir

O pedido foi: *"quando a foto estiver grande, passar para o lado, sem
precisar diminuir e clicar na próxima"*. A tela de foto grande deixou de
ser uma foto so e virou um **visor**: ela não fecha a cada troca, só
troca o que está aparecendo.

- **Setas do teclado** (← → e também ↑ ↓), que o Wolf já usa para tudo.
- **Botão ‹ › embaixo**, com **"3 de 9"** para saber onde se está.
- **Arrastar a foto com o mouse** — o gesto mais natural de todos.

**O detalhe do arrastar:** tentei fazer arrastar rápido (várias fotos
passando de uma vez) e os problemas aparecem rápido — o rato solta a
imagem do servidor e ela pisca, ou passa duas de uma vez. Por isso o
arrasto foi implementado "de próprio": com três fotos (mais que o
celular mostra), dois programinhas de posição resolvem em milissegundos.
Com muita foto, simular o arrasto no mouse arrancaria e soltaria a
imagem do servidor. Então **acima de 12 fotos o arrastar some** e ficam
as setas e o botão, que nunca dão problema — e a dica embaixo muda
sozinha para "use as setas do teclado".

As setas das pontas desligam (‹ na primeira, › na última): o Wolf vê
que acabou, sem precisar contar.

**Testado com a tela aberta**, nos três jeitos: seta → 2, seta ← 1,
botão → 2, botão ← 1, arrastar → 2, arrastar ← 1, e indo até a 6 de 6
a seta › desligou. **Esc** fecha, como sempre.

### 2. A IA respondia com sotaque de Portugal

O Wolf leu as respostas e riu: *"está falando com um tom de português de
Portugal, nós somos Brasileiros"*.

**A causa era uma frase que faltava.** O prompt de **pesquisa** dizia
"português do Brasil" duas vezes; o de **conversa** (quando não tem
pesquisa na web) **não dizia nada**. E sem dizer qual, o modelo escolhe
a variante que acha mais neutra — que é a de Portugal.

Corrigido com uma regra só (`IDIOMA_BR`), usada pelos três prompts:
diz que é do Brasil **e lista as palavras** que ele usa quando
escorrega ('de certeza', 'a nível de', 'equipa', 'ecrã', 'rato',
'ficheiro', 'a seguir está'), mais o erro mais comum de todos: **em
Portugal se gerundiza** ("estou a fazer"), aqui se diz "estou fazendo".

A lista não é enfeite: sem ela o modelo volta para essas palavras na
resposta seguinte.

**Uma confissão:** isso só apareceu porque o Wolf leu as respostas. Nos
meus testes a IA é falsa — e **ninguém testou o tom da voz**. É a mesma
coisa que o "Imortal" do Grêmio: eu achei que sabia, e quem lê é quem
percebe.

Verificacao: `TUDO CERTO`, **355 testes, 0 falhas, 0 avisos** (61 s).

## 2026-10-16 — Galeria de imagens na tela nova (falta o último)

O Wolf perguntou se dava para resumir tudo no programa novo e aposentar o
antigo. Faz o levantamento: o **motor** (`eye_of_thundera.py`) e' dos dois, e
so a **interface** tkinter e' do antigo. A unica coisa que o antigo tinha
e a tela nova nao era a **galeria de imagens** — perguntar "imagens de
God of War" e' a forma como o Wolf sempre procurou as coisas.

Esta e' a ultima peca. Feita ela, o novo fica igual ou melhor.

### Como funciona

- **"imagens de lobos" nao vai para a IA.** O `enviar` reconhece a
  pergunta (`p._quer_imagens`, a mesma funcao do programa antigo) e
  desvia para a busca de imagens, que e' de graca. **Nao gasta chave de
  API** — e nem devia: quem procura foto nao e' o Gemini.
- **As miniaturas viajam dentro do evento, em base64.** Sao pequenas
  (6 KB cada) e nove cabem folgadas.
- **A foto grande NAO viaja junto.** Uma foto de 2 MB em base64 viraria
  uma string de 2,7 MB passando por `evaluate_js` — isso trava a janela.
  A grande fica guardada no Python e a tela pede **uma por vez**, so
  quando o Wolf clica. Como ja foi baixada em segundo plano enquanto ele
  lia a resposta, aparece quase na hora.
- **A grade entra dentro da bolha da resposta**, antes do "copiar /
  salvar / outras perguntas" — as fotos fazem parte da RESPOSTA.
- Clicar abre a foto por cima de tudo, com botao de fechar (Esc tambem
  fecha) e um link para a pagina original.

### Um detalhe do Pillow que custou uma rodada

`from PIL import ImageDraw` traz o **modulo**; a classe e'
`ImageDraw.Draw`. Escrever `ImageDraw(foto)` falha com
`"TypeError: 'module' object is not callable"` — que e' um erro de
pouca ajuda, e que só apareceu porque o teste roda de verdade em vez de
ficar no papel.

### Os testes

Secao 4c7, 14 verificacoes: a pergunta vai para a busca e nao gasta chave,
a tela destrava, o evento chega, as miniaturas vem prontas, a pergunta
fica na conversa, a grande vem no clique, indice inventado nao derruba
nada, e pergunta normal nao vira busca de imagens. A internet nao e'
chamada: o teste finge a busca com fotos geradas aqui.

Verificacao: `TUDO CERTO`, **331 testes, 0 falhas, 0 avisos** (48 s).

## 2026-10-16 — A pasta antiga ficou marcada, mas não pôde ser renomeada

O Wolf pediu para deixar a pasta `C:\Projetos\Eye of Thundera` guardada "com
outro nome". O Windows **recusou o renomeamento** ("acesso negado"),
mesmo por `.NET`, mesmo depois de matar todos os processos. A causa
quase certa e' o `.venv`: ele cria arquivos com permissao especial, e o
Windows nao deixa renomear uma pasta que contem esse tipo de arquivo.

Nao vale a pena insistir — nada ali e' necessario. A solucao que resolve
o problema de verdade (o Wolf saber qual e' a pasta certa) e' um arquivo
`LEIA-ISTO-PRIMEIRO-ESTA-E-A-COPIA-ANTIGA.txt` dentro da pasta velha,
que aponta para `D:\Projetos\Eye of Thundera` e diz o que pode ser apagado
com seguranca (`_arquivo_morto` = 1,3 GB de `.exe` velhos, `.venv` com o
caminho velho gravado dentro, `build`/`dist`).

**A licao:** quando o plano e' "mover", o plano B tem de existir desde o
comeco. "Deixar com outro nome" e' melhor que "deixar como esta", mas
so se o sistema deixar.

## 2026-10-16 — O projeto mudou de pasta: de C: para D:

O Wolf pediu para mudar a pasta do projeto para o `D:` (que tem 353 GB
livres, contra 76 GB no `C:`). Agora vive em:

    D:\Projetos\Eye of Thundera

### O que foi conferido ANTES de mexer

- **`D:` tem 353 GB livres.** O `C:` estava com 76 GB.
- **Nenhum caminho fixo em codigo.** O grep por `C:\Projetos` nao
  achou nada em `.py`, `.spec` ou `.bat` — so em 5 arquivos `.md`, que
  foram atualizados. Era o unico risco real da mudanca.
- **O git nao tinha nada sem salvar**, entao a pasta antiga e a nova
  ficam com exatamente o mesmo estado.

### O que foi feito

1. **Apagado o que da para refazer**: `build/` e `dist/` do PyInstaller
   (233 MB) e o `__pycache__`. Nenhuma perda: o build regenera em 3 min.
2. **Copiado** para o `D:` (1.359 MB em 11 s), conferindo arquivo por
   arquivo antes de seguir.
3. **Recriado o ambiente Python**. Este foi o detalhe que quase passou
   batido: o `.venv` do Windows tem o caminho do projeto **gravado
   dentro** (`pyvenv.cfg` diz `command = ... C:\Projetos\Eye of Thundera\.venv`,
   e o launcher `Scripts\python.exe` tambem). Mover a pasta sem refazer
   o `.venv` deixaria o projeto **sem nenhum Python funcionando** — e o
   primeiro sintoma seria um erro esquisito no meio do `verificar.py`.
4. **Instalado o `requirements.txt` E o `requirements-dev.txt`** no
   ambiente novo. Sem o segundo o `pyflakes` some — e ele e' o que pega
   erro de digitacao antes da verificacao rodar. (Foi exatamente o que
   aconteceu: o `verificar.py` avisou "No module named pyflakes" na
   primeira rodada no `D:`.)
5. **Atualizados os 5 documentos** que citavam o caminho velho.

### A regra que saiu daqui

**Mudar a pasta de um projeto com Python nao e' so copiar arquivo.**
Antes de mexer, conferir tres coisas: caminho fixo no codigo, estado do
git e o ambiente virtual. O terceiro e' o que quebra — e quebra
silencioso, do tipo "o programa funciona mas o `verificar.py` nao roda".

Verificacao no caminho novo: `TUDO CERTO`, **317 testes, 0 falhas,
0 avisos** (47 s).

## 2026-10-16 — Botão direito com correção de palavra (tela nova)

O Wolf perguntou por que clicar com o botão direito sobre uma palavra
errada não abria a caixa de correção. Motivo: **em produção o WebView2
desliga o menu de contexto de proposito** —
`settings.AreDefaultContextMenusEnabled = _state['debug']`. Não é defeito
do Windows nem esquecimento: é o pywebview fazendo o programa se parecer
com um aplicativo e não com uma página.

### O que foi feito

A tela agora monta o menu dela, com as correções da palavra sob o cursor
e os comandos de edição (recortar, copiar, colar, selecionar tudo).

- **A lógica da sugestão foi para o MOTOR**
  (`eye_of_thundera.sugerir_correcao`) e o programa antigo passou a usar a
  mesma função. Uma correção só, para as duas telas nunca discordarem do
  que é "palavra errada" — a mesma lição do `registrar_erro`.
- **O cursor vai para onde foi clicado.** O Chromium (e o WebView2) *não*
  movem o cursor no botão direito; sem `caretRangeFromPoint` o menu
  abriria sempre sobre a última letra digitada.
- **O menu nunca nasce cortado:** ele é medido e puxado para dentro se
  estiver perto da borda.
- **Se alguma chamada falhar, o menu não fica em "carregando" para
  sempre** — o titulo e o aviso saem juntos, no fim da espera.

### Detalhe honesto: a busca demora

`SpellChecker.candidates()` do pyspellchecker leva entre 0,3 s e 3 s,
conforme a palavra. Não há como acelerar sem piorar a qualidade:
limitar a distancia de edicao fica rapido mas **nao acha quase nada**
("represetndo" -> nada), e buscar so em ingles e rapido mas **da
respostas erradas** ("kibia" -> "libia"). Foi medido antes de decidir.

Por isso o dicionario e' aquecido em segundo plano ao abrir o programa
(`_obter_corretor`), e o menu abre na hora com os comandos de edicao: so
a lista de correcoes e' que pode demorar um instante.

### O teste

A secao 4c6 confere 7 casos (palavra errada, trocada, correta, numero,
lixo) mais a tela: evento, `preventDefault`, cursor, troca do texto e
`caretRangeFromPoint`. E confere tambem que o programa antigo usa a
funcao do motor, e nao uma copia.

Verificacao: `TUDO CERTO`, **317 testes, 0 falhas, 0 avisos** (48 s — mais
que os ~35 s de antes porque a verificacao agora mede a correcao de
palavras de verdade, que e' lenta por natureza).

## 2026-10-16 — O defeito que travou a tela: a ponte se perdia dentro da janela

O Wolf abriu a tela nova, perguntou "quem venceu o jogo ontem?" e levou
`TypeError: api[nome] is not a function`. Depois disso o "pensando" ficou
aceso para sempre e ele nao conseguiu mais perguntar NADA.

### A pista que enganava

Todas as 24 funcoes que a tela pede **existem** na ponte ( conferido de
tres maneiras diferentes: no fonte, dentro de uma janela de verdade, e no
que o proprio `.exe` descompacta). O erro dizia "funcao inexistente", mas
a funcao estava la. A mensagem so estava certa sobre o **sintoma**.

### A causa de verdade

O pywebview monta a ponte andando por `dir(ponte)`. Quando acha um
atributo que nao e' funcao **mas tem `__module__`**, ele **entra dentro
dele** procurando mais funcoes. A janela do WebView2 tem:

    janela.native.AccessibilityObject.Bounds.Empty.Empty.Empty.Empty...

Cada coisa leva na mesma coisa, sem fim. O pywebviestoura `maximum
recursion depth exceeded` e fica segundos dentro disso. **Enquanto isso a
ponte fica VAZIA** — e a tela, que ja estava pronta, perguntou nesse
intervalo.

### Os dois consertos

1. **`self.janela` virou `self._janela`.** Tudo que comeca com underscore
   o pywebview pula, entao ele nunca mais entra na janela. Confirmado que
   e' o **unico** atributo com esse problema: `dict`, `list`, `str`, `bool`
   e `None` nao tem `__module__`, entao nao Sao visitados.
2. **A tela passou a esperar a ponte encher** (`esperarPonte()` no
   `app.js`), em vez de confiar na ordem de chegada. E, se alguma chamada
   falhar, ela **destrava** o "pensando" — antes um erro so deixava a tela
   travada.

### A licao

Duas, e as duas vem do mesmo jeito:

- **"Funcao inexistente" nem sempre significa funcao inexistente.**
  `api[nome] is not a function` aparece tanto quando a funcao nao existe
  quanto quando ela existe **mas ainda nao chegou**. Um `TypeError` tao
  generico devia ter levado direto a "e so timing?".
- **Confundir "o programa respondeu" com "o programa respondeu bem".**
  A tela mostrava a lista de conversas normalmente — porque `iniciar()`
  tinha rodado. O defeito so aparecia na **primeira pergunta depois**,
  quando a janela ja estava exposta. A tela "funcionando" enganou.

### O teste que protege

A secao 4c5 do `verificar.py` tem um **controle**: uma ponte com a janela
exposta DEVE entrar em loop, e se nao entrar o teste reprova ("o controle
nao entrou em loop — o teste nao serve para provar nada"). Teste que so
passa quando o defeito existe **nao serve para nada**.

## 2026-10-16 — Tela nova: resumo do dia, backup no programa e memória com data

Mais tres ideias da `IDEIAS.md`, feitas enquanto o Wolf dormia.

### 1. "Resumo do dia"

Botao **"Resumo do dia"** na barra de escrever e atalho **Ctrl+D**. Um
clique e a tela pergunta as noticias de hoje. E' um botao (e nao uma
frase na tela inicial) porque e' o que se pergunta TODO dia: nao faz
sentido obrigar a digitar a mesma frase sempre.

### 2. Cópia de segurança DENTRO do programa

Cartao em Configuracoes > Conversa, com o botao **"Fazer cópia agora"**.
O detalhe: o botao e o `9 - Fazer backup dos meus dados.bat` passam a
usar a **mesma funcao** (`eye_of_thundera.fazer_backup_dados`). Dois jeitos
de fazer a mesma coisa e' a receita para um deles ficar velho — foi
exatamente o que aconteceu hoje com o `registrar_erro`, que existia
so dentro do tkinter e a tela nova nao achava.

### 3. Memória com data

Cada item da aba Memoria mostra **"aprendeu em dd/mm/aaaa"**.

- **As datas vão num arquivo AO LADO do `memoria.json`, nunca dentro
  dele.** O `memoria.json` e' lido pelos dois programas e tem regra de
  ouro (nunca perder uma palavra), entao mexer no formato seria pedir
  problema. Fato antigo, guardado antes das datas existirem, fica sem
  data — a tela mostra isso em vez de inventar um dia.
- **O caminho do arquivo de datas sai do proprio `ARQUIVO_MEMORIA`**, e
  nao de uma pasta solta: assim um teste (que aponta o arquivo da
  memoria para uma pasta temporaria) **nunca escreve na pasta de
  verdade do Wolf**. Ha teste que reprova se isso mudar.
- Toda mudanca na memoria (adicionar, apagar, editar, organizar) devolve
  os fatos **e** as datas juntas, senao a data ficaria velha na tela.

Verificacao: `TUDO CERTO`, **299 testes, 0 falhas, 0 avisos** (31 s).

## 2026-10-16 — Tela nova: "outras perguntas" para continuar

Ideia 4 da `IDEIAS.md`: depois de cada resposta, 3 perguntinhas para
continuar o assunto. Clicar em uma ja manda a pergunta.

- **E' UM BOTAO, e nao automatico — de proposito.** Cada sugestao gasta
  uma chamada de IA; fazer isso sozinho a cada resposta **dobraria o
  custo do programa** sem o Wolf pedir. Com o botao, ele so paga quando
  aperta.
- Usa o **modelo rapido** (o mesmo do roteador) e pede JSON: sao tres
  frases curtas, nao precisa pensar muito.
- O leitor de JSON e' **tolerante**: se a IA responder com
  `"Claro! {...} ate la"` em volta, ele le assim mesmo.
- Se vier besteira ou lista vazia, **avisa na tela** em vez de mostrar
  lista quebrada. No maximo 3. Sem chave, avisa sem chamar a IA. No modo
  exemplo, nao gasta cota nenhuma.
- **6 testes**, todos com IA de mentira (a cota do Wolf nao e' gasta).

### Um vazamento meu nos testes (que os proprios testes pegaram)

A linha que restaurava o `google.genai.Client` de verdade estava escrita
de um jeito que **nao restaurava**: a IA de mentira continuaria valendo
depois do teste, e qualquer teste seguinte passaria a mentir sem querer.
Corrigido (o `Client` original e' guardado antes de trocar).

Tambem: uma troca global de nomes tinha batido em outro bloco de testes
(o de voz). Arrumado por linha, com conferencia.

Verificacao: `TUDO CERTO`, **289 testes, 0 falhas, 0 avisos** (35 s).

## 2026-10-16 — Tela nova: "sites consultados" embaixo da resposta

Ideia **numero 1** da `IDEIAS.md` (a que o Wolf mais gostou): a resposta
nao mostrava de onde tinha vindo. Agora, quando a resposta veio da web,
aparece uma letrinha discreta embaixo dela:

    sites consultados: 3

Clicar abre a lista; clicar num site abre no navegador.

- **Chamei de "sites consultados", e nao "fontes", de proposito.** Sao
  os **resultados da busca**, e nao citacoes: o programa nao confere se
  o que o site diz e' verdadeiro. Dizer "fonte" seria mentir — o mesmo
  cuidado que a regra do apelido ("Imortal" e' apelido do Gremio, nao
  invencao)idou no mesmo dia. O link esta ali justamente para o Wolf
  conferir com os proprios olhos.
- **Nunca aceita link perigoso:** so entram `http` e `https`; um
  `javascript:` e' descartado (e' assim que um site tentaria rodar codigo
  na tela). Link repetido e link vazio tambem saem fora. No maximo 6.
- **O `pesquisar` do programa antigo passou a devolver a lista** (antes
  devolvia vazia de proposito). O programa de sempre ignora esse valor,
  entao **nao mudou nada** para ele.
- As fontes vao **guardadas junto da mensagem**: fechar e reabrir a
  conversa nao faz a lista sumir.
- **4 testes**: tira repetido e o que nao e' link, nunca aceita
  `javascript:`, todo site tem titulo, e sem resultados a lista fica
  vazia (nada e' inventado).

Verificacao: `TUDO CERTO`, **283 testes, 0 falhas** (34 s).

## 2026-10-16 — Tela nova: conversa privada

Ideia 3 da `IDEIAS.md`: um botão para o que o Wolf fala **não ficar
guardado**. Botao "Privada" (cadeado) na barra de escrever; ligado, o
titulo da conversa fica amarelo dizendo **"Conversa privada (não será
salva)"**, para nunca ficar na duvida.

- **A conversa não vai para o arquivo** e **a IA não aprende nada** do
  que for dito nela.
- **A ARMADILHA (que quase ficou):** se o Wolf fizesse uma pergunta
  privada, **desligasse** o modo e fizesse outra pergunta, o programa
  gravaria a conversa **inteira** — incluindo a parte privada. A
  conversa privada mentiria. Por isso **ligar OU desligar começa uma
  conversa nova**, sempre.
- **Um vazamento real encontrado no caminho:** o atalho "lembra que ..."
  grava na memoria **direto**, furando o `aprender` por dentro. Se so o
  `_aprender` fosse desligado, a conversa privada ainda vazaria memoria
  por esse caminho. Fechado e coberto por teste.
- **5 testes**, e o mais importante deles reproduz a armadilha: conversa
  privada, desligar o modo, mandar outra mensagem e conferir que **só a
  mensagem nova** foi salva — a privada **nao** aparece.

## 2026-10-16 — Tela nova: tamanho da letra e "fixar no topo"

Duas ideias da `IDEIAS.md` que nao existiam em NENHUM dos dois programas.

### 1. Tamanho da letra

Falar e' o programa inteiro, e letra pequena cansa a leitura.

- **Ctrl + e Ctrl -** aumentam e diminuem; **Ctrl 0** volta ao normal.
- **Botoes** em Configurações > Conversa (A-, A+, Normal) — ninguem
  precisa decorar atalho para aumentar a letra.
- Vai de **13 px a 26 px**.
- **Fica guardado** neste computador: a tela ja abre do jeito que o Wolf
  deixou (vive no `localStorage` do navegador).
- A letra vem de **uma variavel de CSS** (`--tamanho`), e nao de mexer em
  cada tamanho da tela: assim **um** lugar muda e a tela inteira
  acompanha.
- **Nao chama o Python.** E' so aparencia e nao arrisca as conversas. Ha
  teste que REPROVA se um dia isso mudar.

### 2. Fixar conversa no topo

No menu dos tres pontinhos de cada conversa: **Fixar no topo** /
**Soltar do topo**.

- Grava um campo a mais na conversa (`"fixada": true`). O programa
  antigo **ignora** o campo, entao a conversa continua aparecendo la
  como sempre — so que sem a fixacao.
- A ordem da lista nao vira bagunca: as fixadas sobem, mas entre elas e
  entre as soltas continua valendo "mais nova primeiro", senao a lista
  inteira mudaria de lugar a cada conversa nova.
- Como fixar reescreve o arquivo inteiro, a tela nova **confere depois**
  que a conversa continua la **com o mesmo numero de mensagens**; se
  algo estiver errado, avisa em vez de deixar a conversa quebrada.
- **8 testes**: topo da lista, marca gravada, mensagens intactas, soltar
  volta ao normal, o que nao existe avisa, nao apaga nem cria conversa,
  e o campo novo nao atrapalha a leitura do outro programa.

### Um teste meu quebrou e pulou 110 testes (de novo)

Um dos testes novos da letra falhou na primeira vez (escrevi a condicao
olhando o arquivo errado: `var(--tamanho)` esta no CSS, e
`setProperty("--tamanho")` esta no JS). Como a verificacao **pula as
secoes seguintes quando ha FALHA**, a rodada seguinte rodou **em 2
segundos** e com 78 testes em vez de 274.

Foi percebido pelo **tempo**, nao pelo resultado: 2 segundos é rápido
demais para uma verificacao que costuma levar 35. A regra ja existia nas
instrucoes (confira sempre o total E o tempo, nao so o "TUDO CERTO") e
foi ela que salvou.

Verificacao: `TUDO CERTO`, **274 testes, 0 falhas** (34 s).

## 2026-10-16 — Apelido nao e invencao, e o log de erro agora e' real

Duas correcoes vindas do feedback do Wolf.

### 1. "Imortal" e' o apelido do Grêmio — eu tinha errado

A resposta sobre o proximo jogo do Gremio falou em "Imortal" e eu achei
que era invencao (o nome perguntado era Gremio). **Errado: "Imortal" e'
apelido do mesmo time.** A regra que escrevi ("use ESSE nome, nao troque
por outro parecido") estava partindo de um diagnostico errado e ainda
podia atrapalhar. Reescrita:

> "- Responda exatamente sobre o que foi perguntado. Se a pergunta citar
> um time, uma pessoa ou um produto pelo nome, fale DELE, nao de outro
> parecido. Pode usar o apelido se for o mesmo (Grêmio, por exemplo, também
> é chamado de Imortal e Tricolor)."

As outras duas regras (nao inventar palavras de outros idiomas e nao
terminar perguntando de volta) continuam: elas continuam corretas.

**Licao:** antes de "consertar" uma resposta, confirmar se ela estava
errada mesmo. Aqui a IA estava certa e a regra nova seria o defeito.

### 2. `registrar_erro` nao existia — o conserto nao consertava nada

Para a tela nova deixar rastro de erro (o crash ao arrastar), foi
chamado `eye_of_thundera.registrar_erro(...)`. **A funcao nao existia nesse
escopo**: ela era uma funcao *dentro* do `main` do tkinter. O `pyflakes`
nao acusou nada, e o `try/except` em volta teria engolido o erro em
silencio — o log nunca apareceria.

So apareceu porque o registro foi **testado de verdade**: gravar um erro
de mentira num arquivo de teste e conferir que o arquivo foi criado. E
foi assim que o defeito apareceu.

- **`eye_of_thundera.registrar_erro(onde, erro)` subiu para o nivel do
  modulo**, agora compartilhada: o `main` do tkinter e a tela nova usam
  a mesma. Testado: grava mesmo, e nunca levanta erro.

### 3. O crash ao arrastar e' do WebView2 (nao nosso)

Confirmado na documentacao do proprio WebView2: existem varios relatos
de **"WebView2 crash OnWindowPositionChanged"** e **"Access violation
after rapid resize"**. O que o Wolf viu bate: **as vezes**, **so
arrastando** (maximizar nao cai) e **so no modo real**. E' o navegador
dentro da janela, nao o nosso codigo.

**Nada se perde quando acontece:** cada resposta e' gravada assim que
chega, antes de aparecer na tela. Se a janela cair, so se perde o que
estava sendo escrito no exato instante.

Verificação: `TUDO CERTO`, **262 testes, 0 falhas** (36 s).

## 2026-10-16 — A IA respondia com invenção depois de pesquisar

Com o defeito do prazo corrigido, a pesquisa passou a funcionar de
verdade: a pergunta do proximo jogo do Wolf voltou com data, horario e
local. **Mas a resposta trouxe coisa inventada:** falou do "Imortal" em
vez do Gremio, inventou a palavra "szól", disse que ela significa "falar"
em hungaro e ainda pediu confirmacao.

O programa ja mandava "nunca invente numeros, datas ou fatos", mas
faltavam tres regras. Acrescentadas em `INSTRUCOES` (vale para os DOIS
programas), sem mexer no resto:

- **Responda exatamente sobre o que foi perguntado** — se a pergunta
  citar um time, pessoa ou produto pelo nome, use ESSE nome, nao troque
  por outro parecido.
- **Nunca invente palavras de outros idiomas** e nao pergunte ao usuario
  se elas significam algo.
- **Nao termine fazendo perguntas de volta** para quem perguntou:
  responda e pare.

## 2026-10-16 — A tela nova nao guardava rastro de erro (crash ao arrastar)

O Wolf viu a tela nova **fechar ao arrastar a janela para o monitor
principal**. Nao foi possivel confirmar a causa: a hipotese mais obvio
(diferenca de escala entre os monitores) foi **medida e descartada** — os
dois monitores estao em 96 DPI (100%).

- **A tela nova nao escrevia NADA em log.** O programa de sempre grava
  tudo no `erro.log`; a tela nova engolia qualquer erro em silencio, e um
  crash do Windows nao deixa nem rastro. Agora ela chama
  `eye_of_thundera.registrar_erro(...)`, como o programa antigo.
- **Falta o Wolf confirmar** se acontece sempre ou as vezes, e se
  acontece tambem no modo exemplo (`5 - Ver a tela nova.bat`), que nao
  toca em dado nenhum. Sem isso nao da para reproduzir.

Verificação: `TUDO CERTO`, **262 testes, 0 falhas** (42 s).

## 2026-10-16 — Defeito antigo e silencioso: o programa nunca pesquisava

O Wolf perguntou no programa novo "Quanto será o próximo jogo do Grêmio?"
e a IA respondeu que **não tinha acesso à internet**. Não era erro: a
resposta chegou. Mas era uma resposta ruim, e a causa era grave.

- **A causa:** o programa dá um **prazo** para a IA decidir "isso é papo
  ou é pesquisa?". O prazo estava em **8 segundos**, e o Google exige
  **no mínimo 10**. O Google respondia:
  `400 INVALID_ARGUMENT. Manually set deadline 8s is too short. Minimum
  allowed deadline is 10s.`
- **O efeito:** essa decisão **NUNCA funcionou**, em nenhum momento, em
  nenhum dos dois programas. O `except` que pega o erro é silencioso, e
  o roteador caía na **reserva por palavras** ("hoje", "agora", "notícia",
  "placar", "preço"...). "Próximo jogo" não está na lista, então ia para
  papo — e a IA, sem material de web, respondia que não tinha internet.
- **A correção:** prazo de 8 s → **20 s**. Testado com a chave de
  verdade:

  | pergunta | antes | depois |
  |---|---|---|
  | "Quanto será o próximo jogo do Grêmio?" | papo | **pesquisa** |
  | "Me conta uma curiosidade sobre história" | papo | papo |

  O ponto de interrogação não muda nada: o Google recusava a chamada
  **antes de a IA ler a frase**.
- **Teste novo que impede a volta:** o `verificar.py` lê o prazo no
  código e **reprova** se for menor que 10 s. Conferido que o teste
  reprova com 8 s e aprova com 20 s.
- **Este defeito era do PROGRAMA DE SEMPRE (tkinter), não da tela nova.**
  O `.exe` antigo da Area de Trabalho tinha o defeito; por isso os dois
  `.exe` foram refeitos.

## 2026-10-16 — Rede de seguranca dos dados do Wolf

O backup que existia (`4 - Fazer backup.bat`) protege o **codigo**, nao
as **conversas, a memoria e as chaves** — que sao as coisas que nao da
para refazer.

- **`fazer_backup_dados.py` + `9 - Fazer backup dos meus dados.bat`:**
  copiam `%LOCALAPPDATA%\Eye of Thundera` para um `.zip` em
  `OneDrive\Backup Pesquisa IA\dados`. **So le e copia** — nao muda
  nada. Copias com mais de 15 dias sao apagadas sozinhas.
- **Rodado:** 5 arquivos (config, historico, memoria e duas copias
  antigas da memoria) em `dados_2026-10-16_013640.zip`.

## 2026-10-16 — Defeito corrigido: "Salvar" abria na tela errada

O Wolf avisou que o `7 - Usar a tela nova de verdade.bat` estava
"crashando". **Não era crash.**

- **O programa não caía.** Testado: a tela nova aberta no modo normal
  fica de pé (14 s rodando, sem erro nenhum, e sem `erro.log`).
- **A janela de "Salvar resposta como..." abria no MONITOR ERRADO.**
  Medido com o programa de verdade, procurando a janela do Windows pelo
  nome:

  | | antes | depois |
  |---|---|---|
  | onde a tela nova estava | x=2000 (2º monitor) | x=2000 (2º monitor) |
  | onde a janelinha abria | **x=138, y=0 (1º monitor, canto)** | **x=2068 (2º monitor)** |

  O Wolf estava olhando o segundo monitor; a janelinha abria no
  primeiro. O programa ficava **esperando** ela (e é isso que parece
  "travou"), sem nenhuma pista na tela. Por isso parecia crash.
- **A correção:** `Ponte._onde_esta_a_janela()` devolve o canto da tela
  onde a janela foi aberta, e a janela de Salvar é posicionada ali
  (`geometry("1x1+...")`) **antes** de abrir. A janela de arquivos do
  Tk nasce em cima da janela "pai", então ela passa a nascer junto do
  programa.
- **Um detalhe que custou tempo:** usar `janela.x` do pywebview para
  perguntar onde a janela está **trava até 15 segundos** (a propriedade
  espera a janela ficar "pronta"), e a janelinha demorava tanto que
  parecia que nem abria. Por isso a ancora é a posição **que nós mesmos
  usamos ao abrir**, que é instantânea. Se o Wolf arrastar a janela
  depois, a janelinha pode não sair bem em cima dela — mas continua
  **na tela certa**, que é o que importa.
- **Como a posição foi medida (e não achada):** um programa de teste
  abriu a tela de verdade, chamou o mesmo caminho que o botão, e leu a
  posição da janela do Windows por `EnumWindows` — 4 maneiras de
  ancorar foram comparadas. A que funciona é `geometry("1x1+X+Y")`
  antes de abrir (x=2068). As outras três deixavam a janela no canto
  do primeiro monitor ou fora da tela.
- **Erro meu no meio do caminho:** na primeira versão eu passei um
  argumento a mais para `_onde_esta_a_janela`, e isso **quebrou o Salvar
  inteiro** ("takes 1 positional argument but 2 were given"). Só
  apareceu porque a medição mostra o que a ponte devolveu — um conserto
  feito "no olho" teria passado batido.
- **2 testes novos** (não abrem janela nenhuma): um confere que a
  ancora fica no 2º monitor (o mesmo onde o programa abre), e outro que
  a janela é posicionada antes de abrir.

Verificação: `TUDO CERTO`, **261 testes, 0 falhas** (35 s).

### O que ainda NÃO foi feito: barra de título embutida

O Wolf perguntou se os botões de fechar/minimizar/maximizar e o
arrasto da janela poderiam ficar **dentro** do programa, em vez da
barra do Windows. **Dá**, e foi conferido no pywebview: a opção
`frameless` existe e funciona com o motor `edgechromium` que o programa
usa (o formulário que apaga a borda é criado pelo mesmo caminho do
`winforms`). Nada foi feito ainda — é o trabalho de maior risco que
sobra (mexe na janela do Windows por baixo dos panos), e ele só começa
depois que este conserto estiver commitado. Perde-se "colar" a janela
na borda arrastando e o Windows+setas; ganha-se a tela 100% escura.

## 2026-10-16 — Tela nova: PASSO 7 (a barra de título estava BRANCA)

Defeito de verdade encontrado aqui: **a tela nova abria com a barra de
título do Windows branca**, batendo com o resto da tela escura. O
programa de sempre já escurecia a barra desde 15/10, e o pedido do Wolf
é "nunca janela branca".

- **A causa:** a tela nova chamava `ativar_barra_escura(janela)`, que
  espera um **widget do tkinter** (`janela.update_idletasks()` e
  `janela.winfo_id()`). A janela do pywebview **não tem nenhum dos
  dois**. O erro era engolido pelo `except: pass` e a barra ficava
  branca, sem nenhum aviso.
- **A correção:**
  - `eye_of_thundera.escurecer_hwnd(hwnd)` — escurece a barra a partir do
    **número** da janela, e não de um widget. Assim serve para o tkinter
    e para o HTML. Nunca levanta erro: no pior dos casos a barra fica
    clara e o programa continua funcionando.
  - `eye_of_thundera.escurecer_janela_por_titulo(titulo)` — procura a janela
    entre todas as do Windows pelo título e escurece. A janela pode
    demorar um pouco para o Windows criar, por isso ela repete a
    tentativa por ~10 segundos.
  - `app_web.py` usa essa função nova, numa **tarefa de fundo**: se
    ficasse esperando na thread principal, a janela não apareceria.
  - `ativar_barra_escura` (a do tkinter) **não foi mexida** — ela
    continua funcionando como estava.
- **Atalhos novos:** `Ctrl+N` (conversa nova) e `Ctrl+F` (ir para a
  busca). Sem o `preventDefault`, o navegador abriria a barra de
  endereço e a busca do navegador, que nada têm a ver com o programa.
  O `Ctrl+F` mostra a barra da esquerda se ela estiver recolhida, senão
  não haveria campo nenhum para focar. A aba Ajuda ganhou as duas
  linhas novas.
- **O que já estava pronto e não precisou de nada:** os cantos
  arredondados da caixa (`border-radius: 20px`), a cor da barra de
  rolagem (`::-webkit-scrollbar`) e a cor de fundo da janela
  (`background_color`), que é a mesma do CSS.
- **2 testes novos**, que **não abrem janela nenhuma**: um confere que a
  tela nova usa o caminho certo (e não o do tkinter, que falha), e o
  outro que a função não quebra quando a janela não está aí (título
  inexistente, título vazio, janela 0).

Verificação: `TUDO CERTO`, **259 testes, 0 falhas** (38 s).

### Defeito ainda ABERTO: o "Salvar .txt" da tela nova

Medido em 16/10/2026: o caminho de salvar **não derruba o programa** —
ele **fica esperando** a janela de "Salvar como" (a do Windows) que ele
mesmo abriu, e o teste saiu de lá depois de 8 segundos sem morrer. Ou
sea, se a janela de Salvar não aparece (ou aparece escondida atrás da
tela nova), o Wolf vê o programa "travado" sem saber por quê.

Isso não está corrigido ainda: o caminho atual cria uma janela do
**tkinter** de dentro da thread da ponte, e essa thread não é a do
tkinter. O certo seria usar a janela de salvar **do próprio pywebview**
(`janela.create_file_dialog`), que é a ferramenta da casa. Fica como
próximo trabalho, junto do passo 8.

## 2026-10-16 — Tela nova: PASSO 6 (procurar nas conversas)

Uma caixinha "Procurar nas conversas..." em cima da lista, na barra da
esquerda. É um item que estava na `IDEIAS.md` há semanas.

- **`app_web.py` — `conversas_buscar(termo)`:** procura no **título e
  dentro das mensagens**, e devolve para cada conversa achada: o id, o
  título, um **trecho** com o texto em volta do achado e o **índice da
  mensagem**. Máximo de 30 resultados, para a barra não virar uma parede.
- **A comparação é sem acento e sem diferenciar maiúscula**, usando o
  mesmo `eye_of_thundera._sem_acento` que a Memória já usa. Assim digitar
  `japao` acha "Japão" e `CENOURA` acha "cenoura".
- **Uma letra sozinha não busca** (`vazio: true`): uma letra acha
  conversa demais e polui a tela. O mínimo são 2 letras.
- **`web/app.js`:** os resultados aparecem com o trecho e a palavra
  **destacada** (`<mark>`); clicar abre a conversa e limpa a busca. Se o
  Wolf digitar mais coisa enquanto a busca roda, a resposta velha é
  descartada (senão os resultados ficam trocados com o que ele pediu).
- **`web/estilo.css`:** o campo de busca, os resultados e o destaque.
- **9 testes novos.** As conversas de mentira da busca ficam no arquivo
  de **teste** e são limpas no fim, porque o check do fim da seção
  exige o arquivo de conversa vazio (se sobrasse, o teste seguinte
  acusaria "sobrou conversa no arquivo" sem dizer de onde veio).

Uma decisão que vale registrar: procurar **"Tokio" NÃO acha "Tóquio"**.
Para o computador, `c` e `ç` são letras diferentes. Preferi isso a
"achar qualquer coisa parecida", porque senão a busca mostraria o que o
Python adivinha, e o Wolf não saberia por que um resultado apareceu ali.
Está escrito num teste, para não virar "correção" sem querer.

Verificação: `TUDO CERTO`, **257 testes, 0 falhas** (36 s).

## 2026-10-16 — Tela nova: PASSO 5 (as Configurações de verdade)

As quatro abas já existiam e já gravavam; o que faltava da Tarefa D foi
acrescentado, mais o `Ctrl+S`.

- **Editar um item da Memória clicando no texto** (`memoria_editar`).
  Antes: só dava para apagar e adicionar. Agora o texto vira campo na
  hora; Enter salva, Esc cancela. A troca passa por
  `salvar_memoria` + `_mesclar_memoria`, que é o mesmo caminho do
  programa antigo.
- **Exportar a Memória em `.txt`** (`memoria_exportar`): botão novo,
  reusa a janela de "Salvar como" do Windows (que já sai escura) e o
  arquivo sai com data e "N item(ns):".
- **Aviso do limite de 200 letras.** O `memoria.py` corta o item em
  200 letras **em silêncio** (era assim no programa de hoje). A tela nova
  mostra "faltam N letras" enquanto se digita e **recusa** de salvar
  passando do limite, em vez de cortar a frase pela metade.
- **Aba Ajuda** ganhou a parte de **voz** (microfone e "enviar
  sozinho") e a **tabela de atalhos** (Enter, Shift+Enter, Ctrl+M,
  Ctrl+S, Esc).
- **`Ctrl+S`** salva a última resposta em `.txt`, como no programa
  antigo. Sem isso o navegador abriria a janelinha branca de "salvar
  página". O texto cru agora fica guardado em cada resposta
  (`data-bruto`), porque o que aparece na tela já vem formatado.
- **Novo `7 - Usar a tela nova de verdade.bat`**: abre a tela nova com
  as conversas do Wolf (sem `--demo`). Como é o mesmo arquivo de
  conversas, as barras laterais dos dois programas mostram a mesma
  coisa.

### Um teste que falhou sem explicação (e o que foi feito)

Um teste novo do `.txt` da memória falhou **uma vez** e passou em todas
as outras (11 execuções isoladas + 2 completas). O arquivo impresso no
log **continha** o item que o teste dizia estar faltando — a falha não
se explicava. A causa **não foi achada**.

O que não se fez: aceitar "passou, então tá bom". O teste foi
reescrito para ser mais forte e à prova de formatação: antes procurava
um texto solto dentro do `.txt`; agora compara **item por item** com a
memória de verdade, o que não deixa passar item trocado, item a menos
nem item a mais. Também se descartou a suspeita mais óbvia (a ordem
dos itens mudar entre execuções, por causa do embaralhamento de strings
do Python): testada com 4 sementes diferentes, a ordem é sempre a
mesma.

**A lição fica registrada:** teste que falha e o motivo não aparece
não é teste "instável", é teste que não explica a si mesmo. Reforçar
o teste vale mais que repetir a suíte até ela passar.

Verificação: `TUDO CERTO`, **248 testes, 0 falhas** (45 s).

## 2026-10-16 — Tela nova: o microfone pode ser testado falando

Duas correções e um atalho novo, para o Wolf poder testar o microfone
de verdade sem sujar o histórico.

- **A tela nova abria no MONITOR PRINCIPAL** quando rodava sem `--demo`
  (nascia em x=120, em cima da tela em que o Wolf está trabalhando).
  Agora ela nasce **sempre no segundo monitor** (x=2000), com qualquer
  combinação de flags. É a regra do Wolf: janela de teste nunca cobre a
  tela de trabalho. **Quando a tela nova virar O programa, esta posição
  vai embora**, como nas janelas do tkinter, que seguem o app.
- **Teste novo que trava essa regra:** o `verificar.py` roda as flags da
  tela nova e falha se alguma abrir em x < 1950. Conferido que o teste
  pega o problema se a posição voltar a depender de `--previa`.
- **Separadas duas coisas que estavam misturadas:** "não gravar nada"
  (`--demo`) e "microfone falso" (só para o botão poder ser testado
  sem microfone). Agora são independentes: `--voz` deixa o microfone ser
  o de verdade mesmo no modo exemplo.
- **Novo `6 - Falar com a tela nova.bat`:** a tela nova com microfone de
  verdade e IA de verdade, **sem salvar nenhuma conversa** e sem mexer
  na memória. É o jeito seguro de o Wolf falar e ver a resposta.
- **`5 - Ver a tela nova.bat` continua como era** (só olhar, microfone
  falso), para não puxar o microfone de surpresa.
- **`verificar.py`:** 3 testes novos (a tela nova no 2º monitor; no
  modo exemplo nenhum som de verdade é gravado; com `--voz` grava de
  verdade).

Verificação: `TUDO CERTO`, **238 testes, 0 falhas** (88 s).

## 2026-10-16 — Tela nova: PASSO 4 (o microfone)

O botão do microfone da tela nova deixou de estar apagado. Agora ele
grava, transcreve e joga o que foi falado na caixa de digitar.

- **pp_web.py — Ponte.mic_alternar():** um clique começa a gravar e
o clique seguinte para (é o botão **ou** Ctrl+M, como no programa
  antigo). Devolve na hora, sem travar a janela; o resto vem por evento.
- **Nada de áudio foi reescrito.** Usa o mesmo oz.Gravador, o mesmo
  wav_tem_som ("não ouvi nada"), o mesmo 	ranscrever com a mesma
  ordem de modelos (o bom primeiro, os de reserva depois) e o mesmo
  	entar_com_reserva do programa de hoje.
- **O texto falado NÃO é enviado sozinho**: ele entra na caixa de
  digitar para o Wolf conferir, igual ao programa antigo. Só sai sozinho
  se a opção "enviar" estiver ligada nas Configurações.
- **Três eventos novos para a tela:** "gravando" (ligou/desligou, com
o botão vermelho piscando e o relógio), "voz" (o texto transcrito) e
  "voz_erro" (falhou; com "chave": true a tela abre as Configurações).
- **Erros viram frase em português**, todos: programa montado sem a
biblioteca de som, nenhum microfone ligado, microfone ocupado por
  outro programa, silênçio, chave recusada.
- **--demo finge que ouviu**, para a tela de exemplo funcionar mesmo
sem microfone e sem chave.
- **web/index.html:** o botão do microfone saiu de disabled.
- **web/app.js:** a seção do microfone (relógio, botão vermelho,
Ctrl+M) e os três casos de evento novos.
- **web/estilo.css:** .icone.gravando — vermelho, com um brilho que
pulsa, igual ao do programa atual.
- **erificar.py:** 19 testes novos do microfone. O oz inteiro é
trocado por um de mentira, então o **microfone de verdade não abre** e
a **cota de IA não é gasta**. A falha que teve no caminho foi do
  *teste*, não do programa: ele esperava o modelo de IA repetido na
lista, e a lista certa (a mesma do programa antigo) não repete.

Verificação: TUDO CERTO, **235 testes, 0 falhas** (55 s).

## 2026-10-16 — Tela nova: PASSO 3 (a IA de verdade)

O `enviar()` deixou de responder "passo 3". Agora a pergunta chega na IA
e a resposta volta para a tela enquanto aparece. Commit `1075253`.

- **`app_web.py` — `Ponte.enviar(texto)`:** devolve **na hora** (para a
  janela não travar) e passa o trabalho para a thread `_responder`. A
  resposta volta por `window.PIA.evento(...)`: `"etapa"` enquanto a IA
  trabalha, `"resposta"` no fim, `"erro"` se deu ruim. Só dois erros
  saem de `enviar()` mesmo: pergunta em branco e `"sem_chave"` (o
  `app.js` reconhece esse e abre as Configurações sozinho).
- **Nada foi reescrito.** Reaproveita `eye_of_thundera.perguntar` (busca na
  web), `eye_of_thundera.conversar` (papo normal), o mesmo roteador
  (`_decidir_modo`), a mesma troca automática de chave reserva e o
  mesmo tradutor de erro do programa antigo. Pedido de notícia continua
  pesquisando a pergunta inteira, como antes.
- **`eye_of_thundera.py` — regras compartilhadas, sem mudança de
  comportamento:** `traduzir_erro`, `chave_reserva`, `chave_ativa` e
  `tentar_com_reserva` saíram de dentro da classe `Aplicativo` e viraram
  funções de módulo; os métodos dela passaram a chamar essas funções.
  É o mesmo código, só mudou de lugar. **A tela antiga não tem nada de
  novo — só pode ser usada por duas telas ao mesmo tempo.**
- **A memória continua sem repetir:** depois de responder, a IA é mandada
  aprender em segundo plano e calada (`_aprender`), igual ao
  `_guardar_e_aprender` do programa antigo, com o mesmo limite de
  chamadas. O "lembra que..." grava direto na memória, sem gastar IA.
- **`web/app.js` — ordem garantida (defeito real, achado no caminho):**
  o Python devolve a chamada de `enviar()` e manda os eventos logo
  depois, mas a `Promise` às vezes volta **depois** do primeiro evento.
  Se a IA falhava na hora (chave inválida, internet caiu), o evento
  `erro` chegava antes da pergunta: a resposta aparecia em cima dela e o
  "pensando" ficaria aceso para sempre. Agora os eventos são guardados
  até a pergunta entrar na tela.
- **Modo exemplo (`--demo`):** a IA de verdade responde, mas **nada é
  gravado** (nem conversa, nem memória). `Nova conversa` passou a
  funcionar no exemplo (ela não grava nada); `excluir_conversa` continua
  barrado lá — as conversas do exemplo são de mentira e o arquivo é do
  Wolf.
- **Testes: `testes_tela_nova_ia`, 31 verificações novas.** Nenhuma chama
  a IA de verdade: `conversar`/`perguntar`/`_decidir_modo` são trocados
  por uma resposta de mentira, a `threading` vira uma que roda na hora, e
  histórico/memória/chave ficam apontados para `_tmp`. Cobre: sem chave,
  pergunta em branco, envio duplo, etapa antes da resposta, acento e
  emoji chegando crus (sem `\u` escapado), gravação da conversa, a lista
  da esquerda sendo atualizada, histórico da segunda pergunta, erro de
  chave (português + abre Config.), erro de internet (não mexe nas
  Config.), modo pesquisa × pedido de notícia, aprender ligado e
  desligado, e o modo exemplo não gravando.
- **Teste antigo adaptado (não apagado):** o de "no modo DEMO nada é
  gravado" pedia que `nova_conversa` respondesse erro no exemplo. Como
  ela agora funciona por lá, o teste passou a conferir que ela limpa a
  tela e que nada vai para o disco.
- **Armadilha nova registrada no `INSTRUCOES-PARA-IA.md`:** a
  `carregar_memoria()` tem um cache (`_memoria_cache`) dentro do módulo.
  Um teste que aponta o arquivo para outra pasta **tem que zerar o
  cache**, senão a memória do teste anterior aparece como se fosse do
  Wolf.
- **`.exe` da Área de Trabalho: NÃO foi regenerado.** O programa antigo
  não teve mudança de comportamento (só mudou de lugar), então o `.exe`
  que o Wolf usa continua igual e continua certo.
- **`verificar.bat` = TUDO CERTO**, com **49 verificações da tela nova**
  (as 18 que já existiam — duas delas adaptadas — e mais **31 novas** do
  passo 3 e do modo exemplo).

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
- **Não mexi no `eye_of_thundera.py`** (o opencode estava trabalhando nele).

---

## 2026-10-15 — Tela nova: PASSO 3 (a IA de verdade) + o defeito do Alethe

### 1. A tela nova chama a IA de verdade

- **`enviar(pergunta)`** na ponte: devolve na hora (a janela não trava) e
  o trabalho acontece na thread `_responder`. Só a pergunta vazia, a
  sessão já ocupada e a falta de chave ("sem_chave", que o `app.js`
  reconhece e abre as Configurações) voltam na hora — o resto chega por
  evento.
- **A tela é avisada do que está acontecendo** por `_evento`, que fala
  `window.PIA.evento({...})` com `json.dumps(..., ensure_ascii=False)`
  (sem isso acento e emoji viram `\u00e7` na tela). Tipos: `etapa`
  (os três pontinhos), `resposta`, `erro` e `conversas`.
- **Nada foi reescrito:** reaproveita `eye_of_thundera.perguntar` (com busca
  na web), `eye_of_thundera.conversar` (papo), o mesmo `_decidir_modo` do
  roteador, a mesma chave reserva e o mesmo tradutor de erro.
- **Defeito corrigido no caminho:** a chave reserva estava sendo chamada
  com um dicionário descartável (`{}`), então o programa **esquecia que
  já tinha trocado** e voltava a insistir na chave morta a cada
  mensagem. Agora o dicionário vive na ponte (`self.chaves`), como no
  programa antigo.
- **Modo exemplo (`--demo`)** parou de gastar token: `enviar` simula
  etapas e resposta pelo mesmo caminho da tela, sem chamar o Google.

### 2. Regra compartilhada entre as duas telas (sem duas cópias)

- `traduzir_erro`, `chave_reserva`, `chave_ativa` e `tentar_com_reserva`
  viraram **funções de nível de módulo** no `eye_of_thundera.py`. Os métodos
  antigos do `Aplicativo` agora só chamam elas. Motivo: a tela nova usa
  **a mesma** regra; duas cópias divergiriam sem ninguém perceber.
  Os 9 testes de chave reserva do programa antigo continuam passando.

### 3. Testado

- **Com a IA de verdade:** uma pergunta curta, e a tela respondeu
  *"Um ano comum tem 365 dias, e o bissexto tem 366."* — incluindo
  etapas, gravação da conversa e atualização da lista.
- **Sem gastar token e sem internet:** o `verificar.py` troca só a
  chamada de rede por uma resposta de mentira e confere o caminho
  inteiro (ida, etapas, resposta, gravação, lista, erro em português,
  recusa de pergunta duplicada, pergunta vazia). **TUDO CERTO.**
- **Armadilha do pywebview descoberta nesta rodada:** o `evaluate_js`
  **trava para sempre** se a página não responder, e o pywebview imprime
  um barulho gigante de COM ("maximum recursion depth exceeded",
  "can only be accessed from the UI thread") ao tentar introspecionar a
  janela de outra thread. É ruído dele, não do nosso código. Por isso os
  testes do `verificar.py` **não abrem janela** para testar a IA: eles
  trocam a rede e conversam com a ponte direto, que é o que importa.

### 4. O defeito do plugin do Alethe (achado a pedido do Wolf)

O Alethe escrevia `alethe-bridge.js` num formato que o opencode 2.0.30
recusa (*"Plugin must export a default definition with an id and an
effect or setup function"*), e ele mostrava "1 plugin failed". Confirmei
no log do opencode. O Alethe **reinstala esse arquivo toda vez que
abre** (aparece `[opencode_bridge] plugin instalado em ...` no log), por
isso corrigir na mão não segurava. Criados, na Área de Trabalho:

- `Corrigir o Alethe.bat` + `corrigir-alethe.ps1` — conserta na mão;
- `abrir-alethe.bat` + `abrir-alethe.ps1` + atalho `Alethe.lnk` — abre o
  programa e já aplica a correção sozinho (espera o Alethe instalar o
  arquivo e conserta em seguida; como o opencode recarrega o plugin
  sozinho quando o arquivo muda, o aviso nem chega a aparecer).

Medido: **79 falhas de plugin antes da correção, 0 depois**; o plugin
passou a aparecer no log como `loading plugin`. O script é idempotente
(rodei duas vezes: a segunda diz "já estava corrigido", sem duplicar) e
tira correções antigas antes de reescrever — sem isso ele deixava dois
`export default` no arquivo, que é justamente o erro que ele conserta.

---

## 2026-10-15 — Tela nova: PASSO 2 (as conversas de verdade)

O Wolf aprovou a tela nova ("curti demais mesmo") e mandou seguir o
plano. Passo 2: a lista de conversas passa a funcionar de verdade.

- **`nova_conversa()`**: limpa a conversa aberta e devolve a lista nova.
  **Não grava nada** — conversa sem pergunta não tem o que salvar. É a
  mesma regra do programa antigo (`_nova_conversa` só limpa e zera o id).
- **`excluir_conversa(id)`**: apaga a conversa escolhida do arquivo e, se
  era a que estava aberta, volta para a tela inicial (para a conversa não
  "voltar sozinha" na lista). Faz o que o programa antigo faz, e o que a
  IA aprendeu continua guardado de propósito.
- **A conversa aberta passa a morar dentro da ponte**
  (`Ponte.mensagens` e `Ponte.id_atual`), igual ao programa antigo, que
  também guarda a conversa aberta em `self.mensagens` e só grava no
  arquivo quando há mensagem nova. O `_gravar_conversa()` faz essa
  gravação e já está pronto para o passo 3 usar.
- **A lista da tela agora vem na ordem certa.** A primeira versão ordenava
  pelo texto do horário, e o **teste pegou o defeito**: o horário só tem
  minuto de precisão, então duas conversas no mesmo minuto ficavam em
  ordem aleatória. Agora usa o mesmo critério do programa antigo — o
  arquivo guarda da mais antiga para a mais nova e a lista mostra ao
  contrário (`reversed`).
- **A confirmação de excluir ficou igual à do programa antigo:** o aviso
  agora diz também *"O que o assistente aprendeu sobre você continua
  guardado"*, para ninguém achar que apagar a conversa apaga o que ele
  ensinou.
- **`enviar` continua avisando** que a IA ainda não está ligada (passo 3).
  Nada de fingir que funciona.
- **18 testes novos** no `verificar.py` (seção 5d), todos com os arquivos
  de histórico e memória apontados para uma pasta de teste e restaurados
  no fim: começar vazio sem quebrar, conversa vazia não ser gravada,
  gravação com as 2 mensagens, título = primeira pergunta, ordem da
  lista, abrir conversa, conversa inexistente, nova conversa (limpa a
  tela e não apaga o arquivo), excluir (a certa, devolvendo a lista
  atualizada, limpando a tela se era a aberta, e avisando se não
  existe), aba Memória ler sem mudar nada, e o modo exemplo não tocar em
  nada. O teste confere no fim que **não sobrou conversa no disco**.
- **Conferido com prints:** as duas conversas aparecem na lista (mais nova
  primeiro), o menu "…" abre o Excluir, e o clique na conversa abre as
  duas bolhas com o título no topo e a conversa destacada.
- **`.exe` do programa de sempre:** não precisou ser regerado (o
  `eye_of_thundera.py` não foi tocado neste passo).

---

## 2026-10-15 — Tela nova: PASSO 1 pronto (dá para ver e tocar)

O Wolf pediu para ver a tela nova antes de decidir. Feito o passo 1.

- **Criado `app_web.py`**: a ponte entre o Python e a tela. Abre a janela
  nova (`web\index.html`) e responde o que o `web\app.js` pede.
- **Criado `5 - Ver a tela nova.bat`**: o Wolf dá dois cliques e a tela
  abre no segundo monitor.
- **Criado `Pesquisa IA Tela Nova.spec`**: `.exe` da tela nova em um
  arquivo SEPARADO, de propósito. O `Pesquisa IA.spec` (o programa que já
  funciona) não foi tocado — se a tela nova der problema, o programa de
  sempre não é afetado.
- **`pywebview` entrou no `requirements.txt`**: estava instalado na
  máquina, mas não registrado. Sem isso o `.exe` gerado não abriria.
- **Modo `--demo`**: mostra três conversas de exemplo (com emoji
  COLORIDO) para o Wolf ver a tela cheia. **Não lê nem grava nada dele.**
- **Passo 1 é SÓ LEITURA, de propósito.** As funções que só leem
  funcionam (conversas, memória, chaves — e salvar em .txt, que é
  independente). As que mudam algo devolvem um aviso honesto dizendo em
  qual passo serão feitas (`aviso_honesto`). Assim nenhum teste pode
  mexer nas conversas, na memória ou nas chaves do Wolf. Para quem ler
  o arquivo depois: "funciona" e "ainda não" são coisas diferentes no
  mesmo arquivo, e o motivo está escrito em cima de cada função.
- **Defeito achado e corrigido no CSS:** o aviso ("Cole a sua chave...")
  ficava a 96 px da borda de baixo — exatamente em cima da caixa de
  digitar. Como a caixa cresce quando se escreve muito, o aviso cobria o
  texto. Foi para o topo, abaixo do cabeçalho, onde não atrapalha.
- **Abridor para tirar print da tela nova** (`_tmp\print_web.py`): a
  janela do pywebview não devolve o handle do Windows (devolve o
  controlador do WebView2), então o `PrintWindow` precisou achar a
  janela pelo título com `EnumWindows`. É só conferência, fica em `_tmp`.
- **Ruído conhecido:** o pywebview imprime um erro de COM do WebView2
  ("CoreWebView2Controller members can only be accessed from the UI
  thread") ao tentar ler o zoom. **Não afeta a janela** — ela abre,
  carrega e funciona. Fica registrado para não assustar quem for rodar.
- **Teste:** `verificar.py` passou a checar o `pywebview` (o módulo se
  chama `webview`, não `pywebview` — o teste confundia e dava FALHA) e o
  pyflakes agora cobre `app_web.py`, `memoria.py`, `roteador.py` e
  `voz.py` também.
- **`.exe` do programa de sempre:** não precisou ser regerado (o da
  Área de Trabalho, de 19:23, já é mais novo que o `eye_of_thundera.py`).

### O que o Wolf viu (prints conferidos)
- Tela inicial com 3 conversas de exemplo, bolhas arredondadas,
  emojis **coloridos** de verdade (o foguete vermelho, o alien verde,
  a lua laranja) e caixa de digitar com cantos redondos.
- Aba **Chaves** em cartões, com "Mostrar"/"Testar" e o aviso "Chave
  salva neste computador" (mostrando só os 4 últimos caracteres, nunca a
  chave inteira).
- Aba **Memória** com os 12 fatos do Wolf, busca, "Organizar" e "Apagar
  tudo".

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
  commits, e `eye_of_thundera.py`, `voz.py`, `roteador.py`, `verificar.py` e
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
- **Modificado:** `eye_of_thundera.py`:
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
- **Modificado:** `eye_of_thundera.py`:
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
- **Modificado:** `eye_of_thundera.py`:
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
- **Modificado:** `eye_of_thundera.py` (`_criar_bolha`): duplo clique seleciona
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
  para `D:\Projetos\Eye of Thundera`.
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
- `eye_of_thundera.py`:
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
- `eye_of_thundera.backup-antes-da-selecao.py` (versão antes da correção de
  seleção), `erro-antigo-2026-10-14.log`, `Pesquisa IA.spec.antigo`,
  `Pesquisa IA.exe.antigo` e a cópia do .exe que estava na Área de Trabalho.

### Substituído fora do projeto
- `Pesquisa IA.exe` na Área de Trabalho (em
  `C:\Users\Igor\OneDrive\Área de Trabalho`) pelo novo, gerado em
  `D:\Projetos\Eye of Thundera\dist`.

### Não mexido
- `%LOCALAPPDATA%\Eye of Thundera\` (conversas, memória, chaves do Wolf).
- `IDEIAS.md`, `PLANO-B.txt`, `avatar_usuario.png`, `icone.ico`.

### Testado
- `verificar.py`: TUDO CERTO (3 rodadas seguidas, sem avisos).
- O .exe novo abriu e ficou aberto 9 s sem criar `erro.log`.
- NÃO testado: perguntas reais à IA (precisa de internet e da chave do
  Wolf) e o uso do .exe por um período mais longo.

## 16/10/2026 - Responsividade e acessibilidade das Configurações
- `web/estilo.css`: adicionados estilos de foco visível para navegação por teclado, layout compacto para janelas estreitas e baixas, rolagem horizontal das abas, rolagem segura do corpo e respeito à preferência de movimento reduzido do sistema.
- `web/index.html`: diálogo de Configurações agora declara `aria-modal="true"` e usa o título visível como nome acessível.
- `verificar.py`: teste estático cobre as regras responsivas, foco visível e atributos acessíveis.
- Verificação: `verificar.py` passou com 132 verificações, 0 falhas e 0 avisos; `node --check web/app.js`, `py_compile` e `git diff --check` também passaram. Ainda falta validação visual manual em escala alta do Windows e janela pequena.

## 15/10/2026 - Tela nova: passo 5 (Configuracoes e Memoria de verdade) - feito pelo Claude
- app_web.py: definir_modo, config_salvar, testar_chave, memoria_adicionar/apagar/apagar_tudo/organizar agora gravam de verdade (reaproveitam salvar_config, esquecer_memoria, _mesclar_memoria, organizar_memoria, testar_chave, testar_servico do eye_of_thundera.py).
- Chave vazia nao apaga a chave salva; campos desconhecidos sao ignorados; no modo exemplo nada e gravado.
- verificar.py: nova funcao testes_tela_nova_config (isolada em _tmp, nao toca nos arquivos do Wolf). Nenhum teste foi removido. Resultado: TUDO CERTO.
