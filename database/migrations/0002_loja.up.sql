-- 0002 · Dados configurados da loja (decisão D020): o LLM nunca "sabe" horário, endereço ou políticas.

CREATE TABLE unidades (
    id          INTEGER PRIMARY KEY,
    codigo      TEXT    NOT NULL UNIQUE CHECK (length(trim(codigo)) > 0),
    nome        TEXT    NOT NULL CHECK (length(trim(nome)) > 0),
    logradouro  TEXT    NOT NULL,
    numero      TEXT    NOT NULL,
    bairro      TEXT    NOT NULL,
    cidade      TEXT    NOT NULL,
    uf          TEXT    NOT NULL CHECK (length(uf) = 2 AND uf = upper(uf)),
    cep         TEXT    NOT NULL CHECK (cep GLOB '[0-9][0-9][0-9][0-9][0-9]-[0-9][0-9][0-9]'),
    telefone    TEXT,
    link_mapa   TEXT,
    ativo       INTEGER NOT NULL DEFAULT 1 CHECK (ativo IN (0, 1))
);

-- 0 = domingo ... 6 = sábado. Dia sem linha = fechado.
CREATE TABLE unidade_horarios (
    unidade_id  INTEGER NOT NULL REFERENCES unidades (id) ON DELETE CASCADE,
    dia_semana  INTEGER NOT NULL CHECK (dia_semana BETWEEN 0 AND 6),
    abre        TEXT    NOT NULL CHECK (abre  GLOB '[0-2][0-9]:[0-5][0-9]'),
    fecha       TEXT    NOT NULL CHECK (fecha GLOB '[0-2][0-9]:[0-5][0-9]'),
    PRIMARY KEY (unidade_id, dia_semana),
    CHECK (fecha > abre)
);

CREATE TABLE formas_pagamento (
    id      INTEGER PRIMARY KEY,
    codigo  TEXT    NOT NULL UNIQUE,
    nome    TEXT    NOT NULL UNIQUE,
    ativo   INTEGER NOT NULL DEFAULT 1 CHECK (ativo IN (0, 1))
);

-- Textos oficiais (pagamento, troca, frete, garantia, retirada, atendimento).
CREATE TABLE politicas (
    id             INTEGER PRIMARY KEY,
    codigo         TEXT    NOT NULL UNIQUE CHECK (length(trim(codigo)) > 0),
    titulo         TEXT    NOT NULL,
    texto          TEXT    NOT NULL CHECK (length(trim(texto)) > 0),
    atualizado_em  TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);
