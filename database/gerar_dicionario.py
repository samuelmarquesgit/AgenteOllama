"""Gera docs/db/DATA_DICTIONARY.md a partir do esquema real (migrações aplicadas num banco temporário).

Uso:  .venv\\Scripts\\python database\\gerar_dicionario.py
"""

import re
import sqlite3
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SAIDA = RAIZ / "docs" / "db" / "DATA_DICTIONARY.md"

DESCRICOES = {
    "faq_categorias": "Agrupamento temático das perguntas da FAQ.",
    "faq_perguntas": "Pergunta e resposta revisáveis da base de conhecimento (código estável FAQ-NNN).",
    "faq_variacoes": "Outras formas de fazer a mesma pergunta (melhoram a busca).",
    "faq_palavras_chave": "Termos que identificam o assunto da pergunta (usados na pontuação da busca).",
    "faq_sugestoes": "Respostas geradas pela IA aguardando revisão humana (D010). Palavras de busca derivam da pergunta.",
    "unidades": "Lojas físicas (dados fictícios).",
    "unidade_horarios": "Horário de funcionamento por dia da semana (0 = domingo). Dia sem linha = fechado.",
    "formas_pagamento": "Formas de pagamento aceitas.",
    "politicas": "Textos oficiais (pagamento, troca, garantia, frete, retirada, atendimento).",
    "categorias": "Hierarquia de categorias do catálogo (2 níveis).",
    "marcas": "Marcas do catálogo; todas fictícias na demonstração.",
    "produtos": "Produtos fictícios (SKU FAKE-NNNN). `alimentacao` sustenta o guardrail de voltagem (G20).",
    "especificacoes": "Tipos de especificação técnica e seu tipo de valor.",
    "produto_especificacoes": "Valor de cada especificação por produto (PK composta).",
    "produto_imagens": "Imagens (placeholders locais, sem dependência externa).",
    "produto_precos": "Histórico de preços com vigência; sobreposição bloqueada por trigger.",
    "estoques": "Quantidade por produto e unidade; o total é calculado, não armazenado.",
    "atendimentos_humanos": "Pedidos de atendimento humano (sem dados pessoais; exige consentimento).",
    "avaliacoes": "Avaliação de utilidade da conversa (CSAT 👍/👎).",
}


CABECALHO = [
    "# Dicionário de dados",
    "",
    "> **Gerado automaticamente** por `database/gerar_dicionario.py` a partir das migrações. Não edite à mão.",
    "> Convenções: `snake_case`; PK `INTEGER` (rowid); datas ISO-8601 em `TEXT` (UTC); booleanos `0/1`; dinheiro em centavos (`INTEGER`).",
    "",
]
TABELA_COLUNAS = [
    "| Coluna | Tipo | Nulo? | Padrão | Chave / referência |",
    "|--------|------|:-----:|--------|--------------------|",
]
# CHECK (...) seguido de vírgula ou de fim de linha (re.M: $ casa antes de cada quebra de linha).
REGRA_CHECK = re.compile(r"CHECK \((.+?)\)\s*(?:,|$)", re.M)


def _chaves_estrangeiras(con, tabela: str) -> dict[str, str]:
    return {r["from"]: f"FK → `{r['table']}.{r['to']}` ({r['on_delete']})"
            for r in con.execute(f"PRAGMA foreign_key_list({tabela})")}


def _unicidades(con, tabela: str) -> list[list[str]]:
    return [[c["name"] for c in con.execute(f"PRAGMA index_info({idx['name']})")]
            for idx in con.execute(f"PRAGMA index_list({tabela})")
            if idx["unique"] and idx["origin"] in ("u", "pk")]


def _linha_coluna(c, fks: dict[str, str], unicidades: list[list[str]]) -> str:
    chave = (["PK"] if c["pk"] else []) + (["UNIQUE"] if [c["name"]] in unicidades else []) \
        + ([fks[c["name"]]] if c["name"] in fks else [])
    padrao = (c["dflt_value"] or "").replace("|", "\\|")
    nulo = "não" if c["notnull"] or c["pk"] else "sim"
    padrao_md = f"`{padrao}`" if padrao else ""
    return f"| `{c['name']}` | {c['type']} | {nulo} | {padrao_md} | {' · '.join(chave)} |"


def _secao_tabela(con, tabela: str) -> list[str]:
    sql = con.execute("SELECT sql FROM sqlite_master WHERE name = ?", (tabela,)).fetchone()[0]
    fks = _chaves_estrangeiras(con, tabela)
    unicidades = _unicidades(con, tabela)
    linhas = [f"## `{tabela}`", "", DESCRICOES.get(tabela, ""), "", *TABELA_COLUNAS]
    linhas += [_linha_coluna(c, fks, unicidades) for c in con.execute(f"PRAGMA table_info({tabela})")]
    compostas = [u for u in unicidades if len(u) > 1]
    if compostas:
        linhas += ["", "**Unicidade composta:** " + "; ".join("(" + ", ".join(u) + ")" for u in compostas)]
    regras = REGRA_CHECK.findall(sql)
    if regras:
        linhas += ["", "**Regras (CHECK):**", ""] + [f"- `{r.strip()}`" for r in regras]
    return linhas + [""]


def main() -> None:
    import sys
    sys.path.insert(0, str(RAIZ))
    from app.db.conexao import abrir
    from app.db.migracoes import migrar

    with tempfile.TemporaryDirectory() as tmp:
        con = abrir(Path(tmp) / "dic.db")
        migrar(con)
        tabelas = [r[0] for r in con.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name <> 'schema_migrations' ORDER BY rowid")]
        linhas = list(CABECALHO)
        for t in tabelas:
            linhas += _secao_tabela(con, t)
        con.close()
    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    SAIDA.write_text("\n".join(linhas), encoding="utf-8")
    print(f"{len(tabelas)} tabelas -> {SAIDA}")


if __name__ == "__main__":
    main()
