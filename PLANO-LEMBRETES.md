# Plano: lembretes ("me lembra amanha as 9h de pagar a conta")

Para as outras IAs. Escrito em 17/10/2026, ANTES do codigo.
Origem: Prioridade 8 do SUGESTOES-MELHORIAS-Eye-of-Thundera.md (Wolf escolheu comecar por ela).

## O que o Wolf ganha
Escreve na conversa, em portugues normal, e o programa guarda o lembrete. Na hora
marcada (com o programa aberto) aparece um cartao na tela com "Feito" e "Adiar 10 min".
Se o programa estava fechado, o cartao aparece assim que ele abrir. Nada vai para a
internet e a IA nao e' chamada (nao gasta token, funciona ate sem chave).

## Frases entendidas (tudo local, sem IA)
- criar: "me lembra amanha as 9h de pagar a conta", "me lembra de ligar pro Joao daqui a
  30 minutos", "me lembra segunda as 14h30 de reuniao", "me lembra dia 25 de comprar pao",
  "me lembra 20/10 as 7h de X", "me lembra hoje as 18h de jantar", "me lembra depois de
  amanha as 10 da noite de X"; "lembrete: ..." tambem vale.
- listar: "meus lembretes".
- cancelar: "cancelar lembrete 2" (numero da lista "meus lembretes").
- Frase que so PARECE lembrete ("como me lembrar de coisas?") vai para a IA como sempre:
  a frase precisa COMECAR com "me lembra/lembre/avisa/avise", "lembra-me" ou "lembrete".
- Sem horario ("me lembra de algo"): responde pedindo quando, sem criar nada.
  Exceto "me avisa ..." sem horario, que segue para a IA (pode ser pergunta normal).

## Arquivos
- NOVO lembretes.py: `entender(texto, agora)`, `responder(texto, agora, arquivo)`,
  armazenamento em `%LOCALAPPDATA%/Eye of Thundera/lembretes.json` (lista de
  {id, texto, quando (ISO), feito}), `vencidos`, `concluir`, `adiar`, `apagar`.
  Sem dependencia externa. Arquivo estragado = lista vazia (nunca derruba o app).
- app_web.py: em `Ponte.enviar`, depois do bloco DEMO e ANTES da checagem de chave,
  `lembretes.responder(...)`; se devolver texto, responde na conversa sem chamar a IA.
  Metodos novos: `lembretes_vencidos`, `lembrete_concluir`, `lembrete_adiar`.
  Em modo --demo nao grava nem avisa nada.
- web/app.js + estilo.css: de 30 em 30 s (e ao abrir) pergunta `lembretes_vencidos`;
  mostra cartoes fixos no canto, cores do tema (variaveis CSS), com role="alert".
  Cada id so aparece uma vez por sessao ate virar "Feito" ou "Adiar".
- verificar.py: testes do interpretador (datas fixas), do armazenamento (arquivo em
  `_tmp/`, nunca o real), da ponte e do HTML/JS.
- Tela de verdade fica para depois: nao ha aba nova, tudo pela conversa.

## Nao fazer
Nao usar servico em segundo plano nem notificacao do Windows nesta rodada (pywebview
nao tem; so avisa com o programa aberto - dizer isso ao Wolf). Nao gravar no arquivo
real nos testes. Nao mudar o resto do `enviar`.

## Ideias futuras
Repetir ("todo dia as 9h"), notificacao nativa do Windows, aba "Lembretes" nas Configuracoes.
