# Plano: limpar os resquicios do projeto no C:\

Para as outras IAs. Escrito em 18/10/2026, ANTES de remover qualquer coisa.
Pedido do Wolf: remover qualquer resquicio que sobrou do projeto no C:\.
O projeto vive em D:\Projetos\PesquisaIA; o que estiver no C: e' sobra de versoes antigas e de testes.

## Regra
Nada e' apagado de vez: tudo vai para a Lixeira do Windows (da para desfazer). Antes, a lista do que
vai sair e' mostrada ao Wolf no resumo final.

## Vai para a Lixeira (resquicio)
- C:\Projetos\PesquisaIA  (pasta VAZIA, sobra da pasta antiga) e C:\Projetos (vazia depois disso).
- %LOCALAPPDATA%\Temp\_MEI*  (13 pastas de execucoes antigas do .exe, de 13/10).
- %LOCALAPPDATA%\Temp\pia_build  (build antigo "Pesquisa IA.spec", ~107 MB).
- %LOCALAPPDATA%\Temp\opencode  (~727 arquivos de teste/rascunho de IAs, ~70 MB, 13-14/10; inclui
  "pesquisaidata_backup", copia antiga dos dados).

## FICA (nao e' resquicio)
- %LOCALAPPDATA%\PesquisaIA  : DADOS REAIS do Wolf (chave, conversas, memoria, lembretes, posicao da
  janela). O programa usa isso todo dia. Nunca apagar sem o Wolf pedir.
- Atalho `Eye of Thundera.lnk` da Area de Trabalho: aponta para D:\Projetos\PesquisaIA (ativo).
- Python do sistema e o .venv (D:): servem ao desenvolvimento.
- C:\Users\Igor\diagnostic-backup-20261016-221255: pasta vazia de origem desconhecida; nao e'
  comprovadamente do projeto, fica e o Wolf e' avisado.

## Depois
Conferir que o programa ainda abre dados (config.json, historico.json existem) e que nada em
D:\Projetos\PesquisaIA referencia caminho C:\Projetos. Registrar no HISTORICO-DE-MUDANCAS.md.

## Nao fazer
Nao tocar em AppData\Local\PesquisaIA. Nao esvaziar a Lixeira. Nao mexer em ferramentas de outras
IAs (.codex, .claude, .opencode etc.): so no que e' do projeto.
