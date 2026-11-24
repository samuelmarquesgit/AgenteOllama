-- 0005 · Controle de seeds: guarda o hash de cada arquivo de dados aplicado.
-- Quando knowledge/faq.json (ou loja.json / catalogo.json) muda, o seed correspondente roda de novo
-- automaticamente na próxima conexão (os seeds são idempotentes).

CREATE TABLE seeds_aplicados (
    arquivo      TEXT PRIMARY KEY,
    sha1         TEXT NOT NULL CHECK (length(sha1) = 40),
    aplicado_em  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);
