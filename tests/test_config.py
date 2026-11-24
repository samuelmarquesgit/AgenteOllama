"""RT-012: configuração centralizada e .env.example sincronizado."""

import os

import pytest

from app import config


def _exemplo() -> dict[str, str]:
    linhas = (config.RAIZ / ".env.example").read_text(encoding="utf-8").splitlines()
    return dict(linha.split("=", 1) for linha in linhas if linha and not linha.startswith("#"))


def test_env_example_lista_todas_as_variaveis_com_os_padroes():
    assert _exemplo() == {v.nome: v.padrao for v in config.VARIAVEIS.values()}


def test_nenhuma_variavel_lida_fora_do_registro():
    """Todo os.getenv do app passa pelo app/config.py (evita variável escondida no código)."""
    for arq in (config.RAIZ / "app").rglob("*.py"):
        if arq.name != "config.py":
            assert "os.getenv" not in arq.read_text(encoding="utf-8"), arq


@pytest.mark.parametrize("valor, esperado", [("true", True), ("SIM", True), ("1", True), ("false", False),
                                              ("não", False), ("0", False), ("talvez", True)])
def test_ligado_aceita_formas_comuns(monkeypatch, valor, esperado):
    monkeypatch.setenv("TORK_SERVIR_SUGESTOES", valor)
    assert config.ligado("TORK_SERVIR_SUGESTOES") is esperado


def test_segundos_invalido_ou_baixo_usa_limites(monkeypatch):
    monkeypatch.setenv("OLLAMA_TIMEOUT", "abc")
    assert config.segundos("OLLAMA_TIMEOUT") == 45.0
    monkeypatch.setenv("OLLAMA_TIMEOUT", "0")
    assert config.segundos("OLLAMA_TIMEOUT") == 1.0


def test_caminho_relativo_e_resolvido_a_partir_da_raiz(monkeypatch):
    monkeypatch.setenv("BANCO_SQLITE", "data/x.db")
    assert config.caminho("BANCO_SQLITE") == config.RAIZ / "data" / "x.db"


def test_carregar_env_nao_sobrescreve_e_ignora_desconhecidas(tmp_path, monkeypatch):
    monkeypatch.setenv("OLLAMA_MODELO", "do-ambiente")
    monkeypatch.delenv("OLLAMA_TIMEOUT", raising=False)
    monkeypatch.delenv("SEGREDO_QUALQUER", raising=False)
    env = tmp_path / ".env"
    env.write_text("# comentário\nOLLAMA_MODELO=do-arquivo\nOLLAMA_TIMEOUT='30'\nSEGREDO_QUALQUER=x\n", encoding="utf-8")
    config.carregar_env(env)
    assert os.environ["OLLAMA_MODELO"] == "do-ambiente"
    assert os.environ["OLLAMA_TIMEOUT"] == "30"
    assert "SEGREDO_QUALQUER" not in os.environ
    monkeypatch.delenv("OLLAMA_TIMEOUT")
