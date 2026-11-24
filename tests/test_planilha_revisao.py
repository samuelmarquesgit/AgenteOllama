"""P1.7: planilha de revisão humana (geração e importação)."""

import csv
import json
import shutil

import pytest

from app.db import planilha_revisao as pr


def test_amostra_tem_todas_de_risco_alto_mais_30_e_e_estavel():
    faqs = json.loads(pr.FAQ_JSON.read_text(encoding="utf-8"))
    a, b = pr.amostra(faqs), pr.amostra(faqs)
    altas = {f["id"] for f in faqs if f["nivel_risco"] == "alto"}
    assert [f["id"] for f in a] == [f["id"] for f in b]                 # semente fixa
    assert altas <= {f["id"] for f in a}
    assert len(a) == len(altas) + pr.TAMANHO_AMOSTRA


def test_planilha_versionada_esta_em_dia_com_a_amostra():
    linhas = pr._ler(pr.PLANILHA)
    esperado = [f["id"] for f in pr.amostra(json.loads(pr.FAQ_JSON.read_text(encoding="utf-8")))]
    assert [linha["id"] for linha in linhas] == esperado


@pytest.fixture
def copia(tmp_path):
    faq = tmp_path / "faq.json"
    shutil.copyfile(pr.FAQ_JSON, faq)
    planilha = tmp_path / "planilha.csv"
    pr.gerar(planilha)
    return faq, planilha


def _preencher(planilha, decisoes: dict[str, dict]):
    linhas = pr._ler(planilha)
    for linha in linhas:
        linha.update(decisoes.get(linha["id"], {}))
    with planilha.open("w", encoding="utf-8-sig", newline="") as arq:
        escritor = csv.DictWriter(arq, fieldnames=pr.COLUNAS, delimiter=";")
        escritor.writeheader()
        escritor.writerows(linhas)
    return [linha["id"] for linha in linhas]


def test_importar_aplica_aprovar_ajustar_e_rejeitar(copia):
    faq, planilha = copia
    ids = pr._ler(planilha)
    a, b, c = (linha["id"] for linha in ids[:3])
    revisao = {"revisor": "AB", "data": "2026-11-25"}
    _preencher(planilha, {a: {"decisao": "aprovar", **revisao},
                          b: {"decisao": "ajustar", "resposta_corrigida": "Texto revisado.", **revisao},
                          c: {"decisao": "rejeitar", **revisao}})
    r = pr.importar(planilha, faq)
    assert (r["aprovadas"], r["ajustadas"], r["rejeitadas"], r["erros"]) == (1, 1, 1, [])
    dados = {f["id"]: f for f in json.loads(faq.read_text(encoding="utf-8"))}
    assert dados[a]["status"] == "validado" and dados[a]["revisado_em"] == "2026-11-25"
    assert dados[b]["resposta"] == "Texto revisado." and dados[b]["status"] == "validado"
    assert dados[c]["status"] == "inativo"
    assert "revisado por AB" in dados[a]["fonte"]


@pytest.mark.parametrize("linha, erro", [
    ({"decisao": "talvez", "revisor": "AB", "data": "2026-11-25"}, "decisão inválida"),
    ({"decisao": "aprovar", "revisor": "", "data": "2026-11-25"}, "revisor"),
    ({"decisao": "aprovar", "revisor": "AB", "data": "25/11/2026"}, "data"),
    ({"decisao": "ajustar", "revisor": "AB", "data": "2026-11-25"}, "resposta_corrigida"),
])
def test_linha_invalida_nao_altera_nada(copia, linha, erro):
    faq, planilha = copia
    antes = faq.read_text(encoding="utf-8")
    primeiro = pr._ler(planilha)[0]["id"]
    _preencher(planilha, {primeiro: linha})
    r = pr.importar(planilha, faq)
    assert r["erros"] and erro in r["erros"][0]
    assert faq.read_text(encoding="utf-8") == antes


def test_planilha_em_branco_nao_altera_nada(copia):
    faq, planilha = copia
    antes = faq.read_text(encoding="utf-8")
    r = pr.importar(planilha, faq)
    assert r["ignoradas"] == len(pr._ler(planilha)) and r["erros"] == []
    assert json.loads(faq.read_text(encoding="utf-8")) == json.loads(antes)
