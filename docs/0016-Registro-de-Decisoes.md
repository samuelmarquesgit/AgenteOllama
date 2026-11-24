# 0016 — Registro de decisões

## D001 — Python + FastAPI em vez de NestJS + Next.js (2026-11-19)
O checklist sugeria Node. Escolhemos Python porque o projeto já usava Python e
Ollama, e o MVP precisava ser apresentado em 30 minutos. O frontend é uma única
página HTML servida pela própria API (sem build, sem CORS).

## D002 — Perguntas e respostas em SQLite (2026-11-19)
Banco relacional simples (`data/loja.db`, tabela `faq`), populado na primeira
execução a partir de `knowledge/faq.json`. Não precisa de servidor de banco.

## D003 — Banco primeiro, agente de IA depois (2026-11-19)
A busca no banco é feita por palavras-chave com normalização (acentos, plural
simples, erros de digitação leves). Abaixo da nota 0.5 a pergunta é considerada
inexistente e vai para o Ollama local. A resposta do agente é gravada com
`origem='agente'` e `status='pendente_validacao'` para revisão humana.

## D004 — Perguntas comerciais nunca passam pelo LLM (2026-11-19)
Preço, estoque, frete, pagamento etc. têm respostas fixas no banco. Em empate,
a FAQ comercial tem prioridade, para nunca parecer que informamos preço.

## D005 — Fora do escopo não é gravado (2026-11-19)
O LLM responde `FORA_DO_ESCOPO` para assuntos sem relação com a loja. Isso evita
poluir a base com perguntas aleatórias.

## D006 — Contexto por reescrita da pergunta (2026-11-19)
Em vez de mandar todo o histórico para a busca, a mensagem de continuação é reescrita pelo
Ollama como pergunta independente. Assim a busca no banco continua simples e a base nunca
recebe perguntas soltas. A reescrita só acontece quando a heurística detecta continuação,
para não gastar uma chamada ao LLM em toda mensagem. A memória fica em RAM (sem persistir
conversas de clientes no MVP).

## D007 — Guardrails em camadas, numa pasta própria (2026-11-19)
As regras do prompt sozinhas não bastam (um modelo de 3B as descumpre). Por isso a saída do
LLM é verificada por padrões antes de ir ao cliente ou ao banco, e a entrada é higienizada
antes de chegar ao LLM. Tudo fica em `app/guardrails/` com IDs (G01–G19), para ser fácil de
auditar, testar e evoluir.

## D019 — SQLite normalizado nesta entrega; PostgreSQL depois (2026-11-23)
Decisão do time: "deixe no SQLite nesse primeiro momento, depois colocaremos em um Docker certinho".
O banco foi totalmente normalizado (3FN) em SQLite, com migrações SQL portáveis para facilitar a troca futura.

## D008 (revisada) — Migrações em SQL versionado com executor próprio (2026-11-23)
Em vez do Alembic, arquivos `NNNN_nome.up.sql` / `.down.sql` e um executor de ~100 linhas (`app/db/migracoes.py`).
É uma das opções do plano de banco (DB §0), não acrescenta dependência e o rollback é testado.

## D028 — Catálogo fictício gerado, não copiado da internet (2026-11-23)
Não há lista aberta e licenciada de ferramentas com preços em reais; a API do Mercado Livre exige autenticação e
coletar páginas de varejistas viola os termos de uso. O catálogo é gerado (`SEED=2026`) com marcas inventadas e
preços em faixas aproximadas do varejo brasileiro, documentado como fictício.

## Futuro
Trocar a busca por palavras-chave por embeddings/RAG (MVP 2), painel para
validar as respostas aprendidas e histórico de conversa.

## D029 — Estados das sugestões sem EM_REVISAO por enquanto (2026-11-24)
A RT-002 sugere PENDENTE/EM_REVISAO/APROVADA/REJEITADA. Com um revisor e revisão atômica pelo terminal, o estado
EM_REVISAO não agrega; entra com o painel admin (T-050) por uma migração que recria a tabela (o SQLite não altera CHECK).
Os estados atuais mapeiam 1:1. `TORK_SERVIR_SUGESTOES=false` permite servir só conteúdo aprovado.

