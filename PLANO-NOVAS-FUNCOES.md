# Plano das novas funções do Pesquisa IA

Para a IA que programa. Escrito pelo Claude em 15/10/2026, depois de ler o
código e de ver a tela do programa. Salve este arquivo na pasta do projeto
(`C:\Projetos\PesquisaIA`) e siga na ordem. O Wolf não programa: explique tudo
em português simples.

## 0. Regras que valem para tudo
- Leia antes: INSTRUCOES-PARA-IA.md, PASSO-A-PASSO.md, HISTORICO-DE-MUDANCAS.md,
  PROXIMOS-PASSOS.md. Siga o método deles (causa primeiro, mudança pequena,
  teste novo no verificar.py, `verificar.bat` com TUDO CERTO, commit,
  histórico).
- Uma tarefa por vez (A, B, C, D), cada uma com seu commit.
- NUNCA leia, mostre ou grave nada de `%LOCALAPPDATA%\PesquisaIA\` (conversas,
  memória, chaves do Wolf). Em testes e prints use dados de exemplo
  (troque `carregar_memoria`/`carregar_conversas` por listas falsas).
- O Wolf pode estar com o programa aberto. Antes de copiar o .exe novo para a
  Área de Trabalho, confira se `Pesquisa IA.exe` está rodando; se estiver,
  peça para ele fechar.
- Para ver a tela: rode o app num script, ponha a janela `-topmost` e use
  `PIL.ImageGrab.grab(bbox=...)` com `SetProcessDpiAwareness(1)`. Sem
  `-topmost` o print pega outras janelas.
- **Janela de teste sempre no SEGUNDO monitor:** ele começa em X=1920 e vai
  até X=3840. Coloque a janela em `+2000+100` (ou maior) para não cobrir a
  tela que o Wolf está usando. No `verificar.py` isso já está resolvido:
  `POSICAO_TESTE = "+2000+100"`. Ao abrir o `.exe` para testar, lembre que
  o PyInstaller abre um processo filho: procure a janela pelo nome
  ("Pesquisa IA") em todos os processos, não pelo `MainWindowHandle` do
  processo que você iniciou.

## 1. O que existe hoje (e o que está ruim)
- `_quer_pesquisa(pergunta)` decide por palavras soltas: qualquer "como",
  "qual", "quem", "quando"... vira pesquisa, e frase com mais de 7 palavras
  também. Resultado: papo normal acaba virando pesquisa.
- A decisão é feita na thread da tela (`_enviar`), antes de tudo.
- `INSTRUCOES` é um prompt de "assistente de pesquisa" e é usado também no
  modo amigo (`conversar`), que tenta corrigir o tom por dentro do prompt do
  usuário. A memória entra duas vezes (em `instrucoes_da_ia()` e de novo em
  `conversar`).
- `_gerar_texto`, `_chamar_servico` e `_gerar_texto_rapido` chamam
  `instrucoes_da_ia()` sem saber o modo.
- `aprender_com_o_usuario` só roda se a resposta tiver 120+ caracteres, então
  conversa curta de amigo nunca é aprendida.
- Janela de Configurações: a aba "Chave" mistura chave, opções, plano B e
  ajuda numa rolagem só, sem margem à esquerda (o conteúdo encosta na borda,
  diferente da aba Memória, que tem 24 px). A aba Memória só lista e apaga.

## 2. TAREFA A: assistente amigo que só pesquisa quando precisa
### A1. Novo arquivo `roteador.py` (funções puras, sem importar pesquisa_ia)
- `regra_local(texto, modo)` devolve `"pesquisa"`, `"amigo"` ou `None`:
  - `modo == "sempre"` -> pesquisa; `modo == "nunca"` -> amigo.
  - Começa com `/web`, "pesquise", "pesquisa", "busque", "procure", "dá uma
    olhada na internet" -> pesquisa (e tira o prefixo da consulta).
  - Começa com `/papo`, "sem pesquisar", "não pesquise" -> amigo.
  - Cumprimento, agradecimento, risada, frase de até 3 palavras sem "?" ->
    amigo (evita gastar uma chamada).
- `decidir(texto, historico, chamar_modelo, modo)` devolve
  `{"modo": "pesquisa"|"amigo", "consulta": str, "origem": "regra"|"modelo"|"padrao"}`.
  Ordem: regra_local -> chamar_modelo(prompt) -> heurística de reserva.
  `chamar_modelo` é uma função recebida (assim dá para testar sem internet).
- Prompt do roteador (temperatura 0, resposta só em JSON):
  `{"pesquisar": true|false, "consulta": "...", "motivo": "..."}`.
  PESQUISAR quando: fato atual ou que muda (notícia, preço, cotação, clima,
  placar, lançamento, horário, regra/lei em vigor), coisa específica que o
  modelo pode não saber (produto, jogo, versão, pessoa, empresa), ou o
  usuário pede para pesquisar/conferir. NÃO pesquisar: papo, opinião,
  desabafo, cumprimento, perguntas sobre a IA ou sobre o próprio usuário,
  conhecimento estável (história, ciência, conceitos, matemática, tradução,
  escrever ou ajustar texto, código), recomendação baseada nos gostos dele,
  continuação do assunto anterior. A "consulta" deve ser completa e curta,
  sem depender do histórico ("e o euro?" vira "cotação do euro hoje").
  Mande só as 4 últimas falas, cortadas em 300 caracteres.
- Ler o JSON de forma tolerante (cerca ```json, texto antes/depois). Se não
  der para ler, usar `heuristica_pesquisa(texto)`, que pesquisa só com
  palavras de "agora" (hoje, atual, último, notícia, preço, cotação, clima,
  placar, lançamento, quanto custa, onde comprar, ano atual) e senão devolve
  amigo. Na dúvida: amigo (o prompt do amigo oferece pesquisar).
