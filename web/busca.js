/* Busca na Memória — sem acento, sem maiúscula e com tolerância a erro de
   digitação. O Wolf digita do jeito que lembra ("conta dluz", "coracao"),
   e a Memória guarda o texto do jeito que a IA escreveu ("conta de luz",
   "coração") — os dois precisam se encontrar.

   Tudo roda na tela, sem Python e sem dependência: o custo é um Levenshtein
   por palavra, e a Memória guarda no máximo 200 itens (ver LIMITE em
   app.js), então cada tecla custa poucos milissegundos. */

"use strict";

// NFD separa a letra do acento; tirando as marcas combinantes, "coração" e
// "coracao" viram a mesma palavra.
function busca_normalizar(texto) {
  return String(texto || "").toLowerCase().normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "");
}

// Levenshtein: quantas letras (troca, apaga ou insere) pra virar `a` em `b`.
function busca_distancia(a, b) {
  if (a === b) return 0;
  if (!a.length || !b.length) return Math.max(a.length, b.length);
  const anterior = [];
  for (let i = 0; i <= b.length; i++) anterior[i] = i;
  for (let i = 1; i <= a.length; i++) {
    const atual = [i];
    for (let j = 1; j <= b.length; j++) {
      atual[j] = Math.min(
        atual[j - 1] + 1,
        anterior[j] + 1,
        anterior[j - 1] + (a[i - 1] === b[j - 1] ? 0 : 1));
    }
    for (let j = 0; j <= b.length; j++) anterior[j] = atual[j];
  }
  return anterior[b.length];
}

// 0 = nada a ver, 1 = igual.
function busca_razao(a, b) {
  const maior = Math.max(a.length, b.length);
  return maior ? 1 - busca_distancia(a, b) / maior : 1;
}

/* Compara um item da Memória com o que a pessoa digitou.

   Devolve { achou, pontos }: `achou` é o filtro (bool) e `pontos` é a
   relevância (1 = o texto digitado está inteiro dentro do item), usada para
   colocar o mais provável primeiro.

   Regra: o termo digitado tem que estar inteiro dentro do item, OU cada
   palavra dele tem que casar com alguma palavra do item — por inteiro (palavra
   dentro de palavra: "casa" em "casas") ou parecida o bastante. Palavra
   curta ("de", "a") quase não erra, por isso o limite é mais rígido para ela.

   Limitação conhecida (aceita de propósito): palavra curta com 1 letra de
   diferença casa — "rato" acha "gato" (75% parecido), a mesma conta que faz
   "gatu" achar "gato". Recusar "rato" obrigaria a recusar erro de digitação
   em palavra curta, e achar o item errado custa menos que o usuário não achar
   o item certo. */
function busca_pontos(texto, termo) {
  const n = busca_normalizar(termo);
  if (!n) return { achou: true, pontos: 0 };
  const t = busca_normalizar(texto);
  if (t.includes(n)) return { achou: true, pontos: 1 };

  const palavrasT = t.split(/\s+/);
  const palavrasN = n.split(/\s+/);
  let soma = 0;
  for (const p of palavrasN) {
    let melhor = 0;
    for (const q of palavrasT) {
      if (q.startsWith(p)) {
        melhor = 1;
        break;
      }
      const r = busca_razao(p, q);
      const limite = (p.length < 3 || q.length < 3) ? 0.84 : 0.72;
      if (r >= limite && r > melhor) melhor = r;
    }
    soma += melhor;
  }
  const pontos = soma / palavrasN.length;
  return { achou: pontos >= 0.72, pontos };
}
