# 0021 — Análise crítica pós-v0.5.0 (as 11 perguntas)

> 2026-11-24. Objeto da análise: o Tork como entregue na `v0.5.0` e o plano restante. Feita com **medições novas**, não só opinião. Os scripts estão em `tests/eval/redteam.py` e `tests/eval/redteam_risco.json`, e os números abaixo vêm de execuções com o agente real (IA simulada e também com o Ollama/llama3.2 real). Complementa a [0006](0006-Analise-Critica.md), que analisou o plano antes da execução.

## Evidências coletadas antes de responder

| Teste | Resultado na `v0.5.0` |
|---|---|
| 40 perguntas de risco reformuladas (red team do G26) | **15 foram para a IA generativa** e 2 caíram no catálogo ("solda sem máscara" listou máquinas de solda) |
| 20 perguntas de risco novas (holdout 1) | 11/20 foram para a IA |
| Caminho da IA com o Ollama real (6 perguntas fora da base) | Conteúdo técnico **inventado com confiança**: a rebitadeira "remove a camada de plástico de canos"; "cola de madeira é epóxi ou poliuretano". Essas respostas ficavam como sugestão e eram **servidas de novo** em perguntas quase iguais |
| Fila de sugestões do banco local | SUG-0001 a 0006 com erros (parafuso definido como "estrutura com abertura para receber um martelo"; multímetro "função de tensão (Ω, V)") |
| Classificador de risco com llama3.2 (95 perguntas) | Pegou 70/70 de risco, mas marcou 12/25 comuns como risco; 140 ms por pergunta |

## 1. Os 5 principais pontos fracos

1. **A avaliação mede roteamento, não verdade.** O 95/100 só diz que a pergunta caiu na FAQ esperada. Nenhuma das 150 FAQs está `validado`, e 89 foram escritas com IA. Uma FAQ errada, bem roteada, conta como acerto.
2. **O G26 falhava aberto.** Ele lista temas de risco numa regex, e o que não está na lista vai para a IA. Bastou reformular para escapar ("estufou", "trava de segurança", "água sanitária com detergente", "telhado").
3. **O caminho generativo, com um modelo de 3B, piora o produto.** Ele inventa definições, e o reaproveitamento de sugestões espalhava o erro para outros clientes.
4. **A busca por palavras-chave é frágil e cara de manter.** A tolerância a erro de digitação cria colisões ("fraca" ≈ "França", "compra" ≈ "comprar"), e cada FAQ nova pode quebrar outra. Ainda há falsos positivos: "morsa de bancada" recebe a resposta da furadeira de bancada.
5. **Dependência de pessoas que não estão no circuito.** A revisão humana, a revisão jurídica e o revisor da fila não existem hoje. O modelo inteiro de segurança ("humano no circuito") depende deles.

## 2. Se fracassar em seis meses, por quê?

- Ninguém revisou a base: o conteúdo errado vira "verdade" com o selo da loja e uma resposta técnica errada causa um acidente ou uma reclamação.
- O catálogo continuou fictício: sem estoque e preço reais, o cliente não tem motivo para usar o chat.
- A fila de sugestões cresceu sem dono, e o "aprendizado" virou passivo.
- A manutenção da busca por palavras-chave ficou insustentável acima de algumas centenas de FAQs.
- O projeto dependia de uma pessoa (`bus factor` 1). A branch do colega (`feat/modelo-qwen2.5-3b`) está parada desde 19/11.

## 3. Suposições perigosas ou otimistas demais

- "Roteamento certo é resposta certa." É falso enquanto a base não for revisada.
- "Listar temas de risco cobre o risco." Os holdouts mostram que não cobre.
- "A IA local responde bem o que não está na base." O teste real mostrou o contrário.
- "Vai existir um revisor." Não há nome nem agenda para isso.
- "O conjunto de avaliação é independente." Ele foi escrito pela mesma equipe/IA que escreveu as FAQs. Palavras-chave foram ajustadas olhando os erros e o gabarito mudou em 2 itens.
- "Cliente lê o selo 'não revisada'." Em UX, avisos persistentes tendem a ser ignorados (cegueira de banner).

