# Tarefa D — Pesquisa profunda (deep research)

Status inicial em 16/10/2026 — documentação rápida antes de implementar.
Escopo: adicionar um modo de pesquisa "séria" que procura em mais sites,
lê mais páginas e devolve resposta organizada em tópicos com fontes citadas.

---

## 1. O que será feito (sub-passos)

### Passo 1 — UI
- Botão "Pesquisa séria" na barra de compositor (web/app.js) que
  ativa/desativa pergunta a pergunta (label "Deep").
- Atalho Ctrl+Shift+S (opcional; pode permanecer como toggle local).
- Indicador visual + status "Pesquisando a fundo...".

### Passo 2 — Backend (pesquisa_ia.py)
- Adicionar `cfg["pesquisa_profunda"]` (bool, default False), que habilita
  deep quando on.
- `_gerar_texto` ganha `profundidade=False` que:
  - aumenta nº de resultados de busca (5 → 9)
  - injeta prompt extra: "Responda de forma organizada em tópicos,
    com fontes por parágrafo."
- `perguntar(pergunta, consulta=None, profundo=False)` repassa o flag.
- No modo `tarefa()`, fazer 2 buscas curtas (query original + variação)
  e citar URLs mais longas.

### Passo 3 — Ponte (app_web.py)
- `Ponte.enviar(texto, profundo=False)`.
- Processar flag na thread `tarefa()`, sem bloquear a UI.
- Roteador mantém 20s; se deep der timeout, cai no fallback (simples).

### Passo 4 — Testes (verificar.py)
- `profundo_ativa`: enviar(texto, profundo=True) passa flag não-bloqueante.
- `profundo_ui`: botão "Pesquisa séria" existe em composer.
- `profundo_offline`: `_gerar_texto(profundidade=True, mocked)` produz
  resposta com seções.
- `profundo_fonte`: resposta tem pelo menos 1 `http` quoted.

### Passo 5 — Docs
- Atualizar `IDEIAS.md` item 2 (marcar como feat) e `ROADMAP.md`.
- Commit + push; (opcional) release `.exe`.

---

## 2. Testes que serão feitos

### Automáticos (verificar.py)
- `profundo_ativa` (enviar devolve imediatamente mantendo flag).
- `profundo_ui` (botão presente).
- `profundo_offline` (sem API, sem vazar crash).
- `profundo_fonte` (mínimo uma URL citada).
- `profundo_toggle_off` (desliga não vaza tokens).

### Manuais (Wolf)
- `profundo_1`: "últimas notícias do Grêmio" com Deep on →
  6+ fontes, organização por tópico.
- `profundo_2`: Click em fontes, abre links.
- `profundo_3`: Deep off vs on → diferenças visíveis.
- `profundo_4`: Custo/tempo — tolerável.

---

## 3. Testes que faltam / devem ser criados pelos testadores

| Teste faltando | Motivo | Como cobrir |
|---|---|---|
| `profundo_ambiente_experimental` (api key) | sem key nova | Rodar com key real |
| `profundo_rede_lenta` | sem timeout resolve bem | Simular latência no DevTools |
| `profundo_search_empty` (DuckDuckGo) | sem internet | Testar offline com Web mock |
| `profundo_palavras_vazias` | regression guard | adicionar assertiva em verificar |
| `profundo_deep_recursive_off` | garantir que off não gasta | Teste flag |

---

## 4. Critérios de aceitação
1. Botão toggle visível e funcionando.
2. Deep off = nenhuma overhead extra.
3. Deep on = resposta organizada com fontes.
4. Sem crash e sem console de debug.
5. `verificar.py` continuando TUDO CERTO.
6. `.exe` build + atalho (preservado se release).

---

## 5. Antes de começar
- Rodar `git status` clean.
- Backup (9 - backup.bat) caso necessário.
- Notificar que `.exe` será regenerado (preservando user data).

---

_Versão 0 — esboço rápido por OC em 16/10/2026._
