"""Testes unitários de app/busca.py (normalização, tokens e pontuação)."""

import pytest

from tests.conftest import N_FAQS

from app.busca import (
    Faq,
    _parecido,
    _radical,
    buscar,
    carregar_faq,
    eh_saudacao,
    montar_faqs,
    normalizar,
    nota_combinada,
    pontuar,
    tokens,
)


def faq(id="FAQ-900", categoria="escolha_de_ferramentas", pergunta="Pergunta?", chaves=(), variacoes=(), status="rascunho"):
    return Faq(
        id=id, categoria=categoria, pergunta=pergunta, resposta="Resposta.",
        palavras_chave=list(chaves), variacoes=list(variacoes), status=status,
    )


# ---- normalizar ---------------------------------------------------------------
@pytest.mark.parametrize(
    "entrada, esperado",
    [
        ("Multímetro", "multimetro"),
        ("  FURADEIRA   de   IMPACTO ", "furadeira de impacto"),
        ("Ação, coração! Pressão?", "acao coracao pressao"),
        ("R$ 300,00", "reais 300 00"),
        ("12V/20V", "12v 20v"),
        ("sds-plus", "sds plus"),
        ("", ""),
        ("???", ""),
    ],
)
def test_normalizar(entrada, esperado):
    assert normalizar(entrada) == esperado


# ---- radical (plural simples) -------------------------------------------------
@pytest.mark.parametrize(
    "palavra, esperado",
    [
        ("brocas", "broca"),
        ("discos", "disco"),
        ("padroes", "padrao"),
        ("pressao", "pressao"),   # não termina em s
        ("gas", "gas"),           # curta demais
        ("compasso", "compasso"),  # "ss" não é plural
    ],
)
def test_radical(palavra, esperado):
    assert _radical(palavra) == esperado


# ---- tokens -------------------------------------------------------------------
def test_tokens_remove_stopwords():
    assert tokens("Qual a melhor broca para o concreto?") == {"melhor", "broca", "concreto"}


def test_tokens_remove_numeros_soltos_mas_mantem_alfanumericos():
    assert tokens("bateria 4 ah ou 12v 300") == {"bateria", "ah", "12v"}


def test_tokens_so_stopwords_fica_vazio():
    assert tokens("o que eu posso fazer?") == set()


def test_tokens_aplica_plural():
    assert tokens("brocas e discos") == {"broca", "disco"}


# ---- tolerância a erros de digitação ------------------------------------------
@pytest.mark.parametrize(
    "a, b, esperado",
    [
        ("parafuzadeira", "parafusadeira", True),
        ("furadera", "furadeira", True),
        ("multimetro", "multimetro", True),
        ("broca", "bruxa", False),
        ("sds", "sdx", False),  # palavras curtas exigem igualdade
        ("madeira", "metal", False),
    ],
)
def test_parecido(a, b, esperado):
    assert _parecido(a, b) is esperado


# ---- pontuar ------------------------------------------------------------------
def test_pontuar_pergunta_identica_vale_1():
    f = faq(pergunta="Qual broca usar em madeira?")
    assert pontuar("qual broca usar em madeira", f) == 1.0


def test_pontuar_variacao_identica_vale_1():
    f = faq(variacoes=["broca para madeira"])
    assert pontuar("Broca para madeira!", f) == 1.0


def test_pontuar_palavra_chave_vale_mais_que_texto():
    so_chave = faq(chaves=["concreto"])
    so_texto = faq(pergunta="Como furar concreto?")
    assert pontuar("concreto", so_chave) == 1.0
    assert pontuar("concreto", so_texto) == 0.6


def test_pontuar_cobertura_parcial():
    f = faq(chaves=["broca"])
    assert pontuar("broca concreto", f) == 0.5


def test_pontuar_sem_relacao_vale_zero():
    assert pontuar("bolo de chocolate", faq(chaves=["broca"])) == 0.0


def test_pontuar_pergunta_vazia_vale_zero():
    assert pontuar("   ", faq(chaves=["broca"])) == 0.0


# ---- buscar -------------------------------------------------------------------
def test_buscar_ordena_pela_nota_e_limita():
    faqs = [faq(id=f"F{i}", chaves=["broca"] if i else ["broca", "metal"]) for i in range(5)]
    r = buscar("broca metal", faqs, limite=3)
    assert len(r) == 3
    assert r[0].faq.id == "F0"
    assert r[0].nota >= r[1].nota >= r[2].nota


def test_buscar_ignora_nota_zero():
    assert buscar("bolo", [faq(chaves=["broca"])]) == []


def test_buscar_empate_prefere_comercial():
    tecnica = faq(id="TEC", chaves=["lixadeira"])
    comercial = faq(id="COM", categoria="atendimento_comercial", chaves=["preco"])
    r = buscar("preço lixadeira", [tecnica, comercial])
    assert r[0].faq.id == "COM"


# ---- nota combinada -----------------------------------------------------------
def test_nota_combinada_soma_cobertura_de_varias_faqs():
    a = faq(id="A", chaves=["preco"])
    b = faq(id="B", chaves=["bosch"])
    assert pontuar("preco bosch", a) == 0.5
    assert nota_combinada("preco bosch", [a, b]) == 1.0


def test_nota_combinada_nao_conta_palavra_duas_vezes():
    a = faq(id="A", chaves=["frete"])
    b = faq(id="B", chaves=["frete"])
    assert nota_combinada("frete bosch", [a, b]) == 0.5


def test_nota_combinada_vazia():
    assert nota_combinada("?", [faq(chaves=["x"])]) == 0.0


# ---- saudação -----------------------------------------------------------------
@pytest.mark.parametrize("texto", ["oi", "Olá!", "Bom dia", "boa noite"])
def test_eh_saudacao(texto):
    assert eh_saudacao(texto)


@pytest.mark.parametrize("texto", ["oi, qual broca uso?", "furadeira", ""])
def test_nao_eh_saudacao(texto):
    assert not eh_saudacao(texto)


# ---- carga --------------------------------------------------------------------
def test_montar_faqs_ignora_inativas_e_campos_extras():
    dados = [
        {"id": "A", "categoria": "x", "pergunta": "p", "resposta": "r", "palavras_chave": [], "status": "rascunho",
         "origem": "seed", "criado_em": "2026-01-01"},
        {"id": "B", "categoria": "x", "pergunta": "p", "resposta": "r", "palavras_chave": [], "status": "inativo"},
    ]
    faqs = montar_faqs(dados)
    assert [f.id for f in faqs] == ["A"]


def test_carregar_faq_do_json():
    faqs = carregar_faq()
    assert len(faqs) == N_FAQS
    assert all(isinstance(f, Faq) for f in faqs)


def test_faq_comercial():
    assert faq(categoria="atendimento_comercial").comercial
    assert not faq(categoria="escolha_de_ferramentas").comercial


# ---- regressões encontradas pela suíte -----------------------------------------
def test_voltagem_sem_unidade_vira_v():
    assert tokens("ferramenta 220 na tomada 110") == {"220v", "tomada", "110v"}


def test_pergunta_identica_ganha_empate_de_nota():
    exata = faq(id="EXATA", pergunta="Como conservar minhas ferramentas?")
    cobertura = faq(id="COB", chaves=["conservar"])
    r = buscar("Como conservar minhas ferramentas?", [cobertura, exata])
    assert r[0].faq.id == "EXATA"
