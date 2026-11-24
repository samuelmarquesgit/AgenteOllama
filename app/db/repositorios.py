"""Repositórios: todo acesso ao banco passa por aqui, sempre com SQL parametrizado (DB §7).

Nenhum valor vindo do cliente é concatenado em SQL: os filtros usam `?`.
"""

import sqlite3
from dataclasses import dataclass, field

from app.busca import normalizar, tokens

DIAS = ["domingo", "segunda", "terça", "quarta", "quinta", "sexta", "sábado"]


# =============================================================================
# FAQ
# =============================================================================
class FaqRepository:
    def __init__(self, con: sqlite3.Connection):
        self.con = con

    def listar_categorias(self) -> list[dict]:
        return [dict(r) for r in self.con.execute(
            "SELECT id, codigo, nome, descricao FROM faq_categorias WHERE ativo = 1 ORDER BY nome")]

    def obter_resposta_por_id(self, codigo: str) -> dict | None:
        r = self.con.execute(
            """SELECT p.codigo AS id, p.pergunta, p.resposta, c.codigo AS categoria
               FROM faq_perguntas p JOIN faq_categorias c ON c.id = p.categoria_id
               WHERE p.codigo = ? AND p.status <> 'inativo'""", (codigo,)).fetchone()
        return dict(r) if r else None

    def buscar_perguntas(self, termo: str, limite: int = 10) -> list[dict]:
        """Busca simples por termo em pergunta e variações (sem acento/maiúsculas), ordenada por relevância.

        O termo é normalizado (só letras e números), então curingas como % e _ não têm efeito.
        """
        if not normalizar(termo or ""):
            return []
        return [dict(r) for r in self.con.execute(
            """WITH t AS (SELECT '%' || norm(?) || '%' AS padrao)
               SELECT p.codigo AS id, p.pergunta, p.resposta, c.codigo AS categoria,
                      (CASE WHEN norm(p.pergunta) LIKE t.padrao THEN 2 ELSE 0 END)
                    + (CASE WHEN EXISTS (SELECT 1 FROM faq_variacoes v
                                         WHERE v.pergunta_id = p.id AND norm(v.variacao) LIKE t.padrao) THEN 1 ELSE 0 END) AS score
               FROM faq_perguntas p JOIN faq_categorias c ON c.id = p.categoria_id, t
               WHERE p.status <> 'inativo'
                 AND (norm(p.pergunta) LIKE t.padrao
                      OR EXISTS (SELECT 1 FROM faq_variacoes v WHERE v.pergunta_id = p.id AND norm(v.variacao) LIKE t.padrao))
               ORDER BY score DESC, p.codigo
               LIMIT ?""", (termo, limite))]

    def listar_para_busca(self) -> list[dict]:
        """FAQs ativas + sugestões pendentes, no formato usado pelo motor de busca (app/busca.py)."""
        perguntas = {r["pid"]: {**dict(r), "variacoes": [], "palavras_chave": []} for r in self.con.execute(
            """SELECT p.id AS pid, p.codigo AS id, c.codigo AS categoria, p.pergunta, p.resposta, p.status
               FROM faq_perguntas p JOIN faq_categorias c ON c.id = p.categoria_id
               WHERE p.status <> 'inativo' AND c.ativo = 1
               ORDER BY p.codigo""")}
        for r in self.con.execute("SELECT pergunta_id, variacao FROM faq_variacoes ORDER BY id"):
            if r[0] in perguntas:
                perguntas[r[0]]["variacoes"].append(r[1])
        for r in self.con.execute("SELECT pergunta_id, termo FROM faq_palavras_chave ORDER BY id"):
            if r[0] in perguntas:
                perguntas[r[0]]["palavras_chave"].append(r[1])
        itens = [{k: v for k, v in p.items() if k != "pid"} for p in perguntas.values()]
        itens += SugestaoRepository(self.con).listar_para_busca()
        return itens


INICIO_FAIXA_APROVADAS = 901  # FAQ-001..FAQ-900: knowledge/faq.json · FAQ-901+: aprovadas na revisão humana


