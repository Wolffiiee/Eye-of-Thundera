# Tela nova em HTML (protótipo, NÃO é o programa)

> **Isso aqui não faz parte do Pesquisa IA que você usa.**
> O programa que funciona é o `pesquisa_ia.py` (tkinter), na pasta acima.
> Esta pasta é uma experiência para um dia trocar a tela por uma tela de
> verdade em HTML (que resolveria a seleção de texto, a formatação e os
> emojis coloridos de uma vez).

## Onde parou (15/10/2026, trabalho parou no meio)
- `index.html` — o esqueleto da tela: barra da esquerda com a lista de
  conversas, área da conversa, caixa de digitar, janela de Configurações
  com as 4 abas (Memória, Conversa, Chaves, Ajuda).
- `estilo.css` — o tema escuro. Usa cores novas (mais escuras e mais
  "modernas" que as do programa atual): fundo `#0e0e13`.
- `app.js` — a lógica da tela. **Fala com o Python por
  `window.pywebview.api`**, ou seja: falta a ponte (o arquivo
  `app_web.py`, que ainda não existe) e falta instalar a biblioteca
  `pywebview` no projeto.
- `spike_webview.py` — teste rápido: confere se o `pywebview` funciona
  neste computador, se a janela abre no segundo monitor (x=2000) e se os
  emojis aparecem em cor. **Não foi confirmado** que rodou sem erro.

## Para continuar, o caminho é
1. Rodar o `spike_webview.py` e ver o que ele responde.
2. Se o `pywebview` não funcionar aqui, **parar** e voltar ao tkinter
   (não vale a pena trocar o programa inteiro por uma tela que não abre).
3. Só depois escrever o `app_web.py` (a ponte Python ↔ JavaScript).

## Aviso importante
Isto é **item 7 da lista, o último de todos**, e o plano diz para só fazer
se o Wolf quiser mesmo. Trocar a tela inteira é mexer em tudo de uma vez
(6500 linhas) — o jeito seguro é fazer a tela nova aos poucos, ao lado da
antiga, e só trocar quando ela estiver igual ou melhor.
