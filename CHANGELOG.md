# Changelog

## [0.4.0] — 2026-11-23 — Frontend profissional com a identidade do Tork

### Adicionado
- Chat redesenhado com a identidade visual: logo (versões clara e escura), avatar do Tork nos balões (versão
  "alerta" para bloqueios e erros), selos coloridos por origem, cards de produto com preço e estoque.
- Boas-vindas na voz do Tork e menu com 6 opções (produto, escolha, pedido, pagamento, trocas, atendente),
  submenu de categorias de produtos, sugestões rápidas e "menu" para voltar.
- Estado "Tork está pensando", avaliação 👍/👎 por resposta (`POST /avaliacoes`, sem dados pessoais).
- Tema claro e escuro (automático ou pelo botão), fontes locais (Inter, Barlow Semi Condensed; OFL),
  acessibilidade (foco visível, `role="log"`, `prefers-reduced-motion`), layout de 320 px a desktop.
- Links diretos para a apresentação: `/?q=pergunta` abre o chat já perguntando; `?tema=claro|escuro`.

### Alterado
- Frontend separado em `static/css/tokens.css`, `static/css/chat.css` e `static/js/chat.js` (ES module, sem build);
  nenhum recurso de CDN (a demo funciona sem internet) e nenhum `innerHTML`.


## [0.3.1] — 2026-11-23 — Respostas não revisadas sob controle

### Corrigido
- Uma resposta gerada pela IA e **não revisada** era reaproveitada para perguntas apenas parecidas, com o selo
  "Banco de dados" (ex.: "escreve-se brocantes ou blocantes?" recebia a resposta errada sobre parafusos).
  Agora sugestões só respondem perguntas praticamente iguais e aparecem com o selo "aguardando revisão".
- FAQs novas em `knowledge/faq.json` não entravam em bancos já existentes: os seeds agora se sincronizam pelo
  hash dos arquivos (migração `0005_controle_seeds`), sem apagar sugestões, atendimentos ou avaliações.

### Adicionado
- FAQ-061 sobre parafuso autobrocante (inclui a grafia correta "brocante").
- Revisão humana pelo terminal: `python -m app.db.revisao [rejeitar|aprovar|categorias]`.
- G25: resposta em que a IA admite não ter certeza não é gravada e o Tork oferece atendente; o prompt pede para
  não inventar definições.


## [0.3.0] — 2026-11-23 — Banco normalizado e catálogo fictício

### Adicionado
- **Banco SQLite normalizado (3FN)** com 19 tabelas em 4 migrações SQL versionadas (`up`/`down`), executor com
  transação por migração e tabela `schema_migrations`: FAQ, loja, catálogo e atendimento.
- Integridade no banco: FKs (RESTRICT/CASCADE/SET NULL), unicidades, CHECKs (preço ≥ 0, estoque ≥ 0, formatos,
  consentimento) e triggers (vigência de preço sem sobreposição, `atualizado_em`).
- **Catálogo fictício** determinístico (`SEED=2026`): 25 categorias, 15 marcas inventadas, 300 produtos, 45 tipos
  de especificação, 1.500 associações, histórico de preços e estoque por loja.
- Dados fictícios da loja: 2 unidades, horários, formas de pagamento e políticas (CDC).
- O Tork responde **produto e preço** (com cards) e **horário, endereço e pagamento** a partir do banco, nunca pelo LLM;
  pede a voltagem (G20) e oferece equivalentes quando a marca pedida não existe no catálogo.
- API: `GET /produtos`, `GET /produtos/{sku}`, `GET /loja`, campo `produtos` em `/chat`, arquivos `/static`.
- `docs/db/`: README, DER, dicionário de dados gerado do esquema, catálogo dos seeds, segurança e log de execução.
- 115 testes novos (687 no total).

### Alterado
- Respostas aprendidas pela IA vão para `faq_sugestoes` (código `SUG-0001`), não mais para a FAQ oficial.
- Bancos da v0.2 são convertidos automaticamente; a tabela antiga é preservada como `legado_faq_v02`.
- Geração do ID da conversa com `crypto.getRandomValues`; log de erro sem o caminho bruto da requisição.


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
- `docs/0013-Guardrails.md` e testes `test_guardrails.py` e `test_contexto.py` (572 testes no total).

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
