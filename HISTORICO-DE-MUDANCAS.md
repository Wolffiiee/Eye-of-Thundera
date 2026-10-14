# Histórico de mudanças

Registre aqui toda mudança relevante (a mais nova em cima): o que foi
baixado/instalado, modificado, adicionado, removido ou movido.

---

## 2026-10-14 — Mudança de pasta, correção de cliques e organização

### Local do projeto
- **Movido** de `C:\Users\Igor\OneDrive\Documentos\Projeto Padrão`
  para `C:\Projetos\PesquisaIA`.
  Motivos: o OneDrive sincronizava a pasta `.venv` (centenas de arquivos,
  lento e pode corromper) e o nome antigo tinha acento (`ã`), que já
  causava texto quebrado em scripts.
- A pasta antiga ficou como cópia de segurança, renomeada para
  `Projeto Padrão (ANTIGO - pode apagar)`. Não trabalhar nela.
- O Git veio junto (histórico completo preservado).
- O ambiente `.venv` foi **recriado** do zero no local novo (venv não é
  movível), com Python 3.12.10.

### Baixado / instalado (no `.venv` novo)
Programa (`requirements.txt`, agora com versões fixas):
- google-genai 2.30.1, ddgs 9.16.0, pyspellchecker 0.9.1, pillow 12.3.0
- **httpx 0.28.1** — adicionado ao arquivo porque o código usa `import httpx`
  direto (antes só vinha de carona).
Ferramentas (`requirements-dev.txt`, novo):
- pyinstaller 6.22.3 (gera o .exe), pyflakes 4.0.3 (analisa o código — novo)
- pip atualizado de 25.0.1 para 26.2.1
Dependências automáticas dessas bibliotecas (pydantic, requests, etc.)
foram instaladas junto; não precisam ser listadas.

### Modificado
- `pesquisa_ia.py`:
  - Seleção de texto: `_limpar_selecoes`, `_ao_clicar_fora`,
    `_selecao_propria`, lista `_telas_bolha`; clique novo apaga a seleção
    anterior; Ctrl+C e menu Copiar só usam a seleção da própria bolha.
  - Cliques globais: criados `_despachar_clique`,
    `_registrar_clique_global`, `_remover_clique_global`. Os 3 usos de
    `bind_all`/`unbind_all("<Button-1>")` (menu de ortografia, menu Copiar,
    menu "Excluir" da conversa) agora usam esse sistema.
  - Removida a função morta `_rolar_ajuda` (citava `tela_ajuda`, nome que
    não existe); `_preencher_aba_ajuda(self, pai, ao_rolar=None)` com
    parâmetro opcional.
  - Limpezas do pyflakes: `except ... as erro` sem uso e `global
    _memoria_cache` sem uso.
- `requirements.txt`: versões fixadas (`==`), `httpx` incluído, comentário.
- `Pesquisa IA.spec`: agora também embute `avatar_usuario.png` no .exe
  (antes só o ícone; o .exe da Área de Trabalho ficava sem o avatar).
- `.gitignore`: `*.spec` deixou de ser ignorado (a receita do .exe agora é
  versionada); `_arquivo_morto/` passou a ser ignorado.

### Adicionado
- `verificar.py` + `verificar.bat` — conferência automática com testes de
  tela (seleção, menus, Configurações, erros escondidos), pyflakes e regras
  do projeto. Obrigatória após qualquer alteração.
- `3 - Gerar EXE.bat` — roda o verificador e gera `dist\Pesquisa IA.exe`.
- `requirements-dev.txt`.
- `INSTRUCOES-PARA-IA.md`, `PASSO-A-PASSO.md`, este arquivo e
  `PROMPT-PARA-A-IA.md`.

### Removido do projeto (não copiado para o local novo)
- `cairosvg` e scripts `svg2pdf` — estavam no `.venv` antigo, mas o código
  não os usa.
- Pastas geradas `build/`, `dist/` (antigas) e `__pycache__/`; `.exe` antigo
  da raiz. O `dist\Pesquisa IA.exe` foi regenerado.

### Movido para `_arquivo_morto\` (não apagado)
- `_run41.py`, `_run_debug.py`, `_run_debug2.py` (testes soltos antigos,
  usavam o caminho antigo com acento).
- `pesquisa_ia.backup-antes-da-selecao.py` (versão antes da correção de
  seleção), `erro-antigo-2026-10-14.log`, `Pesquisa IA.spec.antigo`,
  `Pesquisa IA.exe.antigo` e a cópia do .exe que estava na Área de Trabalho.

### Substituído fora do projeto
- `Pesquisa IA.exe` na Área de Trabalho (em
  `C:\Users\Igor\OneDrive\Área de Trabalho`) pelo novo, gerado em
  `C:\Projetos\PesquisaIA\dist`.

### Não mexido
- `%LOCALAPPDATA%\PesquisaIA\` (conversas, memória, chaves do Igor).
- `IDEIAS.md`, `PLANO-B.txt`, `avatar_usuario.png`, `icone.ico`.

### Testado
- `verificar.py`: TUDO CERTO (3 rodadas seguidas, sem avisos).
- O .exe novo abriu e ficou aberto 9 s sem criar `erro.log`.
- NÃO testado: perguntas reais à IA (precisa de internet e da chave do
  Igor) e o uso do .exe por um período mais longo.
