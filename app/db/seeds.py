"""Seeds idempotentes (DB §6): rodar várias vezes não duplica nada (UPSERT por chave natural).

Fontes versionadas:
    knowledge/faq.json                    base de conhecimento (FAQ)
    database/seeds/data/loja.json         unidades, horários, pagamento e políticas (fictícios)
    database/seeds/data/catalogo.json     catálogo fictício (gerado por database/seeds/gerar_catalogo.py)

Uso:  python -m app.db.seeds            (migra, popula e confere as contagens)
"""

import json
import sqlite3
import sys
from pathlib import Path

from app.db.conexao import RAIZ, abrir
from app.db.migracoes import migrar

ARQ_FAQ = RAIZ / "knowledge" / "faq.json"
ARQ_LOJA = RAIZ / "database" / "seeds" / "data" / "loja.json"
ARQ_CATALOGO = RAIZ / "database" / "seeds" / "data" / "catalogo.json"

NOMES_CATEGORIAS_FAQ = {
    "escolha_de_ferramentas": "Escolha de ferramentas",
    "brocas_discos_acessorios": "Brocas, discos e acessórios",
    "baterias_alimentacao": "Baterias e alimentação",
    "medicao_eletronica": "Medição e eletrônica",
    "soldagem_compressores_limpeza": "Soldagem, compressores e limpeza",
    "uso_manutencao_seguranca": "Uso, manutenção e segurança",
    "atendimento_comercial": "Atendimento comercial",
    "diagnostico_comparacao": "Diagnóstico e comparação",
}

# Contagens esperadas (o verificador falha se o banco divergir).
ESPERADO = {
    "faq_categorias": 8,
    "faq_perguntas": 60,
    "unidades": 2,
    "unidade_horarios": 12,
    "formas_pagamento": 4,
    "politicas": 6,
    "categorias": 25,
    "marcas": 15,
    "produtos": 300,
    "especificacoes": 45,
    "produto_especificacoes": 1500,
    "produto_precos": 600,
    "produto_imagens": 300,
    "estoques": 600,
}


def _ler(arq: Path):
    return json.loads(arq.read_text(encoding="utf-8"))


def _id(con, tabela: str, coluna: str, valor) -> int:
    return con.execute(f"SELECT id FROM {tabela} WHERE {coluna} = ?", (valor,)).fetchone()[0]


def seed_faq(con: sqlite3.Connection, arq: Path = ARQ_FAQ) -> int:
    itens = _ler(arq)
    for codigo in sorted({f["categoria"] for f in itens}):
        con.execute(
            """INSERT INTO faq_categorias (codigo, nome) VALUES (?, ?)
               ON CONFLICT (codigo) DO UPDATE SET nome = excluded.nome""",
            (codigo, NOMES_CATEGORIAS_FAQ.get(codigo, codigo.replace("_", " ").capitalize())),
        )
    for f in itens:
        cat = _id(con, "faq_categorias", "codigo", f["categoria"])
        con.execute(
            """INSERT INTO faq_perguntas (codigo, categoria_id, pergunta, resposta, fonte, nivel_risco, status, revisado_em)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT (codigo) DO UPDATE SET
                   categoria_id = excluded.categoria_id, pergunta = excluded.pergunta,
                   resposta = excluded.resposta, fonte = excluded.fonte,
                   nivel_risco = excluded.nivel_risco, status = excluded.status,
                   revisado_em = excluded.revisado_em""",
            (f["id"], cat, f["pergunta"], f["resposta"], f.get("fonte"),
             f.get("nivel_risco", "baixo"), f.get("status", "rascunho"), f.get("revisado_em")),
        )
        pid = _id(con, "faq_perguntas", "codigo", f["id"])
        # Variações e palavras-chave espelham o arquivo (remove as que saíram, insere as novas).
        con.execute("DELETE FROM faq_variacoes WHERE pergunta_id = ?", (pid,))
        con.executemany("INSERT OR IGNORE INTO faq_variacoes (pergunta_id, variacao) VALUES (?, ?)",
                        [(pid, v) for v in f.get("variacoes", [])])
        con.execute("DELETE FROM faq_palavras_chave WHERE pergunta_id = ?", (pid,))
        con.executemany("INSERT OR IGNORE INTO faq_palavras_chave (pergunta_id, termo) VALUES (?, ?)",
                        [(pid, t) for t in f.get("palavras_chave", [])])
    con.commit()
    return len(itens)


def seed_loja(con: sqlite3.Connection, arq: Path = ARQ_LOJA) -> int:
    d = _ler(arq)
    for u in d["unidades"]:
        con.execute(
            """INSERT INTO unidades (codigo, nome, logradouro, numero, bairro, cidade, uf, cep, telefone, link_mapa)
               VALUES (:codigo, :nome, :logradouro, :numero, :bairro, :cidade, :uf, :cep, :telefone, :link_mapa)
               ON CONFLICT (codigo) DO UPDATE SET
                   nome = excluded.nome, logradouro = excluded.logradouro, numero = excluded.numero,
                   bairro = excluded.bairro, cidade = excluded.cidade, uf = excluded.uf, cep = excluded.cep,
                   telefone = excluded.telefone, link_mapa = excluded.link_mapa""",
            {k: u[k] for k in ("codigo", "nome", "logradouro", "numero", "bairro", "cidade", "uf", "cep", "telefone", "link_mapa")},
        )
        uid = _id(con, "unidades", "codigo", u["codigo"])
        con.execute("DELETE FROM unidade_horarios WHERE unidade_id = ?", (uid,))
        con.executemany(
            "INSERT INTO unidade_horarios (unidade_id, dia_semana, abre, fecha) VALUES (?, ?, ?, ?)",
            [(uid, h["dia_semana"], h["abre"], h["fecha"]) for h in u["horarios"]],
        )
    for fp in d["formas_pagamento"]:
        con.execute("""INSERT INTO formas_pagamento (codigo, nome) VALUES (?, ?)
                       ON CONFLICT (codigo) DO UPDATE SET nome = excluded.nome""", (fp["codigo"], fp["nome"]))
    for p in d["politicas"]:
        con.execute("""INSERT INTO politicas (codigo, titulo, texto) VALUES (?, ?, ?)
                       ON CONFLICT (codigo) DO UPDATE SET titulo = excluded.titulo, texto = excluded.texto""",
                    (p["codigo"], p["titulo"], p["texto"]))
    con.commit()
    return len(d["unidades"])


