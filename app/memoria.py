"""Memória de curto prazo das conversas (só em RAM, nada vai para o banco).

Cada conversa guarda as últimas trocas (pergunta já interpretada + resposta).
O número de conversas também é limitado: as mais antigas são descartadas.
"""

from collections import OrderedDict, deque
from dataclasses import dataclass


@dataclass(frozen=True)
class Troca:
    pergunta: str
    resposta: str


class Memoria:
    def __init__(self, trocas_por_conversa: int = 5, max_conversas: int = 1000):
        self.trocas_por_conversa = trocas_por_conversa
        self.max_conversas = max_conversas
        self._conversas: OrderedDict[str, deque[Troca]] = OrderedDict()

    def historico(self, conversa_id: str | None) -> list[Troca]:
        if not conversa_id or conversa_id not in self._conversas:
            return []
        self._conversas.move_to_end(conversa_id)
        return list(self._conversas[conversa_id])

    def registrar(self, conversa_id: str | None, pergunta: str, resposta: str) -> None:
        if not conversa_id:
            return
        trocas = self._conversas.setdefault(conversa_id, deque(maxlen=self.trocas_por_conversa))
        trocas.append(Troca(pergunta, resposta))
        self._conversas.move_to_end(conversa_id)
        while len(self._conversas) > self.max_conversas:
            self._conversas.popitem(last=False)

    def esquecer(self, conversa_id: str) -> None:
        self._conversas.pop(conversa_id, None)

    def __len__(self) -> int:
        return len(self._conversas)
