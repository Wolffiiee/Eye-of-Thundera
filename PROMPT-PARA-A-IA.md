# Prompt para colar na IA que programa

Copie TUDO do bloco abaixo e cole no início da conversa com a IA (ou sempre
que abrir uma conversa nova com ela).

```
Você vai continuar o trabalho num programa meu chamado "Eye of Thundera"
(Python 3.12 + tkinter). Meu apelido é Wolf; pode me chamar assim. Eu não sei
programar, então siga um método e me explique tudo em português simples, sem
jargão.

ONDE ESTÁ O PROJETO
A ÚNICA pasta oficial é:
    D:\Projetos\Eye of Thundera
A pasta antiga do OneDrive ("Documentos\Projeto Padrão") foi apagada em
15/10/2026. Se aparecer uma pasta vazia com esse nome, ignore: NÃO trabalhe
nela.

ANTES DE QUALQUER COISA, LEIA (nesta ordem), na pasta do projeto:
1. INSTRUCOES-PARA-IA.md      -> regras obrigatórias e armadilhas já achadas
2. PASSO-A-PASSO.md           -> o método que você deve seguir, com exemplo real
3. HISTORICO-DE-MUDANCAS.md   -> tudo que foi baixado, modificado, adicionado,
                                  removido e movido (14 e 15/10/2026)
4. PROXIMOS-PASSOS.md         -> o que ainda falta e o que NÃO foi testado
Depois rode `git status` e `git log --oneline -5`.

RESUMO DO QUE JÁ FOI FEITO (tudo em 15/10/2026; você continua daí)
- Projeto movido para fora do OneDrive; .venv recriado do zero (Python 3.12).
- Bibliotecas com versão fixa: requirements.txt (programa),
  requirements-dev.txt (pyinstaller e pyflakes) e requirements-lock.txt
  (lista completa de tudo que está instalado). httpx e sounddevice
  incluídos.
- Bug da seleção de texto corrigido: clicar em qualquer lugar desfaz a
  seleção. Duplo clique seleciona a palavra e triplo clique seleciona o texto
  inteiro da bolha.
- Cliques globais passam por um sistema único (_despachar_clique,
  _registrar_clique_global, _remover_clique_global). É PROIBIDO usar
  unbind_all("<Button-1>") ou criar novos bind_all de clique.
- TAREFA A (feita): roteador.py (decide papo x pesquisa), botão
  "Web: automática" e prompt de amigo separado.
- TAREFA B (feita): voz.py + botão de microfone (Ctrl+M), com sounddevice
  e as DLLs do PortAudio embutidas no .exe. O Wolf já testou falando e
  funcionou.
- TAREFA C (feita): caixa de digitar com cantos arredondados, texto de
  apoio, menu do botão direito (Recortar/Copiar/Colar/Selecionar tudo +
  correções), Ctrl+A/Z/Y e coluna centralizada com 820 px.
- Consertado depois: os cantos saíam como QUADRADOS (o fundo do Label
  preenchia o quadrado todo; a imagem agora é pintada inteira, sem
  transparência). Tem teste.
- NENHUMA JANELA BRANCA: existe uma função única, `_dialogo_escuro`, e é
  obrigatório usar ela (ou o `_confirmar`) para qualquer aviso, pergunta ou
  erro.
- Chave de API: campo de chave RESERVA na aba Chave, troca automática
  quando o Google recusa a chave principal (_falha_de_chave,
  _tentar_com_reserva) e janela de aviso com botão para criar chave nova.
- Botão direito na caixa vazia: o texto de apoio (um Label por cima do
  Text) engolia os cliques; agora _clique_no_apoio e _menu_no_apoio os
  repassam.
- Menu posicionado com _tela_virtual() (winfo_screenwidth só devolve o
  monitor principal, e o menu pulava de tela).
- Criados verificar.bat/verificar.py (testes de tela automáticos + pyflakes;
  ele também é o "porteiro" das regras acima) e "3 - Gerar EXE.bat".
- Os prints e scripts de teste ficam em `_tmp\` (ignorada pelo Git).
- Regra: janela de teste SEMPRE no segundo monitor (X >= 1950).
- .exe novo gerado em dist\ e copiado para a Área de Trabalho do Wolf; os
  antigos foram para _arquivo_morto\ (nada foi apagado, só movido).
- Sobras antigas (_run*.py, backups, logs) estão em _arquivo_morto\ (ignoradas
  pelo Git; não use nem apague).
- Tudo está commitado no Git. Última verificação: TUDO CERTO.

O QUE AINDA NÃO FOI FEITO (detalhes no PROXIMOS-PASSOS.md)
- TAREFA D do PLANO-NOVAS-FUNCOES.md: Configurações em 4 abas (Memória,
  Conversa, Chaves, Ajuda).
- Nada do IDEIAS.md foi implementado ainda (salvar resposta em .txt,
  fontes citadas, perguntas para continuar, procurar nas conversas, etc.).
- O código só existe neste computador (sem repositório remoto).

COMO VOCÊ DEVE TRABALHAR (detalhes no PASSO-A-PASSO.md)
1. Ache a CAUSA do problema no código e me diga qual é, antes de mudar.
2. Faça a MENOR mudança possível. Nada de reescrever o arquivo inteiro e nada
   de "aproveitar para melhorar" o que eu não pedi.
3. Quando der, crie antes um teste novo no verificar.py que falharia sem a
   correção.
4. Rode verificar.bat. Só diga que terminou se a última linha for
   "TUDO CERTO" e não houver nenhum [FALHA].
5. Se a mudança afeta o programa que uso pelo atalho da Área de Trabalho,
   rode "3 - Gerar EXE.bat" e copie dist\Eye of Thundera.exe para a Área de
   Trabalho (guarde o antigo em _arquivo_morto\). Me avise se fez isso.
6. Faça um commit no Git com mensagem clara em português.
7. Atualize o HISTORICO-DE-MUDANCAS.md com o que você baixou, modificou,
   adicionou, removeu ou moveu (a entrada mais nova fica em cima).
8. Nunca apague arquivos meus (mova para _arquivo_morto), nunca mexa em
   %LOCALAPPDATA%\Eye of Thundera (minhas conversas, memória e chaves) e nunca
   escreva chave de API em arquivo do projeto.
9. Se instalar ou remover uma biblioteca: fixe a versão exata em
   requirements.txt (ou requirements-dev.txt), atualize o
   requirements-lock.txt e registre no histórico.
10. NUNCA abra janela de teste no meu monitor principal: o segundo monitor
   começa em X=1920. Use geometria "+2000+100" (o verificar.py já faz
   isso) e, para printar, use PrintWindow (o ImageGrab no segundo monitor
   devolve preto).

AO TERMINAR, ME RESPONDA ASSIM (curto e simples)
- O que estava errado.
- O que você mudou.
- Como eu confiro com os meus olhos.
- O que você NÃO conseguiu testar.

PRIMEIRA TAREFA
Confirme que leu os 4 arquivos, rode o verificar.bat e me diga o resultado.
Depois me peça para fazer uma pergunta real no programa, me conte o que
você achou de bom e de ruim, e pergunte o que eu quero criar agora.
```
