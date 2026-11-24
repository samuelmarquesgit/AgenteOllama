# 0018 — Plano de entrega: 29/11/2026

> **Versão:** 1.0 · **Data:** 2026-11-23 (segunda-feira, noite)
> **Prazo oficial:** até **29/11/2026 00:00** (fim de sábado, 28/11).
> **Extensão possível:** até **30/11/2026 22:00**.
>
> Este documento **tem prioridade sobre o [`0007`](0007-Tasks-Reinicio-do-Projeto.md) até a entrega**. O `0007` continua como plano de longo prazo, após a entrega.

---

## 1. A conta que define o plano

| Item | Valor |
|------|-------|
| Dias úteis até o prazo oficial | **5** (ter 24 → sáb 28) + a noite de hoje |
| Esforço do `0007` até o Gate | ~70 dias-pessoa |
| Capacidade realista do time | **9 a 15 dias-pessoa** (4 pessoas × 5 dias × 3–5 h/dia), **se** os 4 estiverem ativos |
| Capacidade garantida | ~5 dias-pessoa (Samuel + assistente de IA), já que a disponibilidade dos colaboradores não está comprovada |
| **Conclusão** | Cabe **~15–20%** do `0007`. O plano abaixo é desenhado para ser entregue **mesmo se só uma pessoa trabalhar**; o que os colaboradores fizerem é ganho |

**Premissa a confirmar (urgente):** o plano de banco [`0004`](0004-Plano-de-Banco-de-Dados.md) é **a entrega avaliada**.
A "Definição de pronto do MVP 1" dele (PostgreSQL, 3 tabelas de FAQ, 150 perguntas, 450 variações, busca parametrizada, testes e documentação) vira o **núcleo obrigatório** desta entrega.
Se não for avaliado, a seção 7 mostra o plano alternativo.

---

## 2. Escopo da entrega

### P0 — obrigatório (sem isto, não há entrega)

