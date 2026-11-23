# 0001 — Contexto do projeto

> **Leia este documento primeiro** (pessoa ou IA). Ele resume o que é o projeto, de onde veio, em que estado está e o que vem a seguir.
> **Última atualização:** 2026-11-23 · Índice completo da documentação: [`0002-Indice.md`](0002-Indice.md)
>
> 🔴 **Prazo de entrega: 29/11/2026 00:00**, com possível extensão até **30/11/2026 22:00**. Plano em execução: [`0018-Plano-de-Entrega-29-11.md`](0018-Plano-de-Entrega-29-11.md).

## 1. O que é

**ToolExpert AI** é um assistente virtual para lojas de ferramentas elétricas e eletrônicas. O atendente se chama **Tork**.

O Tork:
- responde dúvidas técnicas e comerciais a partir de uma base de perguntas revisadas;
- usa um modelo de linguagem **local** (Ollama) quando a pergunta é nova, e grava a resposta como sugestão para revisão humana;
- entende continuações da conversa ("e para metal?");
- é protegido por guardrails em camadas, com **19 implementados (G01–G19)** e mais 5 planejados;
- **nunca** deve inventar preço, estoque, prazo ou compatibilidade.

## 2. Linha do tempo

| Data | Marco |
|------|-------|
| 2026-11-17 | Primeiro protótipo (`agente.py` de terminal, para oficina mecânica) |
| 2026-11-19 | Checklist do produto (`0003`) e MVP construído e **demonstrado**: FastAPI + SQLite (60 FAQs) + Ollama, aprendizado, 355 testes (PR #1, v0.1.0) |
| 2026-11-19 | Contexto de conversa + pasta `app/guardrails/` (G01–G19), 572 testes (v0.2.0, commit `004c45e`) |
| 2026-11-19 | Plano de banco PostgreSQL do time (`0004`) e primeiro replanejamento + identidade visual (`fcd1748`) |
| 2026-11-23 | Plano v2 (`0005`), desenho conversacional (`0008`), stack gratuita (`0010`), **análise crítica (`0006`)** e **tasks de reinício (`0007`)**; documentação numerada |

## 3. Pessoas

| Pessoa (GitHub) | Papel atual |
|-----------------|-------------|
| `samuelmarquesgit` | Dono do repositório; conduz o projeto; mergeia as PRs |
| `susejgo89` | Colaborador; autor da branch `feat/modelo-qwen2.5-3b` |
| `ffegegsgabad` | Colaborador (sem contribuições ainda) |
| `SahSalema` | Colaborador desde 2026-11-20 (sem contribuições ainda) |

O **dono do produto**, os **donos das frentes** e os **revisores técnico e jurídico** ainda não foram definidos (tasks T-002 e T-004).

## 4. Estado atual

### Código (v0.2)

| Componente | Situação |
|------------|----------|
| API FastAPI (`/chat`, `/health`, `/faqs`, `/conversas`) | Funcionando |
| Banco | SQLite **normalizado (3FN)**, 19 tabelas em 4 migrações; 60 FAQs, loja e catálogo **fictício** de 300 produtos (v0.3, branch `feat/banco-normalizado-sqlite`) |
| IA | Ollama local; padrão `llama3.2` (o `qwen2.5:3b` está numa branch e **não tem licença comercial**) |
| Guardrails | G01–G19 em `app/guardrails/` |
| Testes | 572, todos passando, sem depender do Ollama |
| Frontend | `static/index.html` funcional; identidade do Tork criada (`static/brand/`), ainda não aplicada |

### Git

| Branch | Situação |
|--------|----------|
| `main` | v0.1 (PR #1) |
| `feat/mvp1-agente-loja` | `004c45e` (v0.2), **fora da main** |
| `docs/replanejamento-profissionalizacao` | `fcd1748` + esta reorganização da documentação (local, ainda não enviada) |
| `origin/feat/modelo-qwen2.5-3b` | `0845f4b` (colaborador), vai conflitar com o `004c45e` |

O `README.md` local tem um link para um Google Docs pessoal, não commitado: decidir se pode ser público.

## 5. Decisões e pendências principais

- **Análise crítica (`0006`):** o plano v2 tira 9–11/15 em custo, tempo e risco. A recomendação é cortar ~40% do escopo, acrescentar uma **fase de descoberta (E0)** e testar embeddings antes de investir em palavras-chave.
- **Plano executável:** [`0007-Tasks-Reinicio-do-Projeto.md`](0007-Tasks-Reinicio-do-Projeto.md), com 55 tasks e ~70 dias-pessoa até o Gate.
- **Decisões abertas:** D008–D027 em [`0005`](0005-Plano-de-Profissionalizacao.md), seção 3.
- **Prazo definido (2026-11-23):** 29/11 00:00, extensão possível até 30/11 22:00. O `0018` reduz o escopo ao que cabe em ~5 dias.
- **Pergunta ainda aberta:** o plano de banco PostgreSQL (`0004`) é a entrega avaliada? O `0018` supõe que sim.

## 6. Próximos passos

1. Confirmar se o Postgres é avaliado e seguir o cronograma do [`0018`](0018-Plano-de-Entrega-29-11.md).
2. Decidir sobre o link do Google Docs no `README.md`.
3. Enviar as branches e abrir as PRs (contexto + guardrails + documentação) (T-007).
4. Executar o épico **E0 — Descoberta** (1 semana).
5. Criar o GitHub Projects e as issues a partir do `0007` (T-014).

## 7. Como rodar hoje

```powershell
.venv\Scripts\python -m uvicorn app.main:app --port 8000   # abrir http://127.0.0.1:8000 (localhost acrescenta ~2 s)
.venv\Scripts\python -m pytest -q                          # 572 testes
```

- No Ollama, só o `llama3.2` está instalado.
- Para zerar a base, pare a API e apague `data/loja.db`.
- O Docker está disponível; o `psql` não.

## 8. Glossário

| Termo | Significado |
|-------|-------------|
| **Tork** | Nome do atendente virtual |
| **FAQ** | Pergunta e resposta revisadas, guardadas no banco |
| **Sugestão** | Resposta gerada pela IA que aguarda aprovação humana |
| **Guardrail (Gnn)** | Regra de proteção numerada (ver `0013`) |
| **Fluxo (F-XXX)** | Conversa guiada com etapas (ver `0008`) |
| **Intenção (Inn)** | O que o cliente quer fazer (ver `0008`) |
| **DB §n** | Seção n do plano de banco (`0004`) |
| **Dn** | Decisão numerada (`0005` e `0016`) |
| **T-nnn / En** | Task e épico do plano de reinício (`0007`) |
| **Gate** | Ponto de aprovação antes das fases pós-MVP |
| **C/T/R** | Nota de custo, tempo e risco (1 = ótimo, 5 = péssimo) |
