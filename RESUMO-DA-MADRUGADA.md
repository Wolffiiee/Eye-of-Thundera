# Resumo da madrugada de 16/10/2026 (para o Wolf)

O Wolf foi dormir e deixou o programa "nas mãos do OC". Este arquivo é
o resumo de tudo que foi feito, para ele revisar de manhã sem precisar
ler 40 commits.

## O que estava pendente quando ele dormiu

1. Um "crash" ao arrastar a janela da tela nova (virou pista de um defeito
   antigo — ver abaixo).
2. Duas ideias da lista dele: **fontes citadas** e **tamanho da letra**.
3. O `.exe` da tela nova na sua mesa estava sem as correções do dia.

## Defeitos importantes encontrados e corrigidos

### 1. O programa NUNCA pesquisava na web (defeito antigo e silencioso)

O Wolf perguntou do próximo jogo do Grêmio e a IA respondeu que não tinha
acesso à internet. **Não era erro** — a resposta chegou. A causa era séria:

    400 INVALID_ARGUMENT: "Manually set deadline 8s is too short.
    Minimum allowed deadline is 10s."

O programa dava **8 segundos** para a IA decidir "isso é papo ou é
pesquisa", e o Google exige **no mínimo 10**. Então essa decisão **nunca
funcionou**, e o erro era engolido em silêncio. Só restava a lista de
palavras ("hoje", "agora", "notícia"...), e "próximo jogo" não está nela.

**Corrigido para 20 s**, com teste que reprova se alguém lowering de novo.
Vale para os **dois programas** — e por isso os dois `.exe` foram
refeitos.

### 2. A janela de "Salvar como" abria no monitor errado

Abria em x=138 (primeiro monitor) enquanto o programa estava no segundo
(x=2000). O Wolf achava que o programa tinha travado. Medido e corrigido:
agora nasce em x=2068, junto com o programa.

### 3. A barra de título da tela nova estava branca

A função usada esperava uma peça do tkinter que a tela nova não tem; o
erro era engolido. Corrigido (escurece pelo título da janela).

### 4. "Imortal" NÃO era invenção (erro meu)

O Wolf perguntou do Grêmio e a resposta falou em "Imortal". Achei que era
alucinação e fui "consertar" — **mas "Imortal" é apelido do Grêmio**. A
IA estava certa e eu quase estraguei. A regra foi reescrita para permitir
apelido.

## Ideias da lista dele que ficaram prontas

| Ideia | Como ficou |
|---|---|
| **Fontes citadas** (nº 1) | Letra discreta "sites consultados: 3" embaixo da resposta |
| **Tamanho da letra** | Ctrl + / Ctrl − / Ctrl 0 e botões nas Configurações |
| **Conversa privada** (nº 3) | Botão "Privada": não salva e a IA não aprende |
| **Perguntas para continuar** (nº 4) | Botão "outras perguntas" sugere 3 perguntas |
| **Fixar conversa** | No menu dos três pontinhos |
| **Procurar nas conversas** | Caixinha em cima da lista |
| **Resumo do dia** | Botão + Ctrl+D |
| **Cópia de segurança** | Botão dentro do programa e o `.bat` |
| **Memória com data** | "aprendeu em dd/mm/aaaa" em cada item |

## Decisões que o OC tomou sozinho (para o Wolf conferir)

1. **"Sites consultados", não "fontes".** São resultados de busca; o
   programa não confere se o que o site diz é verdade. Dizer "fonte"
   seria mentir.
2. **"Outras perguntas" é botão, não automático.** Automático dobraria o
   custo de IA sem ele pedir.
3. **Conversa privada: ligar ou desligar começa conversa nova.** Sem isso,
   desligar gravaria a parte privada junto no arquivo — a conversa
   privada mentiria.
4. **As datas da memória vão num arquivo ao lado**, nunca dentro do
   `memoria.json` (que tem regra de ouro e é lido pelos dois programas).
5. **Nada de link `javascript:`** na lista de sites (segurança).

## O que ficou em aberto

- **O crash ao arrastar** é do WebView2 (têm vários relatos oficiais). Não
  dá para consertar no nosso código. Agora a tela nova grava `erro.log`,
  então se repetir há prova. **Nada se perde**: cada resposta é gravada
  antes de aparecer.
- **A barra de título embutida** (sem a barra do Windows) continua de
  fora, como combinado.

## Como testar de manhã

1. `7 - Usar a tela nova de verdade.bat` (ou o `Pesquisa IA Tela Nova.exe`).
2. Pergunte algo do dia: deve vir com "sites consultados: N" embaixo.
3. Clique em **"outras perguntas"**, em **"Privada"**, em **Ctrl +** (letra).
4. Configurações > Conversa: **"Fazer cópia agora"**.
5. Configurações > Memória: veja as datas e clique no texto para editar.

Nada nos dados do Wolf foi alterado em nenhum momento — os testes usam
sempre uma pasta temporária, e há testes que reprovam se isso mudar.