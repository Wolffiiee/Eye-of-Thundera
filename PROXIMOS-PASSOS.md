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
  testou e **o reconhecimento de voz funcionou de verdade**. Se um dia
  aparecer erro de chave de novo, o caminho é o mesmo:
  <https://aistudio.google.com/apikey> → Configurações → Salvar → Testar.
1. **Uma pergunta real** com a chave nova (as respostas normais ainda não
   foram testadas de ponta a ponta). Peça ao Wolf para fazer uma pergunta
   e dizer se a resposta apareceu.
2. ~~**Falar de verdade**~~ — **FEITO em 15/10/2026**: o Wolf falou no
   microfone, o texto transcrito apareceu na caixa e a chave nova funciona.
3. **O botão direito na caixa de digitar com os olhos** (os itens foram
   conferidos pelos testes, mas o visual do menu não foi olhado).
4. Usar o `.exe` por mais tempo (nos testes ele ficou aberto de 13 a 20
   segundos, sem criar `erro.log`).
Se algo falhar, leia o `erro.log` (no `.exe`: `%LOCALAPPDATA%\PesquisaIA\`;
rodando pelo código: na pasta do projeto) e siga o PASSO-A-PASSO.md.

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
- Itens do `IDEIAS.md`. Ordem sugerida (do mais útil para o mais trabalhoso):
  salvar a resposta em .txt, fontes citadas na resposta, perguntas para
  continuar, procurar nas conversas, fixar conversa no topo,
  aumentar/diminuir o texto (Ctrl + / Ctrl -).

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
