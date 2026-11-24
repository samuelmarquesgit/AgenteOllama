"""Fachada do banco usada pelo agente (mantém a interface da v0.2).

O banco é SQLite normalizado (3FN): veja database/migrations/ e docs/db/.
Na primeira conexão, aplica as migrações pendentes e popula os dados de demonstração
(FAQ, loja e catálogo fictício) se o banco estiver vazio.
"""

import sqlite3
from pathlib import Path

from app.db.conexao import abrir, caminho_banco
from app.db.migracoes import migrar
from app.db.repositorios import FaqRepository, SugestaoRepository
from app.db.seeds import popular_tudo

CAMINHO_BANCO = caminho_banco()


def conectar(caminho: Path | str | None = None) -> sqlite3.Connection:
    con = abrir(caminho)
    migrar(con)
    if con.execute("SELECT COUNT(*) FROM faq_perguntas").fetchone()[0] == 0:
        popular_tudo(con)
    importar_legado_v02(con)
    return con


def importar_legado_v02(con: sqlite3.Connection) -> int:
    """Bancos da v0.2 tinham uma tabela única `faq`. As respostas aprendidas pela IA viram
    sugestões pendentes e a tabela antiga é RENOMEADA (nada é apagado). Devolve quantas importou."""
    existe = con.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'faq'").fetchone()
    if not existe:
        return 0
    colunas = {r[1] for r in con.execute("PRAGMA table_info(faq)")}
    importadas = 0
    if {"pergunta", "resposta", "origem"} <= colunas:
        for pergunta, resposta in con.execute("SELECT pergunta, resposta FROM faq WHERE origem = 'agente'").fetchall():
            ja_existe = con.execute("SELECT 1 FROM faq_sugestoes WHERE pergunta = ?", (pergunta,)).fetchone()
            if not ja_existe:
                con.execute("INSERT INTO faq_sugestoes (pergunta, resposta, origem) VALUES (?, ?, 'ollama')", (pergunta, resposta))
                importadas += 1
    con.execute("ALTER TABLE faq RENAME TO legado_faq_v02")
    con.commit()
    return importadas


def listar(con: sqlite3.Connection) -> list[dict]:
    """FAQs ativas + sugestões pendentes, no formato do motor de busca."""
    return FaqRepository(con).listar_para_busca()


def inserir_aprendida(con: sqlite3.Connection, pergunta: str, resposta: str, palavras_chave=None) -> str:
    """Grava uma resposta nova da IA como sugestão pendente de revisão. Devolve o código (SUG-0001)."""
    return SugestaoRepository(con).inserir(pergunta, resposta)
