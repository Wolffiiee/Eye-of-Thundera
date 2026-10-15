# Histórico de mudanças

Registre aqui toda mudança relevante (a mais nova em cima): o que foi
baixado/instalado, modificado, adicionado, removido ou movido.

---

## 2026-10-15 — Tarefa A: amigo que só pesquisa quando precisa

- **Pedido do Wolf:** executar o `PLANO-NOVAS-FUNCOES.md`, Tarefa A.
- **Adicionado:** `roteador.py` (funções puras, só biblioteca padrão, sem
  importar o programa): `regra_local` (cumprimento e comandos `/web` e
  `/papo` decidem na hora, sem gastar IA), `decidir` (regra -> modelo com
  JSON -> heurística de reserva, nunca trava), `heuristica_pesquisa` (só
  pesquisa com palavras de "agora"), `fato_pedido` ("lembra que..." vira
  fato) e `prompt_roteador`.
- **Adicionado:** `PLANO-NOVAS-FUNCOES.md` (plano escrito pelo Claude,
  colocado na pasta pelo Wolf).
- **Modificado:** `pesquisa_ia.py`:
  - `INSTRUCOES` agora abre com "amigo bem informado"; novo
    `INSTRUCOES_AMIGO` (tom de amigo, sem web, sem inventar fatos).
  - `instrucoes_da_ia(modo="pesquisa")`, e o `modo` passa por
    `_gerar_texto`, `_chamar_servico` e `_gerar_texto_rapido` (amigo usa
    temperatura 0.7 e 12 falas; pesquisa continua 0.3 e 6).
  - `perguntar(..., consulta=None)`: a busca usa a consulta do roteador; o
    prompt final continua com a pergunta original.
  - `conversar`: prompt curto (data + pergunta + conversas); bloco de
    memória duplicado removido (a memória já vai no `instrucoes_da_ia`).
  - `_enviar`: a decisão sai da thread da tela e vai para a thread de
    fundo (`_decidir_modo` com o modelo rápido e 8 s de limite); status
    "Pensando..." e depois "Pesquisando na web..." ou "Conversando...".
    Imagens e notícias explícitas continuam pesquisando como antes.
    "Lembra que..." grava direto na memória, sem gastar IA.
  - Novo `cfg["modo_pesquisa"]` (auto|sempre|nunca) com botão pequeno
    ("Web: automática", clique alterna) sob a caixa de digitar, e novo
    `cfg["aprender"]` (padrão ligado). Aprendizado agora roda quando a
    fala tem 12+ caracteres OU a resposta 120+.
  - `_quer_pesquisa` ficou sem uso (o roteador assumiu); mantida no código
    por enquanto.
- **Modificado:** `verificar.py`: 20 testes novos do roteador (regras,
  JSON limpo/cercado/lixo/erro, frases reais, fato pedido, prompts).
- **Não testado:** pergunta real à IA nem uso longo (precisa da chave e do
  Wolf). Os controles de modo na aba Conversa das Configurações ficam
  para a Tarefa D (a aba ainda não existe).
- **Testado:** `verificar.py` = TUDO CERTO. Sem .exe novo (o plano só pede
  .exe ao final de B, C e D).

---

## 2026-10-15 — Duplo/triplo clique, .exe novo e pasta antiga apagada

- **Pedido do Wolf:** fazer tudo que desse, trabalhar só com a pasta nova,
  apagar a antiga e deixar instruções para outra IA continuar.
- **Modificado:** `pesquisa_ia.py` (`_criar_bolha`): duplo clique seleciona
  a palavra, triplo clique seleciona o texto todo da bolha. Ambos limpam as
  outras seleções e avisam os menus abertos (`_despachar_clique`).
- **Modificado:** `verificar.py`: dois testes novos (duplo e triplo clique).
- **Adicionado:** `PROXIMOS-PASSOS.md` (o que falta e o que não foi
  testado) e `requirements-lock.txt` (`pip freeze` completo do .venv).
- **Reescrito:** `PROMPT-PARA-A-IA.md` (estado atual, sem a pasta antiga).
- **Textos:** o usuário agora é chamado de Wolf (apelido) nos guias; o nome de
  usuário do Windows continua Igor (aparece em caminhos).
- **Gerado:** `dist\Pesquisa IA.exe` de novo (PyInstaller 6.22.3), copiado
  para a Área de Trabalho. O anterior foi movido para
  `_arquivo_morto\Pesquisa IA (Area de Trabalho, antes de 15-10).exe.antigo`.
  O .exe novo abriu e ficou 12 s aberto sem criar `erro.log`.
- **Apagado:** o conteúdo da pasta antiga
  `C:\Users\Igor\OneDrive\Documentos\Projeto Padrão` (autorizado pelo
  Wolf). Só havia de exclusivo um `erro.log` antigo, sem valor. Uma pasta
  vazia pode ter sobrado (travada por outro programa); ignorar.
- **Corrigido neste histórico:** a entrada de 14/10 dizia que a pasta antiga
  tinha sido renomeada para "(ANTIGO - pode apagar)"; na verdade nunca foi
  renomeada. Agora foi apagada.
- **Não testado:** pergunta real à IA e uso longo do .exe.

---
## 2026-10-14 — Mudança de pasta, correção de cliques e organização

### Local do projeto
- **Movido** de `C:\Users\Igor\OneDrive\Documentos\Projeto Padrão`
  para `C:\Projetos\PesquisaIA`.
  Motivos: o OneDrive sincronizava a pasta `.venv` (centenas de arquivos,
  lento e pode corromper) e o nome antigo tinha acento (`ã`), que já
  causava texto quebrado em scripts.
- A pasta antiga ficou como cópia de segurança até 15/10/2026, quando foi apagada (ver a entrada de 15/10 acima). Não existe mais.
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
- `%LOCALAPPDATA%\PesquisaIA\` (conversas, memória, chaves do Wolf).
- `IDEIAS.md`, `PLANO-B.txt`, `avatar_usuario.png`, `icone.ico`.

### Testado
- `verificar.py`: TUDO CERTO (3 rodadas seguidas, sem avisos).
- O .exe novo abriu e ficou aberto 9 s sem criar `erro.log`.
- NÃO testado: perguntas reais à IA (precisa de internet e da chave do
  Wolf) e o uso do .exe por um período mais longo.