class SugestaoRepository:
    """Respostas geradas pela IA aguardando revisão (D010)."""

    def __init__(self, con: sqlite3.Connection):
        self.con = con

    @staticmethod
    def codigo(id_: int) -> str:
        return f"SUG-{id_:04d}"

    def inserir(self, pergunta: str, resposta: str, origem: str = "ollama") -> str:
        cur = self.con.execute("INSERT INTO faq_sugestoes (pergunta, resposta, origem) VALUES (?, ?, ?)",
                               (pergunta, resposta, origem))
        self.con.commit()
        return self.codigo(cur.lastrowid)

    def listar_pendentes(self) -> list[dict]:
        return [{**dict(r), "codigo": self.codigo(r["id"])} for r in self.con.execute(
            "SELECT id, pergunta, resposta, criado_em FROM faq_sugestoes WHERE status = 'pendente' ORDER BY id")]

    @staticmethod
    def _id(codigo: str) -> int:
        prefixo, _, numero = codigo.upper().partition("-")
        if prefixo != "SUG" or not numero.isdigit():
            raise ValueError(f"Código de sugestão inválido: {codigo} (formato esperado: SUG-0001)")
        return int(numero)

    def _pendente(self, codigo: str) -> dict:
        linha = self.con.execute("SELECT * FROM faq_sugestoes WHERE id = ?", (self._id(codigo),)).fetchone()
        if linha is None:
            raise ValueError(f"Sugestão {codigo} não encontrada.")
        sugestao = dict(linha)
        if sugestao["status"] != "pendente":
            raise ValueError(f"Sugestão {codigo} já foi revisada (status: {sugestao['status']}).")
        return sugestao

    def rejeitar(self, codigo: str, motivo: str, revisor: str) -> None:
        """Descarta uma resposta gerada pela IA (ela deixa de ser usada pelo Tork)."""
        self._pendente(codigo)
        self.con.execute(
            """UPDATE faq_sugestoes SET status = 'rejeitada', motivo_revisao = ?, revisado_por = ?,
                   revisado_em = strftime('%Y-%m-%dT%H:%M:%SZ', 'now') WHERE id = ?""",
            (motivo, revisor, self._id(codigo)))
        self.con.commit()

    def aprovar(self, codigo: str, categoria: str, revisor: str, resposta: str | None = None,
                nivel_risco: str = "baixo") -> str:
        """Promove a sugestão a FAQ oficial (opcionalmente com a resposta corrigida). Devolve o código FAQ-NNN."""
        sug = self._pendente(codigo)
        linha_cat = self.con.execute("SELECT id FROM faq_categorias WHERE codigo = ?", (categoria,)).fetchone()
        if linha_cat is None:
            raise ValueError(f"Categoria de FAQ inexistente: {categoria}")
        categoria_id = int(linha_cat[0])
        # FAQs aprovadas na revisão usam uma faixa própria (FAQ-901+), separada da faixa do knowledge/faq.json:
        # assim o seed (upsert por código) nunca sobrescreve uma FAQ aprovada por um revisor (achado da RT-001).
        ultimo = self.con.execute(
            "SELECT MAX(CAST(substr(codigo, 5) AS INTEGER)) FROM faq_perguntas WHERE CAST(substr(codigo, 5) AS INTEGER) >= ?",
            (INICIO_FAIXA_APROVADAS,)).fetchone()[0]
        novo = f"FAQ-{(ultimo or INICIO_FAIXA_APROVADAS - 1) + 1:03d}"
        cur = self.con.execute(
            """INSERT INTO faq_perguntas (codigo, categoria_id, pergunta, resposta, fonte, nivel_risco, status,
                                          revisado_por, revisado_em)
               VALUES (?, ?, ?, ?, 'Sugestão da IA revisada por humano', ?, 'validado', ?,
                       strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))""",
            (novo, categoria_id, sug["pergunta"], resposta or sug["resposta"], nivel_risco, revisor))
        self.con.executemany("INSERT OR IGNORE INTO faq_palavras_chave (pergunta_id, termo) VALUES (?, ?)",
                             [(cur.lastrowid, t) for t in sorted(tokens(sug["pergunta"]))])
        self.con.execute(
            """UPDATE faq_sugestoes SET status = 'aprovada', faq_pergunta_id = ?, revisado_por = ?,
                   revisado_em = strftime('%Y-%m-%dT%H:%M:%SZ', 'now') WHERE id = ?""",
            (cur.lastrowid, revisor, sug["id"]))
        self.con.commit()
        return novo

    def listar_para_busca(self) -> list[dict]:
        return [
            {"id": self.codigo(r["id"]), "categoria": "aprendida", "pergunta": r["pergunta"],
             "resposta": r["resposta"], "status": "pendente_validacao", "variacoes": [],
             "palavras_chave": sorted(tokens(r["pergunta"]))}  # derivadas da pergunta, não armazenadas
            for r in self.con.execute("SELECT id, pergunta, resposta FROM faq_sugestoes WHERE status = 'pendente' ORDER BY id")
        ]


