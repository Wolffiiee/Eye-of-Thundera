# Plano: pasta "Eye of Thundera" so com o necessario para rodar

Para as outras IAs. Escrito em 17/10/2026, ANTES de copiar qualquer coisa.
Pedido do Wolf: uma pasta em D:\Projetos com o nome do programa, so com os documentos
necessarios para ele rodar, para ele ter uma ideia de como ficaria. E' uma COPIA: a
pasta de trabalho D:\Projetos\Eye of Thundera continua sendo a original e nada nela muda.

## Destino
D:\Projetos\Eye of Thundera   (nao apagar nem sobrescrever a pasta se ela ja existir:
avisar o Wolf e criar com sufixo)

## Entra (so o que o programa usa para abrir e funcionar)
- app_web.py, eye_of_thundera.py, memoria.py, roteador.py, voz.py, pdf_leitor.py, lembretes.py
  (os `import` do app_web.py e do eye_of_thundera.py; conferido por teste de import)
- web/index.html, web/app.js, web/estilo.css   (a tela; busca.js so entra quando o index.html passar a usar)
- icone.ico            (icone da janela: app_web.py usa RAIZ / "icone.ico")
- requirements.txt     (bibliotecas, versoes fixadas)
- "1 - Instalar.bat" e "2 - Abrir Eye of Thundera.bat"   (instala uma vez / abre)
- LEIA-ME.txt (curto, para quem abrir a pasta)

## Fica de fora (e por que)
- .venv (grande e recriado pelo "1 - Instalar.bat"), .git, build, dist, __pycache__
- verificar*.py/.bat, ferramentas/, _tmp, _troca, _arquivo_morto, Backup, .codex:
  testes e apoio para desenvolver, nao para rodar
- todos os .md de plano/historico/guia, .spec, backups, imagens soltas (avatar_usuario.png
  e Gemini_*.png nao sao usadas pela tela nova), web/spike_webview.py, btns.txt, check_btns*.py
- Dados do Wolf (chave, conversas, memoria, lembretes) ficam em %LOCALAPPDATA%/Eye of Thundera
  e NAO sao copiados: a pasta nova abre limpa ou usa os mesmos dados se rodar na mesma conta.

## Conferencia
1. `python -c "import app_web"` dentro da pasta nova (usando o .venv da original) sem erro de modulo.
2. Listar o que entrou e o tamanho total para mostrar ao Wolf.
3. NAO abrir o programa nem mexer em dados reais.

## Nao fazer
Nao mover arquivos da original. Nao copiar chave/dados. Nao apontar o atalho da Area de
Trabalho para a pasta nova sem o Wolf pedir.

## Atualizacao 18/10
A lista agora e' descoberta pelo script ferramentas/gerar_pasta_limpa.py (le os import a partir do app_web.py e o que o index.html carrega), entao modulos novos (ex.: documento.py) entram sozinhos. Rode de novo para atualizar a pasta; ele so copia por cima e confere o import com -B.
