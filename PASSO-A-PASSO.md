# Passo a passo para corrigir o Eye of Thundera

## Método obrigatório

1. **Entender o sintoma.** Registre o que a pessoa clicou, o que esperava e o que aconteceu.
2. **Verificar o estado do projeto.** Rode git status --short e git log -5 --oneline. Preserve arquivos modificados e não rastreados.
3. **Encontrar a causa.** Leia a função completa e procure logs, traceback e erros de sintaxe. Não corrija no chute.
4. **Proteger os dados.** Não altere %LOCALAPPDATA%/PesquisaIA durante testes. Use cópias temporárias em _tmp.
5. **Adicionar uma verificação de regressão.** O teste deve falhar antes da correção e passar depois, sempre que possível.
6. **Corrigir o mínimo necessário.** Evite misturar correção de bug com reformulação visual.
7. **Executar a suíte:** .venv\Scripts\python.exe verificar.py. Confirme RESULTADO: TUDO CERTO e FALHA: 0.
8. **Validar a interface real.** O atalho Eye of Thundera.lnk abre .venv/Scripts/pythonw.exe com app_web.py, então as mudanças no código-fonte entram em vigor ao fechar e reabrir esse atalho. Não gere um EXE a menos que a tarefa seja especificamente sobre o pacote distribuível.
9. **Atualizar documentos.** Registre a causa e a correção em HISTORICO-DE-MUDANCAS.md; atualize ONDE-PARAMOS.md e PROXIMOS-PASSOS.md quando o estado mudar.
10. **Commit seletivo.** Inclua só os arquivos desta tarefa. Não adicione automaticamente arquivos não rastreados que já estavam no projeto.
11. **Relatar com clareza.** Diga o que mudou, quais testes passaram e o que ainda precisa de confirmação manual.

## Quando a interface abre, mas nenhum botão funciona

- Verifique a sintaxe completa de web/app.js com node --check web/app.js se Node.js estiver instalado.
- Inspecione o console/erro.log e confirme se ligarEventos() e iniciar() são executados.
- Uma chave ou parêntese extra pode impedir o JavaScript inteiro de ser interpretado, mesmo que a janela pywebview abra normalmente.
- Depois de corrigir, acrescente a checagem ao verificar.py para detectar regressões futuras.

## Segurança

Nunca apagar arquivos de dados, chaves, backups ou arquivos antigos. Não usar dados reais nos testes. Não imprimir chaves em logs. Não rodar scripts de instalação ou limpeza sem entender o efeito.
