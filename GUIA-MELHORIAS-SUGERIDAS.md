# Roteiro de melhorias sugeridas — Eye of Thundera

**Tipo:** guia de trabalho para uma futura IA. Este documento descreve mudanças possíveis; não autoriza executá-las automaticamente.
**Preparado em:** 17/10/2026.
**Aplicação em uso:** interface web em `app_web.py` + `web/`, aberta pelo atalho da Área de Trabalho. Não presumir que `dist/Eye of Thundera.exe` seja o aplicativo usado no dia a dia.

## Como usar este roteiro

1. Antes de implementar qualquer etapa, leia `README.md`, `ONDE-PARAMOS.md`, `INSTRUCOES-PARA-IA.md`, `PASSO-A-PASSO.md` e `HISTORICO-DE-MUDANCAS.md`, nessa ordem.
2. Confira `git status --short` e `git log -5 --oneline`. Preserve alterações, exclusões e arquivos não rastreados que já existiam.
3. Faça uma etapa de cada vez. As etapas 1 e 2 são validações manuais pendentes; as etapas 3 a 5 são melhorias de produto opcionais.
4. Antes de editar, inspecione o código atual: este guia é um plano, não substitui o diagnóstico. Requisitos e interface podem ter mudado desde sua criação.
5. Após alterações de código, acrescente verificações de regressão e rode `.venv\Scripts\python.exe verificar.py`. Não rode ações contra dados reais.
6. Se a interface mudar, valide visualmente a interface real ou, quando isso não for possível, declare claramente que só houve validação em demonstração. Atualize `ONDE-PARAMOS.md` e `HISTORICO-DE-MUDANCAS.md`.
7. Não faça commit automaticamente: siga o pedido explícito do usuário e inclua somente arquivos da etapa executada.

## Estado conhecido na preparação

- A interface usada é HTML/JavaScript em `web/`, integrada pelo `app_web.py` via pywebview.
- Já há foco de teclado, rolagem e regras responsivas nas Configurações. Os cartões de tema permitem setas, Enter e Espaço.
- A tela principal já tem lista e busca de conversas, pesquisa web/profunda, modo privado, resumo do dia, microfone, envio, sugestões após resposta e operações de copiar/salvar.
- O carregamento de arquivos já aceita `.txt`, `.md`, `.csv` e `.json`; leitura de PDF e imagens consta como incompleta em `IDEIAS.md`.
- Pendências registradas em `PROXIMOS-PASSOS.md`: confirmar o tema pelo atalho real, conferir a interface com escala do Windows acima de 100%, revisar a nova disposição do menu e a grade em janela estreita, e padronizar textos/estados.
- Na preparação deste guia, `git status --short` também indicava arquivos alterados/excluídos preexistentes, incluindo `show.png`, e `PLANO-RODADA-2026-10-17.md` não rastreado. Preserve-os e reavalie o estado quando começar.

## Etapa 1 — validar a interface real e a persistência do tema

**Objetivo:** confirmar que a versão aberta pelo atalho carrega a interface atual, que os controles respondem e que a escolha de tema persiste após reiniciar.

**Procedimento:**

1. Não altere configuração, conversa, chave ou memória real. Feche a janela existente e abra o atalho `Eye of Thundera.lnk`.
2. Confira visualmente: Nova conversa, Configurações, alternância Web, menu “Mais”, microfone sem iniciar gravação e botão Enviar sem submeter pergunta.
3. Em Configurações > Personalização, selecione um tema de teste somente se o usuário aceitar essa mudança na configuração real. Caso contrário, limite-se a conferir o tema já selecionado.
4. Se autorizado a trocar, feche e reabra pelo atalho e confirme a persistência. Restaure o tema anterior caso a mudança tenha sido apenas temporária.
5. Verifique configurações em escala do Windows acima de 100% e em janela estreita/baixa, observando cortes, rolagem, foco e botões inacessíveis.
6. Faça a checagem de campo de chave apenas com texto sintético: digite, troque de aba, volte e apague sem salvar. Não abra, copie ou registre chaves reais.

**Aceite:** a janela abre sem falha de interface; controles essenciais respondem; tema permanece após reabertura (se alterado com autorização); layout continua utilizável em escala alta e janela estreita; nenhum dado real é modificado sem intenção.

