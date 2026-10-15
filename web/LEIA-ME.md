# Tela nova em HTML (protótipo, em construção)

> **Isso aqui AINDA não é o programa que você usa.**
> O programa que funciona é o `pesquisa_ia.py` (tkinter), na pasta acima,
> e o atalho da Área de Trabalho continua apontando para ele.
> Esta pasta é a tela NOVA, que vamos terminar antes de trocar.

## O teste decisivo já passou (15/10/2026)
Rode `..\.venv\Scripts\python.exe web\spike_webview.py`. Ele abre uma janela
teste no 2º monitor e responde:

| Pergunta | Resultado |
|---|---|
| a janela abre? | sim |
| abre no 2º monitor (x=2000)? | sim |
| Python chama o JavaScript? | sim |
| JavaScript chama o Python (a ponte)? | sim |
| **o emoji sai COLORIDO?** | **sim (63% dos pixels com cor)** |
| dá para selecionar texto? | sim |

Ou seja: **a tela nova funciona neste computador.** E o emoji colorido vem
de graça (no Tk ele só sai de uma cor).

## O que já existe aqui
- `index.html` — o esqueleto: barra da esquerda com as conversas, área da
  conversa, caixa de digitar, janela de Configurações com as 4 abas.
  Os ícones são SVG (desenhados, sem depender de fonte).
- `estilo.css` — o tema escuro. Cores novas, mais escuras que as do
  programa atual: fundo `#0e0e13`, destaque `#3d6bff`.
- `app.js` — a lógica da tela. Fala com o Python por
  `window.pywebview.api`.
- `spike_webview.py` — o teste acima. **Não é do programa.**

## O que falta (ordem de trabalho)
1. ~~`app_web.py` mínimo~~ **FEITO (passo 1)**: a ponte existe, a janela
   abre no 2º monitor, mostra as conversas do Wolf (ou as de exemplo, com
   `--demo`) e abre as 4 abas de Configurações.
2. ~~Conversas de verdade~~ **FEITO (passo 2)**: abrir conversa, criar nova
   e excluir funcionam. A conversa aberta mora na ponte
   (`Ponte.mensagens` / `Ponte.id_atual`) e `_gravar_conversa()` grava no
   arquivo quando há mensagem nova — igual ao programa antigo.
3. **O que falta agora: a IA.** `enviar()` ainda responde "passo 3".
   É aqui que entra `p.perguntar(...)` e o `window.PIA.evento(...)`
   mandando `etapa` (o que ele está fazendo), `resposta` e `erro`.
4. Caixa de digitar, microfone, botão enviar, modo web.
5. Janela de Configurações com as 4 abas funcionando de verdade (gravar).
6. Salvar em .txt, copiar, pesquisar.
7. Atalhos de teclado, cantos arredondados da caixa, borda escura da janela.
8. `verificar.bat` cobrindo a tela nova e `.exe` gerado e testado.

## Como a tela conversa com o Python
- O JavaScript chama com `window.pywebview.api.nomeDaFuncao(...)`.
- A ponte do pywebview é **assíncrona**: a chamada devolve uma Promise, e
  o `app.js` já usa `await` (`async function chamar`). Do lado do Python,
  tudo pode ser normal.
- Para o Python **falar com a tela** (usado no passo 3, para a resposta
  ir aparecendo), é `janela.evaluate_js("window.PIA.evento(" + json +
  ")")`. O `json.dumps(..., ensure_ascii=False)` evita que acento e emoji
  virem lixo.
- Todo teste do `verificar.py` que mexe em conversa ou memória aponta os
  arquivos para `_tmp\teste-tela-nova` e restaura no fim. Nunca teste
  contra os dados do Wolf.

## Como abrir
- **Para o Wolf:** duplo clique em `5 - Ver a tela nova.bat` (abre no 2º
  monitor, em modo exemplo, sem tocar em nada).
- **Para quem programa:** `.venv\Scripts\python.exe app_web.py` (usa as
  conversas de verdade, só leitura). Com `--demo`, usa as de exemplo.

## O `.exe` da tela nova
Existe um spec separado, `Pesquisa IA Tela Nova.spec`, de propósito: o
`Pesquisa IA.spec` (o programa que já funciona) não foi tocado. Se a tela
nova der problema, o programa do Wolf não é afetado. Ainda não foi gerado
(não é preciso até o passo 8).

## Ruído conhecido (não é defeito)
O pywebview imprime um erro de COM do WebView2 ("CoreWebView2Controller
members can only be accessed from the UI thread") quando tenta ler o
zoom da página. A janela abre, carrega e funciona normalmente. É ruído do
próprio pywebview.

## Duas coisas que o teste descobriu (importante)
- A ponte do pywebview é **assíncrona**: `window.pywebview.api.algo(...)`
  devolve uma `Promise`. No JavaScript tem que usar `.then(...)`:
  ```js
  window.pywebview.api.ola('Wolf').then(v => mostrar(v));
  ```
- O `pywebview` **precisa** entrar no `requirements.txt` e no
  `Pesquisa IA.spec`. Ele está instalado nesta máquina, mas não está
  registrado em nenhum dos dois: sem isso, o `.exe` gerado não abre.

## Regra de ouro desta fase
**O `pesquisa_ia.py` continua inteiro e continua sendo o atalho do Wolf.**
A tela nova nasce ao lado da antiga. Só trocamos quando ela estiver igual
ou melhor. Assim nunca sobra o Wolf sem programa funcionando.
