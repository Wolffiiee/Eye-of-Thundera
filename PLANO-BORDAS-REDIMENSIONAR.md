# Plano: redimensionar a janela pelas bordas (faixas na tela)

Para as outras IAs. Escrito em 17/10/2026, antes de mexer no codigo.

## Problema
Wolf testou: arrastar pela barra e maximizar funcionam, mas redimensionar pelas
bordas e cantos NAO. Causa: o WebView2 e' uma janela-filha que cobre toda a area
do cliente e fica com o mouse; a WM_NCHITTEST nunca chega no gancho
(`_cobrir_area_cliente`) da janela principal. Com WM_NCCALCSIZE=0 nao ha borda nativa.

## Solucao (Tecnica A do PLANO-BARRA-PROPRIA.md)
8 faixas finas em HTML (4 bordas + 4 cantos), `position:fixed`, acima de tudo.
Ao apertar o mouse numa faixa, a tela chama `Ponte.janela_redimensionar(borda)`,
que faz ReleaseCapture + SendMessageW(hwnd, WM_NCLBUTTONDOWN, HT_*, 0) - o mesmo
truque do `janela_arrastar` (que ja funciona). O Windows assume o redimensionamento.

## Mudancas
- app_web.py: `Ponte.janela_redimensionar(borda)`; nomes aceitos: esquerda, direita,
  topo, topo-esq, topo-dir, base, base-esq, base-dir -> codigos 10..17 (HT_*).
  Nome invalido ou janela maximizada = nao faz nada.
- web/index.html: `<div id="bordas">` com 8 `<div class="grip" data-borda="...">`.
- web/estilo.css: faixas de 5px (cantos 12px), cursores certos, ocultas com body.maximizada.
- web/app.js: mousedown nas faixas chama a ponte.
- verificar.py: teste de que existem as 8 faixas e que a ponte mapeia certo.

## Nao fazer
Nao remover o gancho WNDPROC sem Wolf testar a janela. Nao apagar testes.
