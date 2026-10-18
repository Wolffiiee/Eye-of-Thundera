# Plano — Sincronização entre computadores (Prioridade 6)

**Data:** 18/10/2026. **Para a IA que programa:** o Wolf não programa; explique
tudo em português simples. Siga na ordem.

## Meta

Ter os dados do programa (conversas, memória, chaves, configuração, lembretes)
iguais em **dois ou mais computadores**, através de uma pasta que o próprio
Windows sincroniza (OneDrive, Dropbox, Google Drive ou qualquer pasta
escolhida pelo usuário).

## O que já existe e aproveitamos

- `eye_of_thundera.fazer_backup_dados()` já copia todos os arquivos de
  `PASTA_CONFIG` para um zip. A sincronização é a mesma ideia, **sem zip** e
  **nos dois sentidos** (importa o que é mais novo, exporta o local).
- `PASTA_CONFIG` = `%LOCALAPPDATA%\Eye of Thundera` concentra todos os arquivos de
  dados (`config.json`, `historico.json`, `memoria.json`, `lembretes.json`,
  `janela.json`, `erro.log`...). É exatamente o que viaja.
- `salvar_config` já valida e grava `config.json` com cópia atômica; o mesmo
  cuidado vale aqui (escrever num temporário e renomear).

## Regras de ouro

1. **Última escrita vence, por arquivo.** Cada arquivo tem seu próprio carimbo
   de modificação; o mais novo ganha. Sem mesclagem: um computador fechado
   depois do outro substitui, e é isso que o usuário espera.
2. **Nada é apagado do outro lado.** A sincronização só **copia**: importa
   arquivos que não existem localmente e sobrescreve os que são mais novos.
   Ela nunca apaga nem move nada.
3. **Cópia atômica.** Escreve `arquivo.tmp` e renomeia para o nome final.
   Se o programa fechar no meio, o arquivo inteiro continua íntegro.
4. **Erro não derruba.** Se a pasta não existe, está vazia, está cheia ou dá
   permissão negada, a sincronização avisa e o programa continua normalmente.
5. **Dados reais intocados nos testes.** Tudo em `_tmp`, com caminhos
   simulados, como manda a regra 5 do `INSTRUCOES-PARA-IA.md`.
6. **Chaves viajam dentro do `config.json`** — como já acontece no backup
   (16/10). Nunca em arquivo separado, nunca em log.

## Etapas

### 1. Módulo `sincronizar.py` (novo)

Funções puras, só biblioteca padrão, sem depender de `eye_of_thundera`:

- `arquivos_de_dados()` — lista os arquivos da pasta de dados que viajan
  (todos os `.json` da `PASTA_CONFIG`, com exceção do `erro.log`, que é só
  diagnóstico local).
- `sincronizar_da_pasta(pasta_origem, pasta_destino)` — copia de `origem` para
  `destino` o que for mais novo (ou não existir). Devolve o que copiou.
- `sincronizar_para_pasta(pasta_origem, pasta_destino)` — o mesmo, no sentido
  contrário.
- `sincronizar_tudo(pasta_dados, pasta_sync)` — importa e exporta, devolve um
  resumo (`importados`, `exportados`, `ignorados`).
- `pasta_padrao()` — `OneDrive\Eye of Thundera` se existir, senão sugere
  `Documentos\Eye of Thundera`.
- `esta_configurada(pasta_sync)` — a pasta existe e é gravável?
- `carimbo_texto(pasta_sync)` — última data em formato legível, para a tela.

### 2. Ponte (`app_web.py`)

- `sincronizar_importar()` — ao **abrir** o programa (no `principal()`, antes
  de criar a janela, em `try`): importa o que for mais novo. Erro vira aviso
  silencioso no log.
- `sincronizar_exportar()` — ao **fechar** (no `ao_fechar`, junto com a
  posição da janela).
- `sincronizar_agora()` — botão na aba Sincronização: importa + exporta e
  devolve o resumo para a tela.
- `sincronizar_config()` — devolve para a tela: pasta configurada, se existe,
  última data sincronizada e estado (ligada/desligada).
- `sincronizar_config_salvar(dados)` — grava a pasta escolhida no
  `config.json` (chave `pasta_sync`).

### 3. Aba Sincronização (interface)

- Botão `Sincronização` no diálogo de Configurações (ao lado dos outros).
- Corpo: campo com a pasta atual (editável), botões **Escolher pasta** (abre
  o diálogo de pasta do Windows) e **Sincronizar agora**, e um texto com o
  estado (última sincronização, arquivos importados/exportados).
- **Escolher pasta** usa o diálogo nativo da janela pywebview (o mesmo
  `ask_folder` já usado em `web/index.html`), para não depender de Tkinter.
- Ao salvar, a aba grava no `config.json` e mostra o resumo da última
  sincronização.

### 4. Testes (`verificar.py`)

- Sincronização de dois lados em `_tmp`: arquivo mais novo na pasta remota é
  importado; mais novo local é exportado; sem conflito quando iguais.
- Cópia atômica: arquivo `.tmp` não fica para trás.
- Erro não derruba: pasta inexistente, vazia ou sem permissão → devolve aviso,
  não exceção.
- Botão e aba existem e o estado é lido sem tocar dados reais.
- Cobertura da interface: aba aparece, botões com nomes acessíveis.

### 5. Documentação e commit

- `HISTORICO-DE-MUDANCAS.md`: o que mudou, como foi verificado.
- `ONDE-PARAMOS.md`: estado atualizado.
- `README.md`: menção à sincronização.
- `PROXIMOS-PASSOS.md`: pendência marcada como concluída.

## Fora de escopo

- Sincronização em tempo real (watch de pasta) — só ao abrir/fechar e no botão.
- Conflito de mesma data em dois computadores — última escrita vence, com
  aviso no log.
- Sincronização de pasta fora do OneDrive/Drive/Dropbox — qualquer pasta
  funciona, mas a pasta padrão sugere OneDrive.
