# Changelog

## [0.6.0] — 2026-11-24 — Falhar fechado em perguntas de risco (análise crítica pós-v0.5.0)

### Segurança
- **Red team do G26:** 50 perguntas (40 de risco reformuladas + 10 de controle) viraram teste de regressão. Na
  v0.5.0, 15 das 40 iam para a IA generativa e 2 caíam no catálogo; agora 50/50 ok.
- **G26 endurecido:** ação perigosa é avaliada antes do catálogo ("solda sem máscara" não lista mais máquinas de
  solda). Novos temas: carga de bateria, mistura química, crianças, trabalho em altura, reservatório sob pressão.
  Novos verbos: "abro a bateria", "travar o gatilho", "tirar a trava de segurança".
- **Falhar fechado:** pergunta que pede julgamento de segurança ("posso...?", "ainda é seguro?", "deixo...?") sem
  FAQ não vai para a IA.
- **G27:** antes de gerar, o Ollama classifica a pergunta (RISCO/SEGURO); risco ou resposta ambígua é encaminhada.
  Com o Ollama real, 0 de 70 perguntas de risco chegaram à geração (`TORK_CLASSIFICAR_RISCO`, padrão ligado).

### Alterado
- **D032:** respostas da IA não são mais reaproveitadas antes da revisão humana (`TORK_SERVIR_SUGESTOES` agora é
  `false` por padrão), porque o llama3.2 inventou conteúdo técnico nos testes com o modelo real.
- Roteiro da demo, guardrails (`0013`), decisões D032/D033 e análise crítica com as 11 perguntas (`docs/0021`).
- Documentação: G20 e G24 documentados; G21 e G22 registrados como parciais.

### Limitações conhecidas
- Com o G27, cerca de metade das perguntas comuns fora da base recebe o encaminhamento seguro em vez da resposta da
  IA, e há cerca de 140 ms a mais por pergunta que chega à IA.
- A base continua sem revisão humana; a avaliação mede roteamento, não correção.


## [0.5.0] — 2026-11-24 — Revisão técnica (RT-001 a RT-014) e plano de entrega

### Adicionado
- **Base de conhecimento ampliada:** 150 FAQs e 452 variações (mínimo de 3 por FAQ), com nível de risco em todas
  (P0.4). As 89 novas foram redigidas com assistência de IA, sem preços, e estão em rascunho até a revisão humana.
- **G26, política de risco (RT-003):** perguntas sobre eletricidade, solda, discos, proteções, baterias de lítio,
  superaquecimento e químicos só são respondidas pela base. Ação perigosa é sempre encaminhada ao manual, a um
  profissional ou a um atendente.
- **Fluxos guiados F-TROCA e F-HUMANO (P1.4):** desistência (CDC art. 49), defeito (garantia) e produto errado
  (atendimento prioritário). Pedido de atendente com resumo mascarado e **consentimento (G23)** antes de gravar.
  Respostas rápidas no chat e na CLI.
- `statusConteudo` em toda resposta (RT-004): o chat avisa quando o conteúdo não foi revisado ou é fictício.
- **Avaliação de roteamento (RT-008):** 100 perguntas com gabarito (`tests/eval/`), relatório em `docs/eval/` e teste
  de regressão (mínimo de 93 acertos e 0 respostas perigosas).
- **Observabilidade (RT-011):** `GET /metricas` com agregados anônimos (origens, guardrails, IA ok/falha, latência
  p50/p95 por etapa).
- **Configuração centralizada (RT-012):** `app/config.py` e `.env.example`.
- **CI (P1.6):** GitHub Actions com Ruff, pytest e avaliação, em Python 3.12 e 3.14.
- **Revisão humana (P1.7):** planilha com 41 FAQs de risco alto + 30 sorteadas e importador
  (`python -m app.db.planilha_revisao`).
- Experimento isolado de embeddings (RT-009) e decisões D029–D031 (sugestões, embeddings, gatilhos de PostgreSQL e
  RAG).

### Corrigido
- **Concorrência (RT-007):** a conexão SQLite compartilhada falhava sob carga (25 de 320 operações). Agora há uma
  conexão por thread, `busy_timeout` e memória com trava: 960 de 960 operações sem erro.
- **Ollama travado (RT-010):** chamadas sem timeout prendiam a requisição para sempre. Agora a resposta tem limite de
  45 s, a reescrita de 10 s, e uma mensagem clara aparece quando a IA cai.
- Uma FAQ aprovada na revisão podia ser sobrescrita pelo seed (RT-001). As aprovadas agora usam a faixa FAQ-901+.
- O rollback da migração do catálogo falhava em banco populado (RT-006).
- A busca entende terminações verbais ("conservo", "escolher") e o filtro comercial ficou mais preciso.
- O status do chat dizia "respostas revisadas" para conteúdo ainda não revisado. Agora diz "respostas na base".

### Alterado
- O roteiro de demonstração (`docs/0015`) foi refeito para a versão atual.


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
- Testes sem avisos: `httpx2` no lugar do `httpx` para o `TestClient` (depreciação do Starlette), conexões SQLite
  dos testes sempre fechadas (eliminou `ResourceWarning`) e `pytest.ini` com `filterwarnings = error`.


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
