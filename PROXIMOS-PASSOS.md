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
- Verificar se os controles carregam, podem ser alterados e salvam corretamente; em Personalização, trocar de tema, fechar e reabrir para confirmar que a escolha permanece.
- Conferir se as chaves aparecem mascaradas e se o texto de ajuda é claro.
- Testar edição e exportação de memória somente com cuidado para não alterar dados reais sem autorização.

## Prioridade 3 — melhorar a experiência visual

- Simplificar a barra de escrita: os quatro botões Web, Pesquisa séria, Privada e Resumo do dia competem por atenção. Considerar agrupar opções secundárias em um menu, mantendo os estados ativos visíveis.
- Na aba Chaves, agrupar o botão de ativação de cada provedor com o cartão da respectiva chave; hoje o controle do Gemini fica separado do cartão da chave.
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

Não fazer uma grande reescrita da interface de uma vez. Não apagar arquivos, dados de conversa, memória ou chaves. Toda correção de comportamento deve ter uma verificação que detecte a regressão.
