# Plano: um unico executavel (sem passo-a-passo)

Para as outras IAs. Escrito em 18/10/2026, ANTES de gerar o .exe.
Pedido do Wolf: na pasta limpa, em vez de varios arquivos + "1 - Instalar" + "2 - Abrir", um
executavel com o icone do programa que faca tudo; so colar a chave de API dentro do programa.

## Decisao
O PyInstaller (Eye of Thundera.spec, onefile, windowed, icone=icone.ico) ja gera um
`Eye of Thundera.exe` que NAO precisa de Python nem de instalacao. Entao nao ha instalador a
escrever: a pasta limpa passa a ter so esse .exe (+ LEIA-ME.txt de 4 linhas).
Primeira vez sem chave: `Ponte.enviar` devolve "sem_chave" e a tela abre Configuracoes > Chaves
(web/app.js). Nada de editar arquivo a mao.

## Passos
1. Rodar verificar.py + verificar_motor.py (TUDO CERTO antes de empacotar).
2. `.venv\Scripts\python.exe -m PyInstaller --noconfirm --clean "Eye of Thundera.spec"`
   (o mesmo de "Gerar o EXE.bat"; os dois .spec ja listam pdf_leitor, lembretes, documento,
   pypdf, pypdfium2, winsdk). NAO rodar atualizar_area_trabalho.py (nao mexer no atalho do Wolf).
3. Conferir: abrir o .exe com Start-Process, esperar ~10 s, ver que continua aberto e que nao
   apareceu erro.log em %LOCALAPPDATA%/Eye of Thundera; fechar o processo.
4. Pasta limpa `D:\Projetos\Eye of Thundera`: so `Eye of Thundera.exe` e `LEIA-ME.txt`.
   A copia de codigo-fonte feita antes (PLANO-PASTA-LIMPA.md) vai para a subpasta `codigo\`
   (nao apagar: o Wolf pode querer ver). `ferramentas/gerar_pasta_limpa.py` continua valendo
   para essa subpasta.
5. Documentar em HISTORICO-DE-MUDANCAS.md, ONDE-PARAMOS.md e commitar (sem dist/ nem build/).

## Limites conhecidos (dizer ao Wolf)
- Precisa do WebView2 Runtime (ja vem no Windows 11 e na maioria dos Windows 10).
- O Windows/SmartScreen pode avisar "app desconhecido" (o .exe nao e assinado): "Mais
  informacoes > Executar assim mesmo".
- O .exe abre devagar na 1a vez (descompacta ~70 MB em %TEMP%\_MEI...).
- Os dados continuam em %LOCALAPPDATA%/Eye of Thundera (mesma conta = mesmos dados).

## Nao fazer
Nao commitar dist/ nem build/. Nao mexer no atalho da Area de Trabalho sem o Wolf pedir.
Nao colocar chave de API dentro do .exe.
