# Plano das novas funções do Pesquisa IA

Para a IA que programa. Escrito pelo Claude em 15/10/2026, depois de ler o
código e de ver a tela do programa. Salve este arquivo na pasta do projeto
(`C:\Projetos\PesquisaIA`) e siga na ordem. O Wolf não programa: explique tudo
em português simples.

## META (decidido pelo Wolf em 15/10/2026): TUDO EM HTML NO FINAL

O programa de hoje é feito com o Tk (tkinter), que é de 2000 e tem
limites sem conserto: **só desenha emoji de uma cor**, a seleção de
texto fica estranha, e cada ícone precisa ser desenhado à mão. Por isso
a tela está sendo reescrita em **HTML** (uma página de navegador dentro
de uma janela do Windows, via `pywebview`).

**Quando acabarem os 8 passos, TODA a tela do Pesquisa IA é HTML.** Não
fica nenhum pedaço de interface no Tk. Pedido do Wolf: "faça com que
seja, para que seja mais fácil de trabalhar". Faz sentido: em HTML é
muito mais fácil de mudar,ixa e deixar bonito.

### O que passa a ser HTML (100%)
- Janela principal: bolhas, caixa de digitar, barra lateral, lista de
  conversas, microfone, modo "Web".
- **Janela de Configurações com as 4 abas** (Memória, Conversa, Chaves,
  Ajuda) — passo 5.
- Janelinhas de aviso e confirmação (já desenhadas por nós, sem as
  brancas do Windows).
- Menu do botão direito, corretor ortográfico, avisos de status.

### O que continua em Python (e é o certo)
O `pesquisa_ia.py` **não é apagado**: ele vira o **motor**, e a tela
HTML passa a ser a **cara**. A tela nova já importa esse arquivo e usa
o que ele tem de melhor (chamar a IA, pesquisar na web, trocar de
chave, traduzir erro, aprender sobre o usuário, gravar a conversa).
Continua em Python porque é o que sabe fazer:
- falar com o Google (e com os serviços de reserva);
- pesquisar na web;
- ler e gravar os arquivos do Wolf (conversas, memória, chaves);
- ouvir o microfone.

### As únicas coisas que continuam sendo do Windows (e tudo bem)
- **A moldura da janela** (a barra de título com fechar/minimizar). A
  barra já é escura.
- **A janela de "Salvar como..."**, que é do próprio Windows (e já é
  aberta escura pelo que o código faz).

### Como a troca acontece (sem ficar sem programa)
A tela nova nasce **ao lado** da antiga, nunca no lugar dela. O atalho
da Área de Trabalho continua no programa de Tk até a tela nova ficar
igual ou melhor. No fim, o `pesquisa_ia.py` deixa de ser a interface e
passa a ser só o motor — que já é como ele funciona hoje.

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

## 8. TAREFA E: emojis coloridos nas respostas (a volta dos emojis)

Pedido do Wolf (15/10/2026): a IA poder usar emojis coloridos de novo, sem
eles ficarem fora da bolha nem em cima da escrita. Hoje estão desligados de
propósito (`_remover_emojis` e o prompt "NÃO use emojis"). Sobraram restos da
tentativa antiga em `pesquisa_ia.py` (perto da linha 48):
`CACHE_EMOJI_COLORIDO` e `REFERENCIAS_IMG_EMOJI`; aproveite ou apague.

### E0. Por que deu errado antes (o Claude testou neste PC em 15/10)
- O Tk do Windows (8.6.15) desenha letras com o sistema antigo do Windows,
  que só conhece emoji de UMA cor. Não tem como consertar por fonte ou
  configuração. Emoji colorido precisa entrar como figurinha (imagem).
- A bolha atual é UM item de texto de Canvas, e o Canvas não aceita imagem no
  meio do texto. A tentativa antiga desenhou as figurinhas por fora, em
  posições calculadas "no olho". Quando a linha quebrava ou a letra tinha
  largura diferente da prevista, a figurinha andava: saía da bolha ou ficava
  em cima da letra.
