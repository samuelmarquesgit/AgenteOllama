"""Guardrail da REESCRITA de perguntas de continuação ("e para metal?").

- G15 A pergunta reescrita pelo LLM só é aceita se for uma única linha curta,
      sem aspas/prefixos, sem marcador de fora do escopo e sem tentativa de
      injeção. Caso contrário, usa-se a pergunta original do cliente.
"""

from app.guardrails.entrada import LIMITE_CARACTERES, eh_injecao, mascarar_dados_pessoais
from app.guardrails.prompts import FORA_DO_ESCOPO

PREFIXOS = ("pergunta reescrita:", "pergunta:", "reescrita:")


def limpar_reescrita(texto: str | None) -> str | None:
    if not texto or not texto.strip():
        return None
    linha = texto.strip().splitlines()[0].strip().strip('"“”\'').strip()
    for prefixo in PREFIXOS:
        if linha.lower().startswith(prefixo):
            linha = linha[len(prefixo):].strip().strip('"“”\'').strip()
    if not linha or len(linha) > LIMITE_CARACTERES or FORA_DO_ESCOPO in linha or eh_injecao(linha):
        return None
    linha, _ = mascarar_dados_pessoais(linha)
    return linha
