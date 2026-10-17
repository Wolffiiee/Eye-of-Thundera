# Onde paramos

Atualizado em 17/10/2026, após acrescentar a leitura de PDF, o foco preso no diálogo e avisos de erro que duram mais.

## Resumo do estado atual

A rodada mais recente acrescentou a **leitura de PDF** arrastado para a conversa. O arquivo vira texto **no próprio computador** (biblioteca `pypdf`, no módulo `pdf_leitor.py`) e o texto entra na caixa de digitar para o usuário conferir e enviar quando quiser — nada é enviado à IA antes do Enter. O arquivo viaja da tela para o Python em pedaços base64, e os casos ruins (PDF com senha, corrompido, grande demais ou digitalizado sem texto) recebem aviso claro, sem travar a janela. O `pypdf` entrou no `requirements.txt`, nos dois `.spec` do PyInstaller e na verificação automática.

Também nesta rodada: o **foco do diálogo** de Configurações agora fica preso dentro da janela enquanto ela está aberta (Tab não escapa para a tela de trás), entra no diálogo ao abrir e volta ao botão que o abriu ao fechar; **avisos de erro** ficam 8 segundos na tela (o normal fica 4,2 s) e podem ser fechados com um clique; e testes novos confirmam que a resposta da IA, a galeria e a voz sempre liberam a tela. Na acessibilidade, os botões e links de “sites consultados” e o campo de pergunta ganharam rótulos e navegação por teclado.

A rodada anterior (paletas e seleção de texto) está descrita abaixo. O logger de erros continua mascarando padrões conhecidos de credenciais; a cobertura não garante remover todo segredo de mensagens inesperadas.

A aba Personalização oferece dez temas: Clássico Dark, Purpurina, Amethyst, Ocean, Forest, Aurora, Pôr do Sol, Rosa Chá, Grafite Dourado e Thundera. As paletas ficam centralizadas em `TEMAS_UI`; o backend valida os nomes e índices pela lista equivalente `TEMAS_VALIDOS`. Testes isolados confirmam gravação e leitura dos temas, rejeição de índices inválidos e contraste de texto de pelo menos 4,5:1 sobre o fundo.

O menu de seleção mostra os atalhos Ctrl+X/C/V/A, aceita setas, Home/End e Escape e devolve o foco à caixa de texto ao fechar. Copiar usa a API do navegador e tenta um fallback compatível com WebView; Recortar só apaga o trecho depois de confirmar a cópia. Uma simulação em modo de demonstração forçou falha e sucesso do fallback sem escrever na área de transferência real: o texto permaneceu após a falha. O clique direito agora calcula a posição do cursor pelo texto e pela geometria da caixa, sem tratar pixels como índices de caracteres. A cópia de uma seleção na resposta também informa sucesso ou falha e preserva espaços selecionados.

As capturas em modo de demonstração foram conferidas em 1180 px e 900 px; os nove cartões são acessíveis por rolagem vertical e não criam rolagem horizontal. `verificar.py` passou com 143 verificações, sem falhas nem avisos. A configuração pessoal não foi alterada; ainda falta confirmar a persistência visualmente pelo atalho real e conferir a escala do Windows acima de 100%.

O Eye of Thundera usa a interface HTML/JavaScript em web/ e a janela Python em app_web.py. O atalho real da Área de Trabalho é Eye of Thundera.lnk e aponta para .venv/Scripts/pythonw.exe com o argumento app_web.py, usando D:/Projetos/PesquisaIA como pasta de trabalho.

### Problema encontrado e corrigido nesta rodada

O menu anterior iniciava a cópia de forma assíncrona e apagava o texto imediatamente, mesmo quando a área de transferência recusava a cópia. O novo fluxo só recorta após sucesso, comunica falhas, preserva o intervalo escolhido enquanto o menu está em foco e oferece fallback para WebView. O menu também recebeu atalhos visíveis e navegação por teclado. A antiga reserva de posição para correções usava `offsetX` (pixels) como se fosse um índice de caractere; foi substituída por medição do texto em uma caixa espelhada.

Um commit recente inseriu uma chave de fechamento extra em web/app.js, imediatamente depois da função abaChaves. O Node.js reportava SyntaxError: Unexpected token '}' na linha 1278. Como o navegador não consegue interpretar o arquivo JavaScript, nenhuma função de inicialização ou registro de cliques era executada: a janela abria, mas os botões não respondiam.

