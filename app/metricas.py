"""Observabilidade (RT-011): contadores e latências em memória, sem texto do cliente.

Guarda só agregados: quantas respostas por origem e por status de conteúdo, guardrails acionados,
chamadas à IA (ok / falha) e latência por etapa (total do /chat, chamada à IA, reescrita).
Nada de pergunta, resposta, id de conversa ou IP. Zera ao reiniciar o processo (suficiente para a
demo; exportar para Prometheus/OpenTelemetry fica para o backlog).
"""

import threading
import time
from collections import Counter, deque
from contextlib import contextmanager

AMOSTRAS_POR_ETAPA = 500  # janela deslizante para os percentis


def _percentil(valores: list[float], p: float) -> float:
    ordenados = sorted(valores)
    return round(ordenados[min(len(ordenados) - 1, int(p * len(ordenados)))], 1)


class Metricas:
    def __init__(self):
        self._trava = threading.Lock()
        self.zerar()

    def zerar(self) -> None:
        with self._trava:
            self._inicio = time.time()
            self._origens: Counter[str] = Counter()
            self._conteudo: Counter[str] = Counter()
            self._guardrails: Counter[str] = Counter()
            self._ia: Counter[str] = Counter()
            self._latencias: dict[str, deque[float]] = {}

    def registrar_resposta(self, origem: str, status_conteudo: str | None, guardrails: list[str]) -> None:
        with self._trava:
            self._origens[origem] += 1
            self._conteudo[status_conteudo or "nenhum"] += 1
            # só o código do guardrail ("G26:risco:solda" -> "G26"), nunca conteúdo
            self._guardrails.update(g.split(":", 1)[0] for g in guardrails)

    def registrar_ia(self, ok: bool) -> None:
        with self._trava:
            self._ia["ok" if ok else "falha"] += 1

    def registrar_latencia(self, etapa: str, ms: float) -> None:
        with self._trava:
            self._latencias.setdefault(etapa, deque(maxlen=AMOSTRAS_POR_ETAPA)).append(ms)

    @contextmanager
    def cronometro(self, etapa: str):
        inicio = time.perf_counter()
        try:
            yield
        finally:
            self.registrar_latencia(etapa, (time.perf_counter() - inicio) * 1000)

    def resumo(self) -> dict:
        with self._trava:
            total = sum(self._origens.values())
            sem_resposta = self._origens["fallback"] + self._origens["fora_do_escopo"] + self._origens["bloqueado"]
            return {
                "desde": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(self._inicio)),
                "respostas": total,
                "por_origem": dict(self._origens),
                "por_status_conteudo": dict(self._conteudo),
                "taxa_base": round(self._origens["banco"] / total, 3) if total else 0.0,
                "taxa_ia": round((self._origens["agente"] + self._origens["sugestao"]) / total, 3) if total else 0.0,
                "taxa_sem_resposta": round(sem_resposta / total, 3) if total else 0.0,
                "guardrails": dict(self._guardrails),
                "ia": dict(self._ia),
                "latencia_ms": {
                    etapa: {"n": len(v), "p50": _percentil(list(v), 0.5), "p95": _percentil(list(v), 0.95),
                            "max": round(max(v), 1)}
                    for etapa, v in self._latencias.items() if v
                },
            }


metricas = Metricas()
