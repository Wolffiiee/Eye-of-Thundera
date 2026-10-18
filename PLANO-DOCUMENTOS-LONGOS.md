# Plano: perguntar sobre um documento longo (Prioridade 7 das sugestoes)

Para as outras IAs. Escrito em 17/10/2026, ANTES do codigo.
Origem: SUGESTOES-MELHORIAS-Eye-of-Thundera.md, Prioridade 7. O modo offline (Ollama,
Prioridade 4) foi CANCELADO pelo Wolf: o programa segue so com as APIs.

## Problema de hoje
Um PDF arrastado vira TEXTO na caixa de digitar (ate 200.000 caracteres) e vai inteiro
numa unica mensagem. Em documento longo isso e' lento, caro (token) e a IA se perde.

## Ideia (simples, local e sem dependencia nova)
"Documento aberto": ao arrastar um PDF com mais de uns poucos paginas, o programa
pergunta se quer ABRIR como documento. Aberto, o texto fica na memoria do programa,
dividido por pagina, e as perguntas seguintes mandam para a IA so os TRECHOS
relevantes (busca local por palavras, sem acento) com o numero da pagina, e a IA
responde citando "(pag. N)". Nada do documento e' enviado antes de o Wolf perguntar.

## Pecas
- NOVO documento.py (sem biblioteca externa, testavel):
  - `abrir(nome, paginas)` guarda texto por pagina; `indice()` = lista de paginas com a
    primeira linha (titulos provaveis: linha curta, numerada ou em CAIXA ALTA);
  - `trechos(pergunta, quantos=6)` ranqueia pedacos de ~1200 caracteres por palavras da
    pergunta (sem acento, sem palavras comuns), devolve [(pagina, texto)];
  - `montar_pergunta(pergunta)` = instrucao curta + trechos com "[pag. N]" + a pergunta;
  - `fechar()`. Tudo limitado (300 paginas, 200.000 caracteres: os mesmos do pdf_leitor).
- pdf_leitor.py: oferecer o texto POR PAGINA (hoje junta tudo): nova funcao, a antiga fica igual.
- app_web.py: Ponte `documento_abrir(id)`, `documento_info()`, `documento_fechar()`;
  em `enviar`, se ha documento aberto e a frase nao e' lembrete, a pergunta e' trocada por
  `montar_pergunta` SO na chamada da IA; na conversa aparece a pergunta do Wolf como ele
  escreveu. Comandos locais: "indice do documento", "resumir documento" (resumo por partes).
- web/app.js + estilo.css: cartao acima da caixa "documento.pdf - 42 paginas [Fechar]",
  cores do tema (variaveis CSS), acessivel (role="status", botao com rotulo).
- verificar.py: documento.py com paginas sinteticas (acha a pagina certa, ignora acento,
  respeita limites, indice), ponte com janela falsa, HTML/JS (cartao e botao Fechar).

## Fases
1. documento.py + testes (sem tela).  2. Ponte + `enviar`.  3. Cartao na tela.  4. Docs.

## Nao fazer
Nao mudar o caminho atual de PDF pequeno (texto na caixa) nem de .txt/.md/.csv.
Nao gravar o documento em disco. Nao mandar o documento inteiro para a IA. Nada de
telemetria. Nao mexer em web/busca.js (outra IA esta nele).