A chave extra foi removida. Também foram corrigidos um texto quebrado na descrição do Gemini e uma duplicação na atualização das datas da memória.

A revisão seguinte encontrou que a aba Personalização existia no JavaScript, mas faltava no HTML; o backend também ignorava tema/temaIdx ao salvar, as cores usavam variáveis CSS que a interface não consumia e a seleção não era aplicada na abertura. Após o teste manual, surgiu mais um defeito: `Ponte.iniciar()` não incluía tema/temaIdx no estado inicial e a interface voltava ao Clássico Dark mesmo com Ocean salvo. Corrigido para retornar `self._cfg_curta()` e incluído teste automatizado que verifica os cinco temas também no payload de inicialização. Corrigido: a aba agora aparece em Configurações, os cinco temas (Clássico Dark, Purpurina, Amethyst, Ocean, Forest) usam as variáveis CSS reais, são salvos pelo backend e reaplicados ao iniciar. A troca é imediata e a aba não mostra um botão Salvar desnecessário. Também foi corrigido o salvamento de respostas: a função deixou de criar uma raiz Tkinter dentro da thread da ponte e passou a usar o diálogo nativo da janela pywebview; o teste automatizado usa uma janela falsa e um arquivo temporário.

A verificação automática agora executa node --check web/app.js quando Node.js está disponível. O contador final também foi corrigido: antes imprimia TESTES: 0 mesmo depois de registrar dezenas de verificações; agora imprime VERIFICACOES e conta as mensagens OK, FALHA e AVISO.

### Revisão de ações e botões — correção encontrada

A revisão estática confirmou que todos os nomes usados nas chamadas da interface existem na ponte Python e que não há IDs duplicados no HTML. Também corrigiu uma colisão de CSS: as sugestões dinâmicas de continuação estavam alterando o estilo dos cartões da página inicial; agora cada bloco tem regras próprias e a grade da página inicial vira uma coluna em janelas estreitas. A revisão encontrou ainda uma falha funcional que os testes antigos não detectavam: `enviar(texto)` ignorava o segundo argumento, então o botão dedicado “Pesquisa séria” e Ctrl+Shift+S não forçavam pesquisa profunda; só funcionavam se o alternador separado já estivesse ligado. A função agora aceita `profundo = estado.profundo` e passa esse valor à ponte. Foi adicionado um teste de regressão para o botão, o atalho e o envio normal.

### Verificação executada

- `verificar.py`: 151 verificações, 0 falhas, 0 avisos; RESULTADO: TUDO CERTO. Inclui a sintaxe JavaScript (Node.js), a leitura de PDF com arquivos sintéticos (simples e comprimido, além de PDF vazio, corrompido e não-PDF), a ponte recebendo o PDF em pedaços, o foco preso no diálogo, a liberação de `ocupado` no `finally` e a duração dos avisos de erro.
- Os testes de PDF usam apenas arquivos sintéticos em `_tmp`; nenhum documento pessoal é lido e nenhum dado real é alterado.
- A leitura de PDF depende do `pypdf`, declarado no `requirements.txt`. Se ele faltar, o programa avisa e continua funcionando; a verificação automática aponta a biblioteca faltando.
- Rodada anterior: capturas em modo demonstração conferidas em 1180 px e 900 px; falha/sucesso da cópia simulados com valores sintéticos e sem alterar a área de transferência real.
- Não foi gerado EXE porque o atalho de uso diário executa `app_web.py` diretamente.

