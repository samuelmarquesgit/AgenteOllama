# Decisões técnicas

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

## Futuro
Trocar a busca por palavras-chave por embeddings/RAG (MVP 2), painel para
validar as respostas aprendidas e histórico de conversa.