- `fato_pedido(texto)`: reconhece "lembra que...", "anota que...", "guarda
  que..." e devolve o fato; o app grava direto em `_mesclar_memoria`, sem
  gastar chamada de IA.

### A2. Mudanças em `pesquisa_ia.py`
1. Chamada do roteador com o modelo rápido (`MODELO_MEMORIA`), cliente com
   timeout de ~8 s e `response_mime_type="application/json"`. Se falhar,
   segue com a heurística (nunca trava a conversa).
2. `_enviar`: tirar `_quer_pesquisa` da thread da tela. Dentro de `tarefa()`
   (thread de fundo): decidir -> se amigo chama `conversar`, senão
   `perguntar(..., consulta=decisao["consulta"])`. Status inicial "Pensando...",
   depois "Pesquisando na web..." ou "Conversando...". Imagens e notícias
   explícitas continuam como hoje (`_quer_imagens`, `_quer_noticias`).
3. `perguntar(..., consulta=None)`: usar `consulta or pergunta` na busca; o
   prompt final continua com a pergunta original do usuário.
4. Novo `cfg["modo_pesquisa"]` (`auto` | `sempre` | `nunca`, padrão `auto`) e
   `cfg["aprender"]` (padrão True). Um botão pequeno ("Web: automática",
   clique alterna) sob a caixa de digitar, e os mesmos controles na aba
   Conversa das Configurações.
5. Prompts separados: manter `INSTRUCOES` (pesquisa) e criar
   `INSTRUCOES_AMIGO`; `instrucoes_da_ia(modo="pesquisa")`. Passar `modo` por
   `_gerar_texto`, `_chamar_servico` e `_gerar_texto_rapido` (padrão
   "pesquisa", para não quebrar nada). No modo amigo: temperatura 0.7 e
   histórico das últimas 12 falas (pesquisa continua 0.3 e 6).
6. `conversar`: prompt curto (data + mensagem + `contexto_das_conversas`).
   Tirar o bloco de memória duplicado.
7. Aprendizado: rodar quando a fala do usuário tiver 12+ caracteres OU a
   resposta 120+, e só se `cfg["aprender"]` estiver ligado.
8. Texto sugerido para `INSTRUCOES_AMIGO` (português do Brasil, texto
   simples, sem asteriscos nem emojis, lista com "•"):
   - Você conversa como um amigo de confiança: natural, caloroso, direto,
     com humor quando combinar. Sem formalidade.
   - Curto quando o papo é leve; mais fundo quando a pessoa pedir.
   - Aqui você NÃO tem resultados da web. Se a resposta depender de algo
     atual e você não tiver certeza, diga isso em uma frase e ofereça
     pesquisar. Nunca invente número, data ou fato.
   - Use o que sabe da pessoa só quando ajudar, de forma natural; nunca diga
     que "lembrou" ou "guardou", nem liste o que sabe dela. Exceção: se ela
     pedir para lembrar de algo, confirme curto ("Anotado!").
   - Dê opinião quando pedirem e discorde com jeito quando precisar.
   - Nada de frases de robô ("Como posso ajudar?" em toda resposta) nem
     repetir a pergunta.
   No `INSTRUCOES` (modo pesquisa), só trocar o tom da primeira frase para
   "amigo bem informado"; o resto das regras fica igual.

