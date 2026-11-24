"""Guardrails de SAÍDA: verificam a resposta gerada pelo LLM antes de enviá-la
ao cliente e antes de gravá-la no banco.

Se alguma regra for violada, a resposta é descartada (não vai para o cliente
nem para o banco) e o cliente recebe RESPOSTA_BLOQUEADA_SAIDA.

- G06 Preço inventado         ("R$ 299", "por 300 reais")
- G07 Estoque inventado       ("temos em estoque", "pronta entrega")
- G08 Prazo de entrega        ("entregamos em 2 dias", "chega em 24 horas")
- G09 Garantia inventada      ("garantia de 2 anos")
- G10 Promoção inventada      ("20% de desconto", "cupom")
- G11 Pedido de dados pessoais ("informe seu CPF", "digite o número do cartão")
- G12 Conselho perigoso       ("retire a proteção", "use sem a proteção", "faça um gato")
- G13 Contato/link inventado  (URLs, e-mails e telefones)
- G14 Tamanho máximo          (respostas longas são cortadas no fim de uma frase)
"""

import re
from dataclasses import dataclass, field

from app.guardrails.entrada import mascarar_dados_pessoais

TAMANHO_MAXIMO = 900

NEGACOES = ("nunca", "não", "nao", "jamais", "evite", "sem nunca", "proibido", "não deve", "nao deve")

REGRAS: list[tuple[str, re.Pattern, bool]] = [
    # (nome, padrão, aceita_negacao) — se aceita_negacao, "nunca retire a proteção" é permitido
    ("preco", re.compile(r"R\$\s*\d|\b\d+(?:[.,]\d+)?\s*reais\b", re.I), False),
    ("estoque", re.compile(r"\b(temos|tem|há|ha)\s+(?:\w+\s+){0,3}em\s+estoque\b|\bpronta[\s-]entrega\b|\bdisponível\s+em\s+estoque\b", re.I), True),
    ("prazo_entrega", re.compile(r"\b(entreg\w*|cheg\w*|envi\w*)\s+(?:\w+\s+){0,2}(em|até)\s+(até\s+)?\d+\s*(h|horas?|dias?|semanas?)\b", re.I), False),
    ("garantia", re.compile(r"\bgarantia\s+(de|por)\s+\d+\s*(dias?|mes(es)?|anos?)\b", re.I), False),
    ("promocao", re.compile(r"\b\d+\s*%\s*(de\s+)?(desconto|off)\b|\bcupom\s+[A-Z0-9]{4,}\b", re.I), False),
    ("pede_dados_pessoais", re.compile(
        r"\b(informe|envie|digite|passe|mande|forneça|forneca|me\s+diga)\b.{0,40}"
        r"\b(cpf|cnpj|cart[aã]o|senha|cvv|endere[cç]o|rg)\b", re.I), True),
    ("conselho_perigoso", re.compile(
        r"\b(retir\w*|remov\w*|tir\w*)\s+(?:\w+\s+){0,3}(prote[cç][aã]o|capa\s+de\s+prote|guarda)\b"
        r"|\bsem\s+a\s+prote[cç][aã]o\b|\bfa[zç]\w*\s+um\s+gato\b|\bjump(ear|er)\b", re.I), True),
    ("contato_inventado", re.compile(r"https?://|\bwww\.|[\w.+-]+@[\w-]+\.[\w.]+|\(?\b\d{2}\)?\s?9?\d{4}-\d{4}\b", re.I), False),
]


@dataclass
class ResultadoSaida:
    permitido: bool
    texto: str
    violacoes: list[str] = field(default_factory=list)


def _negado(texto: str, inicio: int) -> bool:
    """Há uma negação logo antes do trecho? ("nunca retire a proteção")"""
    janela = texto[max(0, inicio - 25):inicio].lower()
    return any(n in janela for n in NEGACOES)


def violacoes(texto: str) -> list[str]:
    encontradas = []
    for nome, padrao, aceita_negacao in REGRAS:
        for m in padrao.finditer(texto):
            if aceita_negacao and _negado(texto, m.start()):
                continue
            encontradas.append(nome)
            break
    return encontradas


def limitar_tamanho(texto: str, maximo: int = TAMANHO_MAXIMO) -> str:
    if len(texto) <= maximo:
        return texto
    corte = texto[:maximo]
    fim = max(corte.rfind(". "), corte.rfind("! "), corte.rfind("? "))
    return corte[: fim + 1] if fim > maximo // 2 else corte.rstrip() + "..."


def verificar_saida(texto: str | None) -> ResultadoSaida:
    if not texto or not texto.strip():
        return ResultadoSaida(False, "", ["vazia"])
    texto = texto.strip()
    encontradas = violacoes(texto)
    if encontradas:
        return ResultadoSaida(False, texto, encontradas)
    texto, _ = mascarar_dados_pessoais(texto)  # defesa extra: nunca devolver dado pessoal
    return ResultadoSaida(True, limitar_tamanho(texto))
