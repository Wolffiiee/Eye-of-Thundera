# Ideias para o Eye of Thundera

Ideias coletadas de outros apps de assistente (ChatGPT, Gemini, Perplexity, Notion
AI, Replika etc.) e das tendências de 2026. Organizadas pelas que combinam mais
com o nosso app (local, grátis, em português, simples de usar).

---

## As que eu mais gostei

### 1. ~~Fontes citadas na resposta~~ **FEITA em 16/10/2026**
Hoje o app junta a resposta mas mostra de onde veio. Agora, quando a
resposta veio da web, aparece uma letrinha discreta embaixo dela:
`sites consultados: 3`. Clicar abre a lista, e cada site abre no
navegador.
Chamei de "sites consultados", e **não** de "fontes", de propósito: são os
**resultados da busca**, não citações — o programa não confere se o que
o site diz é verdade. O link está ali para você conferir com os próprios
olhos. Link `javascript:` é descartado por segurança.

    Fontes usadas: 3   [ver]

E ao clicar, abre a lista dos sites que foram usados, com o título de cada um.
Perplexity e ChatGPT fazem isso, e dá confiança na resposta.

### Galeria de imagens — **FEITA em 16/10/2026 (tela nova)**

Era a ÚLTIMA coisa que o programa antigo (tkinter) tinha e a tela nova
não: perguntar *"imagens de God of War"* e mostrar as fotos na conversa.
Sem ela o antigo não podia ser aposentado.

- A pergunta de imagem **não vai para a IA** — é desviada para a busca
  de imagens, que é de graça. Não gasta chave de API.
- As miniaturas viajam no evento em base64 (6 KB cada).
- **A foto grande não viaja junto** (viraria 2,7 MB de texto e travaria a
  janela): fica no Python e a tela pede uma por vez, quando o Wolf
  clica. Já foi baixada em segundo plano, então aparece quase na hora.
- Clicar abre a foto por cima de tudo, com botão de fechar (Esc fecha) e
  link para a página original.

### 2. Pesquisa profunda — IMPLEMENTADA em 16/10/2026
O botão "Pesquisa séria" liga/desliga o modo profundo na barra de escrita. A tela envia a opção para o motor, que executa o caminho de pesquisa profunda e devolve a resposta organizada com sites consultados. O que falta é validar manualmente o comportamento com perguntas reais e melhorar a clareza visual do estado ligado/desligado.

### 3. ~~Modo conversa privada~~ **FEITA em 16/10/2026**
Botão "Privada" na barra de escrever. Ligado, o que for dito **não é
salvo** e a IA **não aprende nada** — e o título da conversa fica
amarelo avisando, para nunca ficar na dúvida.
Um detalhe de segurança: ligar **ou desligar** começa uma conversa nova,
senão desligar gravaria a conversa inteira junto e a parte privada
vazaria para o arquivo.

### 4. ~~Perguntas para continuar~~ **FEITA em 16/10/2026**
Depois da resposta, um botão discreto **"outras perguntas"** sugere 3
perguntas curtas sobre o mesmo assunto; clicar em uma já manda a pergunta.
**É um botão de propósito, não é automático:** cada sugestão gasta uma
chamada de IA, e fazer isso sozinho a cada resposta dobraria o custo do
programa sem você pedir.
Se a IA responder besteira em vez da lista, a tela avisa em vez de
mostrar coisa quebrada.

