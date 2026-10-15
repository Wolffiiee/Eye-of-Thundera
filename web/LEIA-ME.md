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
   `--demo`) e abre as 4 abas de Configurações. As funções que só leem
   funcionam; as que mudam algo avisam em qual passo serão feitas, para
   nenhum teste mexer nos dados do Wolf.
2. Ligar a lista de conversas e a conversa de verdade (ler do Python).
3. Enviar pergunta e mostrar a resposta aparecendo aos poucos.
4. Caixa de digitar, microfone, botão enviar, modo web.
5. Janela de Configurações com as 4 abas funcionando de verdade (gravar).
6. Salvar em .txt, copiar, pesquisar.
7. Atalhos de teclado, cantos arredondados da caixa, borda escura da janela.
8. `verificar.bat` cobrindo a tela nova e `.exe` gerado e testado.

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
