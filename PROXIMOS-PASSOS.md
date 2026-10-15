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
  menus, microfone, e agora a caixa de digitar da Tarefa C).
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
1. **Uma pergunta normal** (digitando) com a chave nova — é o único
   caminho que nunca foi testado de ponta a ponta.
2. Usar o `.exe` por mais tempo (nos testes ele ficou aberto de 13 a 20
   segundos, sem criar `erro.log`).
Se algo falhar, leia o `erro.log` (no `.exe`: `%LOCALAPPDATA%\PesquisaIA\`;
rodando pelo código: na pasta do projeto) e siga o PASSO-A-PASSO.md.

## O que ainda falta construir (ordem sugerida pelo Wolf em 15/10/2026)

### ORDEM NOVA (Claude, 15/10 à noite): siga esta; a lista antiga logo abaixo
### fica só como histórico. Já feitos: backup, salvar .txt, Tarefas A, B e C.
1. **Memória sem repetição** (pedido do Wolf: "não guardar várias vezes o
   mesmo tipo de informação, ex. prefere ser chamado de Wolf"). O arquivo
   `memoria.py` JÁ EXISTE e está testado (`python memoria.py` = TUDO CERTO),
   só falta ligar no `pesquisa_ia.py` (tudo local, custo de token zero):
   a. `import memoria`.
   b. `_mesclar_memoria(novos)`: `nova, mudou = memoria.mesclar(
      carregar_memoria(), novos)`; se `mudou`, `salvar_memoria(nova)`;
      devolver `nova`. (Troca a regra antiga, que só pegava texto idêntico
      ou contido.)
   c. `salvar_memoria`: guardar as ÚLTIMAS `MAX_MEMORIAS` (`[-MAX_MEMORIAS:]`).
      Hoje é `[:MAX_MEMORIAS]`: quando enche, o programa para de aprender.
   d. `aprender_com_o_usuario`: junto com a conversa, mandar ao modelo o que
      já está guardado (últimos 60 fatos, 120 caracteres cada) com o aviso
      "JÁ GUARDADO: não repita nem reescreva de outro jeito; devolva só o
      que for NOVO ou uma CORREÇÃO. Se não houver, responda NADA".
   e. Ao abrir o programa: `memoria.consolidar(carregar_memoria())`; se mudou,
      copiar antes o `memoria.json` para `memoria_antes_de_organizar.json`
      (só se essa cópia ainda não existir) e salvar. Isso limpa a memória que
      já está cheia de repetição.
   f. `verificar.py`: chamar `memoria.autoteste()` (lista vazia = [OK]).
   g. Na Tarefa D, botão "Organizar" na aba Memória (chama `consolidar`).
2. **TAREFA D** (Configurações em 4 abas; aba Memória com buscar, editar,
   adicionar, exportar, interruptor "aprender sozinho" e o botão Organizar).
3. **Fontes citadas na resposta** (confiança).
4. **TAREFA E: emojis coloridos** (guia completo no `PLANO-NOVAS-FUNCOES.md`,
   seção 8; vale ler a E0 para não repetir o erro de antes). Fica depois da D
   e ANTES de "reescrever em HTML"; se o HTML for aprovado logo, pule a E.
5. Ideias do `IDEIAS.md` (perguntas para continuar, procurar nas conversas,
   fixar conversa no topo, letra maior/menor, conversa privada...).
6. "Gavetas" de memória por assunto (hoje é UMA memória; não confundir com
   os lugares fixos de nome/cidade/idade do `memoria.py`).
7. Reescrever a tela em HTML (só no fim, e só se o Wolf quiser).

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
