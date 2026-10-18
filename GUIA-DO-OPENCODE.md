# Guia do OpenCode para este projeto

Leia primeiro README.md e ONDE-PARAMOS.md. Este guia complementa as instruções do projeto; não substitui o estado atual descrito nesses arquivos.

## Versão e atalho em uso

O programa do dia a dia é Eye of Thundera: app_web.py + web/. O atalho Eye of Thundera.lnk na Área de Trabalho aponta para .venv/Scripts/pythonw.exe, passa app_web.py e usa D:/Projetos/Eye of Thundera como pasta de trabalho. Portanto, alterações no código-fonte aparecem ao fechar e reabrir o atalho; não gere um EXE automaticamente.

O EXE distribuível, quando necessário, é construído por Gerar o EXE.bat e fica em dist/Eye of Thundera.exe. Não presuma que ele seja o alvo do atalho.

## Como trabalhar

1. Confira git status --short e git log -5 --oneline.
2. Leia INSTRUCOES-PARA-IA.md e PASSO-A-PASSO.md.
3. Descubra a causa antes de editar.
4. Faça uma mudança pequena e adicione uma verificação que a proteja.
5. Rode .venv/Scripts/python.exe verificar.py.
6. Se mexeu na interface, abra-a e confira o fluxo real.
7. Atualize ONDE-PARAMOS.md e HISTORICO-DE-MUDANCAS.md.
8. Faça commit somente dos arquivos da tarefa; preserve arquivos não rastreados.

## Dados pessoais

Conversas, memória, configurações e chaves ficam em %LOCALAPPDATA%/Eye of Thundera. Não os leia ou modifique em testes, não imprima chaves e não os inclua no Git.

## Troca manual de modelo no OpenCode

Se o OpenCode chegar ao limite, termine o passo atual em estado seguro, rode verificar.py e registre onde parou. O script ferramentas/trocar_modelo_gratis.py testa a lista ferramentas/modelos-gratis.txt e tenta escolher um modelo gratuito disponível. Só execute essa troca quando necessário; não altere a configuração do OpenCode como parte de uma correção do Eye of Thundera.

## Plugin de troca automática de modelo do OpenCode

O plugin local gratis-sempre fica em %USERPROFILE%/.config/opencode/plugin/gratis-sempre.js; a cópia-fonte e os testes ficam em ferramentas/opencode-gratis-sempre.js e ferramentas/teste-gratis-sempre.mjs. Quando recebe erro de limite, ele marca o modelo como temporariamente indisponível e tenta o próximo modelo gratuito de ferramentas/modelos-gratis.txt. Não ative ao mesmo tempo esse plugin e opencode-runtime-fallback. Se houver problema, confira primeiro a configuração atual do OpenCode antes de mudar qualquer coisa.

## Checklist de entrega

- [ ] Verificação concluída sem falhas.
- [ ] Interface aberta e conferida quando relevante.
- [ ] Histórico e estado atual atualizados.
- [ ] Commit seletivo feito.
- [ ] Usuário informado sobre o que mudou e o que não foi testado.

- **NUNCA apague testes** (o commit 408bc42 apagou ~220 e escondeu coisas que ainda existem: roteador, voz, memoria, ponte, microfone). Eles foram restaurados em `verificar_motor.py` (171 verificacoes). Teste de tela do programa antigo pode ir embora; teste de motor/ponte NAO. Se um teste ficar velho, CONSERTE o teste (ex.: mock sem o parametro novo) e diga ao Wolf.
- `verificar.bat` agora roda os dois arquivos: `verificar.py` e `verificar_motor.py`. Os dois precisam dar TUDO CERTO.
