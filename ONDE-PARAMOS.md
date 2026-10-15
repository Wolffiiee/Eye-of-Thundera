# ONDE A GENTE PAROU (leia isto primeiro)

> Written em 15/10/2026. Se você é uma IA lendo isto: o Wolf não programa.
> Fale com ele em português simples, sem jargão, e chame-o de Wolf.

## Uma linha de resumo
Tela nova do Pesquisa IA em **HTML**: os **passos 1 e 2 estão prontos e
testados**. O que falta é o **passo 3: ligar a IA de verdade** (hoje
`enviar()` responde "passo 3"). O programa antigo (tkinter) **continua
funcionando e não foi tocado** — é o atalho da Área de Trabalho.

## Como ver a tela nova
Duplo clique em **`5 - Ver a tela nova.bat`**. Abre no segundo monitor,
em modo exemplo (conversas de mentira, com emoji colorido), e não mexe em
nada do Wolf.

## Leia nesta ordem antes de mexer em qualquer coisa
1. `INSTRUCOES-PARA-IA.md` — as regras e as armadilhas já descobertas
2. `PASSO-A-PASSO.md` — o método (achar a causa, mudar o mínimo, testar)
3. `HISTORICO-DE-MUDANCAS.md` — tudo que foi feito, com a causa de cada bug
4. `PROXIMOS-PASSOS.md` — **é aqui que está o plano dos 8 passos**
5. `web/LEIA-ME.md` — como a tela nova conversa com o Python

Depois rode `verificar.bat`. **Só diga que terminou se a última linha for
"TUDO CERTO"**.

## Estado atual (confie, foi conferido)
- `verificar.bat` = **TUDO CERTO**, com **18 testes** só da tela nova.
- O `.exe` da Área de Trabalho (19:23) está **atualizado** e roda sem erro.
- O `.git` está limpo; último commit `75d6738` (passo 2).
- Teste instável já consertado (o do foco da caixa de digitar).

## O próximo passo: PASSO 3 — a IA
É o passo grande e o mais importante. O que já está pronto para ele:
- `app_web.py` tem `Ponte.mensagens` e `Ponte.id_atual` (a conversa
  aberta mora na ponte) e o método `_gravar_conversa()`, que grava no
  arquivo quando há mensagem nova. **O passo 3 é quem chama isso.**
- O `web/app.js` já está ouvindo o Python: `window.PIA.evento({tipo: ...})`
  com `tipo` = `"etapa"` (o que ele está fazendo), `"resposta"` ou
  `"erro"`. Use `json.dumps(..., ensure_ascii=False)` para não estragar
  acentos e emoji.
- Do lado do Python, a lógica que chama o Gemini e faz a busca está no
  `pesquisa_ia.py` (função `perguntar`, mais o `_chamar_servico` e a
  chave reserva). **Reaproveite, não reescreva.**

### Como mandar um evento do Python para a tela
```python
import json
janela.evaluate_js(
    "window.PIA.evento(" + json.dumps(
        {"tipo": "etapa", "texto": "Pesquisando na web..."},
        ensure_ascii=False) + ")"
)
```

## Regras que não podem ser quebradas
1. **Nenhuma janela branca.** Todo aviso/erro/pergunta é
   `_dialogo_escuro(...)` (ou `_confirmar`). `messagebox`, `simpledialog`
   e `tk_optionMenu` são PROIBIDOS — o `verificar.py` reprova.
2. **Janela de teste sempre no segundo monitor** (X >= 1950). O
   `verificar.py` já faz isso (`POSICAO_TESTE = "+2000+100"`).
3. **Nada de `unbind_all("<Button-1>")`.** Menus usam
   `_registrar_clique_global` / `_remover_clique_global`.
4. **Nunca mexer nos dados do Wolf** (`%LOCALAPPDATA%\PesquisaIA`) nos
   testes: aponte `p.ARQUIVO_HISTORICO` e `p.ARQUIVO_MEMORIA` para uma
   pasta em `_tmp` e restaure no fim (veja a seção 5d do `verificar.py`).
5. **Nunca apagar nem renomear o `pesquisa_ia.py`.** A tela nova nasce ao
   lado da antiga. Só trocar quando a nova estiver igual ou melhor.
6. Nada de API key escrita no projeto; nada de mexer no histórico/git do
   usuário.
7. Depois de mexer: `verificar.bat` verde, commit, e atualizar
   `HISTORICO-DE-MUDANCAS.md` + este arquivo + `PROXIMOS-PASSOS.md`.

## Armadilhas já descobertas (não repetidas)
- O Tk desenha emoji de **uma cor só**. Na tela HTML sai colorido
  (medido: 63% dos pixels com cor). É por isso que a tela nova existe.
- A ponte do pywebview é **assíncrona**: `window.pywebview.api.algo(...)`
  devolve uma Promise (o `app.js` já usa `await`).
- O `pywebview` precisa estar no `requirements.txt` **e** no spec, senão o
  `.exe` gerado não abre.
- A janela do pywebview não devolve o handle do Windows (devolve o
  controlador do WebView2): para printar, ache a janela pelo título com
  `EnumWindows` + `PrintWindow`.
- O horário da conversa (`%d/%m/%Y as %H:%M`) só tem minuto: **não
  ordenar a lista por ele**. Use `list(reversed(carregar_conversas()))`,
  como o programa antigo.
- A memória não pode perder informação: `memoria.py` tem a regra de ouro
  "organizar nunca pode apagar palavra" e o `autoteste()` barra a volta do
  defeito.
