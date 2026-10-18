# Próximos passos

Atualizado em 18/10/2026. Este documento contém pendências reais; o histórico detalhado fica em HISTORICO-DE-MUDANCAS.md. **Plugins (Prioridade 5) e Sincronização (Prioridade 6) estão implementados — todas as sugestões originais estão prontas.**

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
- [x] Testar manualmente arrastando um PDF de verdade (com texto) e um digitalizado pelo atalho real. **Confirmado pelo usuário em 18/10: "já foram feitos e estão funcionando".**
- [ ] (Opcional, etapa futura) Anexar imagens depende de OCR/visão e de consentimento explícito; ainda não iniciado.

## Prioridade 3.6 — contraste dos temas (corrigido)

- [x] O teste de contraste varre **os 10 temas e os 4 fundos de cada um**, o **texto do botão em repouso e no hover**, o **link** (`--azul-2`), o `--azul` como borda (mínimo 3,0:1) e a **bolinha do interruptor**.
- [x] A viabilidade foi medida antes de implementar (como pedido em `SUGESTOES-MELHORIAS-Eye-of-Thundera.md`, Prioridade 3): um script (`_tmp/planejar_cores.py`) leu as dez paletas, calculou o contraste (WCAG) e buscou o **menor ajuste** que resolve cada par, tema por tema. Os **32 pares** abaixo do mínimo foram todos corrigidos:
  - **Texto apagado** (`--texto-3`): clareado em 9 dos 10 temas (o Thundera já passava), de 1% a 20% na mistura com o branco — agora **4,60:1 ou mais** (antes entre 3,28 e 4,49:1 em 7 temas).
  - **Texto do botão** (Enviar e botão primário): duas chaves novas por tema — `--btn-texto` (branco no Clássico Dark e no Thundera, escuro nos 8 temas de acento claro) e `--btn-hover` (o fundo no hover; nos 8 claros continua o `--azul-2`, nos 2 escuros virou um tom mais fundo). Pior caso agora **4,63:1** — era 1,53:1 no Grafite Dourado e 2,69:1 no Ocean.
  - **`--azul` como borda/anel de foco**: acima de 3,0:1 em todos (Thundera 3,06:1 e Forest 3,07:1; estavam em 2,83 e 2,91).
  - **Bolinha do interruptor** (achado do teste novo): era branca fixa e desaparecia sobre o acento claro (2,2 a 3,0:1). Agora usa `--btn-texto` e o trilho desligado usa `--texto-3` — visível nos dois estados, pior caso 3,21:1.
- [x] O aviso `contraste:` do `verificar.py` sumiu: o teste deixou de ser aviso e **falha** listando o par e o valor medido; a suíte está em **162 verificações, 0 falhas, 0 avisos**.
- [x] Conferido e aprovado pelo usuário (17/10): os temas de acento claro com o texto do botão escuro ficaram bons. Voltar atrás é mexer só em `--btn-texto` e `--btn-hover` do tema — nenhuma outra cor depende disso.

## Prioridade 1 (das sugestões) — OCR local de PDF digitalizado (feito)

- [x] Viabilidade medida antes de implementar: `pytesseract` precisaria do Tesseract instalado no sistema (não é só `pip`); o OCR do Windows já vem com o sistema e leu o PDF sintético em 0,05 s por página, com as 4 frases reconhecidas.
- [x] `pdf_leitor.py` com `_texto_por_ocr()`: renderiza até 20 páginas (`pypdfium2`, ~0,1 s por página) e lê com o OCR do Windows (`winsdk`, pt-BR, com queda para os idiomas do sistema). O texto entra na caixa para revisão, como o PDF com texto.
- [x] Sem as duas bibliotecas, o aviso antigo continua valendo ("pode ser digitalizado"); `requirements.txt` e os dois `.spec` trazem as duas.
- [x] O OCR roda em **thread própria** com limite de 60 s: na thread principal, depois do pywebview, o `await` do OCR nunca volta (o `verificar.py` travou nisso até o problema ser achado).
- [x] Testes novos no `verificar.py` (OCR de 1 e 2 páginas, aviso do limite de 20 páginas, aviso quando as bibliotecas faltam) e conferência na tela com dados isolados em `_tmp`.
- [x] Testar com um PDF digitalizado de verdade (uma página de livro escaneada) e conferir a qualidade da leitura; OCR é aproximado - o texto vai para a caixa justamente para revisão. **Confirmado pelo usuário em 18/10.**

## Prioridade 8 — lembretes ("me lembra amanhã às 9h de pagar a conta")

