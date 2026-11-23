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


def main() -> None:
    import sys
    sys.path.insert(0, str(RAIZ))
    from app.db.conexao import abrir
    from app.db.migracoes import migrar

    with tempfile.TemporaryDirectory() as tmp:
        con = abrir(Path(tmp) / "dic.db")
        migrar(con)
        linhas = [
            "# Dicionário de dados",
            "",
            "> **Gerado automaticamente** por `database/gerar_dicionario.py` a partir das migrações. Não edite à mão.",
            "> Convenções: `snake_case`; PK `INTEGER` (rowid); datas ISO-8601 em `TEXT` (UTC); booleanos `0/1`; dinheiro em centavos (`INTEGER`).",
            "",
        ]
        tabelas = [r[0] for r in con.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name <> 'schema_migrations' ORDER BY rowid")]
        for t in tabelas:
            sql = con.execute("SELECT sql FROM sqlite_master WHERE name = ?", (t,)).fetchone()[0]
            fks = {r["from"]: f"FK → `{r['table']}.{r['to']}` ({r['on_delete']})" for r in con.execute(f"PRAGMA foreign_key_list({t})")}
            uniques = []
            for idx in con.execute(f"PRAGMA index_list({t})"):
                if idx["unique"] and idx["origin"] in ("u", "pk"):
                    cols = [c["name"] for c in con.execute(f"PRAGMA index_info({idx['name']})")]
                    uniques.append(cols)
            linhas += [f"## `{t}`", "", DESCRICOES.get(t, ""), "",
                       "| Coluna | Tipo | Nulo? | Padrão | Chave / referência |",
                       "|--------|------|:-----:|--------|--------------------|"]
            for c in con.execute(f"PRAGMA table_info({t})"):
                chave = []
                if c["pk"]:
                    chave.append("PK")
                if [c["name"]] in uniques:
                    chave.append("UNIQUE")
                if c["name"] in fks:
                    chave.append(fks[c["name"]])
                padrao = (c["dflt_value"] or "").replace("|", "\\|")
                linhas.append(f"| `{c['name']}` | {c['type']} | {'não' if c['notnull'] or c['pk'] else 'sim'} | "
                              f"{('`' + padrao + '`') if padrao else ''} | {' · '.join(chave)} |")
            compostas = [u for u in uniques if len(u) > 1]
            regras = re.findall(r"CHECK \((.+?)\)(?:,|\s*\n|\s*$)", sql)
            if compostas:
                linhas += ["", "**Unicidade composta:** " + "; ".join("(" + ", ".join(u) + ")" for u in compostas)]
            if regras:
                linhas += ["", "**Regras (CHECK):**", ""] + [f"- `{r.strip()}`" for r in regras]
            linhas.append("")
        SAIDA.parent.mkdir(parents=True, exist_ok=True)
        SAIDA.write_text("\n".join(linhas), encoding="utf-8")
        con.close()
    print(f"{len(tabelas)} tabelas -> {SAIDA}")


if __name__ == "__main__":
    main()
