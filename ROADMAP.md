# ROADMAP — Pesquisa IA (renomeado "Eye of Thundera")

Documento de situação real em 16/10/2026. Define o que já foi feito, o que está
pendente e em que ordem trabalhar quando este projeto for retomado.

---

## 1. Estado atual em uma frase

Programa antigo (Tkinter janela cinza) foi aposentado; toda interface
visível é now HTML em Python via `pywebview` (`Eye of Thundera.exe` /
`pythonw app_web.py`). Motor `pesquisa_ia.py` está intacto. 120 assertivas
no `verificar.py` batem verde. Repo em
`https://github.com/Wolffiiee/Eye-of-Thundera.git`.

---

## 2. O que já foi FEITO (entregues)

### Infra e pré-conds
- Git sincronizado com GitHub (main).
- `.exe` da Área de Trabalho + atalho `.lnk` batem hash, atualizados por
  `atualizar_area_trabalho.py` após cada build.
- `verificar.py`: 0 falhas, 0 avisos.
- Scripts `.bat`: 6 arquivos (install, open, verify, backup código, backup
  dados, build). Programa antigo desativado.
- Backup em `Backup/` com `.exe` + `.lnk`.

### Motor (pesquisa_ia.py) — não alterado estruturalmente
- Pesquisa web, IA Gemini + plano B (Groq, OpenRouter).
- Chaves reserva com troca automática; aviso com botão "criar chave".
- Memória sem repetição + datas separadas (arquivo `memoria_datas.json`).
- Transcrever voz via Gemini (sounddevice) + wav robusto.
- Roteador `_quer_pesquisa`, `_quer_imagens`, `_quer_noticias`.

### Interface nova (HTML, web/)
- 4 abas de configurações parciais (Memória, Conversa, Chaves, Ajuda).
- Caixa de digitar com contorno, microfone, enviar via atalhos
  (Ctrl+M, Ctrl+S, Ctrl+N, Ctrl+F, Ctrl+/-/0).
- Resumo do dia (Ctrl+D), procurar conversas, fixar no topo, privada,
  tamanho de letra.
- Galeria de imagens (photo viewer com setas/arrasto), resposta com
  streaming e fontes.
- Corretor ortográfico com menu do botão direito.
- Barra de título escurecida; janela lembra o monitor onde fechou.

### Work de estabilização (esta rodada)
- Atalho `.lnk` apontando para `pythonw.exe app_web.py` (robusto).
- `2 - Abrir Eye of Thundera.bat` mata instâncias antigas antes de lançar.
- 120 testes rodando; nada de código de regressão (Tkinter tjn).
- Rodapé `.exe`/atalho re-sincronizado.

---

## 3. Backlog previsto (o que AINDA falta)

### 🔴 Tarefa D — Configurações em 4 abas (prioridade)
- Aba **Memória**: busca, editar inline, adicionar, contador "n / 80",
  exportar .txt, "Apagar tudo" com confirm. (parcialmente lá).
- Aba **Conversa**: pesquisa (automática/sempre/nunca), "lembrar assunto",
  corretor ortográfico, voz enviar.
- Aba **Chaves**: cartões Gemini/Groq/OpenRouter, "mostrar", testar,
  "Como conseguir chave", botão Salvar único.
- Aba **Ajuda**: atualizar com pesquisa automática, voz e atalhos.
- Rolagem no mouse em todas as abas; estilo uniforme (24px de margem).

### 🟡 Pesquisa profunda
- Modo "pronta pesquisa sôria" que procura mais sites e devolve resposta
  organizada com fontes citrus (ideia #2).

### 🟡 Entrar com a voz (validação final)
- Código e testes prontos. Falta conferir rodando `Pesquisa IA.exe` e
  speak de verdade pelo Wolf.

### 🟡 Arrastar um arquivo para a conversa
- .txt/.pdf / imagem na janela e perguntar sobre.

### 🟡 Gavetas de memória por assunto
- Memória separada por tema (hoje é única).

### 🟢 Ideias pequenas (opcional)
- Exportar pitch (save response) já feito.
- Pesquisa never "por garantia" (não fazer; decisões por roteador).

---

## 4. Regras de ouro (não esquecer)

1. **Motor `pesquisa_ia.py` nunca apagar/reescriver** — tela HTML nasce
   ao lado; dados do usuário em `%LOCALAPPDATA%\PesquisaIA` intocados.
2. **Janela de testes SEMPRE no 2º monitor** (X≥1950). Print via
   `PrintWindow`, não `ImageGrab`.
3. **Não adicionar bind_all de clique** — usar `_registrar_clique_global`.
4. **Nunca pesquisar na web "por garantia"** — deixa roteador decidir.
5. **Causa primeira; mudança pequena; teste novo no verificar.py;
   commit; histórico.**

---

## 5. Ordem sugerida (próxima rodada)

1. **Tarefa D** — Configurações 4 abas (principal impacto UX)
2. **Voz** — validação de ponta a ponta com GW
3. **Pesquisa profunda** — botão "sério" ao lado do envio
4. **Arrastar arquivo** — peque land/oak
5. **Gavetas de memória** — por assunto (com Wolf abrindo)

---

## 6. Como começar quando este Roadmap for usado

```bash
cd D:\Projetos\PesquisaIA
git pull
.\verificar.bat   # TUDO CERTO
# explorar IDEIAS.md + PLANO-NOVAS-FUNCOES.md
```

> Levante o atalho da Nova UI para confirmar estado real antes de
> iniciar nova feature.

---

*Última atualização: 16/10/2026 — após a estabilização da abertura
do atalho da edição nova e limpeza de debug.*