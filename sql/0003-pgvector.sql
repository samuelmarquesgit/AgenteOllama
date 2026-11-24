CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE faq_embeddings (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    pergunta_id BIGINT NOT NULL,
    modelo VARCHAR(100) NOT NULL,
    embedding VECTOR(1536) NOT NULL,

    FOREIGN KEY (pergunta_id)
        REFERENCES faq_perguntas(id)
        ON DELETE CASCADE,

    UNIQUE (pergunta_id, modelo)
);