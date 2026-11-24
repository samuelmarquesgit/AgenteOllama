"""Configuração compartilhada dos testes.

- Os testes NUNCA usam o banco real (data/loja.db) nem o Ollama de verdade.
- `agente` usa um banco SQLite temporário e um "Ollama falso" que registra as chamadas.
"""

import os
import shutil
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
os.environ["BANCO_SQLITE"] = str(Path(tempfile.mkdtemp()) / "teste_import.db")
os.environ["USAR_OLLAMA"] = "true"
os.environ["TORK_SERVIR_SUGESTOES"] = "true"  # a lógica de reaproveitamento é testada; o padrão (false) tem teste próprio
sys.path.insert(0, str(RAIZ))

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app import banco  # noqa: E402
from app.agente import Agente  # noqa: E402
from app.db.seeds import ESPERADO  # noqa: E402

N_FAQS = ESPERADO["faq_perguntas"]  # quantidade de FAQs no knowledge/faq.json

RESPOSTA_FALSA = "Resposta gerada pelo agente."


class OllamaFalso:
    """Substitui o Ollama: devolve uma resposta fixa e guarda as perguntas recebidas."""

    def __init__(self, resposta=RESPOSTA_FALSA):
        self.resposta = resposta
        self.perguntas: list[str] = []
        self.historicos: list[list] = []

    def __call__(self, pergunta, historico=None):
        self.perguntas.append(pergunta)
        self.historicos.append(list(historico or []))
        if callable(self.resposta):
            return self.resposta(pergunta)
        return self.resposta

    @property
    def chamadas(self):
        return len(self.perguntas)


@pytest.fixture(autouse=True)
def ollama_ligado(monkeypatch):
    monkeypatch.setenv("USAR_OLLAMA", "true")


@pytest.fixture(scope="session")
def banco_modelo(tmp_path_factory):
    """Banco migrado e populado UMA vez por sessão; cada teste recebe uma cópia."""
    caminho = tmp_path_factory.mktemp("modelo") / "modelo.db"
    banco.conectar(caminho).close()
    return caminho


@pytest.fixture
def con(tmp_path, banco_modelo):
    destino = tmp_path / "teste.db"
    shutil.copyfile(banco_modelo, destino)
    c = banco.conectar(destino)
    yield c
    c.close()


@pytest.fixture
def conexoes():
    """Abre conexões SQLite extras no teste e garante que todas são fechadas no fim.

    conexoes(caminho)               -> só abre (sem migrar)
    conexoes(caminho, popular=True) -> migra e popula (como a aplicação faz)
    """
    from app.db.conexao import abrir

    abertas = []

    def _abrir(caminho, popular=False):
        c = banco.conectar(caminho) if popular else abrir(caminho)
        abertas.append(c)
        return c

    yield _abrir
    for c in abertas:
        c.close()


@pytest.fixture
def ollama():
    return OllamaFalso()


@pytest.fixture
def reescrita():
    """Reescrita falsa: por padrão não reescreve (devolve None -> usa a original)."""
    return OllamaFalso(resposta=None)


@pytest.fixture
def agente(con, ollama, reescrita):
    return Agente(con, perguntar=ollama, reescrever=reescrita)


@pytest.fixture
def cliente(agente, monkeypatch):
    import app.main as main

    from app.memoria import Memoria

    monkeypatch.setattr(main, "agente", agente)
    monkeypatch.setattr(main, "memoria", Memoria())
    return TestClient(main.app, raise_server_exceptions=False)
