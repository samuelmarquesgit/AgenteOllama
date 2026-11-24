"""Testes do banco SQLite normalizado (DB §8): migrações, integridade, seeds e repositórios."""

import sqlite3

import pytest

from tests.conftest import N_FAQS

from app import banco
from app.db import migracoes, seeds
from app.db.conexao import abrir
from app.db.repositorios import (
    AtendimentoRepository,
    CatalogoRepository,
    FaqRepository,
    FiltroProdutos,
    LojaRepository,
    SugestaoRepository,
)

TABELAS = {
    "faq_categorias", "faq_perguntas", "faq_variacoes", "faq_palavras_chave", "faq_sugestoes",
    "unidades", "unidade_horarios", "formas_pagamento", "politicas",
    "categorias", "marcas", "produtos", "especificacoes", "produto_especificacoes",
    "produto_imagens", "produto_precos", "estoques", "atendimentos_humanos", "avaliacoes", "seeds_aplicados",
}


def tabelas(con):
    return {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type = 'table'")} - {"schema_migrations"}


# =============================================================================
# Migrações
# =============================================================================
def test_migracoes_criam_todas_as_tabelas_em_banco_vazio(tmp_path):
    con = abrir(tmp_path / "vazio.db")
    aplicadas = migracoes.migrar(con)
    assert aplicadas == ["0001", "0002", "0003", "0004", "0005"]
    assert tabelas(con) == TABELAS


def test_migrar_de_novo_nao_faz_nada(tmp_path):
    con = abrir(tmp_path / "x.db")
    migracoes.migrar(con)
    assert migracoes.migrar(con) == []


def test_rollback_e_reaplicacao(tmp_path):
    con = abrir(tmp_path / "rb.db")
    migracoes.migrar(con)
    assert migracoes.reverter(con, "0001") == ["0005", "0004", "0003", "0002", "0001"]
    assert tabelas(con) == set()
    assert migracoes.migrar(con) == ["0001", "0002", "0003", "0004", "0005"]
    assert tabelas(con) == TABELAS


def test_rollback_parcial(tmp_path):
    con = abrir(tmp_path / "rp.db")
    migracoes.migrar(con)
    migracoes.reverter(con, "0003")
    assert migracoes.aplicadas(con) == ["0001", "0002"]
    assert "produtos" not in tabelas(con) and "faq_perguntas" in tabelas(con)


def test_migrar_ate_uma_versao(tmp_path):
    con = abrir(tmp_path / "ate.db")
    assert migracoes.migrar(con, ate="0002") == ["0001", "0002"]


def test_toda_migracao_tem_up_e_down():
    for m in migracoes.descobrir():
        assert m.up.exists() and m.down.exists()


def test_migracao_com_erro_nao_fica_pela_metade(tmp_path):
    pasta = tmp_path / "mig"
    pasta.mkdir()
    (pasta / "0001_ok.up.sql").write_text("CREATE TABLE a (id INTEGER);", encoding="utf-8")
    (pasta / "0001_ok.down.sql").write_text("DROP TABLE a;", encoding="utf-8")
    (pasta / "0002_quebrada.up.sql").write_text("CREATE TABLE b (id INTEGER); SELEC erro;", encoding="utf-8")
    (pasta / "0002_quebrada.down.sql").write_text("DROP TABLE b;", encoding="utf-8")
    con = abrir(tmp_path / "erro.db")
    with pytest.raises(sqlite3.Error):
        migracoes.migrar(con, pasta=pasta)
    assert migracoes.aplicadas(con) == ["0001"]
    assert "b" not in {r[0] for r in con.execute("SELECT name FROM sqlite_master")}


def test_foreign_keys_ligadas(con):
    assert con.execute("PRAGMA foreign_keys").fetchone()[0] == 1


# =============================================================================
# Seeds e contagens
# =============================================================================
def test_contagens_conferem(con):
    assert seeds.verificar(con) == {}


def test_seed_e_idempotente(con):
    antes = seeds.contagens(con)
    seeds.seed_faq(con)
    seeds.seed_loja(con)
    seeds.seed_catalogo(con)
    assert seeds.contagens(con) == antes


def test_verificador_aponta_divergencia(con):
    con.execute("DELETE FROM estoques WHERE rowid IN (SELECT rowid FROM estoques LIMIT 1)")
    assert seeds.verificar(con) == {"estoques": (600, 599)}


def test_conectar_popula_banco_novo(tmp_path):
    c = banco.conectar(tmp_path / "novo.db")
    assert c.execute("SELECT COUNT(*) FROM produtos").fetchone()[0] == 300


def test_dados_de_demonstracao_sao_ficticios(con):
    assert con.execute("SELECT COUNT(*) FROM marcas WHERE ficticia = 0").fetchone()[0] == 0
    assert con.execute("SELECT COUNT(*) FROM produtos WHERE sku NOT LIKE 'FAKE-%'").fetchone()[0] == 0


# =============================================================================
# Integridade referencial (FKs)
# =============================================================================
def test_fk_pergunta_com_categoria_inexistente(con):
    with pytest.raises(sqlite3.IntegrityError):
        con.execute("INSERT INTO faq_perguntas (codigo, categoria_id, pergunta, resposta) VALUES ('FAQ-999', 9999, 'p', 'r')")


def test_fk_restrict_categoria_com_perguntas(con):
    with pytest.raises(sqlite3.IntegrityError):
        con.execute("DELETE FROM faq_categorias WHERE codigo = 'escolha_de_ferramentas'")


def test_fk_cascade_variacoes_e_palavras_chave(con):
    pid = con.execute("SELECT id FROM faq_perguntas WHERE codigo = 'FAQ-001'").fetchone()[0]
    con.execute("DELETE FROM faq_perguntas WHERE id = ?", (pid,))
    assert con.execute("SELECT COUNT(*) FROM faq_variacoes WHERE pergunta_id = ?", (pid,)).fetchone()[0] == 0
    assert con.execute("SELECT COUNT(*) FROM faq_palavras_chave WHERE pergunta_id = ?", (pid,)).fetchone()[0] == 0


def test_fk_restrict_marca_com_produtos(con):
    with pytest.raises(sqlite3.IntegrityError):
        con.execute("DELETE FROM marcas WHERE nome = 'Torqmax'")


def test_fk_cascade_produto_remove_precos_specs_estoque(con):
    pid = con.execute("SELECT id FROM produtos WHERE sku = 'FAKE-0001'").fetchone()[0]
    con.execute("DELETE FROM produtos WHERE id = ?", (pid,))
    for tabela in ("produto_precos", "produto_especificacoes", "estoques", "produto_imagens"):
        assert con.execute(f"SELECT COUNT(*) FROM {tabela} WHERE produto_id = ?", (pid,)).fetchone()[0] == 0


def test_fk_restrict_especificacao_em_uso(con):
    with pytest.raises(sqlite3.IntegrityError):
        con.execute("DELETE FROM especificacoes WHERE codigo = 'potencia_w'")


def test_fk_sugestao_aprovada_perde_vinculo_se_faq_sumir(con):
    pid = con.execute("SELECT id FROM faq_perguntas WHERE codigo = 'FAQ-002'").fetchone()[0]
    con.execute("INSERT INTO faq_sugestoes (pergunta, resposta, status, faq_pergunta_id) VALUES ('p', 'r', 'pendente', ?)", (pid,))
    con.execute("DELETE FROM faq_perguntas WHERE id = ?", (pid,))
    assert con.execute("SELECT faq_pergunta_id FROM faq_sugestoes").fetchone()[0] is None


def test_nenhum_registro_orfao(con):
    assert con.execute("PRAGMA foreign_key_check").fetchall() == []


# =============================================================================
# Unicidade
# =============================================================================
@pytest.mark.parametrize("sql", [
    "INSERT INTO faq_categorias (codigo, nome) VALUES ('outra', 'Escolha de ferramentas')",
    "INSERT INTO faq_categorias (codigo, nome) VALUES ('escolha_de_ferramentas', 'Outro nome')",
    "INSERT INTO marcas (nome) VALUES ('Torqmax')",
    "INSERT INTO produtos (sku, nome, categoria_id, marca_id, alimentacao) VALUES ('FAKE-0001', 'x', 1, 1, 'bateria')",
    "INSERT INTO faq_variacoes (pergunta_id, variacao) SELECT pergunta_id, variacao FROM faq_variacoes LIMIT 1",
    "INSERT INTO estoques (produto_id, unidade_id, quantidade) SELECT produto_id, unidade_id, 1 FROM estoques LIMIT 1",
])
def test_unicidade(con, sql):
    with pytest.raises(sqlite3.IntegrityError):
        con.execute(sql)


# =============================================================================
# CHECKs
# =============================================================================
@pytest.mark.parametrize("sql", [
    "INSERT INTO faq_perguntas (codigo, categoria_id, pergunta, resposta) VALUES ('FAQ-900', 1, '   ', 'r')",
    "INSERT INTO faq_perguntas (codigo, categoria_id, pergunta, resposta) VALUES ('FAQ-901', 1, 'p', '')",
    "INSERT INTO faq_perguntas (codigo, categoria_id, pergunta, resposta) VALUES ('X-1', 1, 'p', 'r')",
    "INSERT INTO faq_perguntas (codigo, categoria_id, pergunta, resposta, nivel_risco) VALUES ('FAQ-902', 1, 'p', 'r', 'enorme')",
    "INSERT INTO faq_perguntas (codigo, categoria_id, pergunta, resposta, status) VALUES ('FAQ-903', 1, 'p', 'r', 'publicado')",
    "INSERT INTO faq_sugestoes (pergunta, resposta, status) VALUES ('p', 'r', 'aprovada')",
    "INSERT INTO produto_precos (produto_id, preco_centavos, inicio_vigencia) VALUES (1, -1, '2030-01-01')",
    "INSERT INTO produto_precos (produto_id, preco_centavos, inicio_vigencia, fim_vigencia) VALUES (1, 100, '2030-01-02', '2030-01-01')",
    "INSERT INTO produto_precos (produto_id, preco_centavos, inicio_vigencia) VALUES (1, 100, '01/01/2030')",
    "UPDATE estoques SET quantidade = -1 WHERE rowid = 1",
    "INSERT INTO produtos (sku, nome, categoria_id, marca_id, alimentacao) VALUES ('ABC-1', 'x', 1, 1, 'bateria')",
    "INSERT INTO produtos (sku, nome, categoria_id, marca_id, alimentacao) VALUES ('FAKE-9999', 'x', 1, 1, '380V')",
    "INSERT INTO unidades (codigo, nome, logradouro, numero, bairro, cidade, uf, cep) VALUES ('X', 'x', 'r', '1', 'b', 'c', 'sc', '89200-000')",
    "INSERT INTO unidades (codigo, nome, logradouro, numero, bairro, cidade, uf, cep) VALUES ('Y', 'y', 'r', '1', 'b', 'c', 'SC', '89200000')",
    "INSERT INTO unidade_horarios (unidade_id, dia_semana, abre, fecha) VALUES (1, 0, '18:00', '08:00')",
    "INSERT INTO unidade_horarios (unidade_id, dia_semana, abre, fecha) VALUES (1, 7, '08:00', '18:00')",
    "INSERT INTO atendimentos_humanos (conversa_ref, resumo, consentimento) VALUES ('c', 'r', 0)",
    "INSERT INTO avaliacoes (conversa_ref, util) VALUES ('c', 5)",
    "UPDATE categorias SET categoria_pai_id = id WHERE codigo = 'furadeiras'",
])
def test_checks_rejeitam_dados_invalidos(con, sql):
    with pytest.raises(sqlite3.IntegrityError):
        con.execute(sql)


# =============================================================================
# Triggers
# =============================================================================
def test_vigencia_de_preco_sobreposta_e_bloqueada(con):
    pid = con.execute("SELECT id FROM produtos WHERE sku = 'FAKE-0001'").fetchone()[0]
    with pytest.raises(sqlite3.IntegrityError, match="sobreposta"):
        con.execute("INSERT INTO produto_precos (produto_id, preco_centavos, inicio_vigencia) VALUES (?, 1000, '2026-12-01')", (pid,))


def test_vigencia_sobreposta_no_update_e_bloqueada(con):
    pid = con.execute("SELECT id FROM produtos WHERE sku = 'FAKE-0001'").fetchone()[0]
    antigo = con.execute("SELECT id FROM produto_precos WHERE produto_id = ? AND fim_vigencia IS NOT NULL", (pid,)).fetchone()[0]
    with pytest.raises(sqlite3.IntegrityError, match="sobreposta"):
        con.execute("UPDATE produto_precos SET fim_vigencia = '2026-12-01' WHERE id = ?", (antigo,))


def test_nova_vigencia_apos_fechar_a_atual(con):
    pid = con.execute("SELECT id FROM produtos WHERE sku = 'FAKE-0002'").fetchone()[0]
    con.execute("UPDATE produto_precos SET fim_vigencia = '2027-01-01' WHERE produto_id = ? AND fim_vigencia IS NULL", (pid,))
    con.execute("INSERT INTO produto_precos (produto_id, preco_centavos, inicio_vigencia) VALUES (?, 12345, '2027-01-01')", (pid,))
    assert con.execute("SELECT COUNT(*) FROM produto_precos WHERE produto_id = ?", (pid,)).fetchone()[0] == 3


def test_atualizado_em_muda_no_update(con):
    con.execute("UPDATE faq_perguntas SET atualizado_em = '2000-01-01T00:00:00Z' WHERE codigo = 'FAQ-001'")
    con.execute("UPDATE faq_perguntas SET resposta = resposta || ' ' WHERE codigo = 'FAQ-001'")
    assert con.execute("SELECT atualizado_em FROM faq_perguntas WHERE codigo = 'FAQ-001'").fetchone()[0] > "2000"


# =============================================================================
# Qualidade dos dados
# =============================================================================
def test_nenhuma_faq_ativa_vazia(con):
    assert con.execute(
        "SELECT COUNT(*) FROM faq_perguntas WHERE status <> 'inativo' AND (trim(pergunta) = '' OR trim(resposta) = '')"
    ).fetchone()[0] == 0


def test_todo_produto_tem_exatamente_um_preco_vigente(con):
    assert con.execute(
        "SELECT COUNT(*) FROM produtos p WHERE (SELECT COUNT(*) FROM vw_preco_atual v WHERE v.produto_id = p.id) <> 1"
    ).fetchone()[0] == 0


def test_precos_positivos(con):
    assert con.execute("SELECT MIN(preco_centavos) FROM produto_precos").fetchone()[0] > 0


def test_especificacoes_coerentes_com_o_tipo(con):
    for valor, tipo in con.execute(
        "SELECT pe.valor, e.tipo_valor FROM produto_especificacoes pe JOIN especificacoes e ON e.id = pe.especificacao_id"
    ):
        if tipo == "numero":
            float(valor)
        elif tipo == "booleano":
            assert valor in ("sim", "não")


def test_cada_produto_tem_cinco_especificacoes(con):
    assert {r[0] for r in con.execute(
        "SELECT COUNT(*) FROM produto_especificacoes GROUP BY produto_id")} == {5}


def test_hierarquia_de_categorias_tem_dois_niveis(con):
    assert con.execute("SELECT COUNT(*) FROM categorias WHERE categoria_pai_id IS NULL").fetchone()[0] == 6
    assert con.execute(
        "SELECT COUNT(*) FROM categorias f JOIN categorias p ON p.id = f.categoria_pai_id WHERE p.categoria_pai_id IS NOT NULL"
    ).fetchone()[0] == 0


# =============================================================================
# Repositórios
# =============================================================================
def test_busca_faq_ignora_acentos_e_maiusculas(con):
    ids = [r["id"] for r in FaqRepository(con).buscar_perguntas("MULTÍMETRO")]
    assert "FAQ-028" in ids


@pytest.mark.parametrize("termo", ["x' OR '1'='1", "'; DROP TABLE faq_perguntas; --", "%", "_", "", "   "])
def test_busca_faq_resiste_a_sql_injection_e_curingas(con, termo):
    assert FaqRepository(con).buscar_perguntas(termo) == []
    assert con.execute("SELECT COUNT(*) FROM faq_perguntas").fetchone()[0] == N_FAQS


def test_busca_faq_termo_inexistente(con):
    assert FaqRepository(con).buscar_perguntas("bolo de chocolate") == []


def test_listar_categorias_e_obter_resposta(con):
    repo = FaqRepository(con)
    assert len(repo.listar_categorias()) == 8
    assert repo.obter_resposta_por_id("FAQ-013")["categoria"] == "brocas_discos_acessorios"
    assert repo.obter_resposta_por_id("FAQ-999") is None


def test_faq_inativa_some_da_busca(con):
    con.execute("UPDATE faq_perguntas SET status = 'inativo' WHERE codigo = 'FAQ-001'")
    assert "FAQ-001" not in [f["id"] for f in banco.listar(con)]


def test_sugestao_entra_na_busca_e_tem_codigo_proprio(con):
    codigo = banco.inserir_aprendida(con, "Como funciona uma tupia?", "Resposta.")
    assert codigo == "SUG-0001"
    item = [f for f in banco.listar(con) if f["id"] == "SUG-0001"][0]
    assert item["categoria"] == "aprendida" and "tupia" in item["palavras_chave"]
    assert SugestaoRepository(con).listar_pendentes()[0]["pergunta"] == "Como funciona uma tupia?"


def test_catalogo_categoria_pai_inclui_filhas(con):
    produtos = CatalogoRepository(con).buscar(FiltroProdutos(categorias=["acessorios"], limite=500))
    assert {p["categoria"] for p in produtos} == {"Brocas", "Discos de corte e desbaste", "Bits e pontas", "Lâminas de serra"}


def test_catalogo_filtros(con):
    repo = CatalogoRepository(con)
    r = repo.buscar(FiltroProdutos(categorias=["parafusadeiras"], alimentacao=["bateria"], preco_max_centavos=50000, limite=50))
    assert r and all(p["preco_centavos"] <= 50000 and p["alimentacao"] == "bateria" for p in r)
    assert all(p["marca"] == "Torqmax" for p in repo.buscar(FiltroProdutos(marca="TORQMAX", limite=50)))


def test_catalogo_ordena_em_estoque_primeiro_e_mais_barato(con):
    r = CatalogoRepository(con).buscar(FiltroProdutos(categorias=["furadeiras"], limite=50))
    em_estoque = [p for p in r if p["estoque_total"] > 0]
    assert r[: len(em_estoque)] == em_estoque
    assert [p["preco_centavos"] for p in em_estoque] == sorted(p["preco_centavos"] for p in em_estoque)


def test_catalogo_obter_produto(con):
    p = CatalogoRepository(con).obter("FAKE-0001")
    assert p["sku"] == "FAKE-0001" and len(p["especificacoes"]) == 4 and len(p["estoque"]) == 2
    assert CatalogoRepository(con).obter("FAKE-9999") is None


def test_loja_horarios_legiveis(con):
    repo = LojaRepository(con)
    centro = repo.unidades()[0]
    assert repo.horario_legivel(centro["horarios"]) == "segunda a sexta, das 08:00 às 18:00; sábado, das 08:00 às 12:00"
    assert repo.formas_pagamento() == ["Pix", "Cartão de crédito", "Cartão de débito", "Boleto bancário"]
    assert "art. 49" in repo.politica("troca")["texto"]


def test_atendimento_exige_consentimento(con):
    repo = AtendimentoRepository(con)
    with pytest.raises(sqlite3.IntegrityError):
        repo.registrar("conv1", "Quero falar sobre troca", consentimento=False)
    repo.registrar("conv1", "Quero falar sobre troca", motivo="troca", prioridade="alta", consentimento=True)
    assert repo.abertos()[0]["prioridade"] == "alta"


def test_avaliacao(con):
    AtendimentoRepository(con).avaliar("conv1", True)
    assert con.execute("SELECT util FROM avaliacoes").fetchone()[0] == 1


def test_importa_banco_legado_v02_sem_apagar(tmp_path):
    caminho = tmp_path / "v02.db"
    antigo = sqlite3.connect(caminho)
    antigo.execute("CREATE TABLE faq (id TEXT PRIMARY KEY, categoria TEXT, pergunta TEXT, variacoes TEXT, palavras_chave TEXT, "
                   "resposta TEXT, fonte TEXT, status TEXT, origem TEXT, criado_em TEXT)")
    antigo.execute("INSERT INTO faq VALUES ('FAQ-001','x','Pergunta seed','[]','[]','r','f','rascunho','seed','t')")
    antigo.execute("INSERT INTO faq VALUES ('FAQ-061','aprendida','Como funciona uma tupia?','[]','[]','Resposta IA','ollama','pendente_validacao','agente','t')")
    antigo.commit()
    antigo.close()

    con = banco.conectar(caminho)
    assert [s["pergunta"] for s in SugestaoRepository(con).listar_pendentes()] == ["Como funciona uma tupia?"]
    assert con.execute("SELECT COUNT(*) FROM legado_faq_v02").fetchone()[0] == 2   # preservado
    assert banco.importar_legado_v02(con) == 0                                      # não importa duas vezes


# =============================================================================
# Revisão humana das sugestões
# =============================================================================
def test_rejeitar_sugestao_tira_da_busca(con):
    codigo = banco.inserir_aprendida(con, "O que é parafuso cabeça chata?", "Resposta errada.")
    SugestaoRepository(con).rejeitar(codigo, "conteúdo incorreto", "revisor")
    assert codigo not in [f["id"] for f in banco.listar(con)]
    status, motivo = con.execute("SELECT status, motivo_revisao FROM faq_sugestoes").fetchone()
    assert (status, motivo) == ("rejeitada", "conteúdo incorreto")


def test_aprovar_sugestao_vira_faq_oficial(con):
    codigo = banco.inserir_aprendida(con, "O que é parafuso cabeça chata?", "Rascunho.")
    novo = SugestaoRepository(con).aprovar(codigo, "brocas_discos_acessorios", "revisor", resposta="Texto revisado.")
    assert novo == f"FAQ-{N_FAQS + 1:03d}"
    faq = FaqRepository(con).obter_resposta_por_id(novo)
    assert faq["resposta"] == "Texto revisado."
    assert con.execute("SELECT status FROM faq_perguntas WHERE codigo = ?", (novo,)).fetchone()[0] == "validado"
    assert codigo not in [f["id"] for f in banco.listar(con)]          # saiu da fila de sugestões
    assert SugestaoRepository(con).listar_pendentes() == []


@pytest.mark.parametrize("codigo", ["SUG-9999", "FAQ-0001", "abc"])
def test_revisao_rejeita_codigo_invalido(con, codigo):
    repo = SugestaoRepository(con)
    with pytest.raises(ValueError):
        repo.rejeitar(codigo, "x", "revisor")


def test_sugestao_ja_revisada_nao_pode_ser_revisada_de_novo(con):
    codigo = banco.inserir_aprendida(con, "Pergunta?", "Resposta.")
    repo = SugestaoRepository(con)
    repo.rejeitar(codigo, "x", "revisor")
    with pytest.raises(ValueError, match="já foi revisada"):
        repo.aprovar(codigo, "brocas_discos_acessorios", "revisor")


def test_aprovar_com_categoria_inexistente(con):
    codigo = banco.inserir_aprendida(con, "Pergunta?", "Resposta.")
    repo = SugestaoRepository(con)
    with pytest.raises(ValueError, match="Categoria"):
        repo.aprovar(codigo, "nao_existe", "revisor")


def test_cli_de_revisao(con, monkeypatch, capsys):
    from app.db import revisao

    monkeypatch.setattr(revisao, "abrir", lambda: con)
    codigo = banco.inserir_aprendida(con, "Pergunta da IA?", "Resposta da IA.")
    assert revisao.main([]) == 0
    assert codigo in capsys.readouterr().out
    assert revisao.main(["rejeitar", codigo, "errada"]) == 0
    assert revisao.main(["rejeitar", codigo]) == 1          # já revisada
    assert revisao.main(["comando_invalido"]) == 2


# =============================================================================
# Sincronização dos seeds com banco existente
# =============================================================================
def test_faq_nova_no_arquivo_entra_em_banco_existente(con, tmp_path, monkeypatch):
    import json as _json

    arq = tmp_path / "faq.json"
    dados = _json.loads(seeds.ARQ_FAQ.read_text(encoding="utf-8"))
    dados.append({**dados[0], "id": "FAQ-900", "pergunta": "Pergunta nova do time?", "variacoes": [], "palavras_chave": ["nova"]})
    arq.write_text(_json.dumps(dados, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setattr(seeds, "ARQ_FAQ", arq)
    con.execute("INSERT INTO faq_sugestoes (pergunta, resposta) VALUES ('p', 'r')")  # dado do usuário

    assert seeds.sincronizar(con) == ["faq.json"]
    assert con.execute("SELECT COUNT(*) FROM faq_perguntas WHERE codigo = 'FAQ-900'").fetchone()[0] == 1
    assert con.execute("SELECT COUNT(*) FROM faq_sugestoes").fetchone()[0] == 1   # preservado


def test_sincronizar_sem_mudanca_nao_reaplica(con):
    assert seeds.sincronizar(con) == []


def test_conectar_banco_antigo_recebe_faq_nova(tmp_path):
    caminho = tmp_path / "antigo.db"
    c = banco.conectar(caminho)
    c.execute("DELETE FROM faq_perguntas WHERE codigo = 'FAQ-061'")
    c.execute("DELETE FROM seeds_aplicados WHERE arquivo = 'faq.json'")  # simula banco anterior à FAQ
    c.commit()
    c.close()
    c = banco.conectar(caminho)
    assert c.execute("SELECT COUNT(*) FROM faq_perguntas WHERE codigo = 'FAQ-061'").fetchone()[0] == 1
