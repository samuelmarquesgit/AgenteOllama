"""Configuração compartilhada dos testes.

- Os testes NUNCA usam o banco real (data/loja.db) nem o Ollama de verdade.
- `agente` usa um banco SQLite temporário e um "Ollama falso" que registra as chamadas.
"""

import os
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
os.environ["BANCO_SQLITE"] = str(Path(tempfile.mkdtemp()) / "teste_import.db")
os.environ["USAR_OLLAMA"] = "true"
sys.path.insert(0, str(RAIZ))

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app import banco  # noqa: E402
from app.agente import Agente  # noqa: E402

RESPOSTA_FALSA = "Resposta gerada pelo agente."


class OllamaFalso:
    """Substitui o Ollama: devolve uma resposta fixa e guarda as perguntas recebidas."""

    def __init__(self, resposta=RESPOSTA_FALSA):
        self.resposta = resposta
        self.perguntas: list[str] = []

    def __call__(self, pergunta):
        self.perguntas.append(pergunta)
        if callable(self.resposta):
            return self.resposta(pergunta)
        return self.resposta

    @property
    def chamadas(self):
        return len(self.perguntas)


@pytest.fixture(autouse=True)
def ollama_ligado(monkeypatch):
    monkeypatch.setenv("USAR_OLLAMA", "true")


@pytest.fixture
def con(tmp_path):
    c = banco.conectar(tmp_path / "teste.db")
    yield c
    c.close()


@pytest.fixture
def ollama():
    return OllamaFalso()


@pytest.fixture
def agente(con, ollama):
    return Agente(con, perguntar=ollama)


@pytest.fixture
def cliente(agente, monkeypatch):
    import app.main as main

    monkeypatch.setattr(main, "agente", agente)
    return TestClient(main.app, raise_server_exceptions=False)
