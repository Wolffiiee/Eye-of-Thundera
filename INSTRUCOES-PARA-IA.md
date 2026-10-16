# Instruções para IA — Eye of Thundera

Atualizado em 16/10/2026. Leia README.md e ONDE-PARAMOS.md antes de mexer no código.

## Estado atual e arquitetura

O programa em uso é a interface HTML/JavaScript aberta por app_web.py com pywebview. O atalho da Área de Trabalho aponta para .venv/Scripts/pythonw.exe, com app_web.py como argumento e D:/Projetos/PesquisaIA como pasta de trabalho. Não presuma que dist/Eye of Thundera.exe é o programa em uso.

- app_web.py: janela, ponte Python/JavaScript, integração com o motor.
- web/index.html, web/app.js, web/estilo.css: interface.
- pesquisa_ia.py: motor compartilhado de conversa, pesquisa, chaves e funções legadas. Embora a interface Tkinter esteja aposentada, o arquivo ainda contém código antigo e não deve ser apagado nem reescrito inteiro.
- memoria.py, roteador.py, voz.py: memória, decisão de modo e voz.
- verificar.py: verificação automatizada.
- Dados pessoais: %LOCALAPPDATA%\PesquisaIA, fora do repositório.

## Regras obrigatórias

1. Leia git status --short e git log -5 antes de editar. Nunca sobrescreva mudanças não rastreadas ou arquivos que já existiam sem entender o motivo.
2. Ache a causa no código antes de corrigir. Faça mudanças pequenas, com contexto suficiente para reverter.
3. Nunca apague dados, chaves, histórico, memória, backups ou arquivos do usuário. Não inclua arquivos temporários preexistentes em commits.
4. Nunca grave nem mostre chaves de API em código, logs, documentação ou commits.
5. Testes de memória, histórico e configuração devem usar arquivos em _tmp e restaurar os caminhos e caches no fim. Nunca apontar testes para os dados reais.
6. Depois de alterar código, rode .venv\Scripts\python.exe verificar.py. A última linha deve ser RESULTADO: TUDO CERTO, sem falhas.
7. Alterações em web/app.js precisam passar na verificação de sintaxe JavaScript. Uma única chave extra impede o arquivo inteiro de executar e deixa a janela aberta sem botões funcionais.
8. Quando a mudança afetar a interface, abra a aplicação e valide visualmente. Testes estáticos não substituem a conferência manual.
9. Atualize HISTORICO-DE-MUDANCAS.md e ONDE-PARAMOS.md. Faça commit somente dos arquivos relacionados à mudança e explique a alteração em português simples.
10. Não faça uma grande reescrita da interface ou do motor sem dividir em etapas e validar cada etapa.

## Armadilhas conhecidas da interface atual

- A ponte pywebview é assíncrona. As chamadas da tela devem passar por chamar(), que espera window.pywebview.api ficar pronta.
- Não exponha a janela nativa como atributo público da ponte. Use o atributo privado _janela; o pywebview pode percorrer objetos públicos e entrar em recursão em objetos nativos.
- O JavaScript deve iniciar depois de pywebviewready. Preserve o mecanismo de espera da ponte.
- Não esconda exceções importantes com except pass. Erros de execução devem ficar visíveis em avisos ou no log de erro.
- Links exibidos na interface precisam ser validados; nunca aceite javascript: como URL de navegação.
- A memória tem cache no módulo. Em testes que mudem o caminho do arquivo, limpe e restaure o cache junto com os caminhos. Use sempre as funções de mesclagem de memoria.py; não acrescente fatos diretamente com append.
- O código Tkinter legado ainda tem menus e eventos compartilhados: nunca use unbind_all("<Button-1>"), pois isso remove os ouvintes de outros menus.
- A tela de demonstração usa --demo. Não use --voz a menos que seja intencional ativar o microfone real.

## Comandos úteis

- Verificar: .venv\Scripts\python.exe verificar.py
- Verificar sintaxe JS manualmente, se Node.js estiver instalado: node --check web\app.js
- Estado do Git: git status --short
- Histórico recente: git log -5 --oneline
- Diferenças: git diff

## Encerramento de cada tarefa

Relate o que estava errado, a causa, os arquivos alterados, os testes executados, o que não foi testado e como o usuário pode conferir. Não diga que está totalmente resolvido sem validar o caminho que o usuário realmente usa.
