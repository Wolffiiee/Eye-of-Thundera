# PLANO — Aviso de cota

> Documento de trabalho da rodada de 18/10/2026.

## O que acontece hoje

Quando a cota do Gemini acaba, o programa **troca de provedor sozinho** e
continua funcionando. O problema é que isso é **silencioso**: o Wolf não faz
ideia de por que as respostas mudaram de repente de estilo, nem de que está
gastando a cota do outro serviço.

Quando não há reserva nenhuma, o erro aparece como mensagem de erro comum.

## O que vamos adicionar

Um aviso honesto e **não repetitivo**, dizendo o que aconteceu.

### Onde aparece

- **Na conversa**, como uma faixa discreta acima da última resposta
  (não como erro: não é erro, é um aviso).
- Some sozinha depois de um tempo, como os outros avisos da tela.

### O que diz

Quando entrou no plano de reserva:
> ⚠ A cota do Gemini acabou por agora. Estou respondendo com o Groq.

Quando não sobrou nada:
> ⚠ A cota do Gemini acabou e não há chave de reserva cadastrada. O programa
> vai continuar tentando o Gemini — mas pode demorar até a cota voltar.

### Regra importante: não encher o saco

O aviso **não pode aparecer a cada pergunta**. Depois de avisar uma vez,
fica quieto por **1 hora**. E se a cota voltar a funcionar, o programa
**perdoa** e volta a avisar na próxima vez que precisar.

Nada de salvar isso em arquivo: é uma coisa da sessão, morre quando o
programa fecha. Isso é proposital — é estado temporário, não dado do usuário.

## Como vamos saber que é cota

O Google responde com **erro 429** ou com a palavra `quota` /
`RESOURCE_EXHAUSTED` no texto. Isso já é reconhecido pelo motor hoje, mas
só para escrever a mensagem de erro. Vamos reaproveitar o mesmo reconhecedor
para o aviso — **sem criar uma segunda lista de palavras**, que é como
esses avisos ficam errados com o tempo.

## Como vamos testar

1. Erro de cota é reconhecido
2. Aviso aparece **uma vez**, não a cada pergunta
3. Depois de 1 hora, avisa de novo
4. Cota voltou → **perdoa**, não avisa mais
5. Erro de **chave** não gera aviso de cota (são coisas diferentes)
6. Erro de **internet** não gera aviso de cota
7. Aviso com e sem chave de reserva, com o texto certo
8. Nada disso derruba o programa

Nada disso toca os dados reais: os testes usam pasta temporária em `_tmp`.

## ⚠️ O que descobri no caminho (e era um BUG de verdade)

Fui mexer no aviso assumindo que o programa **já trocava de provedor quando a
cota acabava**. Testei e... **não trocava**.

O `tentar_com_reserva` só trocava quando a **chave era recusada**. Quando a
**cota** acabava, ele levantava o erro — mesmo com a chave de reserva
perfeitamente configurada. Ou seja: o Wolf perdia o programa inteiro por um
limite que se renova sozinho.

Pior: quando corrigi o primeiro problema, apareceu o segundo. Na segunda
tentativa o código olhava `estado["falhou"]`, que é `False` no caso da cota
(a chave está ótima, só o limite que acabou) — então chamava o **Gemini de
novo** em vez da reserva. Feito de qualquer jeito, a troca nunca funcionava.

**Os dois foram corrigidos.** Agora a cota cai na reserva de verdade.

## Como ficou

| Situação | O que acontece |
|---|---|
| Cota acaba, **tem** reserva | Responde pela reserva + aviso amarelo |
| Cota acaba, **sem** reserva | Falha (não há para onde ir) |
| Chave é recusada | Reserva, como sempre (não muda) |
| **Internet** caiu | **Não** troca (repetir na mesma rede não adianta) |

Detalhe importante: quando a cota cai na reserva, o estado `falhou` **não**
é ligado. A chave está ótima — é só o limite. Então na pergunta seguinte o
Gemini volta a ser o principal, e se a cota voltou, tudo segue normal.

## Andamento

### ✅ `cota.py` — o aviso

Passa em todos os testes (`_tmp/testar_cota.py`):

- avisa **uma vez**, não a cada pergunta (1 hora de silêncio)
- depois de 1 hora, avisa de novo
- cota voltou → **perdoa**, não fica calado a sessão toda
- erro de **chave** não vira aviso de cota
- erro de **internet** não vira aviso de cota
- o texto muda conforme tem ou não tem reserva

**Não salva em arquivo nenhum:** é estado da sessão, proposital. Morre quando
o programa fecha.

### ✅ Reconhecimento de cota, num lugar só

`_falha_de_cota` ficou no motor, junto do texto de erro. Antes a palavra
"quota" estava escrita dentro do `traduzir_erro`; agora é uma função só, e o
aviso usa a mesma. Duas listas de palavras divergem com o tempo — é assim
que aviso começa a errar.

### ✅ O bug da reserva corrigido

Sete cenários testados (`_tmp/testar_cota_reserva.py`), incluindo os dois
bugs acima, "os dois falham" e "internet não troca".

### ✅ Na tela de verdade

Faixa amarela com ⚠, que **não some sozinha** (é a única vez que o Wolf vai
ver). Clicar fecha, e também fecha por Enter ou Espaço no teclado.
Verificado na tela: as duas variantes de texto, o clique, o teclado e os
atributos de acessibilidade.

---

**Estado:** pronto e conferido na tela. Falta ligar no `verificar.py`.