## 4. Três alternativas completamente diferentes

| Alternativa | Como funciona | Por que considerar |
|---|---|---|
| **A. Sem IA generativa para o cliente** | FAQ, menu, catálogo e fluxos; o que não está na base vai para um atendente humano. A IA só **sugere resposta ao atendente** (*agent assist*) | Elimina o risco de conteúdo inventado chegar ao cliente; a IA continua útil e é revisada a cada uso |
| **B. RAG sobre manuais oficiais com citação** | Responde só com trechos dos manuais dos fabricantes, citando a página; sem trecho, não responde | A fonte é verificável; resolve perguntas de modelo específico |
| **C. Busca do cliente + vídeo/guia curado** | Em vez de chat, um buscador de guias revisados (como uma central de ajuda) com o atendente a um clique | É a solução mais barata de manter; o comportamento é previsível |

## 5. A solução mais simples e barata, e a mais robusta

- **Mais simples e barata:** alternativa A sem a parte de *agent assist*: base revisada mais handoff humano. Custo quase zero de IA e risco mínimo; perde o efeito "uau" da demo.
- **Mais robusta:** FAQ revisada como fonte primária, mais RAG com citação de manuais, mais classificador de risco que falha fechado, mais revisão humana com SLA, com avaliação de **correção** (não só de roteamento) num conjunto independente. Exige semanas, dados licenciados e pessoas.

## 6. Como especialistas de outras áreas resolveriam

- **Engenharia de segurança (FMEA):** classificar cada tipo de resposta por severidade × ocorrência × detecção. Pergunta de risco respondida por modelo de 3B tem severidade alta e detecção baixa, então fica proibida por padrão (falhar fechado). Foi isso que fizemos no G27.
- **Aviação/medicina (checklists):** respostas de risco só a partir de texto aprovado, nunca geradas na hora. Isso coincide com o G26.
- **Psicologia/UX:** o aviso só funciona se interromper a ação, por isso o encaminhamento é melhor que o selo. É preciso medir com usuários reais se o "não revisado" é percebido.
- **Finanças:** comparar o custo de um atendimento humano evitado com o custo de um erro (devolução, processo, acidente). Com risco de cauda pesada, o valor esperado da IA livre é negativo.

## 7. Dados e argumentos que contrariam a conclusão

- Ser conservador tem custo: com o G27, **5 de 10** perguntas comuns fora da base deixam de ser respondidas pela IA, e "falhar fechado" piora a experiência nesses casos.
- A busca híbrida com embeddings acertou 97 contra 95 (RT-009). Pode haver ganho real que descartamos cedo.
- A IA acertou parte das perguntas benignas (por exemplo prego × parafuso). A geração não é inútil, é só não confiável.
- Para uma entrega acadêmica, o avaliador pode valorizar justamente o "aprende sozinho" que estamos restringindo.

## 8. Nota rigorosa (custo, tempo, risco de erro)

Escala 1 a 5, em que 5 é melhor (barato, rápido, baixo risco).

| Opção | Custo | Tempo | Risco de erro | Comentário |
|---|---|---|---|---|
| `v0.5.0` como estava | 4 | 5 | **1** | Risco inaceitável: 15/40 e 11/20 perguntas de risco chegavam à IA |
| **`v0.6.0` (G26 endurecido + falhar fechado + G27 + D032)** | 4 | 4 | **3** | 0/70 perguntas de risco chegam à IA com o Ollama real; o conteúdo da base continua não revisado |
| Alternativa A (sem IA para o cliente) | 5 | 4 | 4 | A mais segura; muda a proposta do trabalho |
| Alternativa B (RAG com manuais) | 2 | 1 | 3 | Fora do prazo; depende de licença dos manuais |

