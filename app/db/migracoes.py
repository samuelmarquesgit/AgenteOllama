"""Migrações SQL versionadas (decisão: "SQL versionado", DB §0).

Arquivos em database/migrations/:  NNNN_nome.up.sql  e  NNNN_nome.down.sql
A tabela `schema_migrations` registra o que já foi aplicado; cada migração roda
numa transação (se falhar, nada fica pela metade).

Uso pela linha de comando:
    python -m app.db.migracoes            # aplica todas as pendentes
    python -m app.db.migracoes status     # lista aplicadas e pendentes
    python -m app.db.migracoes down 0002  # reverte até a versão 0002 (inclusive as posteriores)
"""

import re
import sqlite3
import sys
from dataclasses import dataclass
from pathlib import Path

from app.db.conexao import RAIZ, abrir

PASTA = RAIZ / "database" / "migrations"
PADRAO = re.compile(r"^(\d{4})_([a-z0-9_]+)\.(up|down)\.sql$")


@dataclass(frozen=True)
class Migracao:
    versao: str
    nome: str
    up: Path
    down: Path


def descobrir(pasta: Path = PASTA) -> list[Migracao]:
    arquivos: dict[tuple[str, str], dict[str, Path]] = {}
    for arq in pasta.glob("*.sql"):
        m = PADRAO.match(arq.name)
        if m:
            arquivos.setdefault((m.group(1), m.group(2)), {})[m.group(3)] = arq
    migracoes = []
    for (versao, nome), par in sorted(arquivos.items()):
        if set(par) != {"up", "down"}:
            raise RuntimeError(f"Migração {versao}_{nome} precisa de .up.sql e .down.sql")
        migracoes.append(Migracao(versao, nome, par["up"], par["down"]))
    versoes = [m.versao for m in migracoes]
    if len(versoes) != len(set(versoes)):
        raise RuntimeError("Versões de migração duplicadas")
    return migracoes


def _garantir_controle(con: sqlite3.Connection) -> None:
    con.execute(
        """CREATE TABLE IF NOT EXISTS schema_migrations (
               versao      TEXT PRIMARY KEY,
               nome        TEXT NOT NULL,
               aplicada_em TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
           )"""
    )
    con.commit()


def aplicadas(con: sqlite3.Connection) -> list[str]:
    _garantir_controle(con)
    return [r[0] for r in con.execute("SELECT versao FROM schema_migrations ORDER BY versao")]


def _executar(con: sqlite3.Connection, sql: str) -> None:
    # executescript faz COMMIT implícito antes de rodar; o BEGIN/COMMIT explícito torna o bloco atômico.
    con.executescript(f"BEGIN;\n{sql}\nCOMMIT;")


def migrar(con: sqlite3.Connection, ate: str | None = None, pasta: Path = PASTA) -> list[str]:
    """Aplica as migrações pendentes (até a versão `ate`, se informada). Devolve as aplicadas agora."""
    feitas = set(aplicadas(con))
    novas = []
    for m in descobrir(pasta):
        if m.versao in feitas or (ate and m.versao > ate):
            continue
        sql = m.up.read_text(encoding="utf-8")
        sql += f"\nINSERT INTO schema_migrations (versao, nome) VALUES ('{m.versao}', '{m.nome}');"
        try:
            _executar(con, sql)
        except sqlite3.Error:
            con.rollback()
            raise
        novas.append(m.versao)
    return novas


def reverter(con: sqlite3.Connection, ate_versao: str, pasta: Path = PASTA) -> list[str]:
    """Reverte, em ordem decrescente, todas as migrações com versão >= `ate_versao`."""
    feitas = set(aplicadas(con))
    revertidas = []
    for m in reversed(descobrir(pasta)):
        if m.versao in feitas and m.versao >= ate_versao:
            sql = m.down.read_text(encoding="utf-8")
            sql += f"\nDELETE FROM schema_migrations WHERE versao = '{m.versao}';"
            try:
                _executar(con, sql)
            except sqlite3.Error:
                con.rollback()
                raise
            revertidas.append(m.versao)
    return revertidas


def main(argv: list[str]) -> None:
    con = abrir()
    if not argv:
        print("Aplicadas agora:", migrar(con) or "nenhuma (banco em dia)")
    elif argv[0] == "status":
        feitas = set(aplicadas(con))
        for m in descobrir():
            print(f"{m.versao} {m.nome:15} {'aplicada' if m.versao in feitas else 'PENDENTE'}")
    elif argv[0] == "down" and len(argv) == 2:
        print("Revertidas:", reverter(con, argv[1]) or "nenhuma")
    else:
        print(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
