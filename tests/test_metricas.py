"""RT-011: métricas anônimas e endpoint /metricas."""

from fastapi.testclient import TestClient

from app import main
from app.metricas import Metricas


def test_resumo_calcula_taxas_e_so_guarda_codigo_do_guardrail():
    m = Metricas()
    m.registrar_resposta("banco", "rascunho", ["G26:risco:solda"])
    m.registrar_resposta("agente", "gerado_por_ia", [])
    m.registrar_resposta("fallback", None, ["G26:risco_sem_base:eletricidade", "ia:indisponivel"])
    m.registrar_resposta("banco", "validado", [])
    r = m.resumo()
    assert r["respostas"] == 4
    assert (r["taxa_base"], r["taxa_ia"], r["taxa_sem_resposta"]) == (0.5, 0.25, 0.25)
    assert r["guardrails"] == {"G26": 2, "ia": 1}
    assert r["por_status_conteudo"]["nenhum"] == 1


def test_latencia_tem_percentis_e_janela_limitada():
    m = Metricas()
    for ms in range(1, 1001):
        m.registrar_latencia("chat", float(ms))
    lat = m.resumo()["latencia_ms"]["chat"]
    assert lat["n"] == 500                        # janela deslizante
    assert lat["p50"] == 751.0
    assert lat["max"] == 1000.0


def test_resumo_vazio_nao_divide_por_zero():
    r = Metricas().resumo()
    assert r["respostas"] == 0
    assert r["taxa_base"] == 0.0
    assert r["latencia_ms"] == {}


def test_endpoint_metricas_conta_o_chat_sem_guardar_texto():
    main.metricas.zerar()
    cliente = TestClient(main.app)
    pergunta = "Qual a diferença entre furadeira e parafusadeira?"
    assert cliente.post("/chat", json={"message": pergunta, "conversationId": "metricas-1"}).status_code == 200
    r = cliente.get("/metricas")
    assert r.status_code == 200
    dados = r.json()
    assert dados["respostas"] == 1
    assert dados["por_origem"] == {"banco": 1}
    assert dados["latencia_ms"]["chat"]["n"] == 1
    assert "furadeira" not in r.text
    assert "metricas-1" not in r.text