### A3. Testes (no verificar.py, sem internet)
- `regra_local`: "oi" -> amigo; "valeu!" -> amigo; "/web preço do dólar" ->
  pesquisa com consulta "preço do dólar"; "sem pesquisar, o que acha de RPG?"
  -> amigo; modo "sempre"/"nunca" mandam sempre.
- `decidir` com `chamar_modelo` falso: JSON limpo, JSON dentro de ```json,
  texto solto, lixo (cai na heurística), exceção (cai na heurística).
- Frases do mundo real: "como você está hoje?" -> amigo; "quanto está o dólar
  hoje?" -> pesquisa; "me explica o que é uma API" -> amigo; "qual a última
  versão do Windows 11?" -> pesquisa (com a heurística, pelo "última").
- `fato_pedido("lembra que eu gosto de RPG")` -> "gosto de RPG" (ou
  equivalente).
- `instrucoes_da_ia("amigo")` não contém "material achado na web".
Teste real opcional com a chave do Wolf: só com ele pedindo, 5 a 10 chamadas.

## 3. TAREFA B: voz para texto (botão de microfone)
Caminho escolhido: gravar no app e transcrever com o próprio Gemini (o Wolf já
tem a chave; sem conta nova, sem baixar modelo pesado).
- `pip install sounddevice` (traz o PortAudio dentro da roda do Windows). Usar
  `RawInputStream` (16 kHz, mono, int16): não precisa de numpy. Fixar a versão
  em `requirements.txt` e atualizar `requirements-lock.txt`.
- Novo `voz.py`: `microfone_disponivel()`, classe `Gravador` (`iniciar`,
  `parar` devolve WAV via módulo `wave`, `nivel()` para animar), limite de 120 s,
  e `transcrever(cliente, modelos, wav)` com
  `types.Part.from_bytes(data=wav, mime_type="audio/wav")` e a instrução
  "Transcreva fielmente em português do Brasil. Devolva só o texto, com
  pontuação, sem comentar." Tentar os mesmos modelos de `MODELOS_RESERVA`.
- Se o nível do áudio for quase zero: avisar "Não ouvi nada" sem chamar a IA.
- Tela: botão de microfone ao lado do botão de enviar (mesmo estilo cinza,
  desenhado com Pillow como o avião). Estados: parado (cinza), gravando
  (vermelho pulsando, status "Ouvindo... clique de novo para parar"),
  transcrevendo (cinza com status). Atalho Ctrl+M. Texto transcrito entra na
  caixa de digitar na posição do cursor (não envia sozinho; opção
  `cfg["voz_enviar"]` para enviar automático, padrão desligada). Resultado
  volta pela fila `self.fila` como item novo ("voz", texto) tratado em
  `_tratar_item`.
- Mensagens em português para: sem chave, sem microfone, permissão negada,
  sem internet.
- `.spec`: incluir `sounddevice` e `_sounddevice_data` (collect_all) para o
  PortAudio entrar no .exe.
- Teste: gerar uma frase falada com o Windows (`System.Speech.Synthesis` em
  PowerShell, salvando WAV), passar por `voz.transcrever` e conferir o texto.
  No verificar.py: teste offline do `Gravador` com fluxo falso e da montagem
  do WAV (cabeçalho, taxa, duração).
- Alternativa se algo falhar: o ditado do próprio Windows (Win+H) funciona em
  qualquer caixa de texto, sem código.

### B — FEITA em 15/10/2026
Tudo acima foi feito (veja o `HISTORICO-DE-MUDANCAS.md`). Duas coisas
mudaram em relação ao texto original, porque o teste mostrou que eram
necessárias:
- **O que conta como "não ouvi nada"** não é só o volume baixo. Medindo o
  microfone do Wolf, parado ele fica em 5 a 20 (RMS) — e um fone ligado
  perto dele dá um número parecido. Então `wav_tem_som()` agora exige duas
  coisas: volume acima de 60 **e** um trecho pelo menos 8x mais forte que
  o trecho mais fraco da própria gravação (o silêncio entre as palavras).
- **Falta só o teste do Wolf falando de verdade** dentro do `.exe`.

## 4. TAREFA C: interface mais limpa (estilo Claude)
A paleta escura já é boa; não trocar as cores. Melhorar:
- Caixa de digitar: texto de apoio "Pergunte qualquer coisa..." (some ao
  digitar), cantos arredondados, microfone e enviar dentro da caixa.
- Linha pequena embaixo: botão "Web: automática" (Tarefa A) e a dica "Enter
  envia, Shift+Enter quebra a linha".
- Menu do botão direito na caixa de digitar com Recortar, Copiar, Colar,
  Selecionar tudo, e as sugestões do corretor no topo quando a palavra estiver
  errada (hoje o clique direito só mostra algo se houver erro de ortografia;
  aproveitar `_menu_ortografia`, que já cria o popup e usa os cliques
  globais). Atalhos Ctrl+A/Ctrl+Z/Ctrl+Y funcionando.
- Coluna de conversa centralizada com largura máxima (~800 px) em janelas
  largas.
- Tudo sem biblioteca nova de interface (continuar em tkinter, leve).

### C — FEITA em 15/10/2026
Tudo acima foi feito (veja o `HISTORICO-DE-MUDANCAS.md`). Três coisas que
o texto original não dizia e foram necessárias:
- **Cantos arredondados no tkinter não existem.** A solução foi desenhar
  quatro "tampinhas" (uma por canto) por cima da caixa, pintando de fundo
  o que fica fora da curva. Por isso o botão de enviar precisa de um
  respiro da direita **igual ao raio do canto** (`RAIO_CANTO`), senão a
  tampinha passa por cima do botão.
- **Ctrl+Z não funciona sozinho:** o `tk.Text` nasce com o histórico
  desligado. Tem que criar com `undo=True`.
- **A coluna centralizada tem que arrastar a caixa de digitar junto.** Se
  só a conversa centralizar, a caixa continua cruzando a tela toda e fica
  torto. E a linha do "Web: automática" precisa ser guardada como
  `self.linha_modo`, senão ela não acompanha.

## 5. TAREFA D: Configurações reorganizadas
Quatro abas, todas com a mesma margem de 24 px e títulos no mesmo estilo:
1. Memória: busca no topo; lista com editar (clique no texto) e apagar;
   "Adicionar" (o Wolf escreve um gosto/fato à mão); contador (n de 80);
   "Exportar" (salva .txt); "Apagar tudo" com confirmação; chave "Aprender
   automaticamente com as conversas" (`cfg["aprender"]`).
2. Conversa: pesquisa (Automática / Sempre / Nunca), "Lembrar o assunto da
   conversa", corretor ortográfico, voz (enviar automático depois de falar).
3. Chaves: Gemini e plano B (Groq, OpenRouter) em cartões, cada um com campo,
   mostrar, Testar e "Como conseguir a chave"; botão Salvar único e fixo no
   rodapé, com aviso "salvo" discreto em vez de caixa de mensagem.
4. Ajuda: atualizar com pesquisa automática, voz e atalhos.
Compatibilidade (não renomear, o verificar.py e o resto do código usam):
`_abrir_config(aba)`, `_mostrar_aba_config`, `self.var_contexto`,
`self.var_corretor`, `self.var_plano_b`, `_testar_com_retorno`, itens da fila
`teste_reserva_ok`/`teste_reserva_erro`/`teste_ok_form`/`teste_erro_form`,
`salvar_config`, `_atualizar_status_chave`, `_checar_ortografia`. Se mudar os
nomes das abas, atualize os testes (nunca apague).
A rolagem com a roda do mouse precisa funcionar em todos os widgets da aba
(o código atual liga a rolagem em cada filho no final; manter a ideia).

## 6. Fechamento de cada tarefa
`verificar.bat` com TUDO CERTO -> commit -> entrada nova no
HISTORICO-DE-MUDANCAS.md (o que foi baixado, modificado, adicionado,
removido) -> ao final de B, C e D: `3 - Gerar EXE.bat`, abrir o .exe 12 s sem
erro, copiar para a Área de Trabalho (guardando o antigo em `_arquivo_morto`).
Remover do projeto qualquer sobra de teste (pasta `_tmp`, scripts de print).

## 7. O que NÃO fazer
- Não reescrever `pesquisa_ia.py` inteiro nem trocar tkinter por outra
  biblioteca nesta rodada.
- Não criar `unbind_all("<Button-1>")` nem `bind_all` de clique novos (use
  `_registrar_clique_global`).
- Não gravar chave de API em arquivo do projeto, nem imprimir chave em log.
- Não pesquisar na web a cada mensagem "por garantia".
