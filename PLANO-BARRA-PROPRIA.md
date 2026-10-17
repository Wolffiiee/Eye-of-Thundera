# PLANO: barra de titulo propria (sem a barra branca do Windows) e sem nome/icone no topo

Escrito pelo Claude em 17/10/2026, ANTES de mexer no codigo, a pedido do Wolf, para que
qualquer IA (OpenCode, Codex, ChatGPT) entenda a ideia e possa continuar.
Fale com o Wolf em portugues simples; ele nao programa. Leia antes: README.md,
ONDE-PARAMOS.md, INSTRUCOES-PARA-IA.md, GUIA-DO-OPENCODE.md.

## O pedido do Wolf (resumo fiel)
1. Remover o NOME do programa e o ICONE que ficam no topo, a esquerda.
2. Ver se da para REMOVER a barra de titulo padrao do Windows e ter uma barra EMBUTIDA no
   programa (mesma cor do app), com minimizar / maximizar / fechar.
3. Otimizar o que for possivel; acrescentar o que faltar (ver "Backlog desta rodada").

## O que aparece hoje e o que sera removido
Em cada print ha DOIS lugares com nome + icone:
- A. barra do Windows: icone pequeno + "Eye of Thundera" (sai junto com a barra nativa);
- B. topo da barra lateral: `.marca` em `web/index.html` (logo de lupa + "Eye of Thundera").
Decisao: remover A (barra propria SEM nome e SEM icone) e remover B (apagar o bloco
`.marca`, mantendo `.topo-lateral` com o botao "recolher a barra"). Se o Wolf quiser o
nome de volta, e so reativar `.marca`: nao apague o CSS dele, apenas esconda o HTML.

## Como fazer (duas tecnicas; tentar na ORDEM, parar na primeira que passar nos criterios)
### Tecnica B (preferida): manter a janela normal e SO tirar a barra de titulo por dentro
Em `app_web.py`, depois que a janela abre (funcao `ao_abrir`), pegar o HWND (a janela e'
achada pelo titulo `TITULO_JANELA`, como `p.escurecer_janela_por_titulo` ja faz) e:
  - ler o estilo com `GetWindowLongPtrW(hwnd, GWL_STYLE)`;
  - tirar `WS_CAPTION` (0x00C00000) e manter `WS_THICKFRAME` (0x00040000), para continuar
    podendo redimensionar pelas bordas, encaixar com Win+setas e ter sombra;
  - `SetWindowPos(..., SWP_FRAMECHANGED|SWP_NOMOVE|SWP_NOSIZE|SWP_NOZORDER)` para aplicar.
Vantagem: resize, snap e sombra do Windows continuam. Risco: faixa fina de 1 a 8 px nas
bordas quando maximizada (a janela "vaza" da tela). Tratar: ao maximizar, usar
`ShowWindow(SW_MAXIMIZE)` e adicionar `padding` no `body` pelo valor de
`GetSystemMetrics(SM_CXSIZEFRAME)+SM_CXPADDEDBORDER`, ou usar a area de trabalho
(`SystemParametersInfoW(SPI_GETWORKAREA)`) para dimensionar.
### Tecnica A (reserva): `frameless=True` do pywebview
Trocar `frameless=False` por `True` na criacao da janela (linha com `create_window`) e
manter `easy_drag=False` (o arrasto e' so pela barra propria, classe
`pywebview-drag-region`). Problema conhecido: sem a moldura o Windows NAO redimensiona pelas
bordas. Solucao: 8 "alcas" invisiveis de 6 px nas bordas/cantos (HTML `div.alca`), que
chamam `redimensionar(dx, dy, lado)` na ponte (usa `janela.resize` e `janela.move`).
So adotar se a B falhar nos criterios; e dizer ao Wolf que o snap do Windows pode nao
funcionar.

## Criterios de aceite (testar de verdade, nao so no codigo)
[ ] nenhuma barra branca/nativa; nenhum nome nem icone no topo esquerdo;
[ ] arrastar a janela pela faixa de cima; clique duplo na faixa maximiza/restaura;
[ ] botoes minimizar, maximizar/restaurar e fechar funcionam; fechar ainda grava a
    posicao da janela (`ao_fechar`); fechar tem hover vermelho;
