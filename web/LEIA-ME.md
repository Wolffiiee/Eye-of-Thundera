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
3. ~~A IA~~ **FEITO (passo 3, 16/10/2026)**: a pergunta chega na IA e a
   resposta volta por partes. O `enviar()` devolve na hora e o trabalho
   roda numa thread; o que ela faz chega pela tela por `etapa`,
   `resposta`, `erro` e `conversas` (ver `window.PIA.evento`). Reaproveita
   `pesquisa_ia.perguntar`/`conversar`, o roteador, a chave reserva e o
   tradutor de erro do programa antigo — nada disso foi reescrito.
4. ~~Microfone~~ **FEITO (passo 4, 16/10/2026)**: `Ponte.mic_alternar()`
   liga e desliga a gravação com o mesmo `voz.Gravador`, o mesmo
   `wav_tem_som` e o mesmo `transcrever` (com a lista de modelos de
   reserva) do programa antigo — nada foi reescrito. A tela avisa se está
   gravando pelos eventos `gravando` e `voz`; o texto falado **entra na
   caixa de digitar** para o Wolf conferir (só sai sozinho se ele tiver
   ligado "enviar" nas Configurações). Botão ou `Ctrl+M`. Botão ou `Ctrl+M`. No `--demo` ele finge que ouviu; com
   `--voz` (o `6 - Falar com a tela nova.bat`) ele é o microfone de
   verdade, sem gravar nada.
5. ~~Janela de Configurações com as 4 abas~~ **FEITO (passo 5, 16/10/2026)**:
   as quatro abas (Memória, Conversa, Chaves, Ajuda) jáexistiam e já
   gravavam; o que faltava da Tarefa D foi acrescentado: **editar** um
   item **clicando no texto** (`memoria_editar`), **Exportar** a memória
   em `.txt` (`memoria_exportar`), o **aviso do limite de 200 letras**
   (o `memoria.py` corta em silêncio, e agora a tela avisa antes) e a
   aba Ajuda com **voz e a lista de atalhos**. **Ctrl+S** salva a última
   resposta em `.txt`, como no programa antigo (sem isso o navegador
   abriria a janelinha branca de "salvar página").
6. ~~Salvar em .txt, copiar~~ **FEITO** (os dois já existiam; o **Ctrl+S**
   foi acrescentado no passo 5) e ~~procurar~~ **FEITO (passo 6,
   16/10/2026)**: a caixinha "Procurar nas conversas..." na barra da
   esquerda procura no **título** e **dentro das mensagens**, sem levar
   em conta acento nem maiúscula (é o mesmo `_sem_acento` que a Memória
   usa: digitar `japao` acha "Japão", `CENOURA` acha "cenoura").
   Mostra o **trecho** com a palavra destacada e, ao clicar, abre a
   conversa. Uma letra sozinha **não** busca (acharia conversa demais) e
   o máximo é 30 resultados. Deliberadamente, **"Tokio" NÃO acha
   "Tóquio"** — `c` e `ç` são letras diferentes para o computador, e
   melhor isso do que a busca adivinhar. Deixado num teste para não
   virar "correção" depois.
7. Atalhos de teclado (Ctrl+M, Ctrl+S, Esc já existem), cantos
   arredondados da caixa, borda escura da janela.
8. `verificar.bat` cobrindo a tela nova e `.exe` gerado e testado.

## Como a tela conversa com o Python
- O JavaScript chama com `window.pywebview.api.nomeDaFuncao(...)`.
- A ponte do pywebview é **assíncrona**: a chamada devolve uma Promise, e
  o `app.js` já usa `await` (`async function chamar`). Do lado do Python,
  tudo pode ser normal.
