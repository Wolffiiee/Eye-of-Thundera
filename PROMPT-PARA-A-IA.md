# Prompt para colar na IA que programa

Copie TUDO do bloco abaixo e cole no início da conversa com a IA
(ou sempre que abrir uma conversa nova com ela).

```
Você vai trabalhar num programa meu chamado "Pesquisa IA" (Python 3.12 +
tkinter). Eu não sei programar, então preciso que você siga um método e me
explique tudo em português simples, sem jargão.

ONDE ESTÁ O PROJETO
O projeto foi movido hoje (14/10/2026) para:
    C:\Projetos\PesquisaIA
A pasta antiga ("Projeto Padrão (ANTIGO - pode apagar)", dentro do OneDrive)
é só cópia de segurança: NÃO trabalhe nela.

ANTES DE QUALQUER COISA, LEIA (nesta ordem), na pasta do projeto:
1. INSTRUCOES-PARA-IA.md  -> regras obrigatórias e armadilhas já achadas
2. PASSO-A-PASSO.md       -> o método que você deve seguir, com um exemplo
3. HISTORICO-DE-MUDANCAS.md -> tudo o que foi baixado, modificado,
                              adicionado, removido e movido hoje
Depois rode `git status` e `git log --oneline -5`.

O QUE JÁ FOI FEITO HOJE (resumo; detalhes no histórico)
- Pasta movida para fora do OneDrive; ambiente .venv recriado do zero.
- Versões das bibliotecas fixadas em requirements.txt (e httpx incluído);
  ferramentas de desenvolvimento em requirements-dev.txt (pyinstaller e
  pyflakes foram instalados).
- Corrigido o bug da seleção de texto (a seleção não sumia ao clicar fora).
- Criado um sistema único para cliques globais (_despachar_clique,
  _registrar_clique_global, _remover_clique_global). É PROIBIDO usar
  unbind_all("<Button-1>") ou criar novos bind_all de clique.
- Removida uma função morta que citava um nome inexistente.
- Criados verificar.bat/verificar.py (conferência automática com testes de
  tela) e "3 - Gerar EXE.bat" (gera o .exe novo).
- Scripts de teste antigos (_run*.py) foram movidos para _arquivo_morto
  (não use nem apague).
- O .exe da minha Área de Trabalho foi substituído pelo novo.

COMO VOCÊ DEVE TRABALHAR (resumo do PASSO-A-PASSO.md)
1. Ache a CAUSA do problema no código e me diga qual é, antes de mudar.
2. Faça a MENOR mudança possível. Nada de reescrever o arquivo inteiro e
   nada de "aproveitar para melhorar" o que eu não pedi.
3. Quando der, crie um teste novo no verificar.py que falharia sem a
   correção.
4. Rode verificar.bat. Só diga que terminou se a última linha for
   "TUDO CERTO" e não houver nenhum [FALHA].
5. Se mudar algo que eu uso pelo atalho da Área de Trabalho, rode
   "3 - Gerar EXE.bat" e copie dist\Pesquisa IA.exe para a Área de
   Trabalho. Me avise se fez isso.
6. Faça um commit no Git com mensagem clara.
7. Atualize o HISTORICO-DE-MUDANCAS.md com o que você baixou, modificou,
   adicionou, removeu ou moveu.
8. Nunca apague arquivos meus (mova para _arquivo_morto), nunca mexa em
   %LOCALAPPDATA%\PesquisaIA (minhas conversas, memória e chaves) e nunca
   escreva chave de API em arquivo do projeto.
9. Se instalar ou remover uma biblioteca, fixe a versão exata em
   requirements.txt (ou requirements-dev.txt) e registre no histórico.

AO TERMINAR, ME RESPONDA ASSIM (curto e simples)
- O que estava errado.
- O que você mudou.
- Como eu confiro com os meus olhos.
- O que você NÃO conseguiu testar.

PRIMEIRA TAREFA
Confirme que leu os 3 arquivos, rode o verificar.bat e me diga o resultado.
Depois pergunte o que eu quero corrigir ou criar.
```
