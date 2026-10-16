# Roadmap do Eye of Thundera

Este documento foi simplificado para evitar que o plano antigo entre em conflito com a versão atual.

- **Estado real e arquitetura:** README.md
- **Última correção e tarefa em andamento:** ONDE-PARAMOS.md
- **Pendências confirmadas:** PROXIMOS-PASSOS.md
- **Ideias futuras:** IDEIAS.md
- **Registro cronológico:** HISTORICO-DE-MUDANCAS.md

## Estado atual

A interface em uso é web/index.html + web/app.js + web/estilo.css, carregada por app_web.py. O atalho da Área de Trabalho executa o código-fonte com .venv/Scripts/pythonw.exe; não aponta para dist/Eye of Thundera.exe.

Em 16/10/2026 foi corrigido um erro de sintaxe em web/app.js que impedia o arquivo inteiro de executar e deixava a janela sem resposta aos cliques. A verificação automatizada agora verifica a sintaxe JavaScript quando Node.js está disponível e conta corretamente as verificações reportadas.

## Ordem recomendada

1. Confirmar manualmente os cliques no atalho normal após reabri-lo.
2. Validar os fluxos principais das quatro abas de Configurações.
3. Melhorar agrupamento e clareza dos controles sem alterar várias áreas ao mesmo tempo.
4. Atualizar o guia de usuário e eliminar instruções contraditórias remanescentes.
5. Considerar mudanças arquiteturais maiores só depois de estabilizar o fluxo atual.
