# Plano — Plugins (Prioridade 5)

**Data:** 18/10/2026. **Para a IA que programa:** o Wolf não programa; explique
tudo em português simples. Siga na ordem.

## Meta

Permitir **estender o programa sem mexer no código principal**: criar um
arquivo `.py` numa pasta e passar a ter um comando novo na conversa — como os
lembretes, respondido localmente, sem IA e sem chave.

## O que já existe e aproveitamos

- Os **lembretes** são o modelo perfeito: `lembretes.responder(texto)` é
  chamado no `enviar()` (app_web.py) antes da IA; devolve `None` (não é com
  ele) ou a resposta (local, imediata).
- Os dados ficam em `%LOCALAPPDATA%\Eye of Thundera`; a pasta de plugins fica lá
  também (`plugins\`), fora do repositório.
- O diálogo de Configurações já tem abas com `data-aba`; a aba nova segue o
  mesmo padrão (`mostrarAba`, `abrirConfig`, `config_ler`, `config_salvar`).

## Regras de ouro

1. **Um plugin com erro não pode derrubar o programa.** Cada plugin é chamado
   dentro de `try`; erro vai para o log e o plugin é marcado como "com erro" na
   interface, sem travar a conversa.
2. **Plugins respondem só a texto.** Contrato mínimo: função `responder(texto)`
   devolve `None` (não é com ele) ou uma string (resposta). Nada de IA, nada de
   rede, nada de chave — plugins são código local de confiança, como os
   lembretes.
3. **Ativar/desativar pela interface.** A aba Plugins lista os plugins
   encontrados com um interruptor; o estado vai para o `config.json`
   (chave `plugins_ativos`, lista de nomes).
4. **Plugin de exemplo incluído.** Um plugin simples e útil (ex.: `/tempo` —
   mostra data e hora atuais) demonstra o contrato e serve de modelo.
5. **Dados reais intocados nos testes.** Pasta de plugins sintética em `_tmp`,
   como manda a regra 5 do `INSTRUCOES-PARA-IA.md`.
6. **Nenhum segredo em log** — se o plugin escrever algo no log, passa por
   `_sanitizar_erro_log` (padrão do projeto).

## Etapas

### 1. Módulo `plugins.py` (novo)

- `PASTA_PLUGINS` — `%LOCALAPPDATA%\Eye of Thundera\plugins`.
- `descobrir()` — lista os arquivos `.py` da pasta (ignora `__pycache__`,
  `exemplo.py` é incluído, `.txt` e outros não). Para cada um, carrega o módulo
  e lê `NOME` (ou nome do arquivo) e `DESCRICAO` (ou "Sem descrição").
- `carregar()` — devolve os módulos ativos (de acordo com
  `plugins_ativos` do config), cada um com `nome`, `descricao`, `responder`
  e `erro` (None ou a exceção de carregamento).
- `responder(texto)` — pergunta em ordem a cada plugin ativo; devolve a
  primeira resposta não-None, com o nome do plugin. Erros de plugin individual
  são logados e ignorados (o próximo plugin é tentado).
- `plugin_exemplo.py` — incluído na pasta de plugins no primeiro uso (se não
  existir), para o usuário ver o modelo. Responde a `/tempo` com data e hora
  atuais; documenta o contrato nos comentários.
- `garantir_exemplo()` — cria a pasta e o exemplo se faltar (chamado no
  primeiro arranque).

### 2. Ponte (`app_web.py`)

- `plugins_listar()` — devolve para a tela: lista com `nome`, `descricao`,
  `ativo`, `erro` e a pasta onde ficam.
- `plugins_salvar(dados)` — grava a lista de ativos no `config.json` e devolve
  a lista atualizada.
- No `enviar()`: **antes** da checagem de chave e **depois** dos lembretes,
  chama `plugins.responder(texto)`; se houver resposta, entra como mensagem
  normal (como `_responder_lembrete`).
- No `principal()`: chama `plugins.garantir_exemplo()` em `try` (cria pasta e
  plugin de exemplo no primeiro uso).

### 3. Aba Plugins (interface)

- Botão `Plugins` no diálogo de Configurações.
- Corpo: lista de plugins com nome, descrição e interruptor (liga/desliga);
  aviso para plugins com erro; link/abrir a pasta de plugins no explorador.
- Estado lido de `config_ler`, gravado por `config_salvar` (padrão do projeto).
- Acessibilidade: rótulos claros, navegação por teclado, foco visível.

### 4. Testes (`verificar.py`)

- Descoberta: pasta vazia → lista vazia; pasta com 1 plugin → 1 item.
- Resposta: plugin que devolve texto → resposta; plugin que devolve None →
  ignora; plugin com erro → não derruba, marca erro.
- Ativar/desativar: estado lido e gravado sem tocar dados reais.
- Interface: aba aparece, interruptor existe, nomes acessíveis.
- Plugin de exemplo: `/tempo` responde com data e hora.

### 5. Documentação e commit

- `HISTORICO-DE-MUDANCAS.md`, `ONDE-PARAMOS.md`, `README.md` atualizados.
- `PROXIMOS-PASSOS.md`: pendência marcada como concluída.

## Fora de escopo

- Plugins com interface gráfica ou janelas próprias.
- Plugins que chamam a IA ou a rede (o contrato é só texto local).
- Loja/instalação automática de plugins — a pasta é o bastante.
- Assinatura/verificação de plugins (são código de confiança do usuário).
