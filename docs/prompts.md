# Registro de prompts

## P001 — Planejar e executar o MVP básico (2026-11-19)
**Prompt (resumo):** planejar e executar um projeto básico e simples de agente de IA
para uma loja de ferramentas eletrônicas, seguindo `docs/TASKS_AGENTE_LOJA_FERRAMENTAS.md`.

## P002 — Ajuste de escopo para demo em 30 minutos (2026-11-19)
**Prompt (resumo):** como especialista em frontend, um front básico e didático para
demonstração; como especialista em backend, perguntas e respostas em SQLite com uma
API básica que consulta o banco; se a pergunta não existir, consultar o agente e ir
completando a base de dados.

**Resultado:** API FastAPI (`/chat`, `/health`, `/faqs`), banco SQLite com 60 FAQs,
fallback para Ollama (llama3.2) que grava as novas respostas, página de chat com selo
de origem (📚 banco / 🤖 agente) e contador da base, 23 testes automatizados.

## P003 — Documentação completa e publicação (2026-11-19)
**Prompt (resumo):** criar toda a documentação e subir o que foi feito no GitHub.

**Resultado:** `docs/arquitetura.md`, `docs/api.md`, `docs/base-de-conhecimento.md`,
`docs/roteiro-demo.md`, `CHANGELOG.md`, README com índice e checklist atualizado.

## P004 — Suíte de testes (2026-11-19)
**Prompt (resumo):** criar todos os testes necessários para o projeto.

**Resultado:** 355 testes em 6 arquivos (busca, banco, agente, API, integridade da FAQ,
frontend e terminal). A suíte encontrou e corrigiu 2 bugs de busca (desempate de pergunta
idêntica e voltagens sem unidade).

## P005 — Commit e PR semânticos (2026-11-19)
**Prompt (resumo):** criar um commit semântico com uma PR semântica e subir para o GitHub.

## P006 — Contexto da conversa (2026-11-19)
**Prompt (resumo):** a IA não está continuando no contexto anterior; o que podemos fazer para que ela continue a conversa no contexto?

**Resultado:** `conversationId` + memória em RAM + reescrita da pergunta de continuação pelo Ollama;
o agente recebe o histórico e o banco grava só perguntas completas.

## P007 — Pasta de guardrails (2026-11-19)
**Prompt (resumo):** preciso de uma pasta somente com todos os guardrails para não ocorrer problemas; planeje e faça.

**Resultado:** `app/guardrails/` com 19 guardrails (G01–G19) em 6 módulos, `docs/guardrails.md` e testes
nos dois sentidos (bloqueia o que deve e não bloqueia o legítimo, incluindo as 60 respostas oficiais).

## P008 — Commit e PR (2026-11-19)
**Prompt (resumo):** subir as mudanças de contexto e guardrails no GitHub com commit semântico.

