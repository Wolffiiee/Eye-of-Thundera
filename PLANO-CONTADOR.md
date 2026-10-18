# PLANO — Contador de uso

> Documento de trabalho da rodada de 18/10/2026.

## O que o programa faz hoje

O Eye of Thundera **não mostra** quanto o Wolf usa. Se ele manda 200 mensagens
num dia, ou esbarra na cota do Gemini, ou a fatura do Google cresce, ele só
descobre na hora de olhar a conta — ou quando dá erro.

## O que vamos adicionar

Um contador simples, visível na tela, que responde: "quanto eu usei hoje?".

### Onde fica

Rodapé da tela, ao lado da dica de atalhos que já existe
(`Enter envia · Shift+Enter quebra a linha`).

Exemplo: `Enter envia · Shift+Enter quebra a linha · hoje: 23 mensagens`

### O que conta

- **Só o que vai para a IA.** Lembretes, plugins e busca de imagens são
  locais e gratuitos — não devem entrar na conta.
- Conta **uma vez por pergunta**, no momento em que ela sai para a IA.

### Onde fica guardado

Arquivo novo `contagem.json`, na pasta de dados
(`%LOCALAPPDATA%\Eye of Thundera`), junto do `config.json`.

Formato:
```json
{
  "2026-10-18": 23,
  "2026-10-17": 41
}
```

Guarda só os **últimos 30 dias**, para o arquivo não crescer para sempre.
Ao virar o dia, a contagem zera sozinha (o dia é a chave).

### Detalhes que importam

- Contagem **zerada no primeiro dia**: um número absurdamente alto (bug antigo,
  arquivo copiado do PC de outra pessoa) não pode assustar o Wolf.
- Um **guarda** para a data virar (comparar com a data de hoje ao ler).
- O contador **nunca pode derrubar o programa**: se o arquivo falhar, a tela
  simplesmente não mostra nada.
- Botão para **zerar** na aba Conversa, caso o Wolf queira recomeçar.

## Por que um arquivo separado

Se a contagem morasse no `config.json`, cada mensagem reescreveria o arquivo
de configuração — que guarda as **chaves de API**. Mexer nele o tempo todo é
arriscado demais para o ganho. Arquivo separado = zero risco.

## Como vamos testar

1. Contar uma pergunta normal (soma 1)
2. Pergunta de lembrete **não** soma (é local)
3. Pergunta de plugin **não** soma (é local)
4. Vira o dia → zera
5. Arquivo corrompido → não quebra
6. Arquivo ausente → não quebra
7. Só guarda os últimos 30 dias

Nada disso toca os dados reais: os testes usam pasta temporária em `_tmp`.

---

## Andamento

### ✅ `contagem.py` criado e testado

O módulo já existe e passa em **todos os testes** (`_tmp/testar_contagem.py`):

| Teste | Resultado |
|---|---|
| Começa em zero | OK |
| Soma 1, 2, 3 | OK |
| Soma várias de uma vez | OK |
| Conta separada por dia | OK |
| Somar ontem não mexe em hoje | OK |
| Arquivo corrompido → 0, e volta a contar | OK |
| Valores errados são descartados | OK |
| Arquivo ausente → cria sozinho | OK |
| Guarda no máximo 30 dias (hoje sempre fica) | OK |
| Zerar | OK |

**Bug encontrado no caminho:** a validação aceitava uma chave torta
(`"xyz": 5`) como se fosse um dia. Corrigido com `_data_valida()`, que só
aceita data no formato `YYYY-MM-DD`.

**Ponto de atenção (resolvido):** número absurdo vindo de arquivo copiado
do PC de outra pessoa (`999999999`) — o módulo lê, mas a tela vai avisar
antes de mostrar algo assim.

### ✅ Ligado no programa (`app_web.py`)

A contagem acontece no ponto exato em que a pergunta **sai mesmo para a IA**
(logo depois da checagem de chave). Tudo que volta antes — lembrete, plugin,
busca de imagens, índice do documento — é local e **não entra na conta**.

Duas funções para a tela:
- `uso_hoje()` — o número de hoje (número absurdo vira 0, para não assustar)
- `uso_zerar()` — zera a contagem

### ✅ Na tela (`web/`)

- **Rodapé**, ao lado da dica de atalhos, numa etiqueta arredondada discreta
- Atualiza sozinha: ao abrir o programa e a cada resposta recebida
- **Clicar** na etiqueta pergunta e zera
- Se o programa não conseguir ler o contador, ela **some** em silêncio (é só
  um extra de informação, nunca um erro)

### ✅ Conferido na tela de verdade

| Situação | Resultado |
|---|---|
| 23 perguntas | `hoje: 23 perguntas` |
| 1 pergunta | `hoje: 1 pergunta` (singular) |
| 0 | `hoje: 0 perguntas` |
| Contador indisponível | some da tela |
| Volta ao normal | aparece de novo |

### ⏳ Falta

Ligar os testes no `verificar.py`, recompilar o EXE e documentar.

---

**Estado:** pronto e conferido na tela. Falta fechar os testes e recompilar.