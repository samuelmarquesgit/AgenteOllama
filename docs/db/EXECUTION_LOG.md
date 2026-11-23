# Log de execução — banco de dados

> Evidências exigidas pelo plano de banco (DB §0 e §10): comando, saída resumida e arquivos alterados.
> Só registra o que foi **executado e verificado**.

## 2026-11-23 · Banco normalizado em SQLite (branch `feat/banco-normalizado-sqlite`)

**Decisão do time (2026-11-23):** "deixe no SQLite nesse primeiro momento, depois colocaremos em um Docker certinho".
Entrega no repositório do GitHub. Prazo: 29/11/2026 00:00.

### Ambiente

| Item | Valor |
|------|-------|
| Sistema | Windows 11 |
| Python | 3.14 (`.venv` do projeto) |
| SQLite | 3.50.4 (embutido no Python) |

### 1. Migrações

```text
> python -m app.db.migracoes status
0001 faq             aplicada
0002 loja            aplicada
0003 catalogo        aplicada
0004 atendimento     aplicada
```

Rollback testado (`tests/test_banco.py::test_rollback_e_reaplicacao`): `upgrade → downgrade até 0001 → upgrade`, sem erro e com as 19 tabelas recriadas.
Migração com erro não fica pela metade (`test_migracao_com_erro_nao_fica_pela_metade`).

### 2. Seeds e contagens reais

```text
> python -m app.db.seeds
faq_categorias                8  OK
faq_perguntas                60  OK
unidades                      2  OK
unidade_horarios             12  OK
formas_pagamento              4  OK
politicas                     6  OK
categorias                   25  OK
marcas                       15  OK
produtos                    300  OK
especificacoes               45  OK
produto_especificacoes     1500  OK
produto_precos              600  OK
produto_imagens             300  OK
estoques                    600  OK
```

- Segunda execução: mesmas contagens (idempotente). Tempo total: ~0,25 s.
- Gerador do catálogo rodado duas vezes: mesmo SHA-1 do `catalogo.json` (determinístico, `SEED=2026`).

### 3. Planos de consulta (`EXPLAIN QUERY PLAN`, equivalente SQLite ao `EXPLAIN ANALYZE`)

| Consulta | Plano |
|----------|-------|
| FAQ por categoria | `SEARCH faq_perguntas USING INDEX ix_faq_perguntas_categoria_status (categoria_id=?)` |
| Variações de uma pergunta | `SEARCH faq_variacoes USING COVERING INDEX sqlite_autoindex_faq_variacoes_1 (pergunta_id=?)` |
| Produto por SKU | `SEARCH produtos USING COVERING INDEX sqlite_autoindex_produtos_1 (sku=?)` |
| Produtos por categoria | `SEARCH produtos USING COVERING INDEX ix_produtos_categoria (categoria_id=?)` |
| Preço vigente | `SEARCH p USING INDEX ix_produto_precos_produto (produto_id=? AND inicio_vigencia<?)` |

| Medição (máquina de desenvolvimento) | Tempo médio |
|--------------------------------------|-------------|
| Busca de catálogo com 3 filtros (100 execuções) | 0,39 ms |
| Busca de FAQ por termo (100 execuções) | 0,88 ms |
| Carga da FAQ para o motor de busca (20 execuções) | 0,53 ms |

### 4. Testes

```text
> python -m pytest -q
687 passed
```

| Arquivo | Cobre (DB §8) |
|---------|---------------|
| `tests/test_banco.py` | Migrações em banco vazio, rollback, reaplicação, FKs (RESTRICT, CASCADE, SET NULL), unicidades, CHECKs de preço, quantidade, datas, códigos e consentimento, triggers de vigência e `atualizado_em`, contagens, idempotência, SQL injection, acentos, termos inexistentes, importação do banco legado |
| `tests/test_intencoes.py` | Respostas de catálogo e loja vindas do banco, filtros de voltagem e preço, guardrails G20/G24, API `/produtos` e `/loja` |
| Demais arquivos | Comportamento do Tork (FAQ, contexto, guardrails, API, frontend, terminal) agora sobre o banco normalizado |

Nenhum teste usa dados pessoais reais; os CPFs e cartões dos testes de guardrail são números de exemplo.

### 5. Migração do banco local da v0.2

O `data/loja.db` local da demonstração (tabela única `faq`) é convertido na primeira conexão:
as respostas aprendidas viram `faq_sugestoes` e a tabela antiga é **renomeada** para `legado_faq_v02` (nada é apagado).
Verificado numa cópia do banco da demo: 5 respostas aprendidas importadas.

### Arquivos criados ou alterados

`database/migrations/*` (8 arquivos) · `database/seeds/gerar_catalogo.py` · `database/seeds/data/{loja,catalogo}.json` ·
`database/gerar_dicionario.py` · `app/db/{conexao,migracoes,seeds,repositorios}.py` · `app/banco.py` · `app/intencoes.py` ·
`app/agente.py` · `app/main.py` · `static/index.html` · `static/produtos/placeholder.svg` · `knowledge/faq.json` (nível de risco) ·
`tests/test_banco.py` · `tests/test_intencoes.py` · `docs/db/*`

### Pendências

| Pendência | Onde |
|-----------|------|
| Completar 150 FAQs e 450 variações (hoje 60 e 77) | `0018`, P0.4 |
| Revisão humana registrada de 30 FAQs | `0018`, P1.7 |
| PostgreSQL em Docker, papéis com privilégio mínimo e backup | Após a entrega (decisão do time) |
| Rotina de retenção de sugestões e atendimentos | `SECURITY.md` |
