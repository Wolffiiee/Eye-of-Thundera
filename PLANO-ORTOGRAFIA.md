# Plano: melhorar a correcao ortografica

Para as outras IAs. Escrito em 18/10/2026, ANTES do codigo.

## Como e' hoje (tela nova)
- Sublinhado vermelho: corretor do proprio WebView2 (`spellcheck` na caixa, ligado/desligado por
  `web_corretor`). Nao da para mexer nele por fora.
- Botao direito numa palavra: a tela monta o proprio menu (WebView2 desliga o menu padrao) e chama
  `Ponte.sugerir_correcao` -> `eye_of_thundera.sugerir_correcao` (pyspellchecker pt, com en de apoio).
- Dores: a 1a busca leva ~4 s (carrega o dicionario so na hora); nomes do Wolf e giria de chat
  ("vc", "tb", "pq") nao tem sugestao boa; nao ha como "ensinar" uma palavra; ranking so por frequencia.

## Melhorias (todas locais, sem dependencia nova, cada uma com teste)
1. Aquecer os dicionarios em segundo plano ao abrir o programa (thread daemon), para o 1o clique
   direito ser instantaneo.
2. Abreviacoes de chat -> palavra certa, oferecidas como 1a sugestao: vc->voce(com acento), tb/tbm->tambem,
   pq->porque, oq->o que, msm->mesmo, hj->hoje, td->tudo, blz->beleza, obg->obrigado, qdo->quando, etc.
3. Restaurar acento primeiro: "voce"->"voce com acento", "nao"->"nao com acento" (comparar sem acento
   com palavras do dicionario) antes das sugestoes por distancia.
4. Dicionario pessoal: arquivo `dicionario_pessoal.json` em %LOCALAPPDATA%/Eye of Thundera (lista simples,
   leitura robusta: arquivo estragado = vazio). Palavra nele nunca recebe sugestao de "corrigir".
   Nomes proprios da Memoria (palavras com inicial maiuscula nos fatos) entram como "conhecidas" sem
   gravar nada.
5. Menu do botao direito: item "Adicionar ao dicionario" quando a palavra e' desconhecida
   (Ponte.dicionario_adicionar(palavra)); confirmacao em aviso curto. Modo --demo nao grava.
6. Ranking melhor: mesma 1a letra e menor distancia primeiro, depois frequencia; no maximo 6.

## Arquivos
eye_of_thundera.py (sugerir_correcao + helpers; o programa antigo usa a mesma funcao: nao pode quebrar),
app_web.py (Ponte: aquecer + dicionario_adicionar), web/app.js (item do menu), verificar.py
(testes com arquivo em _tmp/, nunca o real).

## Nao fazer
Nao trocar o corretor do navegador por um proprio (sublinhado desenhado a mao): fica para depois,
e' grande. Nao enviar texto digitado para nenhum servico. Nao apagar testes antigos de sugerir_correcao.
