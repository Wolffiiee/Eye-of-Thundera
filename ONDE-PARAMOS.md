# Onde paramos

Atualizado em 18/10/2026, depois da rodada que implementou log de erros
dentro do programa, contador de uso, aviso de cota (com um bug corrigido),
Ctrl+K, Ctrl+Z e "Exportar conversa". Suíte: **233 verificações, 0 falhas,
0 avisos**.

## Resumo do estado atual

A rodada de hoje menambah **seis coisas**, todas verificadas na tela de verdade:

1. **Log de erros dentro do programa** (aba Ajuda): um cartão "Se algo der
   errado" mostra os últimos 8 erros com data, origem e texto. Botões
   Atualizar e Apagar histórico (este pede confirmação). O `erro.log` sempre
   existiu, mas morava dentro do computador — o Wolf não tinha como ver nada
   sem pedir ajuda.
2. **Contador de uso** no rodapé: `hoje: 23 perguntas`, numa etiqueta discreta
   ao lado da dica de atalhos. Conta **só o que vai para a IA** (lembrete,
   plugin, busca de imagens e índice de documento são locais e gratuitos).
   Clicar na etiqueta zera o dia. Arquivo novo `contagem.json`, separado do
   `config.json` de propósito — o config guarda as chaves de API e não pode
   ser reescrito a cada pergunta.
3. **Aviso de cota**: faixa amarela na conversa que não some sozinha (fecha no
   clique, Enter ou Espaço). Avisa **uma vez por hora** — avisar a cada
   pergunta faria o Wolf largar o programa — e perdoa quando a cota volta.
4. **Ctrl+K** abre as Configurações; **Ctrl+Shift+K** vai direto nas Chaves.
5. **Ctrl+Z** desfaz a última troca (pergunta **e** resposta, sempre juntas)
   para mandar de novo. Não rouba o atalho de quem está digitando. Se a
   conversa ficar vazia, ela some do histórico.
6. **Exportar conversa**: botão na barra lateral que salva a conversa inteira
   em `.md` (que o ChatGPT entende melhor) ou `.txt`, com os sites
   consultados junto.

## 🐛 Bugs reais encontrados e corrigidos nesta rodada

- **A cota acabava e o programa falhava mesmo com chave de reserva
  configurada.** O `tentar_com_reserva` só trocava quando a *chave* era
  recusada. Corrigido: agora troca por dois motivos. Pior: corrigindo o
  primeiro bug, apareceu que a 2ª tentativa olhava `estado["falhou"]`, que é
  `False` no caso da cota (a chave está ótima, só o limite acabou) — então
  chamava o Gemini de novo em vez da reserva. Feito de qualquer jeito, nunca
  funcionava.
- **`contagem.py` e `cota.py` não estavam no `.spec`** — o instalador ficaria
  sem contador e sem aviso de cota, sem qualquer aviso. Corrigido nos dois
  arquivos de build.
- **O `fazer_backup.py` salvava na pasta antiga** `OneDrive\Backup Pesquisa
  IA\` com nome `pesquisa-ia_*.zip`. Corrigido e os backups foram movidos.
- **Desfazer com erro no fim da conversa apagava tudo.** Agora a regra é
  previsível: desfaz a última troca, seja a que deu certo ou a que falhou.
- **Leitor do contador aceitava chave torta** (`"xyz": 5`) como se fosse um
  dia. Corrigido.

## Estado do instalador

`gerar_instalador.py` monta tudo num comando (roda os testes → compila →
copia o código → gera o zip). O zip sai com **uma pasta só** na raiz
(`Eye of Thundera`), com o `.exe`, o `_internal`, o `codigo` e o `LEIA-ME`
dentro. Testado descompactando numa pasta limpa: abriu com **um processo
só**, criou a pasta de dados certa e **não levou nenhum dado do Wolf junto**.
Fica em `_tmp\Eye of Thundera.zip` (65,1 MB).

## Renomeação do projeto

O nome antigo "PesquisaIA" foi padronizado para **"Eye of Thundera"**: módulo
(`eye_of_thundera.py`), pasta de trabalho (`D:\Projetos\Eye of Thundera`),
pasta de dados (`%LOCALAPPDATA%\Eye of Thundera`) e backup
(`OneDrive\Backup Eye of Thundera`). A migração dos dados é automática e a
pasta antiga **não foi apagada** (cópia de segurança).

## Pendências reais

- O **usuário ainda não testou** o instalador num outro computador (foi
  adiado de propósito — ele vai pedir quando chegar o momento).
- A pasta antiga `D:\Projetos\PesquisaIA` está vazia mas o Windows ainda
  segura o apagamento (só solta depois de reiniciar). É inofensiva.
- `_tmp\` tem uns 250 arquivos de rascunho (scripts de teste, prints, logs).
  É gitignored, então não causa problema; pode ser apagado quando quiser.

## Ideias para o futuro (não são urgência)

- **Arrastar imagem** para a conversa (precisa de OCR ou visão, e de
  consentimento explícito antes de enviar imagem para um provedor).
- **Separar o motor**: `eye_of_thundera.py` tem ~7.200 linhas, das quais 152
  são da tela tkinter antiga que está morta. Funciona, mas é um arquivo
  grande e meio arriscado de mexer.
