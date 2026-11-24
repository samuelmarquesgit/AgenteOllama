"""Conexão com o SQLite.

- `PRAGMA foreign_keys = ON` em toda conexão (o SQLite vem com FKs desligadas por padrão).
- `PRAGMA busy_timeout`: com várias conexões, uma escrita espera a outra terminar em vez de falhar.
- Função SQL `norm(texto)` registrada: minúsculas e sem acento, para buscas parametrizadas
  que ignoram acentuação (o equivalente ao `unaccent` do PostgreSQL).
- `ConexoesPorThread`: cada thread do servidor usa a sua própria conexão (RT-007). Compartilhar um
  `sqlite3.Connection` entre threads causava erros como "bad parameter or other API misuse".
"""

import os
import sqlite3
import threading
from pathlib import Path

from app.busca import normalizar

RAIZ = Path(__file__).resolve().parents[2]
CAMINHO_PADRAO = RAIZ / "data" / "loja.db"
ESPERA_ESCRITA_MS = 5000


def caminho_banco() -> Path:
    return Path(os.getenv("BANCO_SQLITE", CAMINHO_PADRAO))


def abrir(caminho: Path | str | None = None) -> sqlite3.Connection:
    caminho = Path(caminho) if caminho else caminho_banco()
    caminho.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(caminho, check_same_thread=False, timeout=ESPERA_ESCRITA_MS / 1000)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    con.execute(f"PRAGMA busy_timeout = {ESPERA_ESCRITA_MS}")
    con.create_function("norm", 1, lambda t: normalizar(t) if t is not None else None, deterministic=True)
    return con


class ConexoesPorThread:
    """Entrega uma conexão SQLite exclusiva para cada thread (todas apontam para o mesmo arquivo)."""

    def __init__(self, caminho: Path | str | None = None):
        self.caminho = Path(caminho) if caminho else caminho_banco()
        self._local = threading.local()
        self._abertas: list[sqlite3.Connection] = []
        self._trava = threading.Lock()

    def atual(self) -> sqlite3.Connection:
        con = getattr(self._local, "con", None)
        if con is None:
            con = abrir(self.caminho)
            self._local.con = con
            with self._trava:
                self._abertas.append(con)
        return con

    def fechar_todas(self) -> None:
        with self._trava:
            for con in self._abertas:
                con.close()
            self._abertas.clear()
        self._local = threading.local()
