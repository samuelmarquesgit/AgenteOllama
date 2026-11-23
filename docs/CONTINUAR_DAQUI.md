# Continuar daqui — estado do projeto em 2026-11-19

> Arquivo de retomada. Leia este primeiro na próxima sessão (pessoa ou IA).

## Resumo em 30 segundos

- **ToolExpert AI**: agente de atendimento de uma loja de ferramentas. O atendente se chama **Tork**.
- O **MVP foi demonstrado** em 2026-11-19: FastAPI + SQLite (60 FAQs) + Ollama local como fallback, que grava as respostas novas no banco.
- **Próximo passo:** profissionalizar, conforme [`PLANO_PROFISSIONALIZACAO.md`](PLANO_PROFISSIONALIZACAO.md) (fases F0–F8).
  Isso ainda depende da **aprovação do time** para as decisões D008–D018 e para a identidade visual ([`identidade-visual.md`](identidade-visual.md)).

## Estado do Git

| Item | Situação |
|------|----------|
| `main` (GitHub) | `49c8885`: merge da PR #1 (MVP 0.1: SQLite + Ollama + docs + 355 testes) |
| `feat/mvp1-agente-loja` | `004c45e` **fora da main**: contexto de conversa + `app/guardrails/` (G01–G19) + 572 testes. **Precisa da PR #2** |
| `origin/feat/modelo-qwen2.5-3b` | Commit `0845f4b` de um colaborador: padrão `qwen2.5:3b`. Saiu da main antiga → **vai conflitar** com o `004c45e`. Mensagem em espanhol |
| Local, sem commit | `docs/PLANO_PROFISSIONALIZACAO.md`, `docs/identidade-visual.md`, `static/brand/*.svg`, `docs/CONTINUAR_DAQUI.md`, entrada P009 em `docs/prompts.md` e, do Samuel, `docs/PLANO_EXECUCAO_BANCO_TOOLEXPERT_AI.md` e `sql/0003-pgvector.sql` |
| `README.md` local | Tem um link para um Google Docs pessoal **não commitado**; decidir se pode ser público |

## Para fazer na próxima sessão (em ordem)

1. Decidir sobre o link do Google Docs no `README.md`.
2. Commitar o planejamento numa branch `docs/replanejamento` e abrir a PR.
3. Abrir a **PR #2** com o `004c45e` (contexto + guardrails).
4. Resolver a branch `feat/modelo-qwen2.5-3b`: rebase sobre a nova main e deixar o modelo só no `.env` (D012).
5. O time aprova ou ajusta D008–D018 e a identidade do Tork.
6. Criar os milestones F0–F4 e as issues no GitHub a partir das checklists do plano.
7. Executar a **F0** (pyproject, Ruff, pre-commit, CI, Docker Compose com Postgres 16, templates, `.gitattributes`).

## Como rodar hoje

```powershell
.venv\Scripts\python -m uvicorn app.main:app --port 8000   # abrir http://127.0.0.1:8000 (não use localhost: +2 s)
.venv\Scripts\python -m pytest -q                          # 572 testes, não precisam do Ollama
```

- Ollama instalado só com o `llama3.2`; `qwen2.5:3b` **não está instalado**.
- Para recomeçar a base, pare a API e apague `data/loja.db` (o arquivo fica bloqueado enquanto a API roda).
- Docker 29 disponível (para o Postgres da F0/F1); `psql` não está instalado.

## Decisões abertas (detalhes no plano, seção 3)

| # | Tema | Recomendação |
|---|------|--------------|
| D008 | Migrações | Alembic com SQL explícito |
| D009 | Acesso ao banco | psycopg 3 + SQL parametrizado |
| D010 | Respostas aprendidas | Tabela `faq_sugestoes`, aprovação humana |
| D011 | Busca | `unaccent` + `pg_trgm` |
| D012 | Modelo LLM | Escolher por avaliação (F4); por enquanto via `.env` |
| D013 | pgvector | Dimensão do embedding local (ex.: 768), só na F7 |
| D014 | "Sem LLM" do plano de banco | Vale só para a camada de banco |
| D015 | Frontend | HTML/CSS/JS sem build, modularizado |
| D016 | Branches | GitHub Flow, main protegida |
| D017 | Idioma | pt-BR em código, commits e docs |
| D018 | Atendente | Tork / ToolExpert AI |

## Pessoas

- Samuel (`samuelmarquesgit`): dono do repositório; mergeia as PRs.
- Colaboradores no GitHub: `susejgo89` (autor da branch do qwen2.5:3b), `ffegegsgabad` e `SahSalema` (entrou em 2026-11-20).
- Verificado em 2026-11-23: nenhuma PR, issue, comentário ou commit novo desde a pausa.
  O time agora tem 4 pessoas: rever a divisão de frentes na seção 6 do plano.
