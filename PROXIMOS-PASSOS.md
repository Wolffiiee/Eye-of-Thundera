# Próximos passos

Atualizado em 17/10/2026. Este documento contém pendências reais; o histórico detalhado fica em HISTORICO-DE-MUDANCAS.md.

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
- [ ] Validar visualmente Configurações na escala do Windows acima de 100%; a janela de 900 px foi conferida em modo demonstração.
- [x] Melhorar a hierarquia dos cartões, destacar discretamente o Gemini principal, esclarecer descrições e colocar o seletor de tema em um cartão próprio sem alterar o tema Ocean.
- Conferir se as chaves aparecem mascaradas e se o texto de ajuda é claro.
- Testar edição e exportação de memória somente com cuidado para não alterar dados reais sem autorização.

## Prioridade 3 — melhorar a experiência visual

- [x] Agrupar Pesquisa séria, Privada e Resumo do dia em “Mais”, mantendo indicação dos modos ativos e atalhos existentes.
- [x] Mover o envio único com pesquisa profunda para “Mais”; o atalho Ctrl+Shift+S continua ativo e foi documentado na Ajuda.
- [ ] Reabrir o app pelo atalho e confirmar a persistência da troca de tema; as capturas de demonstração não alteram configuração real.
- [ ] Confirmar visualmente a nova disposição do menu e a troca de abas após digitar texto sintético no campo de chave (sem salvar nem exibir chave real).
- [x] Agrupar “Usar o Gemini (principal)” no cartão da chave correspondente. Conferir visualmente na aba Chaves.
- [x] Trocar a lista de temas por cartões com miniaturas e cinco amostras de cores; navegação por setas, Enter e Espaço.
- [x] Conferir visualmente os cartões e a mudança de paleta em modo de demonstração; a captura marca corretamente o tema mostrado.
- [x] Acrescentar Aurora, Pôr do Sol, Rosa Chá e Grafite Dourado; validar sincronização com backend, persistência isolada, índices inválidos e contraste.
- [x] Corrigir cópia/recorte para usar fallback e preservar o texto em falha; incluir atalhos no menu e navegação por teclado.
- [x] Simular falha e sucesso do fallback em modo demonstração, sem modificar a área de transferência real.
- A correção de estilo dos cartões de sugestão da página inicial já foi aplicada; confirmar que a grade se adapta bem em janela estreita.
- [x] Padronizar acentuação, pontuação, nomes de controles e descrições em português brasileiro (auditado em 17/10: corrigidos acentos que faltavam em `app_web.py`, unificada a frase de “ocupado” e a de “sem chave”; rótulos acessíveis do campo de busca, da lista de conversas e do botão “⋯”).
- [x] Garantir foco visível, rótulos acessíveis e mensagens de erro que não desapareçam antes de poderem ser lidas (erros agora duram 8 s e podem ser fechados com um clique).
- [x] Prender o foco dentro do diálogo de Configurações (Tab), trazer o foco ao abrir e devolvê-lo ao botão de origem ao fechar; Esc fecha.
- [x] Rótulos acessíveis e navegação por teclado em “sites consultados” e no campo de pergunta.
- Verificar Configurações com escala de tela do Windows acima de 100%; a janela de 900 px já foi conferida em modo demonstração.

## Prioridade 3.5 — arquivos anexados (leitura de PDF)

- [x] Leitura local de PDF arrastado para a conversa (`pdf_leitor.py`, biblioteca `pypdf`), com o texto entrando na caixa para revisão antes do envio.
- [x] Casos ruins tratados com mensagem clara: PDF com senha, corrompido, grande demais (>25 MB) e digitalizado (sem texto).
- [x] `pypdf` declarado no `requirements.txt`, nos dois `.spec` do PyInstaller e no `verificar.py`; testes com PDFs sintéticos em `_tmp`.
- [ ] Testar manualmente arrastando um PDF de verdade (com texto) e um digitalizado pelo atalho real.
- [ ] (Opcional, etapa futura) Anexar imagens depende de OCR/visão e de consentimento explícito; ainda não iniciado.

