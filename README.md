# Eye of Thundera

Assistente pessoal de pesquisa, com interface escura em HTML/JavaScript e integração Python via pywebview.

**Estado conferido em 16/10/2026:** o atalho da Área de Trabalho abre o código-fonte em app_web.py. A sintaxe da interface está verificada automaticamente; a aba Personalização oferece cinco temas persistentes; o botão de salvar resposta usa o diálogo da janela pywebview; o botão/atalho de Pesquisa séria força a pesquisa profunda; e as opções secundárias estão agrupadas em “Mais”. A suíte passou com 132 verificações, sem falhas nem avisos. O usuário confirmou que os fluxos principais, o menu “Mais”, o cartão Gemini e a revisão responsiva/acessível estão funcionais. O salvamento das configurações mostra o estado de carregamento, bloqueia edições concorrentes e recupera os controles após falhas.

## Comece por aqui

- **Situação atual e próximo trabalho:** ONDE-PARAMOS.md
- **Regras para alterações com IA:** INSTRUCOES-PARA-IA.md
- **Como testar e corrigir:** PASSO-A-PASSO.md
- **Histórico das correções:** HISTORICO-DE-MUDANCAS.md
- **Backlog real:** PROXIMOS-PASSOS.md
- **Ideias futuras:** IDEIAS.md

## Como o programa abre

O atalho da Área de Trabalho, Eye of Thundera.lnk, aponta para:

- Executável Python: .venv/Scripts/pythonw.exe
- Argumento: app_web.py
- Pasta de trabalho: D:/Projetos/PesquisaIA

Portanto, o atalho executa o código-fonte; não executa dist/Eye of Thundera.exe. Para conferir uma mudança na interface, feche a janela e abra o atalho novamente. Não é necessário gerar um EXE para alterações no código-fonte usado por esse atalho.

Para abrir pelo terminal, na pasta do projeto, use .venv/Scripts/pythonw.exe app_web.py. Para uma demonstração sem usar as conversas reais, execute .venv/Scripts/python.exe app_web.py --demo.

## Mapa do projeto

| Arquivo ou pasta | Responsabilidade |
|---|---|
| app_web.py | Janela pywebview e ponte entre Python e a interface |
| web/index.html | Estrutura da interface |
| web/app.js | Eventos, ações dos botões, conversas e configurações |
| web/estilo.css | Tema, layout e estados visuais |
| pesquisa_ia.py | Motor de conversa, pesquisa, provedores e regras compartilhadas |
| roteador.py | Decide entre conversa, pesquisa e outros modos |
| memoria.py | Organização e manutenção da memória |
| voz.py | Gravação e transcrição de voz |
| verificar.py / verificar.bat | Verificação automatizada |
| requirements.txt | Dependências de execução |
| requirements-dev.txt | Dependências de desenvolvimento e testes |
| _tmp/ | Saídas temporárias e arquivos de diagnóstico; não é documentação oficial |

## Dados pessoais e segurança

Os dados de uso ficam fora do repositório, em %LOCALAPPDATA%/PesquisaIA: configurações, chaves de API, histórico e memória. Não copie esses dados para o Git, não imprima chaves em logs e não aponte testes para os arquivos reais do usuário. Os testes devem usar arquivos temporários em _tmp e restaurar qualquer configuração que alterarem.

Não apague arquivos de histórico ou de backup como forma de limpeza. Arquivos antigos do programa ficam em _arquivo_morto; não use essa pasta como fonte principal do código atual.

## Verificação obrigatória

Na pasta do projeto, execute:

    .venv\Scripts\python.exe verificar.py

O resultado esperado termina em TUDO CERTO, com FALHA: 0. O relatório mostra VERIFICACOES, que é a quantidade de verificações reportadas — não confundir com a quantidade de testes unitários independentes. Quando Node.js está instalado, a suíte também verifica a sintaxe de web/app.js para impedir que uma chave extra desative toda a interface.

## Fluxo de trabalho recomendado

1. Leia ONDE-PARAMOS.md e confira git status e git log.
2. Identifique a causa antes de alterar o código.
3. Faça uma cópia de segurança ou confirme que o Git permite reverter a mudança.
4. Faça a menor alteração possível e adicione um teste que detecte a regressão.
5. Rode verificar.py até passar sem falhas.
6. Confira visualmente a interface quando a mudança afetar a janela.
7. Atualize HISTORICO-DE-MUDANCAS.md e ONDE-PARAMOS.md.
8. Faça commit com uma mensagem que explique a mudança.

## Observações da interface

A tela principal já reúne conversas, busca no histórico, modos de pesquisa, conversa privada, resumo do dia, microfone e envio. As configurações são divididas em Memória, Conversa, Chaves, Ajuda e Personalização. A aba Personalização permite escolher entre cinco temas, aplicados na hora e mantidos na próxima abertura.

Melhorias de UX recomendadas para a próxima rodada: reduzir a sensação de excesso de botões na barra de escrita, agrupar cada provedor junto do seu controle de ativação, padronizar textos e estados de carregamento e verificar a navegação por teclado. Evite uma reformulação visual grande antes de validar os fluxos existentes.
