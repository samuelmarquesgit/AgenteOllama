"""G26 — Política para perguntas técnicas de risco (RT-003).

Perguntas sobre eletricidade, solda, discos de corte, proteções, baterias de lítio danificadas,
superaquecimento e produtos químicos só podem ser respondidas com conteúdo da base de conhecimento.
Se a base não cobrir a pergunta, o Tork NÃO consulta a IA generativa nem reaproveita sugestões não
revisadas: encaminha para o manual, um profissional habilitado ou um atendente.
"""

import re

from app.busca import normalizar

# tema -> padrão sobre o texto normalizado (minúsculas, sem acento)
TEMAS_RISCO: dict[str, re.Pattern] = {
    "eletricidade": re.compile(
        r"\b(tomada|tomadas|fiacao|fio eletrico|energia|energizad\w*|choque|disjuntor|quadro de (luz|energia)"
        r"|rede eletrica|instalacao eletrica|desligar a (luz|energia)|tensao|alta voltagem|curto)\b"),
    "solda": re.compile(r"\b(sold\w*|eletrodo\w*|mascara de solda|arco eletrico)\b"),
    "disco_e_corte": re.compile(r"\b(disco\w*|esmerilh\w*|rebolo\w*|lixadeira angular|serra\w* (circular|marmore))\b"),
    "protecao": re.compile(r"\b(protecao|protecoes|capa de protecao|guarda de protecao|sem (a )?protecao|sem oculos|sem luva\w*|luva\w*)\b"),
    "bateria_litio": re.compile(r"\b(litio|bateria\w* (inchad\w*|estufad\w*|furad\w*|danificad\w*|vazand\w*)|abrir a bateria|celulas?)\b"),
    "superaquecimento": re.compile(r"\b(fumaca|queimad\w*|faisca\w*|superaquec\w*|pegando fogo|derretend\w*)\b"),
    "quimicos": re.compile(r"\b(solvente\w*|decapante\w*|acido\w*|thinner|removedor quimico)\b"),
}

NOTA_MINIMA_RISCO = 0.3  # com tema de risco, aceita FAQ (de risco médio/alto) com nota um pouco menor

# Ações perigosas: sempre encaminhadas, mesmo que alguma FAQ pareça próxima.
ACAO_PERIGOSA = re.compile(
    r"\b((abrir|desmontar|consertar|reparar|recondicionar)\b.{0,30}\b(bateria\w*|celula\w*|carregador\w*|fonte\w*)"
    r"|sem (desligar|cortar|tirar) (a |o )?(energia|luz|disjuntor|chave|tomada)"
    r"|com (a )?(energia|luz) ligada|energizad\w*|fazer (um )?gato|jumpe\w*"
    r"|(retirar|remover|tirar|desativar|anular)\b.{0,20}\b(protecao|trava|sensor|capa)\b.{0,40}\b(para|pra)\b)"
)

RESPOSTA_RISCO_SEM_BASE = (
    "Essa dúvida envolve risco de segurança ({tema}). Para sua proteção, não vou responder sem uma orientação "
    "técnica validada. Consulte o manual do fabricante ou um profissional habilitado. Se quiser, posso chamar "
    "um atendente da loja."
)

REFORCO_RISCO = (
    "\n\n⚠️ Assunto de segurança: confira sempre o manual do fabricante e, na dúvida, procure um profissional habilitado."
)

NOMES_TEMAS = {
    "eletricidade": "eletricidade", "solda": "solda", "disco_e_corte": "discos e corte",
    "protecao": "equipamentos de proteção", "bateria_litio": "baterias de lítio",
    "superaquecimento": "superaquecimento", "quimicos": "produtos químicos",
}


def tema_de_risco(texto: str) -> str | None:
    normalizado = normalizar(texto)
    return next((tema for tema, padrao in TEMAS_RISCO.items() if padrao.search(normalizado)), None)


def acao_perigosa(texto: str) -> bool:
    return bool(ACAO_PERIGOSA.search(normalizar(texto)))


def resposta_sem_base(tema: str) -> str:
    return RESPOSTA_RISCO_SEM_BASE.format(tema=NOMES_TEMAS.get(tema, tema))
