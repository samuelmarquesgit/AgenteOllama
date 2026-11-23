# DER — Diagrama entidade-relacionamento

> 19 tabelas em 4 domínios, uma migração por domínio. Detalhes de cada coluna em [DATA_DICTIONARY.md](DATA_DICTIONARY.md).

## 1. Base de conhecimento (0001_faq)

```mermaid
erDiagram
    faq_categorias ||--o{ faq_perguntas : "agrupa (RESTRICT)"
    faq_perguntas ||--o{ faq_variacoes : "tem (CASCADE)"
    faq_perguntas ||--o{ faq_palavras_chave : "tem (CASCADE)"
    faq_perguntas |o--o{ faq_sugestoes : "originou (SET NULL)"

    faq_categorias { integer id PK
                     text codigo UK
                     text nome UK
                     integer ativo }
    faq_perguntas { integer id PK
                    text codigo UK "FAQ-NNN"
                    integer categoria_id FK
                    text pergunta
                    text resposta
                    text nivel_risco "baixo|medio|alto"
                    text status }
    faq_variacoes { integer id PK
                    integer pergunta_id FK
                    text variacao "UK com pergunta_id" }
    faq_palavras_chave { integer id PK
                         integer pergunta_id FK
                         text termo "UK com pergunta_id" }
    faq_sugestoes { integer id PK
                    text pergunta
                    text resposta
                    text status "pendente|aprovada|rejeitada"
                    integer faq_pergunta_id FK }
```

## 2. Loja (0002_loja)

```mermaid
erDiagram
    unidades ||--o{ unidade_horarios : "funciona (CASCADE)"
    unidades { integer id PK
               text codigo UK
               text nome
               text cidade
               text uf
               text cep }
    unidade_horarios { integer unidade_id PK
                       integer dia_semana PK "0 a 6"
                       text abre
                       text fecha }
    formas_pagamento { integer id PK
                       text codigo UK
                       text nome UK }
    politicas { integer id PK
                text codigo UK
                text titulo
                text texto }
```

## 3. Catálogo fictício (0003_catalogo)

```mermaid
erDiagram
    categorias |o--o{ categorias : "pai de (RESTRICT)"
    categorias ||--o{ produtos : "classifica (RESTRICT)"
    marcas ||--o{ produtos : "fabrica (RESTRICT)"
    produtos ||--o{ produto_especificacoes : "possui (CASCADE)"
    especificacoes ||--o{ produto_especificacoes : "define (RESTRICT)"
    produtos ||--o{ produto_imagens : "tem (CASCADE)"
    produtos ||--o{ produto_precos : "vigência (CASCADE)"
    produtos ||--o{ estoques : "estoque (CASCADE)"
    unidades ||--o{ estoques : "guarda (CASCADE)"

    categorias { integer id PK
                 text codigo UK
                 integer categoria_pai_id FK }
    marcas { integer id PK
             text nome UK
             integer ficticia }
    produtos { integer id PK
               text sku UK "FAKE-NNNN"
               text nome
               integer categoria_id FK
               integer marca_id FK
               text alimentacao "127V|220V|bivolt|bateria|nao_eletrico" }
    especificacoes { integer id PK
                     text codigo UK
                     text tipo_valor "texto|numero|booleano" }
    produto_especificacoes { integer produto_id PK
                             integer especificacao_id PK
                             text valor }
    produto_precos { integer id PK
                     integer produto_id FK
                     integer preco_centavos ">= 0"
                     text inicio_vigencia
                     text fim_vigencia "NULL = vigente" }
    estoques { integer produto_id PK
               integer unidade_id PK
               integer quantidade ">= 0" }
```

## 4. Atendimento (0004_atendimento)

```mermaid
erDiagram
    atendimentos_humanos { integer id PK
                           text conversa_ref
                           text resumo
                           text motivo
                           text prioridade
                           text status
                           integer consentimento "deve ser 1" }
    avaliacoes { integer id PK
                 text conversa_ref
                 integer util "0 ou 1" }
```

## Decisões de normalização

| Decisão | Forma normal / motivo |
|---------|-----------------------|
| Variações e palavras-chave em tabelas próprias (antes eram listas JSON numa coluna) | **1FN**: um valor por célula |
| Horários em `unidade_horarios` (uma linha por dia) | **1FN**; permite horários diferentes por dia |
| Especificações como entidade + tabela associativa com PK composta | **2FN**: o valor depende da chave inteira (produto, especificação) |
| Preço em `produto_precos` com vigência, não coluna em `produtos` | Histórico sem repetir dados do produto; **3FN** |
| Nome da marca e da categoria só nas suas tabelas | **3FN**: sem dependência transitiva em `produtos` |
| Estoque total e preço vigente **não** armazenados (calculados / view `vw_preco_atual`) | Dado derivado não é guardado (evita inconsistência) |
| Palavras de busca de `faq_sugestoes` derivadas da pergunta | Mesmo princípio: não armazenar o derivável |
| `alimentacao` como coluna de `produtos` | Atributo atômico, um valor por SKU (cada voltagem é um SKU diferente) |
| `atendimentos_humanos` sem nome, telefone ou CPF | Minimização de dados (LGPD); identificação só pelo `conversa_ref` |
| `conversa_ref` sem FK | Conversas ainda ficam em memória; a tabela `conversas` entra na fase de histórico (DB §4) |
