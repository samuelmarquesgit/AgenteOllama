"""Guardrails de ESCOPO.

- G04 Comercial sem LLM: perguntas de preço, estoque, frete, pagamento, garantia...
      só são respondidas com os textos fixos do banco; nunca passam pelo LLM.
- G05 Fora do escopo: se o LLM sinaliza FORA_DO_ESCOPO, o cliente recebe uma
      recusa educada e nada é gravado.
"""

from app.guardrails.prompts import FORA_DO_ESCOPO

CATEGORIAS_SEM_LLM = {"atendimento_comercial"}


def pode_usar_llm(categoria: str) -> bool:
    return categoria not in CATEGORIAS_SEM_LLM


def eh_fora_do_escopo(resposta_llm: str | None) -> bool:
    return bool(resposta_llm) and FORA_DO_ESCOPO in resposta_llm
