-- 0004 · Atendimento humano e avaliação (CSAT). Sem dados pessoais: a conversa é identificada
-- só pelo conversationId gerado no navegador (G23: consentimento obrigatório para registrar).

CREATE TABLE atendimentos_humanos (
    id             INTEGER PRIMARY KEY,
    conversa_ref   TEXT    NOT NULL CHECK (length(conversa_ref) BETWEEN 1 AND 64),
    resumo         TEXT    NOT NULL CHECK (length(trim(resumo)) > 0),
    motivo         TEXT    NOT NULL DEFAULT 'pedido_cliente'
                           CHECK (motivo IN ('pedido_cliente', 'fallback', 'frustracao', 'troca', 'risco', 'pj')),
    prioridade     TEXT    NOT NULL DEFAULT 'normal' CHECK (prioridade IN ('normal', 'alta')),
    status         TEXT    NOT NULL DEFAULT 'aberto' CHECK (status IN ('aberto', 'em_atendimento', 'encerrado')),
    consentimento  INTEGER NOT NULL CHECK (consentimento = 1),
    criado_em      TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);
CREATE INDEX ix_atendimentos_status ON atendimentos_humanos (status, prioridade);

CREATE TABLE avaliacoes (
    id            INTEGER PRIMARY KEY,
    conversa_ref  TEXT    NOT NULL CHECK (length(conversa_ref) BETWEEN 1 AND 64),
    util          INTEGER NOT NULL CHECK (util IN (0, 1)),
    criado_em     TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);
