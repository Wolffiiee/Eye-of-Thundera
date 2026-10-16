# Instruções para agentes de código

Antes de alterar o projeto, leia nesta ordem:

1. README.md — mapa e estado geral.
2. ONDE-PARAMOS.md — diagnóstico mais recente e tarefa atual.
3. INSTRUCOES-PARA-IA.md — regras obrigatórias de segurança e manutenção.
4. PASSO-A-PASSO.md — fluxo de diagnóstico, correção e validação.
5. HISTORICO-DE-MUDANCAS.md — contexto de bugs já corrigidos.

O programa usado no dia a dia é a interface web em app_web.py + web/. O atalho da Área de Trabalho aponta para .venv/Scripts/pythonw.exe e app_web.py. Não presuma que dist/Eye of Thundera.exe é o programa que está em uso.

Nunca apague dados pessoais, chaves, arquivos antigos ou arquivos não rastreados. Antes de editar, confira git status e git log. Faça mudanças pequenas, rode verificar.py, valide visualmente quando a interface mudar e atualize ONDE-PARAMOS.md e HISTORICO-DE-MUDANCAS.md.
