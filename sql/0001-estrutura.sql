CREATE TABLE categorias (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nome VARCHAR(150) NOT NULL,
    categoria_pai_id BIGINT,
    CONSTRAINT fk_categoria_pai
        FOREIGN KEY (categoria_pai_id)
        REFERENCES categorias(id)
);

CREATE TABLE marcas (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nome VARCHAR(150) NOT NULL UNIQUE
);

CREATE TABLE produtos (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    categoria_id BIGINT NOT NULL,
    marca_id BIGINT NOT NULL,
    sku VARCHAR(50) NOT NULL UNIQUE,
    nome VARCHAR(250) NOT NULL,
    descricao TEXT,
    preco NUMERIC(12,2) NOT NULL,
    ativo BOOLEAN NOT NULL DEFAULT TRUE,

    CONSTRAINT fk_produto_categoria
        FOREIGN KEY (categoria_id)
        REFERENCES categorias(id),

    CONSTRAINT fk_produto_marca
        FOREIGN KEY (marca_id)
        REFERENCES marcas(id),

    CONSTRAINT ck_produto_preco
        CHECK (preco >= 0)
);

CREATE TABLE especificacoes (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nome VARCHAR(150) NOT NULL,
    unidade VARCHAR(30)
);

CREATE TABLE produto_especificacoes (
    produto_id BIGINT NOT NULL,
    especificacao_id BIGINT NOT NULL,
    valor VARCHAR(150) NOT NULL,

    PRIMARY KEY (produto_id, especificacao_id),

    FOREIGN KEY (produto_id)
        REFERENCES produtos(id),

    FOREIGN KEY (especificacao_id)
        REFERENCES especificacoes(id)
);

CREATE TABLE faq_categorias (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nome VARCHAR(150) NOT NULL UNIQUE
);

CREATE TABLE faq_perguntas (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    categoria_id BIGINT NOT NULL,
    pergunta TEXT NOT NULL,
    resposta TEXT NOT NULL,
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    criado_em TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    FOREIGN KEY (categoria_id)
        REFERENCES faq_categorias(id)
);

CREATE TABLE faq_variacoes (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    pergunta_id BIGINT NOT NULL,
    variacao TEXT NOT NULL,

    FOREIGN KEY (pergunta_id)
        REFERENCES faq_perguntas(id)
        ON DELETE CASCADE
);