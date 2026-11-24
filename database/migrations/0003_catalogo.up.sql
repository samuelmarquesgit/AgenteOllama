-- 0003 · Catálogo de produtos FICTÍCIO para demonstração (DB §3) + estoque fictício (DB §5).
-- Marcas e produtos são inventados; SKUs FAKE-0001...; preços em centavos (inteiro, sem erro de arredondamento).

CREATE TABLE categorias (
    id                INTEGER PRIMARY KEY,
    codigo            TEXT    NOT NULL UNIQUE CHECK (codigo GLOB '[a-z_]*' AND length(codigo) > 0),
    nome              TEXT    NOT NULL UNIQUE,
    categoria_pai_id  INTEGER REFERENCES categorias (id) ON DELETE RESTRICT,
    ativo             INTEGER NOT NULL DEFAULT 1 CHECK (ativo IN (0, 1)),
    CHECK (categoria_pai_id IS NULL OR categoria_pai_id <> id)
    -- Ciclos com mais de um nível são impedidos na aplicação (SQLite não aceita CTE em trigger).
);
CREATE INDEX ix_categorias_pai ON categorias (categoria_pai_id);

CREATE TABLE marcas (
    id        INTEGER PRIMARY KEY,
    nome      TEXT    NOT NULL UNIQUE CHECK (length(trim(nome)) > 0),
    ficticia  INTEGER NOT NULL DEFAULT 1 CHECK (ficticia IN (0, 1)),
    ativo     INTEGER NOT NULL DEFAULT 1 CHECK (ativo IN (0, 1))
);

CREATE TABLE produtos (
    id             INTEGER PRIMARY KEY,
    sku            TEXT    NOT NULL UNIQUE CHECK (sku GLOB 'FAKE-[0-9][0-9][0-9][0-9]'),
    nome           TEXT    NOT NULL CHECK (length(trim(nome)) > 0),
    descricao      TEXT,
    categoria_id   INTEGER NOT NULL REFERENCES categorias (id) ON DELETE RESTRICT,
    marca_id       INTEGER NOT NULL REFERENCES marcas (id) ON DELETE RESTRICT,
    alimentacao    TEXT    NOT NULL CHECK (alimentacao IN ('127V', '220V', 'bivolt', 'bateria', 'nao_eletrico')),
    ativo          INTEGER NOT NULL DEFAULT 1 CHECK (ativo IN (0, 1)),
    criado_em      TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    atualizado_em  TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);
CREATE INDEX ix_produtos_categoria ON produtos (categoria_id);
CREATE INDEX ix_produtos_marca ON produtos (marca_id);
CREATE INDEX ix_produtos_nome ON produtos (nome);

CREATE TABLE especificacoes (
    id          INTEGER PRIMARY KEY,
    codigo      TEXT    NOT NULL UNIQUE,
    nome        TEXT    NOT NULL UNIQUE,
    unidade     TEXT,
    tipo_valor  TEXT    NOT NULL CHECK (tipo_valor IN ('texto', 'numero', 'booleano'))
);

-- Valor guardado como texto; a coerência com tipo_valor é validada na aplicação e nos testes.
CREATE TABLE produto_especificacoes (
    produto_id        INTEGER NOT NULL REFERENCES produtos (id) ON DELETE CASCADE,
    especificacao_id  INTEGER NOT NULL REFERENCES especificacoes (id) ON DELETE RESTRICT,
    valor             TEXT    NOT NULL CHECK (length(trim(valor)) > 0),
    PRIMARY KEY (produto_id, especificacao_id)
);
CREATE INDEX ix_produto_especificacoes_espec ON produto_especificacoes (especificacao_id);

CREATE TABLE produto_imagens (
    id                 INTEGER PRIMARY KEY,
    produto_id         INTEGER NOT NULL REFERENCES produtos (id) ON DELETE CASCADE,
    url                TEXT    NOT NULL,
    texto_alternativo  TEXT    NOT NULL CHECK (length(trim(texto_alternativo)) > 0),
    ordem              INTEGER NOT NULL DEFAULT 1 CHECK (ordem >= 1),
    UNIQUE (produto_id, ordem)
);

CREATE TABLE produto_precos (
    id               INTEGER PRIMARY KEY,
    produto_id       INTEGER NOT NULL REFERENCES produtos (id) ON DELETE CASCADE,
    preco_centavos   INTEGER NOT NULL CHECK (preco_centavos >= 0),
    inicio_vigencia  TEXT    NOT NULL CHECK (inicio_vigencia GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'),
    fim_vigencia     TEXT    CHECK (fim_vigencia IS NULL OR fim_vigencia GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'),
    CHECK (fim_vigencia IS NULL OR fim_vigencia > inicio_vigencia)
);
CREATE INDEX ix_produto_precos_produto ON produto_precos (produto_id, inicio_vigencia);

-- Vigências de preço não podem se sobrepor para o mesmo produto ([inicio, fim) ; fim NULL = em aberto).
CREATE TRIGGER tg_produto_precos_sem_sobreposicao_ins BEFORE INSERT ON produto_precos
BEGIN
    SELECT RAISE(ABORT, 'vigencia de preco sobreposta')
    WHERE EXISTS (
        SELECT 1 FROM produto_precos p
        WHERE p.produto_id = NEW.produto_id
          AND (p.fim_vigencia IS NULL OR p.fim_vigencia > NEW.inicio_vigencia)
          AND (NEW.fim_vigencia IS NULL OR NEW.fim_vigencia > p.inicio_vigencia)
    );
END;

CREATE TRIGGER tg_produto_precos_sem_sobreposicao_upd BEFORE UPDATE ON produto_precos
BEGIN
    SELECT RAISE(ABORT, 'vigencia de preco sobreposta')
    WHERE EXISTS (
        SELECT 1 FROM produto_precos p
        WHERE p.produto_id = NEW.produto_id
          AND p.id <> OLD.id
          AND (p.fim_vigencia IS NULL OR p.fim_vigencia > NEW.inicio_vigencia)
          AND (NEW.fim_vigencia IS NULL OR NEW.fim_vigencia > p.inicio_vigencia)
    );
END;

CREATE TRIGGER tg_produtos_atualizado AFTER UPDATE ON produtos
WHEN NEW.atualizado_em = OLD.atualizado_em
BEGIN
    UPDATE produtos SET atualizado_em = strftime('%Y-%m-%dT%H:%M:%SZ', 'now') WHERE id = NEW.id;
END;

-- Estoque fictício por unidade (DB §5). Total por produto é derivado (não é guardado).
CREATE TABLE estoques (
    produto_id     INTEGER NOT NULL REFERENCES produtos (id) ON DELETE CASCADE,
    unidade_id     INTEGER NOT NULL REFERENCES unidades (id) ON DELETE CASCADE,
    quantidade     INTEGER NOT NULL CHECK (quantidade >= 0),
    atualizado_em  TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    PRIMARY KEY (produto_id, unidade_id)
);
CREATE INDEX ix_estoques_unidade ON estoques (unidade_id);

-- Preço vigente hoje (consulta de leitura; não guarda dado).
CREATE VIEW vw_preco_atual AS
SELECT p.produto_id, p.preco_centavos, p.inicio_vigencia
FROM produto_precos p
WHERE p.inicio_vigencia <= date('now')
  AND (p.fim_vigencia IS NULL OR p.fim_vigencia > date('now'));