- JavaScript: sintaxe aprovada com Node.js.
- Python: app_web.py, pesquisa_ia.py e verificar.py passaram na compilação de sintaxe.
- verificar.py: VERIFICACOES: 135 | FALHA: 0 | AVISO: 0; RESULTADO: TUDO CERTO. Inclui regressão da pesquisa profunda, menu de modos, proteção contra duplo salvamento, persistência isolada das opções, preservação de chaves e campos permitidos, cinco temas, sanitização de credenciais com valores sintéticos, salvar resposta via diálogo pywebview e regras responsivas/acessíveis, sem tocar no config.json real.
- Teste de abertura: o comando usado pelo atalho foi iniciado novamente, a janela com título Eye of Thundera ficou visível no Windows e não foi criado erro.log.
- O usuário confirmou que a validação manual da janela real está em ordem: Nova conversa, Configurações, abas, alternância Web e tema Ocean.
- Pesquisa séria, Privada e Resumo do dia ficam em “Mais”; nesta rodada, o envio único com pesquisa profunda também foi movido para o menu, reduzindo um botão permanente. `Ctrl+Shift+S` continua enviando com pesquisa profunda e aparece na Ajuda.
- O rascunho de novas chaves sobrevive à troca de abas e é limpo após salvar com sucesso. Trocar o tema salva apenas o tema, sem confirmar opções de conversa não salvas.
- O estado atual do Git contém mudanças apenas nos arquivos do Eye of Thundera descritos nesta rodada, além das alterações preexistentes do plugin OpenCode e de `show.png`, que devem permanecer fora do commit.
- O usuário confirmou que o menu “Mais” e o cartão Gemini ficaram bonitos e funcionais.
- O salvamento das configurações mostra “Salvando...”, bloqueia cliques duplicados e desativa temporariamente os controles da aba para não perder alterações concorrentes. Um `finally` reabilita os controles após falha; mensagens de erro ficam visíveis no rodapé. A gravação de `config.json` usa arquivo temporário + `os.replace`, e o teste isolado confirma que uma falha simulada preserva a versão anterior.
- Teste isolado cobre persistência das opções, preservação da chave principal quando o campo fica vazio, atualização da chave reserva e rejeição de campos não permitidos.
- Configurações: foco de teclado destacado, abas podem rolar horizontalmente e o corpo permanece rolável em janelas estreitas/baixas; a interface respeita `prefers-reduced-motion`. O diálogo tem nome acessível e declara modalidade.
- `show.png` aparece como excluído no diretório de trabalho. Não foi alterado nem incluído no commit desta rodada.

## Arquivos centrais

- README.md: entrada principal e mapa do projeto.
- INSTRUCOES-PARA-IA.md: regras obrigatórias para quem altera o código.
- PASSO-A-PASSO.md: método de diagnóstico, correção e teste.
- HISTORICO-DE-MUDANCAS.md: registro cronológico das mudanças.
- PROXIMOS-PASSOS.md: tarefas pendentes confirmadas.
- web/LEIA-ME.md: detalhes da interface e da ponte pywebview.
- pdf_leitor.py: leitura local de PDF (usa `pypdf` quando instalado).

## Dados e segurança

Os dados do usuário ficam em %LOCALAPPDATA%/PesquisaIA, fora do repositório. Não ler, alterar ou apagar os dados reais durante testes. Use pastas temporárias em _tmp. Não exiba chaves de API nem as grave em código, logs ou commits.

## Próximos passos imediatos

1. Fechar e reabrir o Eye of Thundera pelo atalho da Área de Trabalho para carregar a versão atualizada da interface.
2. Testar a leitura de PDF: arrastar um PDF com texto para a janela e conferir se o texto aparece na caixa para revisão antes de enviar. Testar também um PDF digitalizado (deve avisar, sem travar).
3. Confirmar visualmente que a barra principal tem Web, Mais, microfone e Enviar; dentro de Mais, conferir “Modo profundo”, “Enviar com pesquisa profunda”, “Privada” e “Resumo do dia”.
4. Em Configurações > Chaves, digitar um texto de teste que não seja uma chave real, trocar para outra aba e voltar: o rascunho deve permanecer. Apagar esse texto de teste sem salvar. Não exibir nem compartilhar chaves reais.
5. Se quiser confirmar a persistência no uso real, escolher uma das novas paletas pelo atalho e reabrir a aplicação; os dados de configuração real não foram alterados durante esta rodada.
6. Conferir a interface em escala do Windows acima de 100%; nenhuma pergunta à IA é necessária.
7. Se algum clique falhar, consultar %LOCALAPPDATA%/PesquisaIA/erro.log e registrar o erro sem incluir credenciais.

## Estado do Git

As alterações desta rodada abrangem a interface, o backend de temas, verificações, roteiro de capturas e documentos. `show.png` já aparecia como excluído antes desta rodada; foi preservado como está e deve ficar fora do commit. Confira `git status` antes de qualquer outra mudança.
