"""Testes de integração da API (app/main.py)."""

import logging

import pytest

from tests.conftest import RESPOSTA_FALSA


def test_health(cliente):
    r = cliente.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok", "faqs": 60, "aprendidas": 0}


def test_chat_resposta_do_banco(cliente):
    r = cliente.post("/chat", json={"message": "Qual broca usar em madeira?"})
    assert r.status_code == 200
    corpo = r.json()
    assert set(corpo) == {"answer", "matchedFaqId", "confidence", "origem"}
    assert corpo["matchedFaqId"] == "FAQ-014"
    assert corpo["origem"] == "banco"
    assert 0 <= corpo["confidence"] <= 1


def test_chat_aceita_acentos_utf8(cliente):
    r = cliente.post("/chat", json={"message": "Como escolher um multímetro?"})
    assert r.json()["matchedFaqId"] == "FAQ-028"


def test_chat_aprende_e_health_reflete(cliente):
    r = cliente.post("/chat", json={"message": "Como funciona uma tupia de bancada?"})
    assert r.json() == {"answer": RESPOSTA_FALSA, "matchedFaqId": "FAQ-061", "confidence": 0.0, "origem": "agente"}
    assert cliente.get("/health").json() == {"status": "ok", "faqs": 61, "aprendidas": 1}

    nova = [f for f in cliente.get("/faqs").json() if f["id"] == "FAQ-061"][0]
    assert nova["status"] == "pendente_validacao"
    assert nova["categoria"] == "aprendida"


@pytest.mark.parametrize(
    "corpo",
    [{"message": ""}, {"message": "   "}, {"message": "x" * 501}, {}, {"mensagem": "oi"}, {"message": 123}],
)
def test_chat_rejeita_entrada_invalida(cliente, corpo):
    assert cliente.post("/chat", json=corpo).status_code == 422


def test_chat_aceita_500_caracteres(cliente):
    assert cliente.post("/chat", json={"message": "broca " + "a" * 494}).status_code == 200


def test_chat_rejeita_corpo_que_nao_e_json(cliente):
    r = cliente.post("/chat", content="não é json", headers={"Content-Type": "application/json"})
    assert r.status_code == 422


def test_chat_metodo_get_nao_permitido(cliente):
    assert cliente.get("/chat").status_code == 405


def test_erro_interno_nao_expoe_detalhes(cliente, agente, monkeypatch):
    def quebra(_):
        raise RuntimeError("segredo interno: senha=123")

    monkeypatch.setattr(agente, "responder", quebra)
    r = cliente.post("/chat", json={"message": "qualquer"})
    assert r.status_code == 500
    assert r.json() == {"detail": "Erro interno. Tente novamente."}
    assert "segredo" not in r.text


def test_log_nao_guarda_texto_do_cliente(cliente, caplog):
    with caplog.at_level(logging.INFO, logger="agente"):
        cliente.post("/chat", json={"message": "meu cpf é 12345678900, qual broca uso em metal?"})
    assert "chat faq=" in caplog.text
    assert "12345678900" not in caplog.text


def test_faqs_lista_campos_publicos(cliente):
    faqs = cliente.get("/faqs").json()
    assert len(faqs) == 60
    assert set(faqs[0]) == {"id", "categoria", "pergunta", "status"}


def test_pagina_inicial(cliente):
    r = cliente.get("/")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]
    assert "Assistente da Loja de Ferramentas" in r.text


def test_swagger_disponivel(cliente):
    assert cliente.get("/docs").status_code == 200
    assert cliente.get("/openapi.json").json()["info"]["version"] == "0.1.0"