## Prioridade 3.6 — contraste dos temas (rodada de cores, aguarda decisão)

- [x] O teste de contraste agora varre **os 10 temas e os 4 fundos de cada um** (antes só checava `--texto` e `--texto-2` sobre o `--bg`). Texto principal, texto secundário e link passam em todos os temas, em todos os fundos.
- [x] A viabilidade da correção foi medida antes de implementar (como pedido em `SUGESTOES-MELHORIAS-Eye-of-Thundera.md`, Prioridade 3). Restam **32 pares** abaixo do mínimo, contados a cada execução pelo aviso `contraste:` do `verificar.py`:
  - **Texto apagado** (`--texto-3` — horário da conversa, notas e botões de ação, de 11,5 a 13 px): 7 dos 10 temas ficam entre 3,28 e 4,49:1. Precisa clarear de 2% a 14% (ex.: Clássico Dark `#70708a` → `#8989a8`).
  - **Texto branco do botão** (`--azul` no Enviar e no botão primário; `--azul-2` no hover): falha em **9 dos 10 temas** — só o Thundera passa. Pior caso: Grafite Dourado com **1,53:1** (fundo `#f1cd7d` quase branco com letra branca). Em **8 dos 10** temas resolve **só trocando a cor do texto** (branco → escuro), sem tocar em nenhuma cor do tema; Clássico Dark e Thundera precisam escurecer o acento por volta de 15%.
  - **`--azul` como borda/anel de foco** em Thundera (2,83:1) e Forest (2,91:1): abaixo dos 3,0 pedidos para elementos não textuais (WCAG 1.4.11).
- [ ] **Aguarda confirmação do usuário:** corrigir muda a aparência escolhida (cor do texto nos botões de 8 temas, texto apagado mais claro em 7). A cor dos acentos ficaria praticamente igual; a maior diferença é o texto do botão ficar escuro nos temas claros.
- [ ] Depois de aplicar: o aviso `contraste:` do `verificar.py` deve sumir (voltar a 0 avisos).

## Prioridade 8 — lembretes ("me lembra amanhã às 9h de pagar a conta")

- [x] O módulo `lembretes.py` (com plano em `PLANO-LEMBRETES.md`) estava **órfão** — nenhum arquivo o chamava, então o recurso não existia para o usuário. Agora está ligado em `Ponte.enviar`, **antes** da checagem de chave, com os métodos `lembretes_vencidos`, `lembrete_concluir` e `lembrete_adiar`.
- [x] Frases entendidas: "amanhã às 9h", "daqui a 30 minutos", "segunda às 14h30", "dia 25", "20/10 às 7h", "hoje às 18h", "depois de amanhã às 10 da noite" e "lembrete: ..."; listar com "meus lembretes" e cancelar com "cancelar lembrete 2". Frases que só *parecem* lembrete ("como me lembrar de coisas?") continuam indo para a IA.
- [x] Cartões na tela com `role="alert"`, perguntados ao abrir e **de 30 em 30 segundos**, com "Feito" e "Adiar 10 min"; cada lembrete aparece uma vez por sessão. Ficam no **alto à direita**, abaixo da barra de título, para não cobrir os botões de microfone e enviar (o defeito foi visto em captura de tela e corrigido antes do commit).
- [x] Tudo local (`%LOCALAPPDATA%/PesquisaIA/lembretes.json`), sem IA e **funcionando sem chave**. O módulo entrou nos dois `.spec` do PyInstaller, para o `.exe` distribuível incluí-lo.
- [x] Cinco testes novos no `verificar.py` (interpretador com datas fixas, armazenamento, a ponte, o envio sem chave pelo caminho de verdade e a ligação na tela/pacote), todos com arquivos em `_tmp` — nenhum dado real é lido ou alterado.
- [ ] **Testar manualmente** pelo atalho: criar um lembrete para daqui a 1 minuto e conferir o cartão, "Feito" e "Adiar 10 min"; conferir também o cartão que aparece ao abrir o programa com um lembrete já vencido.

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