- [x] O módulo `lembretes.py` (com plano em `PLANO-LEMBRETES.md`) estava **órfão** — nenhum arquivo o chamava, então o recurso não existia para o usuário. Agora está ligado em `Ponte.enviar`, **antes** da checagem de chave, com os métodos `lembretes_vencidos`, `lembrete_concluir` e `lembrete_adiar`.
- [x] Frases entendidas: "amanhã às 9h", "daqui a 30 minutos", "segunda às 14h30", "dia 25", "20/10 às 7h", "hoje às 18h", "depois de amanhã às 10 da noite" e "lembrete: ..."; listar com "meus lembretes" e cancelar com "cancelar lembrete 2". Frases que só *parecem* lembrete ("como me lembrar de coisas?") continuam indo para a IA.
- [x] Cartões na tela com `role="alert"`, perguntados ao abrir e **de 30 em 30 segundos**, com "Feito" e "Adiar 10 min"; cada lembrete aparece uma vez por sessão. Ficam no **alto à direita**, abaixo da barra de título, para não cobrir os botões de microfone e enviar (o defeito foi visto em captura de tela e corrigido antes do commit).
- [x] Tudo local (`%LOCALAPPDATA%/PesquisaIA/lembretes.json`), sem IA e **funcionando sem chave**. O módulo entrou nos dois `.spec` do PyInstaller, para o `.exe` distribuível incluí-lo.
- [x] Cinco testes novos no `verificar.py` (interpretador com datas fixas, armazenamento, a ponte, o envio sem chave pelo caminho de verdade e a ligação na tela/pacote), todos com arquivos em `_tmp` — nenhum dado real é lido ou alterado.
- [x] Testado e aprovado pelo usuário (17/10): o cartão aparece no alto à direita, "Feito" e "Adiar 10 min" funcionam, e os botões de microfone e enviar continuam visíveis.

## Prioridade 7 (das sugestoes) - documento longo (feito, falta teste real)
- [x] Arrastar um PDF de verdade com mais de 10 paginas, ver o cartao "documento aberto", perguntar algo e conferir se a resposta cita a pagina certa; testar "indice do documento", "resumir documento" e o botao Fechar. **Testado e aprovado pelo usuário em 18/10** com um PDF de 12 páginas gerado para o teste (`_tmp/gerar_pdf_longo.py`, apagado depois): as 4 perguntas citaram a página exata (5, 7, 11 e 12), o índice listou os 12 capítulos com as páginas e o resumo cobriu os 10 trechos com o aviso honesto de que não cobre o documento inteiro.
- Modo offline com Ollama (Prioridade 4 das sugestoes): cancelado pelo Wolf.

## Prioridade 2 (das sugestões) — busca na Memória tolerante a erro de digitação (feito)

- [x] Novo `web/busca.js`: Levenshtein iterativo + normalização NFD (acentos). "conta dluz" acha "conta de luz", "cafe" acha "café", "CONTA DE LUZ" funciona com maiúsculas, "casa" acha "casas". Roda na tela, sem Python e sem dependência — a Memória tem no máximo 200 itens, cada tecla custa poucos milissegundos.
- [x] Regra corrigida: `q.startsWith(p)` em vez de `q.includes(p) || p.includes(q)` — a direção `p.includes(q)` fazia "chocolate" achar "a" e "rato" achar "gato".
- [x] Limitação documentada: "rato" ainda acha "gato" (75% parecido, mesma conta que faz "gatu" achar "gato") — matematicamente impossível separar; decisão: manter tolerância e documentar.
- [x] `app.js` usa `busca_pontos` em `desenhar()` com ordenação por relevância; `index.html` carrega `busca.js` antes de `app.js`.
- [x] Dois testes novos no `verificar.py` (existência/regra do `busca.js` e ligação no HTML/`app.js`; e execução dos 18 casos de teste Node.js). Suíte: **172 verificações, 0 falhas, 0 avisos**.
- [x] Termos da busca **pintados** no item (`destacarTexto()` + `escaparHtml()` no `app.js`, `.destaque-busca` no CSS): mesma tolerância do `busca.js`, acentos preservados, HTML escapado; dois testes novos no `verificar.py` (estrutura + lógica Node.js). Suíte: **174 verificações, 0 falhas, 0 avisos**. Avatar da IA (lupa) removido das respostas a pedido do usuário e commitado.
- [x] Testar na tela com a Memória real: digitar um termo com erro de digitação e confirmar que o item aparece primeiro e com o termo pintado. **Confirmado pelo usuário em 18/10: "Está funcionando perfeitamente".**

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
