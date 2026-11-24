"""Testes das respostas com dados do banco: catálogo fictício e informações da loja."""

import pytest

from app.intencoes import detectar_loja, detectar_produto

MARCAS = ["Torqmax", "Voltrix", "Brutus Pro"]


# ---- detecção de produto ------------------------------------------------------
@pytest.mark.parametrize(
    "pergunta, categorias",
    [
        ("Quanto custa uma furadeira?", ["furadeiras"]),
        ("qual o preço da furadeira de impacto?", ["furadeiras_impacto"]),
        ("tem parafusadeira a bateria?", ["parafusadeiras"]),
        ("quero um martelete", ["marteletes"]),
        ("vocês vendem esmerilhadeira?", ["esmerilhadeiras"]),
        ("preço de serra", ["serras_circulares", "serras_tico_tico"]),
        ("tem serra circular?", ["serras_circulares"]),
        ("quanto custa uma bateria 20V?", ["baterias"]),
        ("procuro lavadora de alta pressão", ["lavadoras_alta_pressao"]),
        ("tem trena a laser?", ["medidores_laser"]),
        ("quero óculos de proteção", ["epi"]),
    ],
)
def test_detecta_categoria(pergunta, categorias):
    i = detectar_produto(pergunta, MARCAS)
    assert i is not None and i.filtro.categorias == categorias


@pytest.mark.parametrize(
    "pergunta",
    [
        "Qual broca usar em concreto?",                  # dúvida técnica, sem sinal de compra
        "Qual a diferença entre furadeira e parafusadeira?",
        "Posso colocar disco maior na esmerilhadeira?",
        "Tem uma Bosch por R$ 300?",                     # sem categoria
        "quanto custa o frete?",
    ],
)
def test_nao_confunde_duvida_tecnica_com_compra(pergunta):
    assert detectar_produto(pergunta, MARCAS) is None


@pytest.mark.parametrize(
    "pergunta, alimentacao",
    [
        ("tem furadeira 220V?", ["220V", "bivolt"]),
        ("tem furadeira 127v?", ["127V", "bivolt"]),
        ("tem furadeira 110?", ["127V", "bivolt"]),
        ("quero furadeira bivolt", ["bivolt"]),
        ("quero parafusadeira sem fio", ["bateria"]),
        ("quero furadeira", []),
    ],
)
def test_detecta_alimentacao(pergunta, alimentacao):
    assert detectar_produto(pergunta, MARCAS).filtro.alimentacao == alimentacao


def test_detecta_preco_maximo_e_marca():
    i = detectar_produto("tem parafusadeira Torqmax até R$ 600?", MARCAS)
    assert i.filtro.preco_max_centavos == 60000 and i.filtro.marca == "Torqmax"


def test_detecta_marca_real_fora_do_catalogo():
    assert detectar_produto("quanto custa furadeira bosch?", MARCAS).marca_real == "bosch"


# ---- detecção de loja ---------------------------------------------------------
@pytest.mark.parametrize(
    "pergunta, intencao",
    [
        ("Que horas vocês abrem?", "horario"),
        ("qual o horário de funcionamento?", "horario"),
        ("a loja está aberta?", "horario"),
        ("onde fica a loja?", "endereco"),
        ("qual o endereço?", "endereco"),
        ("aceita pix?", "pagamento"),
        ("vocês parcelam?", "pagamento"),
        ("quais as formas de pagamento?", "pagamento"),
    ],
)
def test_detecta_loja(pergunta, intencao):
    assert detectar_loja(pergunta) == intencao


@pytest.mark.parametrize(
    "pergunta",
    ["Como funciona uma furadeira de impacto?", "posso trocar na loja física?", "como acompanho meu pedido?", "qual broca usar?"],
)
def test_nao_detecta_loja(pergunta):
    assert detectar_loja(pergunta) is None


# ---- agente -------------------------------------------------------------------
def test_agente_responde_produto_com_cards_sem_llm(agente, ollama):
    r = agente.responder("quanto custa uma furadeira de impacto?")
    assert r.origem == "catalogo"
    assert 1 <= len(r.produtos) <= 3
    p = r.produtos[0]
    assert p["sku"].startswith("FAKE-") and p["preco_formatado"].startswith("R$ ")
    assert "fictícios" in r.answer
    assert "G24:dado_do_catalogo" in r.guardrails
    assert ollama.chamadas == 0


def test_agente_pede_voltagem_para_ferramenta_com_fio(agente):
    r = agente.responder("quanto custa uma furadeira?")
    assert "voltagem" in r.answer and "G20:confirmar_voltagem" in r.guardrails


def test_agente_nao_pede_voltagem_quando_informada(agente):
    r = agente.responder("quanto custa uma furadeira 220V?")
    assert "G20:confirmar_voltagem" not in r.guardrails
    assert all(p["alimentacao"] in ("220V", "bivolt") for p in r.produtos)


def test_agente_respeita_preco_maximo(agente):
    r = agente.responder("tem parafusadeira até 400 reais?")
    assert r.produtos and all(p["preco"] <= 400 for p in r.produtos)


def test_agente_sem_resultado(agente):
    r = agente.responder("tem martelete até 10 reais?")
    assert r.origem == "catalogo" and r.produtos == [] and "Não encontrei" in r.answer


def test_agente_marca_real_oferece_equivalentes(agente):
    r = agente.responder("quanto custa uma furadeira makita?")
    assert "não temos a marca Makita" in r.answer and r.produtos


@pytest.mark.parametrize("pergunta, trecho", [
    ("Que horas vocês abrem?", "segunda a sexta"),
    ("onde fica a loja?", "Rua das Ferramentas"),
    ("aceita pix?", "Pix"),
])
def test_agente_responde_dados_da_loja(agente, ollama, pergunta, trecho):
    r = agente.responder(pergunta)
    assert r.origem == "loja" and trecho in r.answer and "fictícios" in r.answer
    assert ollama.chamadas == 0


def test_agente_continua_no_contexto_do_produto(agente, reescrita):
    from app.memoria import Troca

    reescrita.resposta = "Quanto custa uma furadeira de impacto 220V?"
    r = agente.responder("e a de 220V?", [Troca("Quanto custa uma furadeira de impacto?", "...")])
    assert r.origem == "catalogo" and all(p["alimentacao"] in ("220V", "bivolt") for p in r.produtos)


# ---- API ----------------------------------------------------------------------
def test_api_chat_devolve_produtos(cliente):
    corpo = cliente.post("/chat", json={"message": "tem lixadeira?"}).json()
    assert corpo["origem"] == "catalogo" and corpo["produtos"]


def test_api_produtos_com_filtros(cliente):
    r = cliente.get("/produtos", params={"categoria": "parafusadeiras", "preco_max": 500, "limite": 5}).json()
    assert 0 < len(r) <= 5 and all(p["preco"] <= 500 for p in r)


def test_api_produto_detalhe_e_404(cliente):
    assert cliente.get("/produtos/FAKE-0001").json()["sku"] == "FAKE-0001"
    assert cliente.get("/produtos/FAKE-9999").status_code == 404


def test_api_loja(cliente):
    d = cliente.get("/loja").json()
    assert len(d["unidades"]) == 2 and "Pix" in d["formas_pagamento"] and len(d["politicas"]) == 6
