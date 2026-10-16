# Próximos passos (o que falta e o que NÃO foi testado)

Atualizado em 15/10/2026 (depois das Tarefas A, B e C do
`PLANO-NOVAS-FUNCOES.md`). Quem continuar o trabalho (outra IA ou o próprio
Claude em outra conversa): leia isto depois do PASSO-A-PASSO.md.

## Onde as coisas estão agora
- Projeto oficial: `C:\Projetos\PesquisaIA` (única pasta de trabalho).
- Pasta antiga do OneDrive (`Documentos\Projeto Padrão`): o conteúdo foi
  apagado em 15/10/2026. Pode sobrar uma pasta VAZIA, travada por algum
  programa; ignore e não use. O Wolf pode apagá-la à mão depois de reiniciar
  o PC.
- `.exe` novo: `dist\Pesquisa IA.exe`, já copiado para a Área de Trabalho.
  Os anteriores estão em `_arquivo_morto\`.
- Estado: `verificar.bat` = TUDO CERTO (seleção, duplo/triplo clique,
  menus, microfone, caixa de digitar da Tarefa C, e agora os passos 1, 2
  e 3 da tela nova).
- Feito da `PLANO-NOVAS-FUNCOES.md`: **Tarefa A** (roteador amigo/pesquisa),
  **Tarefa B** (microfone) e **Tarefa C** (interface). **Falta a Tarefa D**
  (Configurações em quatro abas).
- Dados do Wolf (conversas, memória, chaves): `%LOCALAPPDATA%\PesquisaIA\`.
  Intocados. Nunca mexer.

## O que ainda NÃO foi testado (fazer primeiro, com o Wolf)
- **A chave de API foi trocada em 15/10/2026 e está funcionando.** A chave
  antiga (que o Google passou a recusar com erro 401 "API key not valid" no
  meio do dia) foi substituída; o Wolf colou a nova em Configurações,
  testou e **o reconhecimento de voz funcionou de verdade**. Além disso,
  o programa agora tem **chave reserva com troca automática** (campo na
  aba Chave) e uma janelinha de aviso com botão para criar chave nova.
  Se um dia a principal cair de novo, a reserva cobre sozinha; sem
  reserva, o botão abre a página do Google.
- **As janelas escuras foram conferidas com os olhos pelo Wolf** (15/10).
- **O botão direito na caixa vazia foi achado pelo Wolf e consertado**;
  falta só ele olhar o corrigido.
1. ~~**Falar com o microfone na tela nova**~~ **FEITO e TESTADO pelo Wolf
   em 16/10/2026**: duplo clique em `6 - Falar com a tela nova.bat`,
   microfone de verdade, **"funcionou perfeitamente"**. Era o último
   caminho sem testar de ponta a ponta da tela nova (o `verificar.py` só
   usa microfone falso, de propósito: o de verdade não abre no teste).
   Aprende-se com isso: quando o Wolf diz que funcionou, pode ir em
   frente — o caminho de código novo, reusando o motor do programa
   antigo, sai certo de primeira.
2. **Uma pergunta normal** (digitando) com a chave nova — ainda não
   testada de ponta a ponta na tela nova (só digitando no programa
   antigo).
3. Usar o `.exe` por mais tempo (nos testes ele ficou aberto de 13 a 20
   segundos, sem criar `erro.log`).
Se algo falhar, leia o `erro.log` (no `.exe`: `%LOCALAPPDATA%\PesquisaIA\`;
rodando pelo código: na pasta do projeto) e siga o PASSO-A-PASSO.md.

## O que ainda falta construir (ordem sugerida pelo Wolf em 15/10/2026)

### ORDEM NOVA (opencode, 15/10, depois do teste decisivo): o HTML FUNCIONA
### neste PC, então a tela nova entra AGORA e a Tarefa E de emojis coloridos
### está CANCELADA (no HTML o emoji colorido vem de graça).
### Já feitos: backup, salvar .txt, Tarefas A, B e C, memória sem repetição
### (ligada e corrigida) e o texto das Configurações que quebrava linha errado.
0. **TELA NOVA EM HTML — o caminho agora.** O teste decisivo passou
   (`web\spike_webview.py`): a janela abre no 2º monitor, a ponte
   Python↔JavaScript funciona e o **emoji sai colorido** (1.855 de 2.937
   pixels com cor, 63%). Antes de começar:
   - pôr `pywebview` no `requirements.txt` **e** no `Pesquisa IA.spec`
     (hoje ele está instalado na máquina, mas não está em nenhum dos dois:
     sem isso o `.exe` gerado não abre);
   - a ponte é **assíncrona**: no JavaScript, `window.pywebview.api.algo(...)`
     devolve uma Promise, então tem que usar `.then(...)` (o teste mostra);
   - os arquivos da tela já existem em `web\` (`index.html`, `estilo.css`,
     `app.js`); falta a ponte em Python (`app_web.py`);
   - **NÃO apague nem renomeie o `pesquisa_ia.py`.** A tela nova nasce AO
     LADO da antiga, e o atalho da Área de Trabalho continua na antiga até
     a nova ficar igual ou melhor. Assim nunca sobra o Wolf sem programa;
   - passos (cada um com commit e `verificar.bat` verde):
     1. ~~`app_web.py` mínimo~~ **FEITO em 15/10/2026** (o Wolf já viu a
        tela): a ponte existe, a janela abre no 2º monitor, mostra as
        conversas (ou as de exemplo, com `--demo`) e abre as 4 abas de
        Configurações. **Passo 1 é SÓ LEITURA**: as funções que mudam
        algo devolvem um aviso dizendo em qual passo serão feitas, para
        nenhum teste mexer nos dados do Wolf. Entrou também o
        `5 - Ver a tela nova.bat` e o spec separado da tela nova.
     2. ~~lista de conversas e conversa de verdade~~ **FEITO em
        15/10/2026**: abrir, criar nova e excluir funcionam; a conversa
        aberta mora na ponte e o `_gravar_conversa()` (que grava no
        arquivo quando há mensagem nova) já está pronto. 18 testes.
        **Já está ligado à IA** (passo 3, feito em 15/10/2026).
     3. ~~enviar pergunta e mostrar a resposta aparecendo por partes~~
        **FEITO em 15/10/2026**: `Ponte.enviar()` devolve na hora e o
        trabalho roda numa thread; a resposta volta por
        `window.PIA.evento(...)` (`etapa`, `resposta`, `erro` e
        `conversas`), reaproveitando `p.perguntar`/`p.conversar`, o
        roteador, a chave reserva e o tradutor de erro do programa
        antigo. **Testado com a IA de verdade** (respondeu certo numa
        pergunta curta) e no `verificar.py` sem gastar token. Corrigido
        no caminho: a chave reserva não se lembrava da troca (era
        chamada com um dicionário descartável, e voltava a insistir na
        chave morta a cada mensagem);
     4. ~~caixa de digitar, microfone, botão enviar, modo web~~
        **FEITO em 16/10/2026**: `Ponte.mic_alternar()` liga e desliga a
        gravação com o mesmo `voz.Gravador`, o mesmo `wav_tem_som` e o
        mesmo `transcrever` (mesma ordem de modelos, com reservas) do
        programa antigo — nada de áudio foi reescrito. A tela é avisada
        pelos eventos `gravando`, `voz` e `voz_erro`; o texto falado
        **entra na caixa de digitar** para o Wolf conferir (só sai sozinho
        se a opção "enviar" estiver ligada). Botão do microfone ou
        `Ctrl+M`. No `--demo` ele finge que ouviu, para a tela de exemplo
        funcionar sem microfone. 19 testes, com microfone e IA falsos (o
        microfone de verdade não abre e a cota não é gasta);
     5. janela de Configurações com as 4 abas gravando de verdade
        (a Tarefa D entra aqui, para não ser feita duas vezes) — **já
        está no código e tem 7 testes** (`config_salvar`, memória
        adicionar/apagar/apagar tudo/organizar, chave vazia não apaga a
        chave salva); falta conferir com o Wolf e ligar o que só existe
        no tkinter;
     6. microfone de ponta a ponta, salvar .txt, copiar, pesquisar;
     7. atalhos de teclado, cantos arredondados da caixa, borda da janela;
     8. `verificar.bat` cobrindo a tela nova + `.exe` gerado e testado
        (usando o spec `Pesquisa IA Tela Nova.spec`, que é separado do
        do programa que já funciona).
1. ~~**Memória sem repetição**~~ **FEITA e corrigida em 15/10/2026** pelo
   opencode: ligada ao programa e com os 2 defeitos que o Claude deixou
   corrigidos (perdia o nome e a data de nascimento; guardava "NADA").
   Falta só o botão "Organizar" na aba Memória (aba 0, passo 5).
2. **TAREFA D** (Configurações em 4 abas; aba Memória com buscar, editar,
   adicionar, exportar, interruptor "aprender sozinho" e o botão Organizar)
   — vai junto com o passo 5 da tela nova, para não fazer duas vezes.
3. **Fontes citadas na resposta** (confiança).
4. ~~**TAREFA E: emojis coloridos**~~ **CANCELADA**: o passo 0 já entrega
   emoji colorido de graça. O guia completo continua no
   `PLANO-NOVAS-FUNCOES.md` seção 8, caso um dia a tela nova seja
   descartada e o programa volte a ser só Tk (aí a E volta a valer).
5. Ideias do `IDEIAS.md` (perguntas para continuar, procurar nas conversas,
   fixar conversa no topo, letra maior/menor, conversa privada...).
6. "Gavetas" de memória por assunto (hoje é UMA memória; não confundir com
   os lugares fixos de nome/cidade/idade do `memoria.py`).
7. ~~**Reescrever a tela em HTML**~~ **DECIDIDO em 15/10/2026**: virou o
   item 0, porque o teste mostrou que funciona neste PC.

(lista do Claude, superada: ela começava em 1. memória sem repetição, que já
foi feita, e punha a tela em HTML por último.)

(lista antiga:)
1. ~~**Backup do código.**~~ **FEITO em 15/10/2026**: existe o
   `4 - Fazer backup.bat`, que grava o projeto (código + histórico do Git)
   num `.zip` na pasta "Backup Pesquisa IA" do OneDrive (que vai para a
   nuvem). O backup foi **conferido descompactando o zip**: os 30 commits
   voltaram e todos os arquivos compilam. Ainda dá para colocar um
   repositório privado no GitHub (uma segunda cópia, em outro servidor) —
   só precisa de uma conta do Wolf. Enquanto isso, lembrar de rodar o
   `4 - Fazer backup.bat` de tempos em tempos.
   (De quebra: o `.git` tinha 48 MB de lixo; limpo, ficou 0,5 MB.)
2. ~~**Salvar a resposta em .txt.**~~ **FEITO em 15/10/2026**: botão de
   disquete embaixo de cada resposta (ao lado do de copiar) e atalho
   **Ctrl+S**, que salvam a resposta num `.txt`. O nome do arquivo sai da
   primeira linha da resposta, limpo (sem caractere que o Windows proíbe e
   sem a numeração de lista). A janela de "Salvar como" é a do Windows e
   ela tenta abrir escura.
3. **Fontes citadas na resposta** — a IA já pesquisa e sabe de onde tirou
   cada coisa; hoje ela joga esse rastro fora. É o que dá confiança.
4. **TAREFA D** do `PLANO-NOVAS-FUNCOES.md`: Configurações em 4 abas
   (Memória, Conversa, Chaves, Ajuda).
5. **Ideias do `IDEIAS.md`**, da mais útil para a menos: perguntas para
   continuar, procurar nas conversas, fixar conversa no topo,
   aumentar/diminuir a letra (Ctrl + / Ctrl -), conversa privada,
   pesquisa "séria", memória com data, exportar tudo.
6. **Memória separada por assunto** ("gavetas", como no sistema que o Wolf
   viu na internet). Hoje existe UMA memória só. Não está em nenhum plano.
7. **Reescrever só a tela em HTML** (manter busca e IA em Python). É o
   que resolve de vez a seleção de texto e a formatação. Trabalho grande,
   deixar pro final.

## Regra da tela de teste (importante)
O segundo monitor do Wolf começa em **X=1920**. **Toda** janela de teste
tem que nascer em `X >= 1950` (o `verificar.py` já faz isso com
`POSICAO_TESTE = "+2000+100"`), para não cobrir a tela que ele está
usando. Para abrir o `.exe`: o PyInstaller sobe um processo filho, então
`MainWindowHandle` do processo iniciado fica vazio — procure a janela pelo
título "Pesquisa IA" em todos os processos. Para printar a janela, use
`PrintWindow` (o `ImageGrab` no segundo monitor devolve preto).

## Coisas pequenas que ainda podem ser feitas
- Rodar `verificar.bat` de vez em quando, mesmo sem mexer em nada.
- Quando o Wolf pedir uma biblioteca nova: fixar a versão em
  `requirements.txt`, atualizar o `requirements-lock.txt`
  (`.venv\Scripts\python.exe -m pip freeze`) e anotar no HISTORICO.

## Sobre trocar de tecnologia (só se o Wolf pedir)
Python não é o problema; o que limita é o tkinter. Opções, da mais simples
para a mais trabalhosa:
1. Continuar em tkinter, trocando o texto desenhado no Canvas por um
   `tk.Text` somente leitura (seleção nativa completa). Mudança pequena.
2. Refazer só a tela em HTML dentro de uma janelinha (`pywebview`), mantendo
   a busca e a IA em Python. Seleção, copiar e formatação ficam como num
   site. É a opção recomendada para o longo prazo.
3. Flet ou PySide6 (Python puro, mais bonitos, mais trabalho).
Regras se for fazer: trabalhar numa branch do Git, manter o `verificar.py`
passando (adaptar os testes à tela nova, nunca apagá-los), e não mexer em
`%LOCALAPPDATA%\PesquisaIA\`.

## Se algo quebrar e você não souber o que fazer
1. `git status` e `git log --oneline -8`.
2. `git stash` (guarda o que está mexido) e rode `verificar.bat` no último
   commit. Se passar, o problema está no que foi guardado: reaplique aos
   poucos (`git stash pop`).
3. Se o `.exe` não gerar, rode `3 - Gerar EXE.bat` e leia a mensagem do
   PyInstaller; o `Pesquisa IA.spec` é a receita.
4. Explique ao Wolf, em português simples, o que aconteceu e o que foi
   desfeito.
