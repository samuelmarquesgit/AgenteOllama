"""Testes da página de chat (estáticos) e da versão de terminal (agente.py)."""

import os
import subprocess
import sys

from tests.conftest import N_FAQS, RAIZ

HTML = (RAIZ / "static" / "index.html").read_text(encoding="utf-8")
JS = (RAIZ / "static" / "js" / "chat.js").read_text(encoding="utf-8")
CSS = (RAIZ / "static" / "css" / "chat.css").read_text(encoding="utf-8")
TOKENS = (RAIZ / "static" / "css" / "tokens.css").read_text(encoding="utf-8")
FRONT = HTML + JS + CSS + TOKENS


# ---- página de chat -----------------------------------------------------------
def test_pagina_carrega_css_e_js_locais():
    for recurso in ["/static/css/tokens.css", "/static/css/chat.css", "/static/js/chat.js", "/static/brand/favicon.svg"]:
        assert recurso in HTML
        assert (RAIZ / recurso.lstrip("/")).exists()


def test_pagina_nao_depende_de_internet():
    # Nada de CDN: fontes, ícones e scripts são servidos pela própria API (demo funciona offline).
    assert "http://" not in FRONT
    assert "https://" not in FRONT
    for fonte in ["inter-latin-400-normal.woff2", "barlow-semi-condensed-latin-700-normal.woff2"]:
        assert fonte in TOKENS
        assert (RAIZ / "static" / "fonts" / fonte).exists()


def test_pagina_usa_endpoints_da_api():
    for endpoint in ['chat: "/chat"', 'health: "/health"', 'conversas: "/conversas"', 'avaliacoes: "/avaliacoes"']:
        assert endpoint in JS


def test_pagina_tem_aviso_de_dados_ficticios_e_privacidade():
    assert "produtos, preços e estoques são fictícios" in HTML
    assert "Não envie dados pessoais" in HTML


def test_pagina_limita_tamanho_igual_a_api():
    assert 'maxlength="500"' in HTML


def test_pagina_tem_selos_de_todas_as_origens():
    for origem in ["banco", "catalogo", "loja", "agente", "sugestao", "fallback", "fora_do_escopo", "saudacao", "bloqueado"]:
        assert f'{origem}: ["' in JS


def test_pagina_acessivel():
    assert 'lang="pt-BR"' in HTML
    assert 'name="viewport"' in HTML
    assert 'aria-label="Sua mensagem"' in HTML
    assert 'aria-live="polite"' in HTML
    assert 'role="log"' in HTML
    assert "prefers-reduced-motion" in CSS
    assert ":focus-visible" in CSS


def test_pagina_nao_insere_html_vindo_da_api():
    # textContent/createTextNode evitam injeção de HTML vinda das respostas.
    assert "createTextNode(texto)" in JS
    assert "innerHTML" not in JS
    assert "insertAdjacentHTML" not in JS
    assert "outerHTML" not in JS


def test_pagina_tem_estado_de_carregamento_e_erro():
    assert "Respondendo..." in JS
    assert "Não consegui responder agora" in JS
    assert "tork-avatar-alerta.svg" in JS


def test_pagina_tem_menu_inicial_e_categorias():
    for rotulo in ["Encontrar um produto", "Ajuda para escolher", "Pedido ou entrega", "Pagamento e parcelamento",
                   "Trocas e garantia", "Falar com um atendente"]:
        assert rotulo in JS
    assert "function mostrarCategorias" in JS
    assert 'texto.toLowerCase() === "menu"' in JS


def test_pagina_tem_avaliacao_e_tema():
    assert "function montarAvaliacao" in JS
    assert "aria-pressed" in JS
    assert "function alternarTema" in JS
    assert 'data-theme="dark"' in TOKENS
    assert "prefers-color-scheme: dark" in TOKENS


def test_id_de_conversa_usa_gerador_criptografico():
    assert "crypto.getRandomValues" in JS or "crypto.randomUUID" in JS
    assert "Math.random" not in JS


def test_cores_da_identidade_visual():
    for cor in ["#C2410C", "#EA580C", "#1C2128", "#F6F5F2"]:
        assert cor in TOKENS


def test_logos_para_tema_claro_e_escuro():
    assert (RAIZ / "static" / "brand" / "logo-toolexpert-escuro.svg").exists()
    assert "logo-escuro" in HTML
    assert "logo-claro" in HTML


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
    assert "function montarCards" in JS
    assert "dados.produtos" in JS
    assert "preco_formatado" in JS
    assert "em_estoque" in JS


def test_pagina_diferencia_resposta_nao_revisada_do_banco():
    assert 'sugestao: ["sugestao"' in JS
    assert "ainda não revisada" in JS