- Para o Python **falar com a tela**, use o `self._evento(...)` da ponte
  (é ele que faz `janela.evaluate_js("window.PIA.evento(" + json + ")")`).
  O `json.dumps(..., ensure_ascii=False)` evita que acento e emoji virem
  lixo — sem ele o ç chega como `\u00e7`. Os tipos de evento são:
  | evento | quando | o que a tela faz |
  |---|---|---|
  | `etapa` | a IA está trabalhando | escreve o que ela está fazendo |
  | `resposta` | a resposta veio | joga a resposta na conversa |
  | `erro` | deu problema | escreve o erro; com `"chave": true` abre as Config. |
  | `conversas` | a lista mudou | redesenha a barra da esquerda |
  | `gravando` | o micro ligou/desligou | acende o botão vermelho e o relógio |
  | `voz` | o áudio foi transcrito | joga o texto na caixa de digitar |
  | `voz_erro` | a transcrição falhou | avisa (e abre as Config. se for chave) |
- Todo teste do `verificar.py` que mexe em conversa, memória, chave ou
  microfone aponta os arquivos para `_tmp\teste-tela-nova*` e restaura no
  fim. No microfone o `voz` inteiro é trocado por um de mentira: o teste
  **não abre o microfone de verdade** e **não gasta cota**. Nunca teste
  contra os dados do Wolf.

## Como abrir
- **Para o Wolf ver a tela (sem mexer em nada):** duplo clique em
  `5 - Ver a tela nova.bat`. Abre no 2º monitor, em modo exemplo: as
  conversas são de exemplo e o **microfone é de mentira** (ele finge que
  ouviu, para o botão poder ser testado mesmo sem microfone).
- **Para o Wolf TESTAR O MICROFONE DE VERDADE:** duplo clique em
  `6 - Falar com a tela nova.bat`. É a mesma tela, com `--voz`: o
  microfone é o real e a IA responde com a chave dele, **mas nenhuma
  conversa é salva** (é `--demo --voz`).
- **Para o Wolf USAR COM OS DADOS DELE:** duplo clique em
  `7 - Usar a tela nova de verdade.bat`. Aí a tela abre com as conversas
  dele e **salva no mesmo arquivo que o programa de sempre** (as duas
  barredas mostram a mesma coisa). Ainda em construção: se algo parecer
  errado, é só fechar — o programa de sempre não muda.
- **Para quem programa:** `.venv\Scripts\python.exe app_web.py` (usa as
  conversas de verdade, e grava).

### As flags (são três coisas independentes)
| flag | o que muda |
|---|---|
| `--demo` | conversas de exemplo e **nada é gravado** |
| `--voz` | o microfone é o **de verdade**, mesmo com `--demo` |
| `--previa` | `--demo` + janela menor (é o que o `5 - Ver a tela nova.bat` usa) |

**Enquanto a tela nova for coisa de teste, ela nasce sempre no 2º
monitor (x=2000)**, com qualquer combinação de flags — para nunca cobrir
a tela em que o Wolf está trabalhando. Isso tem teste no `verificar.py`.
Quando a tela nova virar *o* programa, a posição vai embora, como nas
janelas do tkinter (que seguem o app).

## O `.exe` da tela nova
Existe um spec separado, `Pesquisa IA Tela Nova.spec`, de propósito: o
`Pesquisa IA.spec` (o programa que já funciona) não foi tocado. Se a tela
nova der problema, o programa do Wolf não é afetado. Ainda não foi gerado
(não é preciso até o passo 8).

## Ruído conhecido (não é defeito)
O pywebview imprime erros no console quando a janela abre e **a janela
abre, carrega e funciona normalmente**. São três deles e nenhum é do
nosso código:
- `CoreWebView2Controller members can only be accessed from the UI thread`
  — o pywebview lendo propriedades da janela de fora da thread certa;
- `AccessibilityObject.Bounds ... maximum recursion depth exceeded` e
  `ActiveControl ...` — a mesma coisa, do lado da acessibilidade do
  Windows;
- no teste com `--previa` o console saiu em branco, porque o processo foi
  morto no meio (o Python não chega a esvaziar o buffer dos `print`).

O que importa é a janela aparecer no segundo monitor e responder.

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
