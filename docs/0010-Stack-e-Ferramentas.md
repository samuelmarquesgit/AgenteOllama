# 0010 — Stack e ferramentas gratuitas

> **Versão:** 1.0 · **Data:** 2026-11-23 · Parte do [plano de profissionalização](0005-Plano-de-Profissionalizacao.md).
> Planos gratuitos de serviços e licenças de modelos mudam: **conferir antes de adotar** os itens que não são open source auto-hospedado.

## Princípio

| Categoria | Garantia | Regra |
|-----------|----------|-------|
| Open source **auto-hospedado** | Grátis para sempre | Base de tudo |
| **GitHub** em repositório **público** | Estável há anos | Código, CI, gestão |
| Plano gratuito de serviço pago | Pode mudar, expirar ou "dormir" | Evitar no essencial |

Custo total: **R$ 0**.
Requisito de hardware para desenvolvimento: 16 GB de RAM (32 GB recomendados para modelos de 8B).

## 1. Desenvolvimento

| Ferramenta | Uso | Licença |
|------------|-----|---------|
| VS Code | Editor | MIT |
| **uv** | Python, venv e dependências (fixa a versão por projeto: resolve a colisão de `.venv`) | MIT/Apache |
| Python **3.13** | Versão com suporte amplo das bibliotecas | PSF |
| Docker Engine / **Podman Desktop** | Containers. O Docker Desktop é grátis para pessoas, educação e empresas com menos de 250 funcionários e menos de US$ 10 mi; acima disso, use Podman | Apache |
| Git + GitHub CLI | Versionamento e PRs | GPL/MIT |
| make (ou just) | `make up / test / seed / lint / eval` | GPL/CC0 |

## 2. Banco de dados

| Ferramenta | Uso | Licença |
|------------|-----|---------|
| **PostgreSQL 17** (imagem `pgvector/pgvector:pg17`) | Banco principal; pgvector já incluso para a F7 | PostgreSQL |
| unaccent + pg_trgm | Busca sem acento e tolerante a erro | Nativo |
| **Alembic** | Migrações com rollback | MIT |
| **psycopg 3** | Driver; SQL parametrizado | LGPL |
| DBeaver Community / pgAdmin 4 | GUI e diagrama ER | Apache / PostgreSQL |
| Faker | Seeds sintéticos (`SEED=2026`) | MIT |
| testcontainers-python | Postgres real e descartável nos testes | Apache |
| pg_dump / pgBackRest | Backup e restauração | Livre |

## 3. Backend

| Ferramenta | Uso | Licença |
|------------|-----|---------|
| FastAPI + Uvicorn | API | MIT/BSD |
| Pydantic v2 + pydantic-settings | Validação e configuração por `.env` | MIT |
| slowapi | Rate limit | MIT |
| structlog | Logs em JSON sem dados do cliente | MIT/Apache |
| httpx | Cliente HTTP (Ollama e integrações) | BSD |

## 4. Inteligência artificial

| Ferramenta | Uso | Licença |
|------------|-----|---------|
| **Ollama** | Modelos locais | MIT |
| **qwen3:4b / qwen3:8b** | Candidatos a modelo principal | **Apache 2.0** |
| llama3.2:3b | Base de comparação (modelo atual) | Llama Community (comercial com atribuição) |
| ~~qwen2.5:3b~~ | **Não usar:** *Qwen Research License*, sem uso comercial (os outros tamanhos do Qwen2.5 são Apache) | Restrita |
| nomic-embed-text (768) / bge-m3 (1024) | Embeddings para o RAG (F7) | Apache / MIT |
| Modelo multimodal local (ex.: Qwen2.5-VL 7B, Apache) | "Envie uma foto da ferramenta" (F9), conferir a licença do tamanho escolhido | Verificar |
| **promptfoo** | Avaliação, comparação de modelos, red team | MIT |
| Langfuse (auto-hospedado) | Rastreamento das chamadas ao LLM | MIT |
| Microsoft Presidio (opcional) | Reforço na detecção de dados pessoais | MIT |

## 5. Frontend

| Ferramenta | Uso | Licença |
|------------|-----|---------|
| HTML + CSS + JS (ES modules), sem build | Chat do Tork | — |
| Lucide | Ícones (menu, selos) | ISC |
| Barlow Semi Condensed · Inter · JetBrains Mono | Fontes servidas localmente | SIL OFL |
| Playwright | Testes e2e | Apache |
| axe-core + Lighthouse CI | Acessibilidade e qualidade | MPL/Apache |

## 6. Qualidade e segurança

| Ferramenta | Uso | Licença |
|------------|-----|---------|
| Ruff | Lint e formatação | MIT |
| mypy (ou Pyright) | Tipos | MIT |
| pytest + pytest-cov | Testes e cobertura | MIT |
| pre-commit | Checagens antes do commit | MIT |
| gitleaks | Bloqueia segredos | MIT |
| Bandit + pip-audit | Segurança do código e das dependências | Apache |
| Trivy | Varredura da imagem Docker | Apache |
| CodeQL + Dependabot | Grátis em repositório público | GitHub |
| SonarQube Cloud (opcional) | Painel de qualidade (grátis para público) | Plano gratuito |

## 7. CI/CD e gestão

| Ferramenta | Uso | Custo |
|------------|-----|-------|
| GitHub Actions | CI completo | Ilimitado (repositório público) |
| GitHub Container Registry | Imagens | Grátis (público) |
| Release Please | SemVer + CHANGELOG automáticos | Apache |
| GitHub Projects + Issues + Milestones | Kanban e fases | Grátis |
| Proteção da `main` + CODEOWNERS | PR, revisão e CI obrigatórios | Grátis (público) |
| MkDocs Material + GitHub Pages | Site da documentação | MIT / grátis |
| Mermaid | Diagramas no Markdown | MIT |

## 8. Hospedagem e operação

| Opção | Uso | Observação |
|-------|-----|------------|
| **A. PC do time + Cloudflare Tunnel** | Desenvolvimento e demonstrações | Grátis sem cartão; no ar só com o PC ligado |
| **B. Oracle Cloud Always Free** (ARM, 4 núcleos, 24 GB) | 24 h no ar: Postgres + Ollama 3–4B + API | Exige cartão no cadastro; VMs ociosas podem ser recicladas |
| ❌ Render, Railway, Fly, Heroku | — | Sem plano gratuito, banco expira ou "dorme"; não rodam LLM |
| Docker Compose + **Caddy** | Orquestração e HTTPS automático | Apache |
| **Uptime Kuma** | Monitoramento de disponibilidade | MIT |
| **GlitchTip** | Captura de erros (compatível com Sentry) | MIT |
