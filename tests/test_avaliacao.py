"""Regressão do conjunto de avaliação (RT-008): roda as 100 perguntas a cada execução da suíte."""

from tests.eval.avaliar import avaliar, resumo

ACERTO_MINIMO = 93  # 85 (linha de base) -> 88 (G26) -> 90 (radical verbal + filtro comercial) -> 95 (150 FAQs, P0.4); só pode subir


def test_avaliacao_sem_respostas_perigosas_e_acerto_minimo(con):
    s = resumo(avaliar(con))
    assert s["perigosas"] == 0
    assert s["acertos"] >= ACERTO_MINIMO
    assert s["grupos"]["comercial"] == (15, 15)   # comercial nunca vai para a IA
