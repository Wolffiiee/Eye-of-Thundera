# PLANO: aba Personalizacao com AMOSTRAS de cores (cartoes de tema)

Escrito pelo Claude em 17/10/2026, a pedido do Wolf, ANTES de implementar, para que
qualquer IA (OpenCode, Codex, ChatGPT) entenda a ideia e possa continuar.
Fale com o Wolf em portugues simples; ele nao programa.

## O pedido do Wolf (palavras dele)
"Uma amostra das cores dos temas: em vez de ser uma lista, fosse uma caixinha mostrando
as cores e o nome do tema."

## Como esta hoje (16/10)
- `web/app.js`: `TEMAS_UI` (5 temas: Classico Dark, Purpurina, Amethyst, Ocean, Forest),
  `aplicarTema(indice)`, e `abaPersonalizacao(corpo)` que desenha um `<select>`.
- `web/estilo.css`: `.cartao-tema`, `.select-tema`, `.nota-tema`.
- Backend (`app_web.py`): ja guarda `tema` (nome) e `temaIdx` (0..4) via `config_salvar`
  e devolve os dois em `iniciar()`. **NAO MUDA NADA NO PYTHON.**

## O que sera feito (so front-end, 3 arquivos)
1. **`web/app.js` - `abaPersonalizacao`**: trocar o `<select>` por uma GRADE de cartoes
   (um por tema), no lugar da lista:
   - cada cartao e um `<button role="radio" aria-checked="true|false">` dentro de um
     `<div role="radiogroup" aria-label="Tema da interface">`;
   - dentro do cartao: uma MINIATURA do app pintada com as cores DAQUELE tema
     (barra lateral, balao do usuario, balao da resposta, caixa de escrever e o botao
     de destaque), uma fileira de 5 bolinhas de cor (bg, superficie, texto, azul, azul-2)
     e o NOME do tema embaixo;
   - o cartao do tema ativo ganha borda na cor de destaque e uma marca de "selecionado";
   - clicar escolhe: chama o MESMO fluxo de hoje (`aplicarTema(idx)` + 
     `chamar("config_salvar", { tema: tema.nome, temaIdx: idx, chaves: {} })`; se der erro,
     volta ao tema anterior e avisa). Nao mudar esse payload.
   - teclado: setas movem a selecao entre cartoes, Enter/Espaco escolhe, Tab entra/sai
     do grupo (padrao radiogroup, `tabindex` 0 so no ativo).
2. **`web/estilo.css`**: `.grade-temas` (grid `repeat(auto-fill, minmax(150px, 1fr))`,
   gap 12px, funciona em janela pequena), `.amostra-tema`, `.amostra-*` da miniatura,
   `.bolinhas-tema`, estados `:hover`, `:focus-visible`, `.ativo`. A miniatura usa as
   cores do tema por `style` inline (variaveis `--m-bg` etc.), NAO as variaveis globais,
   senao todos os cartoes ficariam iguais ao tema atual.
3. **`verificar.py`**: os testes de hoje procuram o texto do `<select>` no codigo. Eles
   devem ser ATUALIZADOS (nao apagados) para os novos marcadores: `cartao-tema`,
   `role="radiogroup"`, `aria-label` "Tema da interface", 5 cartoes, o payload
   `config_salvar` identico, `.grade-temas` no CSS. Manter os testes de persistencia e de
   `iniciar()` (backend) exatamente como estao.

## Fonte unica de verdade
`TEMAS_UI` continua sendo a UNICA lista de cores. A miniatura e as bolinhas LEEM dela.
Para criar um tema novo: acrescentar um objeto em `TEMAS_UI` **e** o nome em
`temas_validos` do `app_web.py` (indice 0..N) **e** subir o limite `<= 4` do backend.
(Hoje o backend aceita 0..4; se adicionar tema, mexer nos dois lugares e no teste.)

## O que NAO fazer
- Nao mexer em `aplicarTema`, na gravacao do tema, nem no Python.
- Nao apagar teste de tema/persistencia; so atualizar os marcadores do `<select>`.
- Nao usar imagem/PNG para a amostra: so HTML+CSS (leve, nitido em qualquer escala).
- Nao deixar a escolha depender do botao "Salvar": o tema salva na hora, como hoje.

## Como conferir (obrigatorio)
1. `verificar.bat` com os dois arquivos TUDO CERTO.
2. `ferramentas\tirar_prints.py` (modo exemplo) e olhar o print da aba Personalizacao;
   trocar o tema por clique e ver se a tela inteira muda e o cartao ativo acompanha.
3. Janela pequena (900 px de largura): os cartoes quebram linha, sem barra horizontal.
4. Gerar o .exe (`Gerar o EXE.bat`), abrir e testar a troca de tema DE VERDADE.

## Ordem de trabalho
(1) CSS e funcao `cartaoTema(tema, idx, ativo)` -> (2) trocar o `<select>` -> (3) teclado
-> (4) atualizar testes -> (5) prints e conferencia -> (6) .exe -> (7) HISTORICO e
ONDE-PARAMOS -> (8) commit.
