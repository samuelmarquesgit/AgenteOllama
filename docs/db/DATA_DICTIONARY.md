# Dicionário de dados

> **Gerado automaticamente** por `database/gerar_dicionario.py` a partir das migrações. Não edite à mão.
> Convenções: `snake_case`; PK `INTEGER` (rowid); datas ISO-8601 em `TEXT` (UTC); booleanos `0/1`; dinheiro em centavos (`INTEGER`).

## `faq_categorias`

Agrupamento temático das perguntas da FAQ.

| Coluna | Tipo | Nulo? | Padrão | Chave / referência |
|--------|------|:-----:|--------|--------------------|
| `id` | INTEGER | não |  | PK |
| `codigo` | TEXT | não |  | UNIQUE |
| `nome` | TEXT | não |  | UNIQUE |
| `descricao` | TEXT | sim |  |  |
| `ativo` | INTEGER | não | `1` |  |
| `criado_em` | TEXT | não | `strftime('%Y-%m-%dT%H:%M:%SZ', 'now')` |  |
| `atualizado_em` | TEXT | não | `strftime('%Y-%m-%dT%H:%M:%SZ', 'now')` |  |

**Regras (CHECK):**

- `codigo GLOB '[a-z_]*' AND length(codigo) > 0`
- `length(trim(nome)) > 0`
- `ativo IN (0, 1)`

## `faq_perguntas`

Pergunta e resposta revisáveis da base de conhecimento (código estável FAQ-NNN).

| Coluna | Tipo | Nulo? | Padrão | Chave / referência |
|--------|------|:-----:|--------|--------------------|
| `id` | INTEGER | não |  | PK |
| `codigo` | TEXT | não |  | UNIQUE |
| `categoria_id` | INTEGER | não |  | FK → `faq_categorias.id` (RESTRICT) |
| `pergunta` | TEXT | não |  |  |
| `resposta` | TEXT | não |  |  |
| `fonte` | TEXT | sim |  |  |
| `nivel_risco` | TEXT | não | `'baixo'` |  |
| `status` | TEXT | não | `'rascunho'` |  |
| `revisado_por` | TEXT | sim |  |  |
| `revisado_em` | TEXT | sim |  |  |
| `criado_em` | TEXT | não | `strftime('%Y-%m-%dT%H:%M:%SZ', 'now')` |  |
| `atualizado_em` | TEXT | não | `strftime('%Y-%m-%dT%H:%M:%SZ', 'now')` |  |

**Regras (CHECK):**

- `codigo GLOB 'FAQ-[0-9][0-9][0-9]*'`
- `length(trim(pergunta)) > 0`
- `length(trim(resposta)) > 0`
- `nivel_risco IN ('baixo', 'medio', 'alto')`
- `status IN ('rascunho', 'pendente_validacao', 'validado', 'inativo')`

## `faq_variacoes`

Outras formas de fazer a mesma pergunta (melhoram a busca).

| Coluna | Tipo | Nulo? | Padrão | Chave / referência |
|--------|------|:-----:|--------|--------------------|
| `id` | INTEGER | não |  | PK |
| `pergunta_id` | INTEGER | não |  | FK → `faq_perguntas.id` (CASCADE) |
| `variacao` | TEXT | não |  |  |
| `criado_em` | TEXT | não | `strftime('%Y-%m-%dT%H:%M:%SZ', 'now')` |  |

**Unicidade composta:** (pergunta_id, variacao)

**Regras (CHECK):**

- `length(trim(variacao)) > 0`

## `faq_palavras_chave`

Termos que identificam o assunto da pergunta (usados na pontuação da busca).

| Coluna | Tipo | Nulo? | Padrão | Chave / referência |
|--------|------|:-----:|--------|--------------------|
| `id` | INTEGER | não |  | PK |
| `pergunta_id` | INTEGER | não |  | FK → `faq_perguntas.id` (CASCADE) |
| `termo` | TEXT | não |  |  |

**Unicidade composta:** (pergunta_id, termo)

**Regras (CHECK):**

- `length(trim(termo)) > 0`