def seed_catalogo(con: sqlite3.Connection, arq: Path = ARQ_CATALOGO) -> int:
    d = _ler(arq)
    for nome in d["marcas"]:
        con.execute("INSERT INTO marcas (nome, ficticia) VALUES (?, 1) ON CONFLICT (nome) DO NOTHING", (nome,))
    for c in d["categorias"]:  # pais vêm antes dos filhos no arquivo
        pai = _id(con, "categorias", "codigo", c["pai"]) if c["pai"] else None
        con.execute("""INSERT INTO categorias (codigo, nome, categoria_pai_id) VALUES (?, ?, ?)
                       ON CONFLICT (codigo) DO UPDATE SET nome = excluded.nome, categoria_pai_id = excluded.categoria_pai_id""",
                    (c["codigo"], c["nome"], pai))
    for e in d["especificacoes"]:
        con.execute("""INSERT INTO especificacoes (codigo, nome, unidade, tipo_valor) VALUES (?, ?, ?, ?)
                       ON CONFLICT (codigo) DO UPDATE SET nome = excluded.nome, unidade = excluded.unidade,
                       tipo_valor = excluded.tipo_valor""",
                    (e["codigo"], e["nome"], e["unidade"], e["tipo_valor"]))
    esp = {r["codigo"]: r["id"] for r in con.execute("SELECT id, codigo FROM especificacoes")}
    uni = {r["codigo"]: r["id"] for r in con.execute("SELECT id, codigo FROM unidades")}
    for p in d["produtos"]:
        con.execute(
            """INSERT INTO produtos (sku, nome, descricao, categoria_id, marca_id, alimentacao)
               VALUES (?, ?, ?, (SELECT id FROM categorias WHERE codigo = ?), (SELECT id FROM marcas WHERE nome = ?), ?)
               ON CONFLICT (sku) DO UPDATE SET nome = excluded.nome, descricao = excluded.descricao,
                   categoria_id = excluded.categoria_id, marca_id = excluded.marca_id, alimentacao = excluded.alimentacao""",
            (p["sku"], p["nome"], p["descricao"], p["categoria"], p["marca"], p["alimentacao"]),
        )
        pid = _id(con, "produtos", "sku", p["sku"])
        con.execute("DELETE FROM produto_especificacoes WHERE produto_id = ?", (pid,))
        con.executemany("INSERT INTO produto_especificacoes (produto_id, especificacao_id, valor) VALUES (?, ?, ?)",
                        [(pid, esp[c], v) for c, v in p["especificacoes"]])
        con.execute("DELETE FROM produto_precos WHERE produto_id = ?", (pid,))
        for pr in p["precos"]:
            con.execute("INSERT INTO produto_precos (produto_id, preco_centavos, inicio_vigencia, fim_vigencia) VALUES (?, ?, ?, ?)",
                        (pid, pr["preco_centavos"], pr["inicio"], pr["fim"]))
        con.execute("""INSERT INTO produto_imagens (produto_id, url, texto_alternativo, ordem)
                       VALUES (?, '/static/produtos/placeholder.svg', ?, 1)
                       ON CONFLICT (produto_id, ordem) DO UPDATE SET texto_alternativo = excluded.texto_alternativo""",
                    (pid, f"Imagem ilustrativa: {p['nome']}"))
        for cod, qtd in p["estoque"].items():
            con.execute("""INSERT INTO estoques (produto_id, unidade_id, quantidade) VALUES (?, ?, ?)
                           ON CONFLICT (produto_id, unidade_id) DO UPDATE SET quantidade = excluded.quantidade""",
                        (pid, uni[cod], qtd))
    con.commit()
    return len(d["produtos"])


def contagens(con: sqlite3.Connection) -> dict[str, int]:
    return {t: con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t in ESPERADO}


def verificar(con: sqlite3.Connection, esperado: dict[str, int] = ESPERADO) -> dict[str, tuple[int, int]]:
    """Devolve só as divergências {tabela: (esperado, real)}. Vazio = tudo certo."""
    reais = contagens(con)
    return {t: (esperado[t], reais[t]) for t in esperado if reais[t] != esperado[t]}


def popular_tudo(con: sqlite3.Connection) -> None:
    migrar(con)
    seed_faq(con)
    seed_loja(con)       # antes do catálogo: estoques referenciam unidades
    seed_catalogo(con)


def main() -> int:
    con = abrir()
    popular_tudo(con)
    divergencias = verificar(con)
    for t, n in contagens(con).items():
        print(f"{t:24} {n:6}  {'OK' if t not in divergencias else f'ESPERADO {ESPERADO[t]}'}")
    return 1 if divergencias else 0


if __name__ == "__main__":
    sys.exit(main())