- "HTML": o navegador desenha emoji colorido sozinho, por isso o opencode
  falou em HTML. É a solução grande (item "reescrever a tela em HTML") e NÃO é
  necessária para os emojis. `tkinterweb` não serve (usa o desenho de texto do
  Tk, o mesmo problema).

### E1. Caminho recomendado (testado: fica no lugar e quebra linha certo)
Trocar o texto da bolha por um `tk.Text` somente leitura, dentro do mesmo
Canvas arredondado (`create_window`), e pôr cada emoji como imagem NO MEIO do
texto com `image_create`. A imagem vira parte da linha: quebra com a frase,
sobe e desce com ela e não sai da bolha.
```python
from PIL import Image, ImageDraw, ImageFont, ImageTk
FONTE_EMOJI = r"C:\Windows\Fonts\seguiemj.ttf"   # já vem com o Windows

def figurinha_de_emoji(emoji, altura):
    chave = (emoji, altura)
    if chave not in CACHE_EMOJI_COLORIDO:
        fonte = ImageFont.truetype(FONTE_EMOJI, 109)       # tamanho fixo
        img = Image.new("RGBA", (200, 160), (0, 0, 0, 0))
        ImageDraw.Draw(img).text((10, 10), emoji, font=fonte,
                                 embedded_color=True)      # <- a cor
        img = img.crop(img.getbbox())
        lado = max(img.size)                               # quadrado, centrado
        quadro = Image.new("RGBA", (lado, lado), (0, 0, 0, 0))
        quadro.paste(img, ((lado - img.width) // 2, (lado - img.height) // 2))
        foto = ImageTk.PhotoImage(quadro.resize((altura, altura), Image.LANCZOS))
        CACHE_EMOJI_COLORIDO[chave] = foto   # guardar, senão o Tk apaga a imagem
    return CACHE_EMOJI_COLORIDO[chave]

# no texto:  texto.image_create("end", image=figurinha_de_emoji("\U0001F3AE", 22),
#                               align="center", padx=1)
```
- Medido aqui: Pillow 12.3.0, FreeType 2.14.3, fonte existe. `altura` = a altura
  de linha da fonte do texto (`tkfont.Font.metrics("linespace")`), +2 no máximo.
  `align="center"` ficou bom; ajuste a olho se subir ou descer.
- Opções do `tk.Text`: `state="disabled"` (depois de inserir), `wrap="word"`,
  `borderwidth=0`, `highlightthickness=0`, `padx=0`, `pady=0`, `insertwidth=0`,
  mesma cor e fonte da bolha, `spacing1=2`, `spacing3=2`.
- Altura da bolha: `texto.count("1.0", "end", "displaylines")` depois de fixar a
  largura em caracteres (ou `winfo_reqheight()`); refazer quando a janela
  mudar de tamanho (já existe `_redim_id`). A roda do mouse em cima do Text
  tem que rolar o CHAT, não o Text.
- A animação de "digitando" hoje mexe no item de texto do Canvas: portar para
  inserir no `tk.Text` (cuidado, é a parte que mais quebra).

### E2. Achar os emojis no texto
Emoji pode ter vários caracteres juntos (bandeira, tom de pele, família, 1️⃣).
Comece por esta expressão e teste com os casos abaixo:
```python
EMOJI_RE = re.compile(
    "(?:[\U0001F1E6-\U0001F1FF]{2}"                       # bandeira
    "|[0-9#*]\ufe0f?\u20e3"                               # tecla 1️⃣
    "|[\U0001F300-\U0001FAFF\u2B50\u2B55\u231A\u231B\u23E9-\u23F3]"
    "[\ufe0f\U0001F3FB-\U0001F3FF]*"                      # emoji comum + tom
    "|[\u2600-\u27BF\u2190-\u21FF\u2B05-\u2B07]\ufe0f"  # símbolo SÓ se pedir emoji (FE0F)
    ")(?:\u200d[\U0001F300-\U0001FAFF\u2640\u2642\u2764]\ufe0f?"
    "[\U0001F3FB-\U0001F3FF]*)*")
```
Tem que continuar TEXTO normal: "•", "–", "→", "✓", "©", "™", "°", "R$", "❤"
(sem FE0F). Tem que contar como UM emoji: "👍🏽", "❤️", "1️⃣", "🇧🇷", "👨‍💻".

