"""Testes de app/banco.py (SQLite)."""

import json

from app import banco


def test_conectar_cria_arquivo_tabela_e_popula(tmp_path):
    caminho = tmp_path / "sub" / "novo.db"
    con = banco.conectar(caminho)
    assert caminho.exists()
    assert con.execute("SELECT COUNT(*) FROM faq").fetchone()[0] == 60
    assert con.execute("SELECT COUNT(*) FROM faq WHERE origem='seed'").fetchone()[0] == 60
    con.close()


def test_conectar_de_novo_nao_duplica(tmp_path):
    caminho = tmp_path / "x.db"
    banco.conectar(caminho).close()
    con = banco.conectar(caminho)
    assert con.execute("SELECT COUNT(*) FROM faq").fetchone()[0] == 60
    con.close()


def test_popular_e_idempotente(con):
    banco.popular(con)
    assert con.execute("SELECT COUNT(*) FROM faq").fetchone()[0] == 60


def test_listar_converte_json(con):
    faqs = banco.listar(con)
    assert len(faqs) == 60
    primeira = faqs[0]
    assert isinstance(primeira["variacoes"], list)
    assert isinstance(primeira["palavras_chave"], list)
    assert primeira["id"] == "FAQ-001"


def test_listar_ignora_inativas(con):
    con.execute("UPDATE faq SET status='inativo' WHERE id='FAQ-001'")
    ids = [f["id"] for f in banco.listar(con)]
    assert "FAQ-001" not in ids
    assert len(ids) == 59


def test_proximo_id(con):
    assert banco.proximo_id(con) == "FAQ-061"


def test_inserir_aprendida(con):
    novo = banco.inserir_aprendida(con, "Pergunta nova?", "Resposta nova.", ["pergunta", "nova"])
    assert novo == "FAQ-061"
    linha = dict(con.execute("SELECT * FROM faq WHERE id=?", (novo,)).fetchone())
    assert linha["categoria"] == "aprendida"
    assert linha["origem"] == "agente"
    assert linha["status"] == "pendente_validacao"
    assert linha["fonte"] == "ollama"
    assert json.loads(linha["palavras_chave"]) == ["pergunta", "nova"]
    assert banco.proximo_id(con) == "FAQ-062"


def test_inserir_aprendida_persiste_apos_reabrir(tmp_path):
    caminho = tmp_path / "p.db"
    con = banco.conectar(caminho)
    banco.inserir_aprendida(con, "P?", "R.", [])
    con.close()
    con = banco.conectar(caminho)
    assert con.execute("SELECT COUNT(*) FROM faq").fetchone()[0] == 61
    con.close()


def test_proximo_id_banco_vazio(tmp_path):
    import sqlite3

    con = sqlite3.connect(tmp_path / "vazio.db")
    con.executescript(banco.ESQUEMA)
    assert banco.proximo_id(con) == "FAQ-001"
    con.close()
