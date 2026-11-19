"""Guardrails do APRENDIZADO: o que pode ser gravado no banco.

- G16 Só grava resposta do LLM que passou por TODOS os guardrails de saída.
- G17 Só grava pergunta com assunto identificável (ao menos 2 palavras relevantes),
      para não poluir a base com "e?", "ok", "hum".
- G18 Nunca grava pergunta que ainda contenha dado pessoal (mesmo mascarado).
- G19 Tudo que é gravado fica com status 'pendente_validacao' (ver app/banco.py).
"""

from app.busca import tokens
from app.guardrails.entrada import ROTULOS

MIN_PALAVRAS_RELEVANTES = 2

# Interjeições e respostas curtas que não identificam assunto nenhum.
SEM_ASSUNTO = {
    "ok", "okay", "hmm", "hm", "hum", "uhum", "eh", "beleza", "blz", "valeu", "vlw", "certo",
    "entendi", "legal", "show", "top", "kkk", "kkkk", "haha", "rs", "obrigad", "brigado",
    "perfeito", "otimo", "massa", "pode", "claro", "duvida", "pergunta", "outra",
}


def palavras_com_assunto(pergunta: str) -> set[str]:
    return {t for t in tokens(pergunta) if t not in SEM_ASSUNTO}


def pode_gravar(pergunta: str, resposta_aprovada: bool, tinha_dados_pessoais: bool = False) -> bool:
    if not resposta_aprovada or tinha_dados_pessoais:
        return False
    if any(rotulo in pergunta for rotulo in ROTULOS.values()):
        return False
    return len(palavras_com_assunto(pergunta)) >= MIN_PALAVRAS_RELEVANTES