## `faq_sugestoes`

Respostas geradas pela IA aguardando revisão humana (D010). Palavras de busca derivam da pergunta.

| Coluna | Tipo | Nulo? | Padrão | Chave / referência |
|--------|------|:-----:|--------|--------------------|
| `id` | INTEGER | não |  | PK |
| `pergunta` | TEXT | não |  |  |
| `resposta` | TEXT | não |  |  |
| `origem` | TEXT | não | `'ollama'` |  |
| `status` | TEXT | não | `'pendente'` |  |
| `faq_pergunta_id` | INTEGER | sim |  | FK → `faq_perguntas.id` (SET NULL) |
| `motivo_revisao` | TEXT | sim |  |  |
| `revisado_por` | TEXT | sim |  |  |
| `revisado_em` | TEXT | sim |  |  |
| `criado_em` | TEXT | não | `strftime('%Y-%m-%dT%H:%M:%SZ', 'now')` |  |

**Regras (CHECK):**

- `length(trim(pergunta)) > 0`
- `length(trim(resposta)) > 0`
- `origem IN ('ollama', 'time')`
- `status IN ('pendente', 'aprovada', 'rejeitada')`
- `status <> 'aprovada' OR faq_pergunta_id IS NOT NULL`

## `unidades`

Lojas físicas (dados fictícios).

| Coluna | Tipo | Nulo? | Padrão | Chave / referência |
|--------|------|:-----:|--------|--------------------|
| `id` | INTEGER | não |  | PK |
| `codigo` | TEXT | não |  | UNIQUE |
| `nome` | TEXT | não |  |  |
| `logradouro` | TEXT | não |  |  |
| `numero` | TEXT | não |  |  |
| `bairro` | TEXT | não |  |  |
| `cidade` | TEXT | não |  |  |
| `uf` | TEXT | não |  |  |
| `cep` | TEXT | não |  |  |
| `telefone` | TEXT | sim |  |  |
| `link_mapa` | TEXT | sim |  |  |
| `ativo` | INTEGER | não | `1` |  |

**Regras (CHECK):**

- `length(trim(codigo)) > 0`
- `length(trim(nome)) > 0`
- `length(uf) = 2 AND uf = upper(uf)`
- `cep GLOB '[0-9][0-9][0-9][0-9][0-9]-[0-9][0-9][0-9]'`
- `ativo IN (0, 1)`

## `unidade_horarios`

Horário de funcionamento por dia da semana (0 = domingo). Dia sem linha = fechado.

| Coluna | Tipo | Nulo? | Padrão | Chave / referência |
|--------|------|:-----:|--------|--------------------|
| `unidade_id` | INTEGER | não |  | PK · FK → `unidades.id` (CASCADE) |
| `dia_semana` | INTEGER | não |  | PK |
| `abre` | TEXT | não |  |  |
| `fecha` | TEXT | não |  |  |

**Unicidade composta:** (unidade_id, dia_semana)

**Regras (CHECK):**

- `dia_semana BETWEEN 0 AND 6`
- `abre  GLOB '[0-2][0-9]:[0-5][0-9]'`
- `fecha GLOB '[0-2][0-9]:[0-5][0-9]'`
- `fecha > abre`

## `formas_pagamento`

Formas de pagamento aceitas.

| Coluna | Tipo | Nulo? | Padrão | Chave / referência |
|--------|------|:-----:|--------|--------------------|
| `id` | INTEGER | não |  | PK |
| `codigo` | TEXT | não |  | UNIQUE |
| `nome` | TEXT | não |  | UNIQUE |
| `ativo` | INTEGER | não | `1` |  |

**Regras (CHECK):**

- `ativo IN (0, 1)`

## `politicas`

Textos oficiais (pagamento, troca, garantia, frete, retirada, atendimento).

| Coluna | Tipo | Nulo? | Padrão | Chave / referência |
|--------|------|:-----:|--------|--------------------|
| `id` | INTEGER | não |  | PK |
| `codigo` | TEXT | não |  | UNIQUE |
| `titulo` | TEXT | não |  |  |
| `texto` | TEXT | não |  |  |
| `atualizado_em` | TEXT | não | `strftime('%Y-%m-%dT%H:%M:%SZ', 'now')` |  |

