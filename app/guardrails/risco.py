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
    # "capa de protecao", "sem a protecao" e "sem luvas" já casam pelas palavras soltas
    "protecao": re.compile(r"\b(protecao|protecoes|sem oculos|luvas?)\b"),
    "bateria_litio": re.compile(r"\b(litio|celulas?|bateria\w*\b.{0,25}\b(inch|estuf|furad|danific|vaz)\w*)\b"),
    "carga_bateria": re.compile(r"\bcarreg\w*\b.{0,40}\b(noite toda|perto da cama|dormindo|sem supervisao)\b"),
    "superaquecimento": re.compile(r"\b(fumaca|queimad\w*|faisca\w*|superaquec\w*|pegando fogo|derret\w*)\b"),
    "quimicos": re.compile(r"\b(solvente\w*|decapante\w*|acido\w*|thinner|gasolina|alcool|querosene|cloro)\b"),
    "mistura_quimica": re.compile(r"\b(agua sanitaria|misturar (produtos|agua sanitaria|cloro))\b"),
    "criancas": re.compile(r"\b(criancas?|filh[oa]s?|sobrinh[oa]s?|net[oa]s?|menor de idade)\b"),
    "altura": re.compile(r"\b(telhado|andaime|escada|em altura|cinto de seguranca)\b"),
    "vaso_de_pressao": re.compile(r"\b(tanque|reservatorio)\b.{0,30}\b(enferruj|corroi|corroid|amassad|vaz)\w*"),
}

NOTA_MINIMA_RISCO = 0.3  # com tema de risco, aceita FAQ (de risco médio/alto) com nota um pouco menor

# Ações perigosas: sempre encaminhadas, mesmo que alguma FAQ pareça próxima. Avaliadas ANTES do catálogo.
# Uma regex por ideia, para manter cada padrão simples (e auditável).
ACOES_PERIGOSAS: tuple[re.Pattern, ...] = (
    re.compile(r"\b(abr(ir|o|i|indo)|desmont\w*|consert\w*|repar\w*|recondicion\w*)\b.{0,30}\b(bateria|celula|carregador|fonte)"),
    re.compile(r"\bsem (desligar|cortar|tirar) (a |o )?(energia|luz|disjuntor|chave|tomada)"),
    re.compile(r"\b(com (a )?(energia|luz) ligada|energizad\w*|fazer (um )?gato|jumpe\w*)"),
    re.compile(r"\b(retirar|remover|tirar|desativar|anular)\b.{0,20}\b(protecao|trava|sensor|capa)\b.{0,40}\b(para|pra)\b"),
    re.compile(r"\b(retirar|remover|tirar|desativar|anular)\b.{0,20}\btrava de seguranca"),
    re.compile(r"\b(funcionar|usar|ligar)\b.{0,30}\bsem (a |o )?(protecao|capa)\b"),
    re.compile(r"\b(travar|prender|amarrar)\b.{0,25}\b(gatilho|botao|interruptor)"),
    re.compile(r"\bsem (precisar )?(segurar|apertar) (o )?(gatilho|botao)"),
    re.compile(r"\bsem (a |o )?(mascara|cinto)\b"),
    re.compile(r"\badapt\w*\b.{0,15}\b(fios?|cabos?)\b"),
)

# Falhar fechado (análise crítica pós-v0.5.0): listar temas não generaliza. Pergunta que pede um JULGAMENTO
# de segurança/permissão ("posso...?", "ainda é seguro?", "deixo...?") e não tem FAQ não vai para a IA.
PEDIDOS_DE_JULGAMENTO: tuple[re.Pattern, ...] = (
    re.compile(r"^(posso|pode|podemos|da pra|da para|deixo|continuo|uso)\b"),
    re.compile(r"\b(e seguro|e perigoso|tem (problema|perigo|risco)|e normal|faz mal)\b"),
    re.compile(r"\b(ainda (posso|da|e|serve)|posso (continuar|usar assim|deixar)|assim mesmo)\b"),
)


def pede_julgamento_de_seguranca(texto: str) -> bool:
    normalizado = normalizar(texto)
    return any(padrao.search(normalizado) for padrao in PEDIDOS_DE_JULGAMENTO)


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
    "carga_bateria": "carga de baterias", "mistura_quimica": "mistura de produtos químicos",
    "criancas": "uso por crianças", "seguranca": "segurança", "julgamento": "segurança no uso", "altura": "trabalho em altura", "vaso_de_pressao": "reservatório sob pressão",
}


def tema_de_risco(texto: str) -> str | None:
    normalizado = normalizar(texto)
    return next((tema for tema, padrao in TEMAS_RISCO.items() if padrao.search(normalizado)), None)


def acao_perigosa(texto: str) -> bool:
    normalizado = normalizar(texto)
    return any(padrao.search(normalizado) for padrao in ACOES_PERIGOSAS)


def resposta_sem_base(tema: str) -> str:
    return RESPOSTA_RISCO_SEM_BASE.format(tema=NOMES_TEMAS.get(tema, tema))
