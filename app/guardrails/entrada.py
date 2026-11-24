"""Guardrails de ENTRADA: o que o cliente envia, antes de qualquer processamento.

- G01 Tamanho: mensagem vazia ou com mais de LIMITE_CARACTERES é rejeitada.
- G02 Dados pessoais: CPF, CNPJ, cartão, e-mail, telefone e CEP são mascarados
      ANTES de chegar ao LLM, ao banco, à memória da conversa ou ao log.
- G03 Prompt injection: tentativas de mudar as regras do agente são bloqueadas.
"""

import re
from dataclasses import dataclass, field

from app.busca import normalizar

LIMITE_CARACTERES = 500

# Ordem importa: padrões mais específicos primeiro.
PADROES_DADOS_PESSOAIS: list[tuple[str, re.Pattern]] = [
    ("email", re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")),
    ("cnpj", re.compile(r"\b\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}\b")),
    ("cpf", re.compile(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b")),
    ("cartao", re.compile(r"\b(?:\d[ -]?){12,18}\d\b")),
    ("telefone", re.compile(r"(?:\(?\b\d{2}\)?\s?)?\b9?\d{4}[-\s]?\d{4}\b")),
    ("cep", re.compile(r"\b\d{5}-\d{3}\b")),
]

ROTULOS = {
    "email": "[e-mail removido]",
    "cnpj": "[CNPJ removido]",
    "cpf": "[CPF removido]",
    "cartao": "[cartão removido]",
    "telefone": "[telefone removido]",
    "cep": "[CEP removido]",
}

# Frases (já normalizadas: sem acento, minúsculas) típicas de prompt injection.
PADROES_INJECAO = [
    r"\bignor\w* (as |todas as |suas |essas |tod\w+ )*(instruc|regra|orientac)",
    r"\besquec\w* (as |todas as |suas )*(instruc|regra)",
    r"\bdesconsider\w* (as |todas as |suas )*(instruc|regra)",
    r"\b(prompt|instrucoes) (do|de) sistema\b",
    r"\bsystem prompt\b",
    r"\b(revel|mostr|repit)\w* (o |as |suas |seu )*(prompt|instruc)",
    r"\bvoce agora (e|sera)\b",
    r"\ba partir de agora voce\b",
    r"\bfinja (que|ser)\b",
    r"\bmodo (desenvolvedor|dev|deus|sem restric)",
    r"\bjailbreak\b",
    r"\bignore (all|previous|the above)\b",
    r"\b(act|pretend) as\b",
    r"\bsem (filtro|restric|regra)s?\b",
]


@dataclass
class ResultadoEntrada:
    permitido: bool
    texto: str                      # mensagem já higienizada (use SEMPRE esta)
    motivo: str | None = None       # "vazia" | "muito_longa" | "injecao"
    dados_pessoais: list[str] = field(default_factory=list)


def mascarar_dados_pessoais(texto: str) -> tuple[str, list[str]]:
    """Troca dados pessoais por rótulos. Devolve (texto, tipos encontrados)."""
    encontrados = []
    for tipo, padrao in PADROES_DADOS_PESSOAIS:
        texto, n = padrao.subn(ROTULOS[tipo], texto)
        if n:
            encontrados.append(tipo)
    return texto, encontrados


def remover_rotulos(texto: str) -> str:
    """Tira os rótulos "[CPF removido]" etc. (eles atrapalham a busca e o LLM)."""
    for rotulo in ROTULOS.values():
        texto = texto.replace(rotulo, " ")
    texto = re.sub(r"\b(meu|minha|o|a)\s+(cpf|cnpj|cartao|cartão|e-?mail|telefone|whats\w*|cep)\s+(e|é|eh)?\s*[,:]?", " ", texto, flags=re.I)
    return " ".join(texto.split()).strip(" ,;:")


def eh_injecao(texto: str) -> bool:
    normalizado = normalizar(texto)
    return any(re.search(p, normalizado) for p in PADROES_INJECAO)


def verificar_entrada(texto: str) -> ResultadoEntrada:
    texto = (texto or "").strip()
    if not texto:
        return ResultadoEntrada(False, "", "vazia")
    if len(texto) > LIMITE_CARACTERES:
        return ResultadoEntrada(False, "", "muito_longa")

    texto, dados = mascarar_dados_pessoais(texto)
    if eh_injecao(texto):
        return ResultadoEntrada(False, texto, "injecao", dados)
    return ResultadoEntrada(True, texto, None, dados)
