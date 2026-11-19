# Changelog

## [0.2.0] — 2026-11-19 — Contexto e guardrails

### Adicionado
- **Contexto da conversa:** `conversationId` no `/chat`, memória em RAM (5 trocas por conversa),
  detecção de continuação e reescrita da pergunta pelo Ollama ("e para metal?" → "Qual broca usar em metal?").
  O agente recebe o histórico e o banco grava só a pergunta completa.
- `DELETE /conversas/{id}` e campos `perguntaInterpretada` e `guardrails` na resposta.
- **Pasta `app/guardrails/`** com 19 guardrails em camadas: entrada (tamanho, dados pessoais, prompt injection),
  escopo (comercial sem LLM, fora do escopo), prompt, saída (preço/estoque/prazo/garantia/desconto inventados,
  pedido de dados, conselho perigoso, links/telefones, tamanho), reescrita e aprendizado.
- Página: linha "Entendi como…", selo 🛡️ de bloqueio e lista de guardrails acionados.
- Terminal: memória de conversa e comando `nova`.
- `docs/guardrails.md` e testes `test_guardrails.py` e `test_contexto.py` (572 testes no total).

### Alterado
- Pergunta com sinal comercial que não está no banco agora recebe os textos comerciais fixos em vez de ir ao LLM.
- "tem" deixou de ser palavra-chave da FAQ-041 (era genérica demais).

## [0.1.0] — 2026-11-19 — MVP 1

### Adicionado
- Base inicial com 60 FAQs (`knowledge/faq.json`) em 8 categorias, com variações e palavras-chave.
- Banco SQLite (`data/loja.db`) criado e populado automaticamente.
- Busca por palavras-chave com normalização, plural simples e tolerância a erros de digitação.
- Agente de IA local (Ollama / llama3.2) acionado quando a pergunta não existe no banco;
  a resposta é gravada como `pendente_validacao`.
- Proteções: perguntas comerciais nunca passam pelo LLM; perguntas fora do assunto não são gravadas.
- API FastAPI: `GET /health`, `POST /chat`, `GET /faqs`.
- Página de chat com selo de origem (banco/agente), contador da base e sugestões de perguntas.
- Versão de terminal (`agente.py`).
- 355 testes automatizados (pytest) que não dependem do Ollama: busca, banco, regras do agente,
  API, integridade da FAQ, página de chat e versão de terminal.
- Documentação: README, arquitetura, API, base de conhecimento, roteiro de demo, decisões e prompts.
- Esquema PostgreSQL planejado (`sql/0001-estrutura.sql`) e consulta de exemplo (`sql/0002-consultabaseconhecimento.sql`).

### Corrigido
- Pergunta idêntica à cadastrada podia perder o empate para outra FAQ com a mesma nota.
- Voltagens sem unidade ("220", "110") eram descartadas na busca; agora viram "220v"/"110v".

### Alterado
- O `agente.py` original (atendimento de oficina mecânica) foi substituído pelo agente da loja de ferramentas.