**Regras (CHECK):**

- `length(trim(codigo)) > 0`
- `length(trim(texto)) > 0`

## `categorias`

Hierarquia de categorias do catálogo (2 níveis).

| Coluna | Tipo | Nulo? | Padrão | Chave / referência |
|--------|------|:-----:|--------|--------------------|
| `id` | INTEGER | não |  | PK |
| `codigo` | TEXT | não |  | UNIQUE |
| `nome` | TEXT | não |  | UNIQUE |
| `categoria_pai_id` | INTEGER | sim |  | FK → `categorias.id` (RESTRICT) |
| `ativo` | INTEGER | não | `1` |  |

**Regras (CHECK):**

- `codigo GLOB '[a-z_]*' AND length(codigo) > 0`
- `ativo IN (0, 1)`
- `categoria_pai_id IS NULL OR categoria_pai_id <> id`

## `marcas`

Marcas do catálogo; todas fictícias na demonstração.

| Coluna | Tipo | Nulo? | Padrão | Chave / referência |
|--------|------|:-----:|--------|--------------------|
| `id` | INTEGER | não |  | PK |
| `nome` | TEXT | não |  | UNIQUE |
| `ficticia` | INTEGER | não | `1` |  |
| `ativo` | INTEGER | não | `1` |  |

**Regras (CHECK):**

- `length(trim(nome)) > 0`
- `ficticia IN (0, 1)`
- `ativo IN (0, 1)`

## `produtos`

Produtos fictícios (SKU FAKE-NNNN). `alimentacao` sustenta o guardrail de voltagem (G20).

| Coluna | Tipo | Nulo? | Padrão | Chave / referência |
|--------|------|:-----:|--------|--------------------|
| `id` | INTEGER | não |  | PK |
| `sku` | TEXT | não |  | UNIQUE |
| `nome` | TEXT | não |  |  |
| `descricao` | TEXT | sim |  |  |
| `categoria_id` | INTEGER | não |  | FK → `categorias.id` (RESTRICT) |
| `marca_id` | INTEGER | não |  | FK → `marcas.id` (RESTRICT) |
| `alimentacao` | TEXT | não |  |  |
| `ativo` | INTEGER | não | `1` |  |
| `criado_em` | TEXT | não | `strftime('%Y-%m-%dT%H:%M:%SZ', 'now')` |  |
| `atualizado_em` | TEXT | não | `strftime('%Y-%m-%dT%H:%M:%SZ', 'now')` |  |

**Regras (CHECK):**

- `sku GLOB 'FAKE-[0-9][0-9][0-9][0-9]'`
- `length(trim(nome)) > 0`
- `alimentacao IN ('127V', '220V', 'bivolt', 'bateria', 'nao_eletrico')`
- `ativo IN (0, 1)`

## `especificacoes`

Tipos de especificação técnica e seu tipo de valor.

| Coluna | Tipo | Nulo? | Padrão | Chave / referência |
|--------|------|:-----:|--------|--------------------|
| `id` | INTEGER | não |  | PK |
| `codigo` | TEXT | não |  | UNIQUE |
| `nome` | TEXT | não |  | UNIQUE |
| `unidade` | TEXT | sim |  |  |
| `tipo_valor` | TEXT | não |  |  |

**Regras (CHECK):**

- `tipo_valor IN ('texto', 'numero', 'booleano')`

## `produto_especificacoes`

Valor de cada especificação por produto (PK composta).

| Coluna | Tipo | Nulo? | Padrão | Chave / referência |
|--------|------|:-----:|--------|--------------------|
| `produto_id` | INTEGER | não |  | PK · FK → `produtos.id` (CASCADE) |
| `especificacao_id` | INTEGER | não |  | PK · FK → `especificacoes.id` (RESTRICT) |
| `valor` | TEXT | não |  |  |

**Unicidade composta:** (produto_id, especificacao_id)

