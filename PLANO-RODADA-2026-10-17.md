# Plano da rodada — cores e seleção de texto

Preparado antes de alterar o código, conforme pedido do usuário.

## Objetivos

1. Ampliar as opções de cores da aba Personalização sem quebrar a compatibilidade com configurações existentes.
2. Revisar o fluxo de selecionar texto e o menu de contexto com Copiar e ações relacionadas; corrigir problemas encontrados e simplificar o uso.
3. Atualizar verificações automatizadas, validar visualmente a interface e documentar o resultado.

## Etapas

1. Ler as instruções e o estado atual do Git; preservar alterações, arquivos não rastreados, dados reais e `show.png`.
2. Mapear as paletas, limites e persistência de temas no frontend, backend e verificações; escolher combinações adicionais distintas e legíveis.
3. Seguir os eventos de seleção de texto, clique direito, foco e comandos Copiar/Recortar/Colar/Selecionar tudo na interface ativa; identificar a causa de qualquer atrito antes de editar.
4. Implementar mudanças pequenas e incluir verificações de regressão para paletas e seleção/menu.
5. Rodar `verificar.py`, conferir o diff e capturar a interface em modo de demonstração; testar visualmente os cartões e o menu de texto sem usar conversas ou credenciais reais.
6. Atualizar `README.md`, `ONDE-PARAMOS.md`, `HISTORICO-DE-MUDANCAS.md` e `PROXIMOS-PASSOS.md` com o que foi feito, testado e ficou pendente.
7. Fazer commit seletivo somente dos arquivos desta rodada, mantendo exclusões e arquivos preexistentes fora.

## Limites de segurança e escopo

- Não ler nem alterar `%LOCALAPPDATA%\Eye of Thundera`, chaves, conversas, memória ou histórico pessoal.
- Não apagar, restaurar ou incluir no commit `show.png` ou outros arquivos alheios à rodada.
- O atalho diário abre `app_web.py`; não gerar EXE sem necessidade.
- Se persistência de temas exigir mudanças no backend, ajustar limites, validação e testes em conjunto; caso contrário, limitar ao frontend.

## Resultado

- Quatro paletas novas foram adicionadas; frontend e backend agora oferecem nove nomes/índices sincronizados.
- O menu de texto recebeu cópia segura com fallback, Recortar condicionado ao sucesso, atalhos, suporte de teclado e posicionamento de cursor corrigido.
- `verificar.py` passou com 143 verificações, 0 falhas e 0 avisos.
- A demonstração visual e a simulação sintética do clipboard passaram sem alterar configuração pessoal nem área de transferência real.
- Continua pendente apenas a confirmação manual da persistência pelo atalho real e a revisão com escala do Windows acima de 100%.
