# 0002 — Índice da documentação

> Todos os documentos do projeto, numerados na ordem de leitura recomendada.
> **Convenção:** `NNNN-Titulo-Em-Palavras.md`; os números não se repetem nem são reaproveitados; documentos novos recebem o próximo número livre.

## Comece por aqui

> 🔴 **Entrega em 29/11/2026 00:00** (extensão possível até 30/11 22:00): o plano vigente é o [`0018`](0018-Plano-de-Entrega-29-11.md).

| Nº | Documento | Para quem | Tipo | Status |
|----|-----------|-----------|------|--------|
| 0001 | [Contexto do projeto](0001-Contexto.md) | Todos | Visão geral e estado atual | ✅ Vigente |
| 0002 | [Índice](0002-Indice.md) | Todos | Navegação | ✅ Vigente |

## Planejamento

| Nº | Documento | Para quem | Tipo | Status |
|----|-----------|-----------|------|--------|
| 0003 | [Requisitos do produto](0003-Requisitos-do-Produto.md) | Produto, conteúdo | Checklist original do MVP + banco inicial de 60 FAQs | 📚 Referência (base histórica) |
| 0004 | [Plano de banco de dados](0004-Plano-de-Banco-de-Dados.md) | Dados | Plano PostgreSQL em 3FN (citado como DB §n) | 📝 Aprovado pelo autor; executar via `0007` |
| 0005 | [Plano de profissionalização (v2)](0005-Plano-de-Profissionalizacao.md) | Todos | Visão, decisões D008–D027, arquitetura alvo, fases F0–F9 | 🔶 Proposta (escopo revisto por `0006`/`0007`) |
| 0006 | [Análise crítica](0006-Analise-Critica.md) | Todos | 11 perguntas críticas sobre o projeto; recomendação de escopo | 🔶 Proposta |
| 0007 | [Tasks: reinício do projeto](0007-Tasks-Reinicio-do-Projeto.md) | Todos | Plano de longo prazo: 10 épicos, 55 tasks, críticas e notas | 🔶 Proposta (após a entrega de 29/11) |
| **0018** | [**Plano de entrega: 29/11**](0018-Plano-de-Entrega-29-11.md) | Todos | **Plano vigente até a entrega:** escopo P0/P1/P2, cronograma diário, riscos, 11 perguntas | 🔴 **Prioritário** |

## Produto e experiência

| Nº | Documento | Para quem | Tipo | Status |
|----|-----------|-----------|------|--------|
| 0008 | [Desenho conversacional](0008-Desenho-Conversacional.md) | IA e conversa, Experiência | Intenções, menu, fluxos, escalonamento, métricas | 🔶 Proposta |
| 0009 | [Identidade visual](0009-Identidade-Visual.md) | Experiência | Tork: nome, avatar, cores, tipografia, tom de voz | 🔶 Proposta |

## Técnico

| Nº | Documento | Para quem | Tipo | Status |
|----|-----------|-----------|------|--------|
| 0010 | [Stack e ferramentas](0010-Stack-e-Ferramentas.md) | Plataforma | Ferramentas gratuitas e hospedagem | 🔶 Proposta |
| 0011 | [Arquitetura atual](0011-Arquitetura-Atual.md) | Desenvolvimento | Como a v0.2 funciona (busca, contexto, dados) | ✅ Vigente para a v0.2 |
| 0012 | [Referência da API](0012-Referencia-da-API.md) | Desenvolvimento, integrações | Endpoints, campos e exemplos | ✅ Vigente para a v0.2 |
| 0013 | [Guardrails](0013-Guardrails.md) | IA e conversa | Catálogo G01–G19 e como adicionar | ✅ Vigente (G20–G24 em `0005`/`0007`) |
| 0014 | [Base de conhecimento](0014-Base-de-Conhecimento.md) | Dados, conteúdo | Formato da FAQ e revisão das sugestões | ✅ Vigente para a v0.2 |
| 0019 | [Fluxograma do sistema](0019-Fluxograma-do-Sistema.md) | Todos | Fluxograma completo em Mermaid + componentes, fluxos, ciclo da FAQ, dados, trabalho e cronograma | 🔶 Proposta (alvo da entrega de 29/11) |

## Operação e registros

| Nº | Documento | Para quem | Tipo | Status |
|----|-----------|-----------|------|--------|
| 0015 | [Roteiro de demonstração](0015-Roteiro-de-Demonstracao.md) | Quem apresenta | Passo a passo da demo e plano B | ✅ Vigente para a v0.2 |
| 0016 | [Registro de decisões](0016-Registro-de-Decisoes.md) | Todos | Decisões aprovadas (D001–D007) | ✅ Vigente |
| 0017 | [Registro de prompts](0017-Registro-de-Prompts.md) | Todos | Histórico dos pedidos feitos à IA e resultados | ✅ Vigente |

## Fora da pasta `docs/`

| Local | Conteúdo |
|-------|----------|
| [`README.md`](../README.md) | Instalação, execução, testes e visão rápida |
| [`CHANGELOG.md`](../CHANGELOG.md) | Histórico de versões |
| [`app/guardrails/README.md`](../app/guardrails/README.md) | Mapa dos arquivos de guardrails |
| [`static/brand/`](../static/brand/) | Avatar, logo e favicon do Tork |
| [`sql/`](../sql/) | Esboços SQL do time (PostgreSQL); serão substituídos pelas migrações da E2 |

## Legenda de status

| Status | Significado |
|--------|-------------|
| ✅ Vigente | Descreve o que existe hoje ou uma decisão aprovada |
| 🔶 Proposta | Aguarda aprovação do time |
| 📝 Aprovado pelo autor | Escrito por um membro do time; execução via `0007` |
| 📚 Referência | Base histórica; consultar, mas o plano vigente está em outro documento |
| 🔴 Prioritário | Plano em execução agora; tem precedência sobre os demais |