### 5. ~~Conversa importante (fixar)~~ **FEITA em 16/10/2026**
Na barra da esquerda da tela nova, no menu dos tres pontinhos: "Fixar no topo" / "Soltar do topo". A conversa sobe no arquivo com as mensagens intactas e o programa antigo continua enxergando ela normalmente.
(Original, que e' a ideia) Na lista em cascata, dar para "fixar" uma conversa no topo — por exemplo, no
menu dos três pontinhos ter "Fixar no topo". Assim as conversas que você mais
usa ficam sempre à mão.

### 6. ~~Procurar nas conversas~~ **FEITA em 16/10/2026**
Caixinha "Procurar nas conversas..." em cima da lista, procurando no titulo e nas mensagens, sem levar em conta acento nem maiuscula. Mostra o trecho com a palavra destacada.
(Ideia original) Uma caixinha de busca na lista de conversas, para achar rapidinho aquela
conversa de semana passada ("aquela do bolo de cenoura").

---

## Ideias pequenas (dá para fazer rapidinho)

- ~~**Aumentar/diminuir o texto**~~ - **FEITO em 16/10/2026** (tela nova): Ctrl +, Ctrl - e Ctrl 0, e botoes em Configuracoes > Conversa. Vai de 13 a 26 px e fica guardado.
- (Ideia original) **Aumentar/diminuir o texto** — um botão ou atalho (Ctrl + / Ctrl -) para
  deixar a letra do chat maior. Ajuda muito na leitura.
- ~~**Salvar a resposta num arquivo**~~ - **FEITO em 15/10/2026**: botão de
  disquete embaixo de cada resposta (ao lado do de copiar) e Ctrl+S, que
  salvam a última resposta num .txt com o nome tirado da primeira linha.
- ~~**Atalhos novos**~~ - **FEITOS em 16/10/2026** (tela nova): Ctrl+M microfone, Ctrl+S salvar, Ctrl+N conversa nova, Ctrl+F procurar, Ctrl+, / Ctrl- / Ctrl 0 para a letra.
- (Ideia original) **Atalhos novos** — por exemplo Ctrl+F para procurar na conversa, e um
  atalho para abrir as Configurações.
- ~~**Resumo do dia**~~ - **FEITO em 16/10/2026** (tela nova): botão "Resumo do dia" na barra de escrever e atalho **Ctrl+D**. Um clique e a tela pergunta as notícias de hoje — é o que se pergunta todo dia, não faz sentido obrigar a digitar a mesma frase sempre.
- (Ideia original) **Resumo do dia** — um botão que monta um resumo das notícias do dia, sem
  você precisar perguntar.

---

## Ideias maiores (valem para depois)

- ~~**Entrar com a voz**~~ — IMPLEMENTADO: microfone na barra de escrita; a transcrição entra na caixa para revisão antes do envio.
- **Arrastar um arquivo para a conversa** — implementado para texto e PDF (16/10 e 17/10/2026): a janela aceita `.txt`, `.md`, `.csv` e `.json` e carrega o texto para a caixa. Um `.pdf` também é aceito: o texto é extraído **no computador** (`pdf_leitor.py` + `pypdf`) e entra na caixa para revisão antes do envio. PDF digitalizado (sem texto), com senha, corrompido ou grande demais recebe aviso claro. **Imagens ainda não** — dependem de OCR/visão e de consentimento explícito antes de enviar a um provedor.
- ~~**Memória com data**~~ — FEITA em 16/10/2026: cada item da aba Memória mostra a data quando ela existe; as datas ficam em arquivo separado de `memoria.json`. Itens antigos sem data não recebem uma data inventada.
- ~~**Gavetas por assunto na memória**~~ — IMPLEMENTADAS: os fatos podem ser agrupados e filtrados por assunto na aba Memória.
- ~~**Exportar tudo**~~ - **FEITO em 16/10/2026**: botão "Fazer cópia agora" em Configurações > Conversa, que copia conversas, memória e chaves num `.zip` no OneDrive. É o mesmo que o `9 - Fazer backup dos meus dados.bat`, com a mesma função.
- (Ideia original) **Exportar tudo** — um botão para salvar a memória e as conversas num
  arquivo só, como backup.

---

## O que eu NÃO recomendo

- **Deixar a memória aparecer demais** — o ponto forte do nosso app é a memória
  discreta. Apps como o ChatGPT passaram a mostrar "usamos sua memória", e
  muita gente achou invasivo. O nosso jeito (invisível) é melhor.
- **Encher de abas** — manter o app simples. As três abas de Configurações já
  dão conta.