**Regras (CHECK):**

- `length(trim(valor)) > 0`

## `produto_imagens`

Imagens (placeholders locais, sem dependência externa).

| Coluna | Tipo | Nulo? | Padrão | Chave / referência |
|--------|------|:-----:|--------|--------------------|
| `id` | INTEGER | não |  | PK |
| `produto_id` | INTEGER | não |  | FK → `produtos.id` (CASCADE) |
| `url` | TEXT | não |  |  |
| `texto_alternativo` | TEXT | não |  |  |
| `ordem` | INTEGER | não | `1` |  |

**Unicidade composta:** (produto_id, ordem)

**Regras (CHECK):**

- `length(trim(texto_alternativo)) > 0`
- `ordem >= 1`

## `produto_precos`

Histórico de preços com vigência; sobreposição bloqueada por trigger.

| Coluna | Tipo | Nulo? | Padrão | Chave / referência |
|--------|------|:-----:|--------|--------------------|
| `id` | INTEGER | não |  | PK |
| `produto_id` | INTEGER | não |  | FK → `produtos.id` (CASCADE) |
| `preco_centavos` | INTEGER | não |  |  |
| `inicio_vigencia` | TEXT | não |  |  |
| `fim_vigencia` | TEXT | sim |  |  |

**Regras (CHECK):**

- `preco_centavos >= 0`
- `inicio_vigencia GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'`
- `fim_vigencia IS NULL OR fim_vigencia GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'`
- `fim_vigencia IS NULL OR fim_vigencia > inicio_vigencia`

## `estoques`

Quantidade por produto e unidade; o total é calculado, não armazenado.

| Coluna | Tipo | Nulo? | Padrão | Chave / referência |
|--------|------|:-----:|--------|--------------------|
| `produto_id` | INTEGER | não |  | PK · FK → `produtos.id` (CASCADE) |
| `unidade_id` | INTEGER | não |  | PK · FK → `unidades.id` (CASCADE) |
| `quantidade` | INTEGER | não |  |  |
| `atualizado_em` | TEXT | não | `strftime('%Y-%m-%dT%H:%M:%SZ', 'now')` |  |

**Unicidade composta:** (produto_id, unidade_id)

**Regras (CHECK):**

- `quantidade >= 0`

## `atendimentos_humanos`

Pedidos de atendimento humano (sem dados pessoais; exige consentimento).

| Coluna | Tipo | Nulo? | Padrão | Chave / referência |
|--------|------|:-----:|--------|--------------------|
| `id` | INTEGER | não |  | PK |
| `conversa_ref` | TEXT | não |  |  |
| `resumo` | TEXT | não |  |  |
| `motivo` | TEXT | não | `'pedido_cliente'` |  |
| `prioridade` | TEXT | não | `'normal'` |  |
| `status` | TEXT | não | `'aberto'` |  |
| `consentimento` | INTEGER | não |  |  |
| `criado_em` | TEXT | não | `strftime('%Y-%m-%dT%H:%M:%SZ', 'now')` |  |

**Regras (CHECK):**

- `length(conversa_ref) BETWEEN 1 AND 64`
- `length(trim(resumo)) > 0`
- `motivo IN ('pedido_cliente', 'fallback', 'frustracao', 'troca', 'risco', 'pj')`
- `prioridade IN ('normal', 'alta')`
- `status IN ('aberto', 'em_atendimento', 'encerrado')`
- `consentimento = 1`

## `avaliacoes`

Avaliação de utilidade da conversa (CSAT 👍/👎).

| Coluna | Tipo | Nulo? | Padrão | Chave / referência |
|--------|------|:-----:|--------|--------------------|
| `id` | INTEGER | não |  | PK |
| `conversa_ref` | TEXT | não |  |  |
| `util` | INTEGER | não |  |  |
| `criado_em` | TEXT | não | `strftime('%Y-%m-%dT%H:%M:%SZ', 'now')` |  |

**Regras (CHECK):**

- `length(conversa_ref) BETWEEN 1 AND 64`
- `util IN (0, 1)`
