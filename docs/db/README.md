# Banco de dados — ToolExpert AI

> SQLite normalizado (3FN) nesta entrega; o PostgreSQL em Docker fica para depois, por decisão do time (2026-11-23).
> As migrações foram escritas em SQL portável sempre que possível, para facilitar a migração futura.

| Documento | Conteúdo |
|-----------|----------|
| [DER.md](DER.md) | Diagrama entidade-relacionamento, cardinalidades e decisões de normalização |
| [DATA_DICTIONARY.md](DATA_DICTIONARY.md) | Coluna, tipo, nulidade, chaves e regras de cada tabela (**gerado do esquema**) |
| [SEED_CATALOG.md](SEED_CATALOG.md) | O que os seeds criam, contagens e características dos dados fictícios |
| [SECURITY.md](SECURITY.md) | Acesso, dados pessoais e retenção |
| [EXECUTION_LOG.md](EXECUTION_LOG.md) | Evidências: comandos, contagens reais, testes e planos de consulta |

## Pré-requisitos

- Python 3.12+ com as dependências do projeto (`requirements.txt`). O SQLite já vem com o Python.
- Nada mais: sem Docker, sem servidor, sem internet.

## Comandos

```powershell
# Aplicar migrações pendentes (cria data/loja.db se não existir)
.venv\Scripts\python -m app.db.migracoes

# Ver o estado das migrações
.venv\Scripts\python -m app.db.migracoes status

# Reverter até uma versão (ex.: desfaz 0004 e 0003)
.venv\Scripts\python -m app.db.migracoes down 0003

# Migrar + popular + conferir contagens (falha com código 1 se divergir)
.venv\Scripts\python -m app.db.seeds

# Regenerar o catálogo fictício (determinístico, SEED=2026) e o dicionário de dados
.venv\Scripts\python database\seeds\gerar_catalogo.py
.venv\Scripts\python database\gerar_dicionario.py

# Testes do banco
.venv\Scripts\python -m pytest tests/test_banco.py -q
```

A API e o terminal (`agente.py`) migram e populam o banco sozinhos na primeira execução.
Para outro arquivo, defina `BANCO_SQLITE=caminho\arquivo.db`.

**Reset (apenas em desenvolvimento):** pare a API e apague `data/loja.db`; na próxima execução ele é recriado.
As respostas aprendidas pela IA (tabela `faq_sugestoes`) são perdidas no reset.

## Estrutura

```
database/
├─ migrations/        0001_faq · 0002_loja · 0003_catalogo · 0004_atendimento  (.up.sql / .down.sql)
├─ seeds/
│  ├─ gerar_catalogo.py      gera data/catalogo.json (determinístico)
│  └─ data/                  loja.json · catalogo.json
└─ gerar_dicionario.py       gera docs/db/DATA_DICTIONARY.md
app/db/
├─ conexao.py         abre o SQLite com FKs ligadas e a função norm() (sem acento)
├─ migracoes.py       executor de migrações (transação por migração, tabela schema_migrations)
├─ seeds.py           seeds idempotentes (UPSERT) + verificador de contagens
└─ repositorios.py    FAQ, sugestões, loja, catálogo e atendimento (SQL parametrizado)
knowledge/faq.json    fonte da base de conhecimento (60 FAQs; meta do plano: 150)
```

## Decisões

| Tema | Decisão | Motivo |
|------|---------|--------|
| Motor | **SQLite** agora; PostgreSQL depois | Decisão do time para a entrega de 29/11; zero instalação |
| Migrações | **SQL versionado** (`NNNN_nome.up/down.sql`) + executor próprio | Uma das opções do DB §0; sem dependência extra; rollback testado |
| `atualizado_em` | **Trigger** `AFTER UPDATE` | Fica correto mesmo se alguém atualizar direto no banco |
| Sem acento na busca | Função `norm()` registrada na conexão | Equivalente ao `unaccent` do PostgreSQL; consulta continua parametrizada |
| Dinheiro | `preco_centavos INTEGER` | Sem erro de arredondamento de ponto flutuante |
| Vigência de preço | Triggers impedem sobreposição | O SQLite não tem `EXCLUDE USING gist` |
| Ciclos de categoria | `CHECK` impede autorreferência; ciclos maiores na aplicação | O SQLite não aceita CTE dentro de trigger |
| Respostas da IA | Tabela própria `faq_sugestoes` (D010) | FAQ oficial fica limpa; aprovação humana |

## Diferenças em relação ao plano PostgreSQL (DB §0–§10)

| Item do plano | Nesta entrega | Na migração para o PostgreSQL |
|---------------|---------------|-------------------------------|
| PostgreSQL 16+ | SQLite 3.50 | Trocar a conexão e ajustar tipos (`timestamptz`, `numeric(12,2)`, `boolean`, `identity`) |
| `unaccent`/`pg_trgm` | `norm()` em Python + `LIKE` | Extensões nativas + índice trigram |
| Usuário de aplicação com privilégio mínimo (DB §9) | Não se aplica ao SQLite (arquivo local) | Papéis `toolexpert_migrator` e `toolexpert_app` |
| `EXPLAIN (ANALYZE, BUFFERS)` | `EXPLAIN QUERY PLAN` (ver log) | Rodar o `EXPLAIN ANALYZE` |
| 150 FAQs / 450 variações | **60 FAQs / 77 variações** (conteúdo é a próxima tarefa) | — |
