"""Testes da página de chat (estáticos) e da versão de terminal (agente.py)."""

import os
import subprocess
import sys

from tests.conftest import N_FAQS, RAIZ

HTML = (RAIZ / "static" / "index.html").read_text(encoding="utf-8")


# ---- página de chat -----------------------------------------------------------
def test_pagina_usa_endpoints_da_api():
    assert 'fetch("/chat"' in HTML
    assert 'fetch("/health")' in HTML


def test_pagina_tem_aviso_de_versao_inicial():
    assert "não consulto preços, estoque" in HTML


def test_pagina_limita_tamanho_igual_a_api():
    assert 'maxlength="500"' in HTML


def test_pagina_tem_selos_de_origem():
    for origem in ["banco:", "agente:", "fallback:", "fora_do_escopo:", "saudacao:"]:
        assert origem in HTML


def test_pagina_acessivel():
    assert 'lang="pt-BR"' in HTML
    assert 'name="viewport"' in HTML
    assert 'aria-label="Sua mensagem"' in HTML
    assert 'aria-live="polite"' in HTML


def test_pagina_nao_usa_innerhtml_com_texto_do_usuario():
    # textContent/createTextNode evitam injeção de HTML vinda das respostas.
    assert "createTextNode(texto)" in HTML
    assert HTML.count("innerHTML") == 1  # só para limpar a conversa
    assert 'innerHTML = ""' in HTML


def test_pagina_tem_estado_de_carregamento_e_erro():
    assert "Respondendo..." in HTML
    assert "Não consegui responder agora" in HTML


# ---- versão de terminal -------------------------------------------------------
def _rodar_cli(entrada, tmp_path):
    env = {**os.environ, "BANCO_SQLITE": str(tmp_path / "cli.db"), "USAR_OLLAMA": "false",
           "PYTHONIOENCODING": "utf-8"}
    return subprocess.run(
        [sys.executable, "agente.py"], input=entrada, capture_output=True, text=True,
        encoding="utf-8", cwd=RAIZ, env=env, timeout=60,
    )


def test_cli_responde_e_encerra(tmp_path):
    r = _rodar_cli("Qual broca usar em concreto?\n\nsair\n", tmp_path)
    assert r.returncode == 0, r.stderr
    assert f"{N_FAQS} perguntas no banco" in r.stdout
    assert "📚 banco" in r.stdout
    assert "SDS-plus" in r.stdout


def test_cli_sem_ollama_usa_fallback(tmp_path):
    r = _rodar_cli("Como funciona uma tupia de bancada?\nsair\n", tmp_path)
    assert r.returncode == 0, r.stderr
    assert "sem resposta" in r.stdout


def test_pagina_monta_cards_de_produto_com_seguranca():
    assert "function montarCards" in HTML
    assert "dados.produtos" in HTML
    assert 'catalogo: ["catalogo"' in HTML and 'loja: ["loja"' in HTML


def test_pagina_diferencia_resposta_nao_revisada_do_banco():
    assert 'sugestao: ["sugestao"' in HTML
    assert "ainda não revisada" in HTML
