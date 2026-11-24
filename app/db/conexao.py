"""Conexão com o SQLite.

- `PRAGMA foreign_keys = ON` em toda conexão (o SQLite vem com FKs desligadas por padrão).
- Função SQL `norm(texto)` registrada: minúsculas e sem acento, para buscas parametrizadas
  que ignoram acentuação (o equivalente ao `unaccent` do PostgreSQL).
"""

import os
import sqlite3
from pathlib import Path

from app.busca import normalizar

RAIZ = Path(__file__).resolve().parents[2]
CAMINHO_PADRAO = RAIZ / "data" / "loja.db"


def caminho_banco() -> Path:
    return Path(os.getenv("BANCO_SQLITE", CAMINHO_PADRAO))


def abrir(caminho: Path | str | None = None) -> sqlite3.Connection:
    caminho = Path(caminho) if caminho else caminho_banco()
    caminho.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(caminho, check_same_thread=False)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    con.create_function("norm", 1, lambda t: normalizar(t) if t is not None else None, deterministic=True)
    return con