## 9. O que faltou perguntar

- **A resposta está certa?** Não existe avaliação de *correção*, só de roteamento. É preciso de 20 a 30 respostas julgadas por um humano.
- **Retenção (LGPD):** `atendimentos_humanos` e `avaliacoes` não têm prazo de retenção nem rotina de exclusão.
- **Quem lê a fila de atendimento humano?** O F-HUMANO grava, mas ninguém é notificado.
- **Acessibilidade e mobile reais:** não houve teste com leitor de tela nem com usuários.
- **Custo de hardware:** a demo depende de GPU local (2,6 GB); como fica numa máquina sem GPU?
- **Conteúdo jurídico:** os textos do CDC precisam de responsável identificado.

## 10. Prós e contras → denominador comum

| Opção | Prós | Contras |
|---|---|---|
| Manter a IA livre (v0.5.0) | Demo impressionante; responde quase tudo | Conteúdo inventado e risco à segurança |
| Remover a IA do cliente (A) | Mais seguro e mais barato | Perde a proposta do trabalho e a demo |
| **Denominador comum (executado na v0.6.0)** | A IA continua respondendo dúvidas **comuns** fora da base, com selo de não revisada. Perguntas de **risco** nunca chegam a ela (G26 + falhar fechado + G27). O que a IA gera **não é reaproveitado** antes da revisão (D032) | Metade das perguntas comuns fora da base cai no encaminhamento; a base continua sem revisão |

## 11. Sem concordar por educação

A minha própria entrega da `v0.5.0` tinha uma falha de segurança séria. O G26 passava na avaliação porque **a avaliação foi ajustada junto com ele**; em perguntas novas, ele deixava passar mais da metade. O número "0 respostas perigosas" era otimista. A correção certa não era aumentar a lista de palavras, e sim **inverter o padrão** (falhar fechado). Também é preciso admitir que o "aprende sozinho" com um modelo de 3B não deveria servir conteúdo a outros clientes sem revisão.

## Plano refeito e executado (v0.6.0)

| # | Ação | Evidência |
|---|---|---|
| 1 | Red team de 50 perguntas (40 de risco + 10 de controle) como **teste de regressão** | `tests/eval/redteam.py`; `tests/test_g27_redteam.py`. Era 33/50, agora é 50/50 (ajustado nele, então é regressão, não generalização) |
| 2 | G26 endurecido: ação perigosa avaliada **antes do catálogo**; novos temas (carga de bateria, mistura química, crianças, altura, vaso de pressão); verbos ("abro", "travar o gatilho", "sem máscara") | `app/guardrails/risco.py` |
| 3 | **Falhar fechado:** pergunta que pede julgamento de segurança ("posso...?", "ainda é seguro?", "deixo...?") sem FAQ não vai para a IA | holdout 1: de 11/20 para 1/20 com IA simulada |
| 4 | **G27:** antes de gerar, o próprio Ollama classifica a pergunta; RISCO ou resposta ambígua não é respondida pela IA; Ollama fora vira a mensagem de IA indisponível. `TORK_CLASSIFICAR_RISCO` | Ponta a ponta com o Ollama real: **0/70** perguntas de risco chegaram à geração; 5/10 comuns foram respondidas pela IA |
| 5 | **D032:** `TORK_SERVIR_SUGESTOES` passa a ser `false` por padrão; a resposta da IA só volta a ser servida depois de aprovada | `app/config.py`, `.env.example`, `tests/test_config.py` |
| 6 | Avaliação RT-008 mantida | 95/100, 0 perigosas (a IA é simulada; o G27 não atua nela) |

**Continua pendente (não resolvido por código):** revisão humana e jurídica, avaliação de correção feita por um humano, retenção LGPD, notificação da fila de atendimento e um conjunto de avaliação escrito por terceiros.
