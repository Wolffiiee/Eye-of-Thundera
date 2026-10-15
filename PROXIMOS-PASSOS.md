# Próximos passos (o que o Claude pretendia fazer e deixou anotado)

Atualizado em 15/10/2026. Quem continuar o trabalho (outra IA ou o próprio
Claude em outra conversa): leia isto depois do PASSO-A-PASSO.md.

## Onde as coisas estão agora
- Projeto oficial: `C:\Projetos\PesquisaIA` (única pasta de trabalho).
- Pasta antiga do OneDrive (`Documentos\Projeto Padrão`): o conteúdo foi
  apagado em 15/10/2026. Pode sobrar uma pasta VAZIA, travada por algum
  programa; ignore e não use. O Wolf pode apagá-la à mão depois de reiniciar
  o PC.
- `.exe` novo: `dist\Pesquisa IA.exe`, já copiado para a Área de Trabalho
  (`C:\Users\Igor\OneDrive\Área de Trabalho`). O antigo está em
  `_arquivo_morto\`.
- Estado: `verificar.bat` = TUDO CERTO (inclui os testes de seleção, duplo
  clique, triplo clique, menus e janela de Configurações).
- Dados do Wolf (conversas, memória, chaves): `%LOCALAPPDATA%\PesquisaIA\`.
  Intocados. Nunca mexer.

## O que ainda NÃO foi testado (fazer primeiro, com o Wolf)
1. Uma pergunta real à IA (precisa de internet e da chave dele). Peça ao
   Wolf para fazer uma pergunta e dizer se a resposta apareceu, se dá para
   selecionar, dar duplo clique numa palavra e clicar fora.
2. Usar o `.exe` por mais tempo (ele só ficou aberto uns 12 segundos nos
   testes, sem criar `erro.log`).
Se algo falhar, leia o `erro.log` (no `.exe`: `%LOCALAPPDATA%\PesquisaIA\`;
rodando pelo código: na pasta do projeto) e siga o PASSO-A-PASSO.md.

## Coisas pequenas que ainda podem ser feitas
- Rodar `verificar.bat` de vez em quando, mesmo sem mexer em nada.
- Quando o Wolf pedir uma biblioteca nova: fixar a versão em
  `requirements.txt`, atualizar o `requirements-lock.txt`
  (`.venv\Scripts\python.exe -m pip freeze`) e anotar no HISTORICO.
- Itens do `IDEIAS.md`. Ordem sugerida (do mais útil para o mais trabalhoso):
  aumentar/diminuir o texto (Ctrl + / Ctrl -), salvar a resposta em .txt,
  fontes citadas na resposta, perguntas para continuar, procurar nas
  conversas, fixar conversa no topo.

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
