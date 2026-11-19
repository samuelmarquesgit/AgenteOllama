"""Banco SQLite com as perguntas e respostas.

Na primeira execução a tabela é criada e populada com knowledge/faq.json
(60 FAQs iniciais). Depois disso, respostas novas geradas pelo agente também
são gravadas aqui, com origem='agente' e status='pendente_validacao'.
"""

import json
import os
import sqlite3
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CAMINHO_SEED = RAIZ / "knowledge" / "faq.json"
CAMINHO_BANCO = Path(os.getenv("BANCO_SQLITE", RAIZ / "data" / "loja.db"))

ESQUEMA = """
CREATE TABLE IF NOT EXISTS faq (
    id             TEXT PRIMARY KEY,
    categoria      TEXT NOT NULL,
    pergunta       TEXT NOT NULL,
    variacoes      TEXT NOT NULL DEFAULT '[]',   -- lista JSON
    palavras_chave TEXT NOT NULL DEFAULT '[]',   -- lista JSON
    resposta       TEXT NOT NULL,
    fonte          TEXT,
    status         TEXT NOT NULL DEFAULT 'rascunho',
    origem         TEXT NOT NULL DEFAULT 'seed', -- seed | agente
    criado_em      TEXT NOT NULL
);
"""


def conectar(caminho: Path | str = CAMINHO_BANCO) -> sqlite3.Connection:
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(caminho, check_same_thread=False)
    con.row_factory = sqlite3.Row
    con.executescript(ESQUEMA)
    if con.execute("SELECT COUNT(*) FROM faq").fetchone()[0] == 0:
        popular(con)
    return con


def popular(con: sqlite3.Connection, caminho_seed: Path = CAMINHO_SEED) -> int:
    agora = datetime.now().isoformat(timespec="seconds")
    itens = json.loads(caminho_seed.read_text(encoding="utf-8"))
    con.executemany(
        """INSERT OR IGNORE INTO faq
           (id, categoria, pergunta, variacoes, palavras_chave, resposta, fonte, status, origem, criado_em)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'seed', ?)""",
        [
            (
                f["id"], f["categoria"], f["pergunta"],
                json.dumps(f["variacoes"], ensure_ascii=False),
                json.dumps(f["palavras_chave"], ensure_ascii=False),
                f["resposta"], f.get("fonte"), f.get("status", "rascunho"), agora,
            )
            for f in itens
        ],
    )
    con.commit()
    return len(itens)


def listar(con: sqlite3.Connection) -> list[dict]:
    linhas = con.execute("SELECT * FROM faq WHERE status != 'inativo' ORDER BY criado_em, id").fetchall()
    resultado = []
    for linha in linhas:
        d = dict(linha)
        d["variacoes"] = json.loads(d["variacoes"])
        d["palavras_chave"] = json.loads(d["palavras_chave"])
        resultado.append(d)
    return resultado


def proximo_id(con: sqlite3.Connection) -> str:
    ids = [r[0] for r in con.execute("SELECT id FROM faq WHERE id LIKE 'FAQ-%'")]
    maior = max((int(i.split("-")[1]) for i in ids), default=0)
    return f"FAQ-{maior + 1:03d}"


def inserir_aprendida(con: sqlite3.Connection, pergunta: str, resposta: str, palavras_chave: list[str]) -> str:
    """Grava uma resposta nova vinda do agente (fica pendente de validação humana)."""
    novo_id = proximo_id(con)
    con.execute(
        """INSERT INTO faq (id, categoria, pergunta, variacoes, palavras_chave, resposta,
                            fonte, status, origem, criado_em)
           VALUES (?, 'aprendida', ?, '[]', ?, ?, 'ollama', 'pendente_validacao', 'agente', ?)""",
        (
            novo_id, pergunta,
            json.dumps(palavras_chave, ensure_ascii=False),
            resposta, datetime.now().isoformat(timespec="seconds"),
        ),
    )
    con.commit()
    return novo_id
