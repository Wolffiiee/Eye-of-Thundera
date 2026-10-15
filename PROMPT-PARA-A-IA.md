# Prompt para colar na IA que programa

Copie TUDO do bloco abaixo e cole no início da conversa com a IA (ou sempre
que abrir uma conversa nova com ela).

```
Você vai continuar o trabalho num programa meu chamado "Pesquisa IA"
(Python 3.12 + tkinter). Meu apelido é Wolf; pode me chamar assim. Eu não sei
programar, então siga um método e me explique tudo em português simples, sem
jargão.

ONDE ESTÁ O PROJETO
A ÚNICA pasta oficial é:
    C:\Projetos\PesquisaIA
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

RESUMO DO QUE O CLAUDE JÁ FEZ (você continua de onde ele parou)
- Projeto movido para fora do OneDrive; .venv recriado do zero (Python 3.12).
- Bibliotecas com versão fixa: requirements.txt (programa),
  requirements-dev.txt (pyinstaller e pyflakes) e requirements-lock.txt
  (lista completa de tudo que está instalado). httpx foi incluído.
- Bug da seleção de texto corrigido: clicar em qualquer lugar desfaz a
  seleção. Duplo clique seleciona a palavra e triplo clique seleciona o texto
  inteiro da bolha (novidade de 15/10).
- Cliques globais agora passam por um sistema único (_despachar_clique,
  _registrar_clique_global, _remover_clique_global). É PROIBIDO usar
  unbind_all("<Button-1>") ou criar novos bind_all de clique.
- Criados verificar.bat/verificar.py (testes de tela automáticos + pyflakes)
  e "3 - Gerar EXE.bat" (gera o .exe).
- .exe novo gerado em dist\ e copiado para a Área de Trabalho do Wolf; o
  antigo foi para _arquivo_morto\ (nada foi apagado do projeto, só movido).
- Sobras antigas (_run*.py, backups, logs) estão em _arquivo_morto\ (ignoradas
  pelo Git; não use nem apague).
- Tudo está commitado no Git. Última verificação: TUDO CERTO.

COMO VOCÊ DEVE TRABALHAR (detalhes no PASSO-A-PASSO.md)
1. Ache a CAUSA do problema no código e me diga qual é, antes de mudar.
2. Faça a MENOR mudança possível. Nada de reescrever o arquivo inteiro e nada
   de "aproveitar para melhorar" o que eu não pedi.
3. Quando der, crie antes um teste novo no verificar.py que falharia sem a
   correção.
4. Rode verificar.bat. Só diga que terminou se a última linha for
   "TUDO CERTO" e não houver nenhum [FALHA].
5. Se a mudança afeta o programa que uso pelo atalho da Área de Trabalho,
   rode "3 - Gerar EXE.bat" e copie dist\Pesquisa IA.exe para a Área de
   Trabalho (guarde o antigo em _arquivo_morto\). Me avise se fez isso.
6. Faça um commit no Git com mensagem clara em português.
7. Atualize o HISTORICO-DE-MUDANCAS.md com o que você baixou, modificou,
   adicionou, removeu ou moveu (a entrada mais nova fica em cima).
8. Nunca apague arquivos meus (mova para _arquivo_morto), nunca mexa em
   %LOCALAPPDATA%\PesquisaIA (minhas conversas, memória e chaves) e nunca
   escreva chave de API em arquivo do projeto.
9. Se instalar ou remover uma biblioteca: fixe a versão exata em
   requirements.txt (ou requirements-dev.txt), atualize o
   requirements-lock.txt e registre no histórico.

AO TERMINAR, ME RESPONDA ASSIM (curto e simples)
- O que estava errado.
- O que você mudou.
- Como eu confiro com os meus olhos.
- O que você NÃO conseguiu testar.

PRIMEIRA TAREFA
Confirme que leu os 4 arquivos, rode o verificar.bat e me diga o resultado.
Depois me peça para fazer uma pergunta real no programa (o Claude não
conseguiu testar isso) e pergunte o que eu quero corrigir ou criar.
```
