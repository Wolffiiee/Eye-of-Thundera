# GUIA DO OPENCODE (leia ANTES de mexer em qualquer coisa)

Escrito pelo Claude em 16/10/2026 a pedido do Wolf. O Wolf nao programa:
fale em portugues simples, chame-o de Wolf, nunca use jargao sem explicar.

## 1. Regra de ouro: SO EXISTE A VERSAO NOVA
- O programa e' o **Eye of Thundera** (tela em HTML: `app_web.py` + pasta `web/`).
- O programa antigo (tkinter, `Pesquisa IA.exe`) esta APOSENTADO. NAO mexa nele,
  NAO gere .exe dele, NAO crie atalho para ele, NAO crie teste novo para ele.
  Copias antigas ficam em `_arquivo_morto/` (nao apague, nao use).
- `pesquisa_ia.py` ainda e' o MOTOR (memoria, busca, conversa, chaves). Pode e
  deve ser usado/editado quando a tela nova precisar. So o pedaco de TELA
  (classes Tk: Aplicativo, Dica, Botao, Chip, Avatar...) e' lixo morto.
  Proxima limpeza combinada: mover o motor para `nucleo.py` SEM tkinter e deixar
  `pesquisa_ia.py` como ponte fina. Faca em passos pequenos, com `verificar.bat`
  verde entre cada um, e so depois de avisar o Wolf.

## 2. Area de Trabalho: UM icone so
- Deve existir somente `Eye of Thundera.exe`. NADA de `.lnk` extra, nada de
  "Pesquisa IA", nada de "Wolf.lnk".
- Quem cuida disso e' `atualizar_area_trabalho.py` (chamado por `Gerar o EXE.bat`).
  Nao crie outros scripts que mexam na Area de Trabalho.
- Antes de dizer "pronto": liste a Area de Trabalho e CONFIRA com os olhos.
- Confira tambem que o hash do .exe da mesa == `dist\Eye of Thundera.exe`.

## 3. Como trabalhar sem errar
1. `git status` e `git log -5` primeiro. Leia `ONDE-PARAMOS.md`.
2. Mude o MINIMO. Um assunto por vez. Um commit por assunto.
3. Rode `verificar.bat`. So diga que terminou se a ultima linha for TUDO CERTO.
   NUNCA apague teste para "passar".
4. Mexeu em `web/` ou `app_web.py`? Gere o .exe (`Gerar o EXE.bat`), abra-o de
   verdade e confira a tela. Teste no codigo nao enxerga tela quebrada.
5. Caminhos: o projeto vive em `D:\Projetos\PesquisaIA`. Nao escreva caminho
   fixo em codigo novo (use `Path(__file__)`). Nunca use `C:\Projetos`.
6. Nunca apague arquivos do Wolf (conversas, memoria, config). Para "sumir"
   algo, MOVA para `_arquivo_morto/`.
7. Nunca mostre nem grave chave de API em arquivo do projeto, log ou commit.
8. Termine SEMPRE atualizando `ONDE-PARAMOS.md` (estado) e
   `HISTORICO-DE-MUDANCAS.md` (o que mudou e por que).

## 4. LIMITE DE USO: trocar para modelo GRATIS antes de parar
Quando aparecer erro 429, "rate limit", "quota", "credits", ou voce sentir que
o contexto esta acabando:
1. Termine o passo atual em estado seguro (verificar verde, commit feito).
2. Escreva em `ONDE-PARAMOS.md` onde parou e o proximo passo.
3. Rode `.venv\Scripts\python.exe ferramentas\trocar_modelo_gratis.py`
   (ou peça ao Wolf o duplo clique em `10 - Trocar para modelo gratis.bat`).
   Ele testa, em ordem, a lista de `ferramentas\modelos-gratis.txt` e grava no
   `opencode.json` o primeiro que responder (com copia de seguranca).
4. Diga ao Wolf: "Troquei para <modelo> (gratis). Abra uma sessao nova e
   mande 'continuar'." Na sessao aberta, `/models` troca na hora.
5. Se a lista ficar velha: `opencode models | findstr /i "free"` e ajuste o txt.
6. Modelo gratis e' mais fraco: faca tarefas pequenas, leia o codigo antes de
   editar, rode `verificar.bat` com mais frequencia.
Observacao: o 9router (`9router/Arsenal`) e o Ollama so funcionam se estiverem
ligados; o script pula sozinho o que nao responder.

### Troca automatica (ja instalada)
O OpenCode usa o plugin **opencode-runtime-fallback** (em opencode.json, campo plugin). A lista de modelos dele fica em %USERPROFILE%\.config\opencode\opencode-fallback.json. Quando um modelo estourar o limite, ele passa para o proximo da lista sozinho. NAO instale outro plugin de troca por cima (brigam entre si). Se a lista ficar velha, confira com: opencode models e tire os nomes que sumiram.
Backup do plugin proprio que escrevi (nao instalado): ferramentas\opencode-gratis-sempre.js + 11 - Instalar plugin gratis-sempre.bat (so usar se o runtime-fallback der problema; remover o outro antes).

## 5. Checklist de entrega
[ ] verificar.bat = TUDO CERTO   [ ] .exe novo aberto e olhado
[ ] Area de Trabalho = 1 icone   [ ] ONDE-PARAMOS + HISTORICO atualizados
[ ] commit feito                 [ ] avisei o Wolf em portugues simples

## 6. Armadilhas ja vistas (16/10)
- Os arquivos Eye of Thundera.spec e Eye of Thundera (debug).spec DEVEM empacotar **app_web.py**. Com pesquisa_ia.py o .exe abre o programa ANTIGO.
- Depois de gerar o .exe: ABRA e confira (titulo da janela Eye of Thundera, sem caixa de erro). Nunca deixe codigo de depuracao (gravar em eyethundera_debug.txt) no app_web.py.
- webview.start() so pode ser chamado UMA vez, no fim de principal().