**Se falhar:** anote ação, resultado esperado e resultado observado. Consulte o log de erro sem copiar credenciais. Corrija em etapa isolada, com teste de regressão.

## Etapa 2 — revisar menu, responsividade e consistência de textos/estados

**Objetivo:** reduzir dúvidas na barra de escrita e deixar mensagens de andamento e erro previsíveis.

**Inspecionar:** `web/index.html`, `web/app.js`, `web/estilo.css` e os textos da Ajuda. Localize os estados existentes de conversa, pesquisa, espera, sucesso e falha antes de propor novos.

**Como fazer:**

1. Observe o fluxo real da barra em largura normal e estreita. Identifique comandos usados raramente e preserve fácil acesso a Enviar, microfone e controles ativos. Não mova comandos apenas por preferência estética; confirme que atalhos e rótulos continuam descobríveis.
2. Liste todos os textos de estado e mensagens de erro. Defina uma linguagem curta e consistente em português brasileiro, com nomes iguais para a mesma ação em botões, menus e Ajuda.
3. Para operações assíncronas, mostre qual ação está ocorrendo (por exemplo, pensando ou pesquisando), evite estados que pareçam congelamento e reabilite controles em sucesso e falha. Não deixe erros importantes sumirem antes que possam ser lidos.
4. Garanta foco visível, rótulos acessíveis, ordem lógica de Tab e que teclado não acione ações duplicadas. Não interrompa atalhos existentes.
5. Faça mudanças pequenas em HTML/CSS/JS e teste textos, estados de sucesso/erro, uso por teclado, largura reduzida e preferência de movimento reduzido.

**Aceite:** nomes e mensagens consistentes; operação em andamento perceptível; falhas visíveis e controles recuperados; barra utilizável por teclado e em janela estreita; atalhos documentados permanecem funcionais.

## Etapa 3 — completar a navegação por teclado na conversa

**Objetivo:** permitir operar a conversa e entender o foco sem depender exclusivamente do mouse, ampliando o trabalho já iniciado nas Configurações e nos cartões de tema.

**Diagnóstico antes de codificar:** percorra a aplicação com Tab e Shift+Tab, inspecione atributos semânticos em `web/index.html` e a criação dinâmica de mensagens e sugestões em `web/app.js`. Registre elementos sem nome, sem foco, com ordem inesperada ou sem retorno de foco após fechar diálogos/menus.

**Implementação proposta:**

1. Corrija semântica e nomes acessíveis de botões apenas onde estiverem ausentes ou ambíguos; não duplique rótulos visíveis em leitores de tela.
2. Garanta que mensagens novas e resultados de pesquisa sejam anunciados sem mover o foco de forma inesperada. Use uma região de status adequada para atualizações curtas e evite anunciar continuamente texto longo da resposta.
3. Garanta que menus e diálogos possam ser abertos, percorridos e fechados por teclado, que Escape feche quando apropriado e que o foco retorne ao controle que abriu o elemento.
4. Torne sugestões de continuação, lista de fontes/sites e visualização de imagem acessíveis por teclado e com nomes compreensíveis. Preserve o comportamento atual do clique.
5. Verifique visibilidade de foco e contraste com os cinco temas, além de `prefers-reduced-motion`. Evite adicionar atalhos globais que conflitem com o campo de texto ou com os atalhos documentados.
6. Adicione verificações em `verificar.py` para os atributos e fluxos que possam ser checados sem dados pessoais. Faça verificação manual com teclado no WebView real; teste com leitor de tela se disponível e registre se não foi possível.

**Aceite:** fluxo principal (nova conversa, busca, enviar, ler resposta, abrir sites/fontes, usar sugestão e fechar visualização) pode ser percorrido por teclado; foco fica visível e previsível; anúncios não repetem toda a resposta; atalhos existentes passam.

## Etapa 4 — leitura de PDF e imagens anexados

**Objetivo:** completar a ideia já registrada em `IDEIAS.md` para ampliar os formatos que podem ser arrastados para a conversa.

**Escopo inicial recomendado:** PDF primeiro. Imagens devem ser uma etapa posterior e independente, pois exigem OCR ou visão por modelo, análise de formato/tamanho e decisão sobre envio externo.

**Diagnóstico e desenho:**