### E3. Limites descobertos (não é bug seu)
Aqui o Pillow não tem `raqm`, e o Windows não traz bandeiras. Resultado do
teste: 👨‍💻 (sequência com ZWJ) aparece só como 👨, e 🇧🇷 aparece como as letras
BR. Escolha:
- (a) começar simples: se for sequência ZWJ ou bandeira, mostrar o primeiro
  componente ou o texto. Nunca quebrar.
- (b) só se o Wolf sentir falta: baixar PNGs do Twemoji (fork `jdecked/twemoji`,
  licença CC-BY 4.0: dar crédito na aba Ajuda e criar `LICENCAS.md`), só os
  ~300 mais usados, em `emojis\` com nome = códigos em hexadecimal ligados por
  "-" (ex.: `1f468-200d-1f4bb.png`), e incluir a pasta em `datas` do `.spec`.

### E4. Copiar e selecionar
O `tk.Text` seleciona sozinho (arrastar, duplo e triplo clique, Ctrl+A). O
código de seleção do Canvas das bolhas pode sair, MAS os testes de seleção do
`verificar.py` devem ser ADAPTADOS ao Text (nunca apagados): clique fora
desfaz, clique em outra bolha desfaz, duplo clique pega a palavra, triplo pega
tudo, botão direito copia só a seleção da própria bolha.
A imagem não tem texto: ao copiar, reconstrua o texto com
`texto.dump(ini, fim, text=True, image=True)` e um dicionário
nome-da-imagem para emoji. Ctrl+C, botão direito, botão de copiar e Ctrl+S
precisam devolver os emojis de verdade.

### E5. Prompts e chave
- `INSTRUCOES` (modo pesquisa): sem emoji, a menos que o Wolf use.
  `INSTRUCOES_AMIGO`: "pode usar emoji com moderação (0 a 2 por resposta,
  só quando combinar com o clima)". Continua proibido asterisco.
- `_remover_emojis` deixa de ser chamado no texto da IA; fica só para os
  títulos da barra lateral e nomes de arquivo (`_nome_de_resposta`). O .txt
  salvo mantém os emojis (UTF-8).
- Chave `cfg["emojis"]` (padrão ligada) na aba Conversa: desligada, o prompt
  pede sem emoji e `_remover_emojis` volta a valer.

### E6. Testes novos no `verificar.py`
- A expressão acima: os casos de E2.
- `figurinha_de_emoji` devolve imagem com a altura pedida e pixels visíveis.
- Bolha com "Oi 😀 tudo bem? 🎮": a caixa de cada imagem (`texto.bbox`) fica
  dentro da linha de texto (±3 px) e o Text inteiro dentro do polígono da
  bolha; repetir com a linha quebrando exatamente no emoji.
- Selecionar tudo e copiar devolve o texto original com os emojis.
- Fonte de emoji ausente (trocar `FONTE_EMOJI` por caminho falso): o emoji
  aparece como texto e nada quebra.
- Conferência visual com o Wolf (janela de teste em X >= 1950; para tirar
  print use `PrintWindow`, regra da seção de tela de teste).

### E7. Ordem e cuidados
Depois da Tarefa D e antes de "reescrever em HTML". Se o Wolf decidir fazer a
tela em HTML logo, PULE a Tarefa E (lá o emoji colorido vem de graça).
Trabalhe numa branch do Git e em passos, cada um com commit e verde:
1. bolha vira `tk.Text` SEM emoji (igual por fora, testes adaptados) -> é o
   passo arriscado; 2. figurinhas; 3. prompts e chave; 4. gerar o .exe.