| # | Item | Origem |
|---|------|--------|
| P0.1 | ✅ Repositório consolidado: contexto, guardrails e documentação na `main` (PRs #1 a #7; `v0.5.0`) | T-007 |
| P0.2 | ✅ ~~PostgreSQL via Docker~~ **SQLite normalizado** (decisão do time, D019) com **migrações SQL versionadas** up/down + executor | DB §0–2, T-016 |
| P0.3 | ✅ Tabelas da FAQ (DB §2) + `faq_sugestoes`, e também loja, catálogo fictício (300 produtos) e atendimento: 19 tabelas em 3FN | DB §2–5, T-016, T-017 |
| P0.4 | ✅ **150 FAQs + 452 variações** em 8 categorias, com seed idempotente (sincronização por hash) e verificador de contagens. Mantido em JSON (não YAML), sem nova dependência. Conteúdo novo em rascunho até a revisão (P1.7). Avaliação RT-008: 90 → 95/100, 0 perigosas | DB §6, T-022–T-024, T-026 |
| P0.5 | ✅ Busca **parametrizada** (função `norm()` sem acento + LIKE) usada pelo Tork; comportamento mantido | DB §7, T-020 |
| P0.6 | ✅ 687 testes, incluindo FKs, unicidades, CHECKs, triggers, contagens, SQL injection, acentos e rollback | DB §8, T-021 |
| P0.7 | ✅ `docs/db/`: README, DER, dicionário de dados (gerado), catálogo do seed, segurança e log de execução | DB §1, §10 |
| P0.8 | 🟡 Demo funcionando (roteiro `0015` atualizado e conferido) + versão ✅ `v0.5.0` (tag e release em 2026-11-24) + **vídeo de reserva** (falta, time) | T-052, T-055 |

### P1 — importante (faz a entrega se destacar)

| # | Item | Origem |
|---|------|--------|
| P1.1 | ✅ Identidade do Tork aplicada ao chat (cores, avatar, logo, selos, fontes locais, tema claro/escuro) | T-041, T-042 |
| P1.2 | ✅ Boas-vindas + **menu em botões** com submenu de categorias, sugestões, avaliação 👍/👎 e links diretos `/?q=` | T-043, T-044 |
| P1.3 | ✅ Respostas da loja (horário, endereço, pagamento, trocas) a partir do **banco** (tabelas `unidades`, `politicas` e `formas_pagamento`; seed fictício), no lugar do `loja.yaml` previsto | T-030, T-035 |
| P1.4 | ✅ Fluxo **F-TROCA** (CDC) e **F-HUMANO** (resumo mascarado + consentimento G23 → `atendimentos_humanos`, dentro/fora do horário), na API, no chat (respostas rápidas) e na CLI | T-032, T-033 |
| P1.5 | ✅ **G20** (confirmação de voltagem): resposta do catálogo com ferramenta com fio pede para confirmar 127/220 V quando o cliente não informou (`app/intencoes.py`; testes nos dois sentidos em `tests/test_intencoes.py`). Ainda não há passo obrigatório nos fluxos (não existe F-ESCOLHA) | T-037 |
| P1.6 | ✅ CI mínimo: Ruff + pytest + avaliação de roteamento (Python 3.12 e 3.14). ~~Serviço Postgres~~: banco é SQLite (D019) | T-010 |
| P1.7 | 🟡 Planilha pronta (`docs/revisao/`: 41 de risco alto + 30 sorteadas, importador validado por testes). **Falta a revisão humana em si** (time) | T-025 |

### P2 — só se sobrar tempo, ou na extensão

| # | Item |
|---|------|
| P2.1 | Fluxo F-ESCOLHA |
| P2.2 | Comparação rápida `qwen3:4b` × `llama3.2:3b` (20 perguntas, notas humanas) |
| P2.3 | Acesso externo pelo Cloudflare Tunnel |
| P2.4 | Papéis de banco com privilégio mínimo (DB §9) |
| P2.5 | `EXPLAIN (ANALYZE, BUFFERS)` registrado |

### Fora desta entrega (vai para o `0007`, após 30/11)

uv, mypy, pre-commit, Alembic, Playwright, painel admin, roteador de intenções completo, F-PROD e F-PEDIDO, catálogo, histórico persistente, RAG, avaliação com promptfoo, hospedagem 24 h.

---

## 3. Cronograma

| Dia | Meta do dia | Itens | "Pronto" ao fim do dia |
|-----|-------------|-------|------------------------|
| **Seg 23** (noite) | Decidir e organizar | Confirmar a premissa; definir quem faz o quê; P0.1 (PRs); criar as issues desta lista | `main` atualizada; cada pessoa sabe o que fazer |
| **Ter 24** | Banco de pé | P0.2, P0.3; migrar as 60 FAQs atuais para o Postgres; P0.5 inicial; P1.6 | `make up` sobe o Postgres; o Tork responde a partir do Postgres com as 60 FAQs |
| **Qua 25** | Conteúdo | P0.4 (rascunho das 90 novas + 450 variações, priorizando os temas da pesquisa: voltagem, garantia/CDC, compatibilidade, manutenção); P1.1 | 150/450 no seed, verificador verde; chat com a cara do Tork |
| **Qui 26** | Revisão e conversa | P1.7 (revisão), P1.2, P1.3, P1.4, P1.5 | Amostra revisada; menu e respostas da loja funcionando |
| **Sex 27** | Qualidade e documentação | P0.6, P0.7; correções; **congelar funcionalidades às 18h** | Testes verdes; `docs/db/` completo |
| **Sáb 28** | Entrega | Ensaio da demo, gravar o vídeo de reserva, P0.8 (`v0.5.0`), revisar a documentação, **entregar até 23:00** | Entregue com 1 h de folga |
| *Dom 29 – seg 30* | *Reserva* | *Só correções ou P2, e só se a extensão for confirmada* | *Entrega final até 30/11 20:00 (2 h antes do limite)* |

### Divisão sugerida (se os 4 estiverem ativos)

| Pessoa | Frente | Itens |
|--------|--------|-------|
| A | Dados | P0.2, P0.3, P0.5, P0.6 |
| B | Conteúdo | P0.4, P1.7 (com revisor) |
| C | Experiência | P1.1, P1.2, P1.3 |
| D | Conversa e plataforma | P1.4, P1.5, P1.6, P0.7 |

**Se só uma pessoa estiver ativa:** fazer **só o P0**, nesta ordem: P0.1 → P0.2/P0.3 → P0.5 → P0.4 → P0.6 → P0.7 → P0.8. O P1.1 (identidade) entra se sobrar meio dia.

---

## 4. Riscos desta entrega

| Risco | Prob. | Impacto | Mitigação |
|-------|:-----:|:-------:|-----------|
| **Conteúdo:** 90 FAQs + 450 variações sem revisão real | Alta | Alto | Rascunho assistido por IA **declarado como tal**; revisão humana de 30 + as de risco alto; o restante marcado `pendente_validacao` no banco e na documentação |
| A migração para o Postgres quebra a demo | Média | Alto | Tag `v0.2.0` (SQLite) como **demo de reserva**; migrar primeiro com as 60 FAQs e só depois crescer |
| Colaboradores não aparecem | Alta | Médio | O P0 foi dimensionado para uma pessoa; o P1 é bônus |
| Docker ou Postgres não sobe na máquina de alguém | Média | Médio | Compose testado em 2 máquinas na terça; quem não conseguir trabalha em conteúdo ou frontend |
| Escopo cresce no meio da semana | Alta | Alto | Congelamento na sexta às 18h; nada de P2 antes de o P0 estar verde |
| Contar com a extensão | Média | Alto | Plano fecha no sábado; a extensão é só reserva |
| Ollama lento na hora da demo | Média | Médio | Pergunta de aquecimento; vídeo de reserva; respostas do banco não dependem do Ollama |

---

## 5. Análise crítica do plano de entrega (11 perguntas)

| # | Pergunta | Resposta |
|---|----------|----------|
| 1 | **5 pontos fracos** | (1) 150 FAQs + 450 variações em ~2 dias é o gargalo, e a revisão será parcial; (2) o plano depende da premissa de que o Postgres é avaliado, ainda não confirmada; (3) disponibilidade dos colaboradores desconhecida; (4) migrar banco e crescer conteúdo na mesma semana mexe em duas fundações ao mesmo tempo; (5) quase nenhum tempo para teste com usuários reais |
| 2 | **Por que fracassaria** | Conteúdo atrasa e consome sábado e domingo; a migração quebra algo e a demo cai; o time tenta encaixar P1/P2 antes de fechar o P0; ninguém revisa as FAQs e uma resposta errada aparece na apresentação |
| 3 | **Suposições perigosas** | Que o Docker funciona em todas as máquinas; que a IA rascunha 90 FAQs corretas; que a extensão vai ser concedida; que os 572 testes migram sem dor para o Postgres; que "450 variações" geradas são naturais |
| 4 | **Três alternativas** | (a) Entregar a v0.2 (SQLite) + documentação de banco **sem implementar** o Postgres: 1 dia de trabalho, mas não cumpre a definição de pronto do DB §10; (b) Postgres **só** com as 60 FAQs + 180 variações, com qualidade alta, e declarar a meta de 150/450 como próxima etapa; (c) Supabase (Postgres gerenciado gratuito) em vez de Docker, para evitar problemas de instalação |
| 5 | **Mais simples × mais robusta** | Mais simples: alternativa (b), Postgres + 60 FAQs bem revisadas + documentação, ~4 dias-pessoa. Mais robusta: P0 + P1 + P2 inteiros, ~15 dias-pessoa, só com o time completo dedicado |
| 6 | **Outra área** | Gestão de projetos (*timeboxing* e MoSCoW): fixar o prazo e variar o escopo, nunca o contrário. Engenharia de produção: terminar uma peça inteira antes de começar a próxima (fluxo contínuo); aqui, banco completo antes de conteúdo e conteúdo antes de interface |
| 7 | **Dados contrários** | A demo do MVP foi aprovada sem Postgres; parte da avaliação pode valorizar a experiência (Tork, menu) mais do que o banco; o próprio DB §10 pede 150/450, então a alternativa (b) arrisca a nota de banco |
| 8 | **Nota C/T/R** | Plano P0+P1: **custo 1 · tempo 4 · risco 3 = 8/15**. Só P0: **1 · 3 · 2 = 6/15**. Alternativa (b): **1 · 2 · 2 = 5/15**, mas incompleta em relação ao DB §10 |
| 9 | **O que falta perguntar** | Como será a entrega: link do repositório, apresentação ao vivo, vídeo, relatório? Há critérios de avaliação escritos? Conteúdo rascunhado por IA é permitido e precisa ser declarado? Quem apresenta? |
| 10 | **Denominador comum** | Fazer o **P0 completo**, com o conteúdo rascunhado por IA, **declarado** e com amostra revisada; P1 na ordem P1.1 → P1.2 → P1.7 → P1.6 → P1.3/P1.4/P1.5; P2 só na extensão. Se na quarta à noite o conteúdo estiver abaixo de 100 FAQs, cair para a alternativa (b) e documentar |
| 11 | **Sem concordar por educação** | Não dá para entregar o plano de profissionalização inteiro nesta semana. Tentar faria a entrega sair pior do que a v0.2. Escolha poucas coisas e termine-as bem |

---

## 6. Critérios de "entregue"

- [ ] `docker compose up` + seed + `pytest` funcionam a partir de um clone limpo, seguindo o README.
- [ ] Postgres com as 4 tabelas, **150 perguntas, 450 variações e 8 categorias**, conferidos pelo verificador.
- [ ] O Tork responde a partir do Postgres; a busca usa consultas parametrizadas.
- [ ] Testes verdes, incluindo os de banco; resultado registrado em `docs/db/EXECUTION_LOG.md`.
- [ ] `docs/db/` completo; o DB §10 marcado `[x]` só no que foi comprovado.
- [ ] Declaração de uso de IA no conteúdo e no código, e de quais FAQs foram revisadas por humanos.
- [ ] Tag `v0.3.0`, CHANGELOG e vídeo de reserva da demo.

## 7. Se o Postgres não for avaliado

O plano troca o P0.2–P0.7 por: **mesmo esquema 3FN no SQLite** (sem Docker), as mesmas 150/450 FAQs e mais tempo para o P1 (identidade, menu, fluxos e teste com 3 usuários). Economia estimada: 2 dias-pessoa.