1. Localize a ponte de arrastar/soltar e os limites atuais em `app_web.py` e `web/`.
2. Inspecione dependências e licença antes de escolher uma biblioteca PDF. Prefira extração local de texto, sem upload automático.
3. Defina limites de tamanho, número de páginas, tempo de processamento e comportamento para PDF digitalizado sem camada de texto. Mostre aviso claro quando não houver texto extraível.
4. Trate erros de arquivo inválido, protegido por senha ou excessivamente grande sem travar a janela. Não execute conteúdo embutido nem abra links automaticamente.
5. Insira o texto extraído como contexto visível/revisável para o usuário, com indicação do nome do arquivo e opção de remover antes do envio. Não envie o conteúdo à IA até o usuário enviar a mensagem.
6. Para imagens, proponha fluxo separado: informar formatos e tamanho aceitos, pré-visualização, remoção, consentimento explícito antes de transmitir a um provedor, e não guardar cópia sem solicitação.
7. Crie testes com arquivos sintéticos em `_tmp` (PDF com texto, PDF vazio/corrompido e imagem local de teste). Não use documentos pessoais.

**Aceite de PDF:** extração local testada com arquivo sintético; texto apresentado para revisão; arquivo sem texto, inválido, protegido e grande tratados com mensagem compreensível; nenhuma chamada externa ocorre antes do envio; arquivos reais do usuário não são lidos nos testes.

## Etapa 5 — polimento de estados e recuperação de falhas

**Objetivo:** garantir que operações longas ou falhas do provedor não deixem a interface em estado confuso.

**Inspecionar:** indicador atual de ocupado, envio/cancelamento, mensagens de erro da ponte e gravação de configurações. Identifique se já há cancelamento antes de propor um botão novo.

**Como fazer:**

1. Defina estados explícitos necessários, reutilizando os existentes: aguardando, conversando, pesquisando, concluído e falha.
2. Em cada caminho, confirme que o estado ocupado é limpo em `finally`/equivalente e que controles voltam ao estado correto.
3. Separe erro de conexão, falta de configuração, limite do provedor e erro local apenas quando o código conseguir identificá-los com segurança. Não inferir causas a partir de mensagens vagas.
4. Não incluir prompts, conversas, tokens, cabeçalhos ou chaves nas mensagens de erro e logs. A sanitização existente é baseada em padrões e não substitui evitar segredos.
5. Não implementar cancelamento interrompendo threads de forma insegura. Se cancelamento for necessário, desenhe cooperação e estados da ponte antes de alterar.
6. Cubra caminhos de sucesso, erro e recuperação com dublês/fakes e dados sintéticos; não chame APIs reais nem use a configuração real.

**Aceite:** nenhuma falha deixa controles desabilitados; usuário consegue distinguir espera de erro; mensagem é útil sem divulgar dados sensíveis; a interface aceita uma nova ação depois da recuperação.

## Ordem sugerida

1. Etapa 1: validações manuais já pendentes e sem código.
2. Etapa 2: consistência do menu, textos e estados; dividir em mudanças pequenas.
3. Etapa 3: navegação por teclado na conversa.
4. Etapa 5: recuperação de falhas, coordenada com a Etapa 2 se houver sobreposição.
5. Etapa 4: PDF local; imagens somente depois de decidir como será o consentimento e o envio ao provedor.

Não é obrigatório executar todas as etapas. Antes de iniciar uma implementação futura, confirme que ela ainda faz sentido diante do código e dos documentos atuais.

## Checklist para encerrar cada etapa

- [ ] Diagnóstico e arquivos envolvidos registrados.
- [ ] Nenhuma alteração preexistente foi descartada ou incluída por acidente.
- [ ] Testes novos cobrem a regressão relevante e usam somente dados sintéticos/temporários.
- [ ] `.venv\Scripts\python.exe verificar.py` termina em `RESULTADO: TUDO CERTO`, sem falhas.
- [ ] JavaScript passa pela verificação de sintaxe incluída ou disponível.
- [ ] Interface validada visualmente quando afetada; limitações manuais declaradas.
- [ ] `ONDE-PARAMOS.md`, `HISTORICO-DE-MUDANCAS.md` e, quando necessário, `PROXIMOS-PASSOS.md` atualizados.
- [ ] Relato final informa o que mudou, como foi verificado e o que ficou pendente.
