"""Todos os guardrails do agente em um só lugar.

Camadas (na ordem em que são aplicadas):

    ENTRADA      entrada.py      G01 tamanho · G02 dados pessoais · G03 prompt injection
    ESCOPO       escopo.py       G04 comercial sem LLM · G05 fora do escopo
    PROMPT       prompts.py      regras no prompt de sistema do LLM
    SAÍDA        saida.py        G06–G13 conteúdo proibido · G14 tamanho
    REESCRITA    reescrita.py    G15 pergunta reescrita válida
    APRENDIZADO  aprendizado.py  G16–G19 o que pode ser gravado no banco

Documentação completa: docs/0013-Guardrails.md
"""

from app.guardrails.aprendizado import pode_gravar
from app.guardrails.entrada import (
    LIMITE_CARACTERES,
    ResultadoEntrada,
    eh_injecao,
    mascarar_dados_pessoais,
    verificar_entrada,
)
from app.guardrails.escopo import eh_fora_do_escopo, pode_usar_llm
from app.guardrails.reescrita import limpar_reescrita
from app.guardrails.saida import ResultadoSaida, verificar_saida

__all__ = [
    "LIMITE_CARACTERES",
    "ResultadoEntrada",
    "ResultadoSaida",
    "eh_fora_do_escopo",
    "eh_injecao",
    "limpar_reescrita",
    "mascarar_dados_pessoais",
    "pode_gravar",
    "pode_usar_llm",
    "verificar_entrada",
    "verificar_saida",
]
