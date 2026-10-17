# Onde paramos

Atualizado em 16/10/2026, após corrigir a persistência do tema e a ação de pesquisa profunda.

## Resumo do estado atual

O Eye of Thundera usa a interface HTML/JavaScript em web/ e a janela Python em app_web.py. O atalho real da Área de Trabalho é Eye of Thundera.lnk e aponta para .venv/Scripts/pythonw.exe com o argumento app_web.py, usando D:/Projetos/PesquisaIA como pasta de trabalho.

### Problema encontrado e corrigido nesta rodada

Um commit recente inseriu uma chave de fechamento extra em web/app.js, imediatamente depois da função abaChaves. O Node.js reportava SyntaxError: Unexpected token '}' na linha 1278. Como o navegador não consegue interpretar o arquivo JavaScript, nenhuma função de inicialização ou registro de cliques era executada: a janela abria, mas os botões não respondiam.

A chave extra foi removida. Também foram corrigidos um texto quebrado na descrição do Gemini e uma duplicação na atualização das datas da memória.

A revisão seguinte encontrou que a aba Personalização existia no JavaScript, mas faltava no HTML; o backend também ignorava tema/temaIdx ao salvar, as cores usavam variáveis CSS que a interface não consumia e a seleção não era aplicada na abertura. Após o teste manual, surgiu mais um defeito: `Ponte.iniciar()` não incluía tema/temaIdx no estado inicial e a interface voltava ao Clássico Dark mesmo com Ocean salvo. Corrigido para retornar `self._cfg_curta()` e incluído teste automatizado que verifica os cinco temas também no payload de inicialização. Corrigido: a aba agora aparece em Configurações, os cinco temas (Clássico Dark, Purpurina, Amethyst, Ocean, Forest) usam as variáveis CSS reais, são salvos pelo backend e reaplicados ao iniciar. A troca é imediata e a aba não mostra um botão Salvar desnecessário. Também foi corrigido o salvamento de respostas: a função deixou de criar uma raiz Tkinter dentro da thread da ponte e passou a usar o diálogo nativo da janela pywebview; o teste automatizado usa uma janela falsa e um arquivo temporário.

A verificação automática agora executa node --check web/app.js quando Node.js está disponível. O contador final também foi corrigido: antes imprimia TESTES: 0 mesmo depois de registrar dezenas de verificações; agora imprime VERIFICACOES e conta as mensagens OK, FALHA e AVISO.

### Revisão de ações e botões — correção encontrada

A revisão estática confirmou que todos os nomes usados nas chamadas da interface existem na ponte Python e que não há IDs duplicados no HTML. Ela também encontrou uma falha funcional que os testes antigos não detectavam: `enviar(texto)` ignorava o segundo argumento, então o botão dedicado “Pesquisa séria” e Ctrl+Shift+S não forçavam pesquisa profunda; só funcionavam se o alternador separado já estivesse ligado. A função agora aceita `profundo = estado.profundo` e passa esse valor à ponte. Foi adicionado um teste de regressão para o botão, o atalho e o envio normal.

### Verificação executada

- JavaScript: sintaxe aprovada com Node.js.
- Python: app_web.py, pesquisa_ia.py, memoria.py e roteador.py passaram na compilação de sintaxe.
- verificar.py: VERIFICACOES: 127 | FALHA: 0 | AVISO: 0; RESULTADO: TUDO CERTO. Inclui teste de regressão para o botão/atalho de pesquisa profunda, testes isolados dos cinco temas e teste de salvar resposta via diálogo pywebview, sem tocar no config.json real.
- Teste de abertura: o comando usado pelo atalho foi iniciado novamente, a janela com título Eye of Thundera ficou visível no Windows e não foi criado erro.log.
- Ainda falta confirmar manualmente que os cliques respondem. A suíte automatizada e a abertura da janela não substituem esse teste manual completo.

## Arquivos centrais

- README.md: entrada principal e mapa do projeto.
- INSTRUCOES-PARA-IA.md: regras obrigatórias para quem altera o código.
- PASSO-A-PASSO.md: método de diagnóstico, correção e teste.
- HISTORICO-DE-MUDANCAS.md: registro cronológico das mudanças.
- PROXIMOS-PASSOS.md: tarefas pendentes confirmadas.
- web/LEIA-ME.md: detalhes da interface e da ponte pywebview.

## Dados e segurança

Os dados do usuário ficam em %LOCALAPPDATA%/PesquisaIA, fora do repositório. Não ler, alterar ou apagar os dados reais durante testes. Use pastas temporárias em _tmp. Não exiba chaves de API nem as grave em código, logs ou commits.

## Próximos passos imediatos

1. Fechar qualquer janela de demonstração ou versão antiga e abrir novamente o atalho Eye of Thundera na Área de Trabalho.
2. Testar Nova conversa, Configurações, alternância Web e envio de uma pergunta curta. Não enviar uma pergunta real sem confirmar que a chave está configurada e que o usuário deseja gastar cota.
3. Se qualquer clique falhar, consultar %LOCALAPPDATA%/PesquisaIA/erro.log e registrar o erro sem incluir chaves.
4. Conferir manualmente as cinco abas de Configurações e validar se as descrições correspondem aos controles reais; confirmar que a escolha de tema permanece após reabrir.
5. Avaliar melhorias visuais em mudanças separadas, depois de validar os fluxos principais.

## Estado do Git

Antes de continuar, confira git status. Os arquivos de diagnóstico não rastreados check_lnk.py, check_lnk2.py, test_shortcut.py, show.png, verify_err.txt e verify_out.txt já existiam antes desta revisão; não foram apagados nem incluídos no commit automaticamente.