# =============================================================================
# Loja
# =============================================================================
class LojaRepository:
    def __init__(self, con: sqlite3.Connection):
        self.con = con

    def unidades(self) -> list[dict]:
        unidades = [dict(r) for r in self.con.execute(
            "SELECT id, codigo, nome, logradouro, numero, bairro, cidade, uf, cep, telefone, link_mapa "
            "FROM unidades WHERE ativo = 1 ORDER BY id")]
        for u in unidades:
            u["horarios"] = [dict(h) for h in self.con.execute(
                "SELECT dia_semana, abre, fecha FROM unidade_horarios WHERE unidade_id = ? ORDER BY dia_semana", (u["id"],))]
        return unidades

    def formas_pagamento(self) -> list[str]:
        return [r[0] for r in self.con.execute("SELECT nome FROM formas_pagamento WHERE ativo = 1 ORDER BY id")]

    def politica(self, codigo: str) -> dict | None:
        r = self.con.execute("SELECT codigo, titulo, texto FROM politicas WHERE codigo = ?", (codigo,)).fetchone()
        return dict(r) if r else None

    @staticmethod
    def horario_legivel(horarios: list[dict]) -> str:
        """[(1,08:00,18:00) ... (6,08:00,12:00)] -> 'segunda a sexta, das 08:00 às 18:00; sábado, das 08:00 às 12:00'."""
        grupos: list[tuple[list[int], str, str]] = []
        for h in horarios:
            if grupos and grupos[-1][1:] == (h["abre"], h["fecha"]) and grupos[-1][0][-1] == h["dia_semana"] - 1:
                grupos[-1][0].append(h["dia_semana"])
            else:
                grupos.append(([h["dia_semana"]], h["abre"], h["fecha"]))
        partes = []
        for dias, abre, fecha in grupos:
            nome = DIAS[dias[0]] if len(dias) == 1 else f"{DIAS[dias[0]]} a {DIAS[dias[-1]]}"
            partes.append(f"{nome}, das {abre} às {fecha}")
        return "; ".join(partes) if partes else "horário não informado"


# =============================================================================
# Catálogo (fictício)
# =============================================================================
@dataclass
class FiltroProdutos:
    categorias: list[str] = field(default_factory=list)   # códigos de categoria (folha ou pai)
    alimentacao: list[str] = field(default_factory=list)  # '127V', '220V', 'bivolt', 'bateria'
    marca: str | None = None
    preco_max_centavos: int | None = None
    so_em_estoque: bool = False
    limite: int = 3


