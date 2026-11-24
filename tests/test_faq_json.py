"""Integridade da base inicial (knowledge/faq.json).

Garante que o arquivo continua válido quando alguém editar as FAQs à mão.
"""

import json
import re

import pytest

from app.busca import CAMINHO_FAQ, buscar, carregar_faq

DADOS = json.loads(CAMINHO_FAQ.read_text(encoding="utf-8"))
FAQS = carregar_faq()
CATEGORIAS = {
    "escolha_de_ferramentas", "brocas_discos_acessorios", "baterias_alimentacao",
    "medicao_eletronica", "soldagem_compressores_limpeza", "uso_manutencao_seguranca",
    "atendimento_comercial", "diagnostico_comparacao",
}
CAMPOS = {"id", "categoria", "pergunta", "variacoes", "palavras_chave", "resposta", "fonte", "revisado_em", "status", "nivel_risco"}


def test_tem_pelo_menos_60_faqs():
    assert len(DADOS) >= 60  # meta do plano de banco: 150


def test_ids_unicos_e_no_formato():
    ids = [f["id"] for f in DADOS]
    assert len(ids) == len(set(ids))
    assert all(re.fullmatch(r"FAQ-\d{3}", i) for i in ids)


@pytest.mark.parametrize("item", DADOS, ids=lambda f: f["id"])
def test_campos_obrigatorios(item):
    assert set(item) == CAMPOS
    assert item["categoria"] in CATEGORIAS
    assert item["pergunta"].strip() and item["resposta"].strip()
    assert item["palavras_chave"], "toda FAQ precisa de palavras-chave"
    assert isinstance(item["variacoes"], list)
    assert item["status"] in {"rascunho", "pendente_validacao", "validado", "inativo"}
    assert item["nivel_risco"] in {"baixo", "medio", "alto"}


def test_comerciais_estao_pendentes_de_validacao():
    for f in DADOS:
        if f["categoria"] == "atendimento_comercial":
            assert f["status"] == "pendente_validacao", f["id"]


def test_nenhuma_resposta_informa_preco():
    for f in DADOS:
        assert not re.search(r"R\$\s*\d", f["resposta"]), f["id"]


def test_nenhuma_resposta_pede_dados_pessoais():
    for f in DADOS:
        texto = f["resposta"].lower()
        assert "informe seu cpf" not in texto and "informe o cpf" not in texto, f["id"]


@pytest.mark.parametrize("faq", FAQS, ids=lambda f: f.id)
def test_cada_pergunta_encontra_a_propria_faq(faq):
    r = buscar(faq.pergunta, FAQS)
    assert r and r[0].faq.id == faq.id and r[0].nota == 1.0


@pytest.mark.parametrize(
    "faq, variacao",
    [(f, v) for f in FAQS for v in f.variacoes],
    ids=lambda x: x.id if hasattr(x, "id") else x[:30],
)
def test_cada_variacao_encontra_a_propria_faq(faq, variacao):
    assert buscar(variacao, FAQS)[0].faq.id == faq.id
