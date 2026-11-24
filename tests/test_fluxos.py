"""P1.4: fluxos guiados F-TROCA e F-HUMANO (T-032, T-033) e consentimento G23 (T-039)."""

from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from app import main
from app.db.repositorios import AtendimentoRepository
from app.fluxos import Fluxos

TERCA_10H = datetime(2026, 11, 24, 10, 0)    # terça-feira, dentro do horário
DOMINGO_10H = datetime(2026, 11, 29, 10, 0)  # domingo, fora do horário
SABADO_13H = datetime(2026, 11, 28, 13, 0)   # sábado depois das 12:00


@pytest.fixture
def fluxos(con):
    return Fluxos(lambda: con, agora=lambda: TERCA_10H)


def _conversa(fluxos, *mensagens, conversa="c1"):
    return [fluxos.tratar(conversa, m) for m in mensagens]


# ---------------------------------------------------------------- início
@pytest.mark.parametrize("mensagem", [
    "Quero falar com um atendente", "posso falar com uma pessoa?", "me passa para um humano",
    "preciso de um atendente", "quero atendimento humano",
])
def test_pedidos_de_atendente_abrem_f_humano(fluxos, mensagem):
    r = fluxos.tratar("c1", mensagem)
    assert r and r.passo == "humano_resumo"


@pytest.mark.parametrize("mensagem", [
    "Posso trocar ou devolver um produto?", "quero devolver", "como faço uma troca", "quero trocar o produto",
    "Trocas e garantia",
])
def test_pedidos_de_troca_abrem_f_troca(fluxos, mensagem):
    r = fluxos.tratar("c1", mensagem)
    assert r and r.passo == "troca_motivo" and len(r.opcoes) == 3


@pytest.mark.parametrize("mensagem", [
    "como trocar o disco da esmerilhadeira?", "quero trocar a escova de carvão", "qual broca usar em madeira?",
    "a pessoa que me atendeu foi ótima", "Olá",
])
def test_duvidas_comuns_nao_abrem_fluxo(fluxos, mensagem):
    assert fluxos.tratar("c1", mensagem) is None


def test_sem_conversation_id_nao_ha_fluxo(fluxos):
    assert fluxos.tratar(None, "quero falar com um atendente") is None


# ---------------------------------------------------------------- F-TROCA
def test_troca_desistencia_online_cita_cdc(fluxos):
    _, canal, final = _conversa(fluxos, "quero devolver", "Desisti da compra", "Comprei online")
    assert canal.passo == "troca_canal"
    assert "7 dias" in final.answer and "art. 49" in final.answer and final.encerrado
    assert not fluxos.ativo("c1")


def test_troca_desistencia_loja_fisica_usa_politica_da_loja(fluxos):
    *_, final = _conversa(fluxos, "Trocas e garantia", "me arrependi", "foi na loja física")
    assert final.passo == "troca_loja" and "30 dias" in final.answer


def test_troca_defeito_orienta_garantia_sem_registrar(fluxos, con):
    _, final = _conversa(fluxos, "quero devolver", "Produto com defeito")
    assert "90 dias" in final.answer and "assistência técnica autorizada" in final.answer
    assert AtendimentoRepository(con).abertos() == []


def test_produto_errado_vira_atendimento_prioritario_com_consentimento(fluxos, con):
    _, consentimento, final = _conversa(fluxos, "quero devolver", "veio na voltagem errada", "sim")
    assert consentimento.passo == "humano_consentimento" and "prioritária" in consentimento.answer
    assert final.protocolo
    [registro] = AtendimentoRepository(con).abertos()
    assert (registro["motivo"], registro["prioridade"]) == ("troca", "alta")


def test_motivo_ja_na_primeira_mensagem_pula_a_pergunta(fluxos):
    r = fluxos.tratar("c1", "quero devolver, veio com defeito")
    assert r.passo == "troca_defeito"


def test_resposta_nao_entendida_repete_e_depois_desiste(fluxos):
    _, primeira, segunda = _conversa(fluxos, "quero devolver", "hmm", "sei la")
    assert primeira.passo == "troca_motivo" and "não entendi" in primeira.answer
    assert segunda.passo == "nao_entendido" and segunda.encerrado and not fluxos.ativo("c1")


# ---------------------------------------------------------------- F-HUMANO e G23
def test_humano_registra_resumo_mascarado_so_com_consentimento(fluxos, con):
    _, consentimento, final = _conversa(
        fluxos, "quero falar com um atendente", "meu cpf é 123.456.789-09 e o pedido não chegou", "sim")
    assert "123.456.789-09" not in consentimento.answer
    assert "protocolo" in final.answer and "em instantes" in final.answer
    [registro] = AtendimentoRepository(con).abertos()
    assert "123.456.789-09" not in registro["resumo"] and "pedido não chegou" in registro["resumo"]
    assert (registro["motivo"], registro["prioridade"]) == ("pedido_cliente", "normal")


def test_sem_consentimento_nada_e_gravado_e_mostra_contato(fluxos, con):
    *_, final = _conversa(fluxos, "quero falar com um atendente", "dúvida sobre nota fiscal", "não")
    assert final.passo == "humano_recusado" and "telefone" in final.answer
    assert AtendimentoRepository(con).abertos() == []


@pytest.mark.parametrize("agora", [DOMINGO_10H, SABADO_13H])
def test_fora_do_horario_informa_horario_e_registra(con, agora):
    fluxos = Fluxos(lambda: con, agora=lambda: agora)
    *_, final = _conversa(fluxos, "quero falar com um atendente", "quero um orçamento", "pode")
    assert "segunda a sexta" in final.answer and "retornaremos" in final.answer
    assert len(AtendimentoRepository(con).abertos()) == 1


def test_cancelar_encerra_o_fluxo_a_qualquer_momento(fluxos, con):
    _, saiu = _conversa(fluxos, "quero falar com um atendente", "cancelar")
    assert saiu.passo == "saiu" and not fluxos.ativo("c1")
    assert fluxos.tratar("c1", "qual broca usar em madeira?") is None
    assert AtendimentoRepository(con).abertos() == []


def test_resumo_longo_e_cortado(fluxos, con):
    _conversa(fluxos, "quero falar com um atendente", "x" * 900, "sim")
    assert len(AtendimentoRepository(con).abertos()[0]["resumo"]) <= 300


def test_conversas_sao_independentes(fluxos):
    fluxos.tratar("a", "quero falar com um atendente")
    assert fluxos.ativo("a") and not fluxos.ativo("b")
    assert fluxos.tratar("b", "qual broca usar em madeira?") is None


# ---------------------------------------------------------------- API
def test_api_fluxo_devolve_opcoes_e_esquecer_conversa_encerra():
    cliente = TestClient(main.app)
    r = cliente.post("/chat", json={"message": "Posso trocar ou devolver um produto?", "conversationId": "fluxo-api"})
    corpo = r.json()
    assert corpo["origem"] == "fluxo" and corpo["opcoes"] and corpo["fluxoAberto"] and corpo["statusConteudo"] == "dados_demonstracao"
    assert cliente.delete("/conversas/fluxo-api").status_code == 204
    assert not main.fluxos.ativo("fluxo-api")


def test_api_sem_conversation_id_responde_pela_faq():
    r = TestClient(main.app).post("/chat", json={"message": "Quero falar com um atendente"})
    assert r.json()["origem"] != "fluxo"