## D030 — Embeddings não entram no Gate; busca textual continua (RT-009, 2026-11-24)
Um experimento isolado (`tests/eval/experimento_embeddings.py`, relatório em `docs/eval/experimento-embeddings.md`) rodou as mesmas 100 perguntas da RT-008 com `nomic-embed-text`:

- busca textual atual: **95/100**;
- busca semântica pura: **78/100**, com 0/10 nas perguntas sem resposta na base, porque sempre "acha" alguma FAQ;
- busca híbrida (semântica só quando a textual não acha), com limiar de cosseno 0,75: **97/100**, 0 perigosas e +13 ms de mediana por pergunta.

O ganho de 2 perguntas foi medido com o limiar ajustado **no próprio conjunto de avaliação**, então provavelmente está superestimado. Adotar a híbrida também cria uma segunda dependência do Ollama no caminho da busca: hoje a busca funciona com o Ollama desligado. **Decisão:** não trocar agora. Volta à pauta (MVP 2) se a híbrida mantiver o ganho num conjunto de validação escrito por outra pessoa, com o Ollama desligado tratado como fallback para a busca textual.

## D031 — Gatilhos para PostgreSQL e RAG (RT-013, 2026-11-24)
O MVP fica em SQLite (D019). Os testes de RT-007 mostram 960/960 operações concorrentes sem erro e 30 usuários simultâneos com 100% de respostas 200/204.

| Migrar para | Quando (qualquer um dos gatilhos) | Custo / risco |
|---|---|---|
| **PostgreSQL** (Docker) | mais de uma instância da API ao mesmo tempo; escrita concorrente sustentada com `database is locked` nos logs; painel admin multiusuário (T-050); backup/retenção exigidos por política (LGPD, F6) | serviço a mais para operar; as migrações SQL já são portáveis (D008), mas `norm()` e os triggers precisam de equivalentes |
| **RAG com manuais** | perguntas que dependem do modelo exato (torque, consumíveis, códigos de erro) passarem de ~10% do volume de fallback em `/metricas`; manuais com licença de uso | risco de alucinação citando o manual errado; exige citação da fonte e os guardrails G06–G13 e G26 na saída |
| **Embeddings na busca** | ver D030: ganho confirmado em conjunto de validação independente | segundo modelo carregado; latência; busca passa a depender do Ollama |

Benefício esperado da migração: escala horizontal e operação padrão de mercado. Enquanto nenhum gatilho ocorrer, o custo supera o benefício para a entrega acadêmica.

## D032 — Resposta da IA não é reaproveitada antes da revisão (2026-11-24)
`TORK_SERVIR_SUGESTOES` passa a ser `false` por padrão. Com o Ollama real, o llama3.2 inventou conteúdo técnico (rebitadeira, cola de madeira; ver `0021`), e servir essa resposta a outros clientes espalhava o erro. A IA continua respondendo na hora, com selo de não revisada. A resposta vai para a fila e só é servida de novo depois de aprovada (`python -m app.db.revisao aprovar`). `true` restaura o comportamento anterior, por exemplo para a demo.

## D033 — Falhar fechado em perguntas de risco: G26 endurecido + G27 (2026-11-24)
O G26 listava temas numa regex e deixava passar reformulações (15/40 no red team; 11/20 num holdout). Decisão:
1. ação perigosa é avaliada antes do catálogo;
2. pergunta que pede julgamento de segurança, sem FAQ, não vai para a IA;
3. **G27:** antes de gerar, o Ollama classifica a pergunta; RISCO ou resposta ambígua é encaminhada.

O resultado, com o Ollama real, foi 0/70 perguntas de risco chegando à geração. O custo é que metade das perguntas comuns fora da base também é encaminhada, mais cerca de 140 ms por pergunta. A segurança foi preferida à cobertura. `TORK_CLASSIFICAR_RISCO=false` desliga o G27.
