# Próximos passos

Atualizado em 16/10/2026. Este documento contém pendências reais; o histórico detalhado fica em HISTORICO-DE-MUDANCAS.md.

## Prioridade 1 — validar a correção da interface

- Corrigido na revisão de 16/10: o botão dedicado “Pesquisa séria” e o atalho Ctrl+Shift+S chamavam `enviar(undefined, true)`, mas a função ignorava o segundo argumento e enviava só o estado do alternador “Pesquisa séria”. Agora o argumento chega à ponte Python; o verificador cobre o botão, o atalho e o envio normal.
- Fechar a janela que estava aberta antes da correção.
- Abrir Eye of Thundera pelo atalho da Área de Trabalho.
- Conferir se Nova conversa, Configurações, Web e enviar respondem.
- Fazer uma pergunta curta somente quando o usuário estiver pronto para testar a integração com a IA.
- Testar Ctrl+S em uma resposta de exemplo, confirmar que o diálogo de salvar aparece na frente e que cancelar não gera erro.
- Se falhar, ler %LOCALAPPDATA%/PesquisaIA/erro.log e registrar o traceback sem dados secretos.

## Prioridade 2 — conferir os fluxos de configuração

- Abrir cada aba: Memória, Conversa, Chaves, Ajuda e Personalização.
- [x] Teste isolado confirma persistência dos controles, preservação da chave salva quando o campo fica vazio e rejeição de campos de chave não permitidos.
- [x] Preservar chaves digitadas no rascunho ao trocar de aba; limpar o rascunho temporário depois de salvar com sucesso.
- [x] Alterar o tema sem salvar opções de conversa que ainda estejam em rascunho.
- [x] Durante o salvamento, bloquear temporariamente os controles da aba para evitar perder edições; garantir que eles sejam reabilitados mesmo se ocorrer uma falha.
- [ ] Validar visualmente Configurações em janela menor e escala do Windows acima de 100%; as regras responsivas e os testes estáticos já foram adicionados.
- [x] Melhorar a hierarquia dos cartões, destacar discretamente o Gemini principal, esclarecer descrições e colocar o seletor de tema em um cartão próprio sem alterar o tema Ocean.
- Conferir se as chaves aparecem mascaradas e se o texto de ajuda é claro.
- Testar edição e exportação de memória somente com cuidado para não alterar dados reais sem autorização.

## Prioridade 3 — melhorar a experiência visual

- [x] Agrupar Pesquisa séria, Privada e Resumo do dia em “Mais”, mantendo indicação dos modos ativos e atalhos existentes.
- [x] Mover o envio único com pesquisa profunda para “Mais”; o atalho Ctrl+Shift+S continua ativo e foi documentado na Ajuda.
- [ ] Reabrir o app e confirmar visualmente a nova disposição do menu, além de conferir a troca de abas após digitar uma chave (sem precisar salvar nem exibir a chave aqui).
- [x] Agrupar “Usar o Gemini (principal)” no cartão da chave correspondente. Conferir visualmente na aba Chaves.
- A correção de estilo dos cartões de sugestão da página inicial já foi aplicada; confirmar que a grade se adapta bem em janela estreita.
- Padronizar acentuação, pontuação, nomes de controles e descrições em português brasileiro.
- Garantir foco visível, rótulos acessíveis, estados de carregamento e mensagens de erro que não desapareçam antes de poderem ser lidas.
- Verificar a janela de Configurações em resolução menor e com escala de tela do Windows acima de 100%.

## Prioridade 4 — manter os documentos coerentes

- Usar README.md como ponto de entrada.
- Atualizar ONDE-PARAMOS.md depois de cada rodada.
- Registrar mudanças em HISTORICO-DE-MUDANCAS.md.
- Manter IDEIAS.md para ideias ainda não implementadas, marcando claramente o que já existe.
- Tratar documentos de planos antigos como históricos, não como descrição do estado atual.

## Regras de segurança

- [x] O logger mascara padrões conhecidos de credenciais antes de gravar mensagens no `erro.log`; o teste usa valores sintéticos e não chama APIs.
- [ ] Se surgirem novos provedores ou formatos de autenticação, revisar `_sanitizar_erro_log()` e adicionar exemplos sintéticos. A redação por padrões não é garantia absoluta: não incluir segredos em mensagens de erro.
- Não fazer uma grande reescrita da interface de uma vez. Não apagar arquivos, dados de conversa, memória ou chaves. Toda correção de comportamento deve ter uma verificação que detecte a regressão.