class CatalogoRepository:
    def __init__(self, con: sqlite3.Connection):
        self.con = con

    def marcas(self) -> list[str]:
        return [r[0] for r in self.con.execute("SELECT nome FROM marcas WHERE ativo = 1 ORDER BY nome")]

    def buscar(self, f: FiltroProdutos) -> list[dict]:
        where = ["p.ativo = 1"]
        params: list = []
        if f.categorias:
            marcas_cat = ",".join("?" * len(f.categorias))
            where.append(f"(c.codigo IN ({marcas_cat}) OR cp.codigo IN ({marcas_cat}))")
            params += f.categorias + f.categorias
        if f.alimentacao:
            where.append(f"p.alimentacao IN ({','.join('?' * len(f.alimentacao))})")
            params += f.alimentacao
        if f.marca:
            where.append("norm(m.nome) = norm(?)")
            params.append(f.marca)
        if f.preco_max_centavos is not None:
            where.append("pa.preco_centavos <= ?")
            params.append(f.preco_max_centavos)
        having = "HAVING estoque_total > 0" if f.so_em_estoque else ""
        sql = f"""
            SELECT p.sku, p.nome, p.descricao, p.alimentacao, m.nome AS marca, c.nome AS categoria,
                   pa.preco_centavos, COALESCE(SUM(e.quantidade), 0) AS estoque_total,
                   (SELECT url FROM produto_imagens i WHERE i.produto_id = p.id ORDER BY ordem LIMIT 1) AS imagem
            FROM produtos p
            JOIN marcas m ON m.id = p.marca_id
            JOIN categorias c ON c.id = p.categoria_id
            LEFT JOIN categorias cp ON cp.id = c.categoria_pai_id
            JOIN vw_preco_atual pa ON pa.produto_id = p.id
            LEFT JOIN estoques e ON e.produto_id = p.id
            WHERE {' AND '.join(where)}
            GROUP BY p.id
            {having}
            ORDER BY (COALESCE(SUM(e.quantidade), 0) > 0) DESC, pa.preco_centavos ASC, p.sku
            LIMIT ?"""
        params.append(f.limite)
        produtos = [dict(r) for r in self.con.execute(sql, params)]
        for p in produtos:
            p["especificacoes"] = self.especificacoes(p["sku"], limite=3)
        return produtos

    def contar(self, f: FiltroProdutos) -> int:
        return len(self.buscar(FiltroProdutos(**{**f.__dict__, "limite": 10_000})))

    def especificacoes(self, sku: str, limite: int | None = None) -> list[dict]:
        sql = """SELECT e.nome, pe.valor, e.unidade, e.tipo_valor
                 FROM produto_especificacoes pe
                 JOIN especificacoes e ON e.id = pe.especificacao_id
                 JOIN produtos p ON p.id = pe.produto_id
                 WHERE p.sku = ? AND e.codigo <> 'garantia_meses'
                 ORDER BY e.id"""
        linhas = [dict(r) for r in self.con.execute(sql, (sku,))]
        return linhas[:limite] if limite else linhas

    def obter(self, sku: str) -> dict | None:
        r = self.con.execute(
            """SELECT p.sku, p.nome, p.descricao, p.alimentacao, m.nome AS marca, c.nome AS categoria,
                      pa.preco_centavos
               FROM produtos p JOIN marcas m ON m.id = p.marca_id JOIN categorias c ON c.id = p.categoria_id
               LEFT JOIN vw_preco_atual pa ON pa.produto_id = p.id
               WHERE p.sku = ?""", (sku,)).fetchone()
        if not r:
            return None
        produto = dict(r)
        produto["especificacoes"] = self.especificacoes(sku)
        produto["estoque"] = [dict(e) for e in self.con.execute(
            """SELECT u.nome AS unidade, e.quantidade FROM estoques e
               JOIN unidades u ON u.id = e.unidade_id JOIN produtos p ON p.id = e.produto_id
               WHERE p.sku = ? ORDER BY u.id""", (sku,))]
        return produto


# =============================================================================
# Atendimento
# =============================================================================
class AtendimentoRepository:
    def __init__(self, con: sqlite3.Connection):
        self.con = con

    def registrar(self, conversa_ref: str, resumo: str, motivo: str = "pedido_cliente",
                  prioridade: str = "normal", consentimento: bool = False) -> int:
        cur = self.con.execute(
            """INSERT INTO atendimentos_humanos (conversa_ref, resumo, motivo, prioridade, consentimento)
               VALUES (?, ?, ?, ?, ?)""", (conversa_ref, resumo, motivo, prioridade, 1 if consentimento else 0))
        self.con.commit()
        return cur.lastrowid

    def abertos(self) -> list[dict]:
        return [dict(r) for r in self.con.execute(
            "SELECT id, resumo, motivo, prioridade, criado_em FROM atendimentos_humanos "
            "WHERE status = 'aberto' ORDER BY prioridade = 'alta' DESC, id")]

    def avaliar(self, conversa_ref: str, util: bool) -> int:
        cur = self.con.execute("INSERT INTO avaliacoes (conversa_ref, util) VALUES (?, ?)",
                               (conversa_ref, 1 if util else 0))
        self.con.commit()
        return cur.lastrowid
