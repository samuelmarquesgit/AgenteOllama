-- 0001 · Base de conhecimento (FAQ) — 3FN (DB §2)
-- Convenções: snake_case, PK INTEGER (rowid), datas ISO-8601 em TEXT (UTC), booleanos 0/1.

CREATE TABLE faq_categorias (
    id             INTEGER PRIMARY KEY,
    codigo         TEXT    NOT NULL UNIQUE CHECK (codigo GLOB '[a-z_]*' AND length(codigo) > 0),
    nome           TEXT    NOT NULL UNIQUE CHECK (length(trim(nome)) > 0),
    descricao      TEXT,
    ativo          INTEGER NOT NULL DEFAULT 1 CHECK (ativo IN (0, 1)),
    criado_em      TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    atualizado_em  TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

CREATE TABLE faq_perguntas (
    id             INTEGER PRIMARY KEY,
    codigo         TEXT    NOT NULL UNIQUE CHECK (codigo GLOB 'FAQ-[0-9][0-9][0-9]*'),
    categoria_id   INTEGER NOT NULL REFERENCES faq_categorias (id) ON DELETE RESTRICT,
    pergunta       TEXT    NOT NULL CHECK (length(trim(pergunta)) > 0),
    resposta       TEXT    NOT NULL CHECK (length(trim(resposta)) > 0),
    fonte          TEXT,
    nivel_risco    TEXT    NOT NULL DEFAULT 'baixo' CHECK (nivel_risco IN ('baixo', 'medio', 'alto')),
    status         TEXT    NOT NULL DEFAULT 'rascunho'
                           CHECK (status IN ('rascunho', 'pendente_validacao', 'validado', 'inativo')),
    revisado_por   TEXT,
    revisado_em    TEXT,
    criado_em      TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    atualizado_em  TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);
CREATE INDEX ix_faq_perguntas_categoria_status ON faq_perguntas (categoria_id, status);

CREATE TABLE faq_variacoes (
    id           INTEGER PRIMARY KEY,
    pergunta_id  INTEGER NOT NULL REFERENCES faq_perguntas (id) ON DELETE CASCADE,
    variacao     TEXT    NOT NULL CHECK (length(trim(variacao)) > 0),
    criado_em    TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    UNIQUE (pergunta_id, variacao)
);
CREATE INDEX ix_faq_variacoes_pergunta ON faq_variacoes (pergunta_id);

-- Termos que identificam o assunto (usados pela busca). Extensão documentada ao DB §2.
CREATE TABLE faq_palavras_chave (
    id           INTEGER PRIMARY KEY,
    pergunta_id  INTEGER NOT NULL REFERENCES faq_perguntas (id) ON DELETE CASCADE,
    termo        TEXT    NOT NULL CHECK (length(trim(termo)) > 0),
    UNIQUE (pergunta_id, termo)
);
CREATE INDEX ix_faq_palavras_chave_pergunta ON faq_palavras_chave (pergunta_id);

-- Respostas geradas pela IA aguardando revisão humana (decisão D010).
-- As palavras de busca NÃO são guardadas: derivam da pergunta (3FN).
CREATE TABLE faq_sugestoes (
    id               INTEGER PRIMARY KEY,
    pergunta         TEXT    NOT NULL CHECK (length(trim(pergunta)) > 0),
    resposta         TEXT    NOT NULL CHECK (length(trim(resposta)) > 0),
    origem           TEXT    NOT NULL DEFAULT 'ollama' CHECK (origem IN ('ollama', 'time')),
    status           TEXT    NOT NULL DEFAULT 'pendente' CHECK (status IN ('pendente', 'aprovada', 'rejeitada')),
    faq_pergunta_id  INTEGER REFERENCES faq_perguntas (id) ON DELETE SET NULL,
    motivo_revisao   TEXT,
    revisado_por     TEXT,
    revisado_em      TEXT,
    criado_em        TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    CHECK (status <> 'aprovada' OR faq_pergunta_id IS NOT NULL)
);
CREATE INDEX ix_faq_sugestoes_status ON faq_sugestoes (status);

-- atualizado_em mantido pelo banco (escolha documentada em docs/db/README.md).
CREATE TRIGGER tg_faq_categorias_atualizado AFTER UPDATE ON faq_categorias
WHEN NEW.atualizado_em = OLD.atualizado_em
BEGIN
    UPDATE faq_categorias SET atualizado_em = strftime('%Y-%m-%dT%H:%M:%SZ', 'now') WHERE id = NEW.id;
END;

CREATE TRIGGER tg_faq_perguntas_atualizado AFTER UPDATE ON faq_perguntas
WHEN NEW.atualizado_em = OLD.atualizado_em
BEGIN
    UPDATE faq_perguntas SET atualizado_em = strftime('%Y-%m-%dT%H:%M:%SZ', 'now') WHERE id = NEW.id;
END;
