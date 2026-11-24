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
