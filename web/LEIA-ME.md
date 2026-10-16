# Interface web do Eye of Thundera

**Estado:** esta é a interface usada pelo atalho da Área de Trabalho; não é mais um protótipo separado.

## Arquivos

- index.html: estrutura e elementos da tela.
- estilo.css: tema escuro, layout, responsividade e estados visuais.
- app.js: eventos, renderização das conversas, botões, atalhos e configurações.
- ../app_web.py: cria a janela pywebview e expõe a ponte Python.

## Como funciona a ponte

O JavaScript chama funções expostas por window.pywebview.api. A ponte é assíncrona; as chamadas passam pela função chamar(), que espera a API ficar pronta e mostra um aviso se a chamada falhar.

O evento pywebviewready é usado para iniciar a interface depois que o WebView está pronto. Não remova essa espera sem uma alternativa testada. Uma falha de sintaxe em app.js impede o arquivo inteiro de executar e deixa a janela visualmente aberta, mas sem cliques funcionais; por isso verificar.py executa node --check quando Node.js está disponível.

## Modos de execução

- Sem argumentos: usa as conversas e configurações reais.
- --demo: usa conversas de exemplo e não deve gravar dados reais.
- --previa: demonstração em janela menor, posicionada para a tela secundária.
- --voz: permite testar o microfone real no modo de demonstração; use somente quando isso for intencional.

## Verificação

Na pasta do projeto, rode .venv/Scripts/python.exe verificar.py. Depois de alterações na interface, abra o programa e confira visualmente o fluxo afetado. Os testes estáticos não garantem que todos os cliques funcionem no WebView real.

## Regras importantes

- Não exponha chaves ou objetos internos do Python como atributos públicos da ponte.
- Mantenha o nome da janela da ponte como atributo privado (_janela), para evitar que pywebview tente percorrer objetos nativos recursivamente.
- Não teste operações destrutivas com os arquivos reais de memória, histórico ou configurações.
- Para mudanças grandes de estilo, faça uma seção de cada vez e preserve os estados de foco, hover, desabilitado, carregando e erro.
