# ONDE A GENTE PAROU (leia isto primeiro)

> Escrito em 16/10/2026. Se você é uma IA lendo isto: o Wolf não programa.
> Fale com ele em português simples, sem jargão, e chame-o de Wolf.

## Uma linha de resumo
Tela nova do Pesquisa IA em **HTML**: os **passos 1, 2 e 3 estão prontos e
testados** — a IA de verdade responde no passo 3. Falta o **passo 4: o
microfone e o modo web**. O programa antigo (tkinter) **continua
funcionando e não foi tocado** — é o atalho da Área de Trabalho.

## Como ver a tela nova
Duplo clique em **`5 - Ver a tela nova.bat`**. Abre no segundo monitor, em
modo exemplo (as conversas mostradas são de mentira, com emoji colorido).
Desde o passo 3 **a IA de verdade também responde por lá**, mas nada é
gravado — nem conversa, nem memória — enquanto a janela estiver no modo
exemplo. Para usar com as conversas de verdade:
`.venv\Scripts\python.exe app_web.py`.

## Leia nesta ordem antes de mexer em qualquer coisa
1. `INSTRUCOES-PARA-IA.md` — as regras e as armadilhas já descobertas
2. `PASSO-A-PASSO.md` — o método (achar a causa, mudar o mínimo, testar)
3. `HISTORICO-DE-MUDANCAS.md` — tudo que foi feito, com a causa de cada bug
4. `PROXIMOS-PASSOS.md` — **é aqui que está o plano dos 8 passos**
5. `web/LEIA-ME.md` — como a tela nova conversa com o Python

Depois rode `verificar.bat`. **Só diga que terminou se a última linha for
"TUDO CERTO"**.

## Estado atual (confie, foi conferido)
- `verificar.bat` = **TUDO CERTO**, com **197 verificações** no total (49
  só da tela nova; as 31 do passo 3 estão em `testes_tela_nova_ia`).
- O `.exe` da Área de Trabalho **não foi regenerado**: o programa antigo
  não teve mudança de comportamento (o passo 3 só *moveu* regras de
  lugar, para as duas telas usarem a mesma), então o `.exe` continua
  igual e continua certo.
- O `.git` está limpo; último commit `1075253` (passo 3).
- **Cuidado: o teste "clicar no texto de apoio não focou a caixa" ainda
  oscila.** Ele falhou em 1 rodada em 8 e as outras passaram. É da tela
  tkinter antiga, não da tela nova — se ele falhar, rode o `verificar.bat`
  de novo antes de achar que quebrou algo.

## Como o passo 3 ficou (leia antes de mexer no `app_web.py`)
`Ponte.enviar(texto)` devolve **na hora** e passa o trabalho para a
thread `_responder`. A tela recebe tudo por eventos.

```python
# como a tela manda o que a IA está fazendo:
self._evento({"tipo": "etapa", "texto": "Consultando a inteligência artificial"})
```
O `_evento` já cuida do `json.dumps(..., ensure_ascii=False)` e engole o
erro se a janela já foi fechada. Os quatro tipos de evento são:
`etapa`, `resposta`, `erro` (com `"chave": True` quando for a chave) e
`conversas` (atualiza a barra da esquerda).

O que reaproveita o `pesquisa_ia.py` (não reescreva): `conversar`,
`perguntar`, `_decidir_modo`, `tentar_com_reserva`, `traduzir_erro`,
`_mesclar_memoria` e `aprender_com_o_usuario`.

## O próximo passo: PASSO 4 — microfone e modo web
A caixa de digitar e o botão enviar **já existem e já funcionam**
(`#entrada` e `#btn-enviar` do `web/index.html`, ligados no
`web/app.js`). O que o passo 4 tem que trazer de novo é:
- o **microfone**: `voz.py` grava e transcreve; o botão `#btn-mic` já
  existe, mas ainda é `aviso_honesto("microfone")`;
- o **modo web**: o botão `#btn-web` e o `definir_modo()` já existem, e o
  modo pesquisado pelo `enviar()` vem de `cfg["modo_pesquisa"]`
  (`auto` / `sempre` / `nunca`). Hoje `definir_modo()` ainda devolve o
  aviso, então dá para só gravar o valor no config.
- o `cfg["voz_enviar"]` (enviar sozinho depois de falar) é desta mesma
  etapa.

O passo 5 é a Tarefa D (Configurações gravando de verdade). Não faça as
duas coisas junto: cada passo é um commit e um `verificar.bat` verde.

## Regras que não podem ser quebradas
1. **Nenhuma janela branca.** Todo aviso/erro/pergunta é
   `_dialogo_escuro(...)` (ou `_confirmar`). `messagebox`, `simpledialog`
   e `tk_optionMenu` são PROIBIDOS — o `verificar.py` reprova.
2. **Janela de teste sempre no segundo monitor** (X >= 1950). O
   `verificar.py` já faz isso (`POSICAO_TESTE = "+2000+100"`).
3. **Nada de `unbind_all("<Button-1>")`.** Menus usam
   `_registrar_clique_global` / `_remover_clique_global`.
4. **Nunca mexer nos dados do Wolf** (`%LOCALAPPDATA%\PesquisaIA`) nos
   testes: aponte `p.ARQUIVO_HISTORICO`, `p.ARQUIVO_MEMORIA` e
   `p.ARQUIVO_CONFIG` para uma pasta em `_tmp` e restaure no fim (veja a
   seção 5d do `verificar.py`). Zere também `p._memoria_cache`, senão a
   memória do teste anterior aparece como se fosse dele.
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