[ ] redimensionar pelas bordas funciona e a janela nao passa da tela quando maximizada;
[ ] funciona em escala do Windows 100%, 125%, 150% (DPI);
[ ] os 9 temas mudam a barra junto (usar `var(--bg)` e `var(--texto-2)`, nada fixo);
[ ] nada na barra rouba o clique dos botoes existentes (botao recolher, Configuracoes).

## Mudancas por arquivo
- `web/index.html`: criar `<div id="barra-titulo" class="pywebview-drag-region">` com o
  grupo `.botoes-janela` (3 botoes, icones em SVG inline, `aria-label` em portugues:
  "Minimizar", "Maximizar", "Fechar"); remover o bloco `.marca` da lateral.
- `web/estilo.css`: `#barra-titulo` (altura 32 px, fundo `var(--bg)`, sem borda ou borda
  de 1 px `var(--borda)`), `.botoes-janela button` (46x32, sem borda, hover
  `var(--superficie)`), `.fechar:hover` vermelho `#e5484d`; empurrar o conteudo
  (`#app` ou equivalente) para baixo da barra; manter `.marca` no CSS.
- `web/app.js`: ligar os 3 botoes a `chamar("janela_minimizar")`,
  `chamar("janela_maximizar")`, `chamar("janela_fechar")`; clique duplo na faixa chama
  maximizar; trocar o icone de maximizar/restaurar conforme o retorno; esperar a ponte
  (use o `chamar` que ja existe, ele cuida disso).
- `app_web.py`: na classe `Ponte`, metodos `janela_minimizar()`, `janela_maximizar()`
  (alterna e devolve `{"maximizada": bool}`), `janela_fechar()`; usar `self._janela`
  (COM underscore: o pywebview se perde se o nome for publico, ver ONDE-PARAMOS /
  RESUMO-DA-MADRUGADA). Em `ao_abrir`, aplicar a Tecnica B. Em modo `DEMO` os metodos
  funcionam normalmente (so mexem na janela).
- `verificar.py`: o teste da "barra de titulo escura" (secao 4c) NAO se apaga: atualizar
  para o novo comportamento (a barra propria existe, usa variaveis de tema, e a funcao de
  escurecer so e' chamada quando a barra nativa ainda existir). Novos testes: HTML tem
  `#barra-titulo` e NAO tem `.marca` visivel; `Ponte.janela_*` com janela falsa; CSS usa
  variaveis de tema na barra; o payload de `iniciar()` nao muda.

## O que NAO fazer
- Nao tirar `TITULO_JANELA`: o Windows precisa dele (barra de tarefas, Alt+Tab) e a
  janela e' achada por ele. Ele so deixa de aparecer DENTRO da janela.
- Nao mexer em tema, chaves, memoria, conversas. Nao apagar teste.
- Nao deixar codigo de depuracao no `app_web.py` (a ultima vez derrubou o programa).
- Nao gerar .exe antes de abrir e testar com `python app_web.py`.

## Como conferir
1. `verificar.bat` (dois arquivos) = TUDO CERTO.
2. `ferramentas\tirar_prints.py` (modo exemplo) e olhar `01-tela-inicial.png`.
3. Abrir de verdade (`python app_web.py --demo`): arrastar, maximizar, restaurar,
   redimensionar, minimizar, fechar, trocar tema.
4. So entao atualizar HISTORICO-DE-MUDANCAS.md e ONDE-PARAMOS.md.

## Backlog desta rodada (depois da barra)
1. Negrito em lista aparecendo com `**asteriscos**` (visto nos prints de 16/10): conferir o
   renderizador de markdown de `web/app.js` e corrigir com teste.
2. Remover o CSS morto `.select-tema` (nao ha mais `<select>` de tema).
3. Itens ja pendentes em PROXIMOS-PASSOS.md (conferir escala do Windows acima de 100%).
