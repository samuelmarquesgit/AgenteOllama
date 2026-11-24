"""Intenções respondidas com DADOS DO BANCO (nunca pelo LLM):

- Catálogo (I02/I14): "quanto custa uma furadeira de impacto 220V?", "tem parafusadeira até R$ 600?"
- Loja (I13/I19): horário, endereço e formas de pagamento.

A detecção é por regras sobre o texto normalizado: previsível e testável (decisão D021).
"""

import re
from dataclasses import dataclass, field

from app.busca import normalizar
from app.db.repositorios import CatalogoRepository, FiltroProdutos, LojaRepository

AVISO_DEMO = "Preços e estoques fictícios (catálogo de demonstração)."

# Ordem importa: termos mais específicos primeiro.
TERMOS_CATEGORIA: list[tuple[str, str, str]] = [
    # (regex sobre o texto normalizado, código da categoria, nome legível)
    (r"\bfuradei?ras? de impacto\b|\bimpacto\b", "furadeiras_impacto", "furadeiras de impacto"),
    (r"\bmartelet(e|es)\b|\brompedor", "marteletes", "marteletes"),
    (r"\b(a?parafus|parafuz)adei?ras?\b|\baparafusadoras?\b", "parafusadeiras", "parafusadeiras"),
    (r"\besmerilhadei?ras?\b|\blixadeiras? angular", "esmerilhadeiras", "esmerilhadeiras"),
    (r"\bserras? circular", "serras_circulares", "serras circulares"),
    (r"\btico ?tico\b", "serras_tico_tico", "serras tico-tico"),
    (r"\blixadei?ras?\b", "lixadeiras", "lixadeiras"),
    (r"\bfuradei?ras?\b", "furadeiras", "furadeiras"),
    (r"\bbrocas?\b", "brocas", "brocas"),
    (r"\bdiscos?\b", "discos", "discos"),
    (r"\bbits?\b|\bponteiras?\b|\bpontas\b", "bits_pontas", "bits e pontas"),
    (r"\blaminas?\b", "laminas_serra", "lâminas de serra"),
    (r"\bcarregador(es)?\b", "carregadores", "carregadores"),
    (r"\bmultimetros?\b|\balicates? amperimetro", "multimetros", "multímetros"),
    (r"\btrenas?\b|\bnive(l|is) (a )?laser\b", "medidores_laser", "trenas e níveis a laser"),
    (r"\boculos\b|\bluvas?\b|\bprotetor(es)? auricular|\bmascaras?\b|\bepi\b", "epi", "equipamentos de proteção"),
    (r"\bcompressor(es)?\b", "compressores", "compressores"),
    (r"\blavadoras?\b|\blava ?jato\b|\balta pressao\b", "lavadoras_alta_pressao", "lavadoras de alta pressão"),
    (r"\bserras?\b", "SERRAS", "serras"),
    (r"\bbaterias?\b", "baterias", "baterias"),
]

SINAIS_COMPRA = re.compile(
    r"\b(precos?|quanto custa|quanto (e|sai|ta|esta)|custa|valor(es)?|compra(r)?|quero|procuro|procurando"
    r"|tem|tens|tem ai|vende(m)?|voces tem|estoque|disponive(l|is)|opcoes|opcao|modelos?|mostr(a|e|ar)"
    r"|baratas?|baratos?|mais em conta|catalogo|encontrar um produto|ate reais|ate \d+)\b"
)

MARCAS_REAIS = ["bosch", "makita", "dewalt", "stanley", "black decker", "vonder", "tramontina",
                "milwaukee", "wap", "karcher", "einhell", "skil", "worx", "ryobi"]

INTENCOES_LOJA = {
    # "como funciona a furadeira?" NÃO é horário: só "funcionamento" ou "loja ... aberta" contam.
    "horario": re.compile(r"\b(horarios?|abre(m)?|fecha(m)?|funcionamento|que horas"
                          r"|(loja|voces) (esta|estao|fica|ficam) abert\w*)\b"),
    "endereco": re.compile(r"\b(endereco|enderecos|onde (fica|ficam|voces ficam|e a loja)|localizacao|como chego|unidades|filia(l|is))\b"),
    "pagamento": re.compile(r"\b(pagamento|pagar|pix|cartao|cartoes|boleto|parcel\w*|formas? de pagamento)\b"),
}
# Mensagens com estes termos são de outro assunto (ex.: "trocar na loja física" não é pedido de endereço).
EXCLUI_LOJA = re.compile(r"\b(troca(r)?|devolu|garantia|pedido|frete|entrega)\b")


@dataclass
class IntencaoProduto:
    filtro: FiltroProdutos
    nome_categoria: str
    marca_real: str | None = None
    voltagem_informada: bool = False


@dataclass
class RespostaDados:
    texto: str
    origem: str                      # "catalogo" | "loja"
    produtos: list[dict] = field(default_factory=list)
    guardrails: list[str] = field(default_factory=list)


def _reais(centavos: int) -> str:
    inteiro, cent = divmod(int(centavos), 100)
    return f"R$ {inteiro:,}".replace(",", ".") + f",{cent:02d}"


COM_FIO = ["127V", "220V", "bivolt"]
REGRAS_ALIMENTACAO: list[tuple[str, list[str]]] = [
    (r"\b(a bateria|sem fio|cordless)\b", ["bateria"]),
    (r"\bbivolt\b", ["bivolt"]),
    (r"\b220 ?v?\b", ["220V", "bivolt"]),
    (r"\b(127|110) ?v?\b", ["127V", "bivolt"]),
    (r"\bcom fio\b", COM_FIO),
]
PRECO_MAXIMO = re.compile(r"\b(?:ate|menos de|abaixo de|no maximo|max)\s+(?:reais\s+)?(\d{2,6})\b")


def _categorias(texto: str) -> tuple[list[str], str | None]:
    """Categorias citadas no texto (com as exceções: 'a bateria', 'serra' genérica, 'furadeira de impacto')."""
    categorias: list[str] = []
    nome = None
    for padrao, codigo, legivel in TERMOS_CATEGORIA:
        if not re.search(padrao, texto) or _ignorar_categoria(codigo, categorias):
            continue
        categorias += ["serras_circulares", "serras_tico_tico"] if codigo == "SERRAS" else [codigo]
        nome = nome or legivel
    return categorias, nome


def _ignorar_categoria(codigo: str, ja_encontradas: list[str]) -> bool:
    if codigo == "baterias":
        return bool(ja_encontradas)  # "parafusadeira a bateria": bateria é a alimentação, não a categoria
    if codigo == "SERRAS":
        return any(c.startswith("serras") for c in ja_encontradas)
    return codigo == "furadeiras" and "furadeiras_impacto" in ja_encontradas


def _alimentacao(texto: str, categorias: list[str]) -> list[str]:
    if "bateria" in texto and "baterias" not in categorias:
        return ["bateria"]
    return next((valor for padrao, valor in REGRAS_ALIMENTACAO if re.search(padrao, texto)), [])


def _preco_maximo(texto: str) -> int | None:
    m = PRECO_MAXIMO.search(texto)
    return int(m.group(1)) * 100 if m else None


def _marca_citada(texto: str, marcas: list[str]) -> str | None:
    return next((mc for mc in marcas if re.search(rf"\b{re.escape(normalizar(mc))}\b", texto)), None)


def detectar_produto(pergunta: str, marcas_catalogo: list[str]) -> IntencaoProduto | None:
    texto = normalizar(pergunta)
    if not SINAIS_COMPRA.search(texto):
        return None
    categorias, nome = _categorias(texto)
    if not categorias:
        return None
    alimentacao = _alimentacao(texto, categorias)
    return IntencaoProduto(
        filtro=FiltroProdutos(categorias=categorias, alimentacao=alimentacao,
                              marca=_marca_citada(texto, marcas_catalogo), preco_max_centavos=_preco_maximo(texto)),
        nome_categoria=nome or "produtos",
        marca_real=_marca_citada(texto, MARCAS_REAIS),
        voltagem_informada=bool(alimentacao) and alimentacao != COM_FIO,
    )


def produto_publico(p: dict) -> dict:
    return {
        "sku": p["sku"], "nome": p["nome"], "marca": p["marca"], "categoria": p["categoria"],
        "alimentacao": p["alimentacao"], "preco": p["preco_centavos"] / 100, "preco_formatado": _reais(p["preco_centavos"]),
        "em_estoque": p["estoque_total"] > 0, "imagem": p["imagem"],
        "especificacoes": [{"nome": e["nome"], "valor": e["valor"], "unidade": e["unidade"]} for e in p["especificacoes"]],
    }


def responder_produto(intencao: IntencaoProduto, repo: CatalogoRepository) -> RespostaDados:
    produtos = repo.buscar(intencao.filtro)
    total = repo.contar(intencao.filtro)
    guardrails = ["G24:dado_do_catalogo"]
    linhas = []
    if intencao.marca_real:
        linhas.append(f"No catálogo de demonstração não temos a marca {intencao.marca_real.title()}, "
                      "mas estas opções equivalentes podem ajudar:")
    if not produtos:
        texto = (f"Não encontrei {intencao.nome_categoria} com esses filtros no catálogo de demonstração. "
                 "Quer tentar outra faixa de preço ou voltagem, ou falar com um atendente?")
        return RespostaDados(" ".join(linhas + [texto]), "catalogo", [], guardrails)

    if not intencao.marca_real:
        linhas.append(f"Encontrei {total} {'opção' if total == 1 else 'opções'} de {intencao.nome_categoria}. "
                      f"{'Esta é a de' if len(produtos) == 1 else f'Estas são as {len(produtos)} de'} melhor preço:")
    for p in produtos:
        estoque = "em estoque" if p["estoque_total"] > 0 else "sem estoque no momento"
        linhas.append(f"• {p['nome']}: {_reais(p['preco_centavos'])} ({estoque})")

    com_fio = any(p["alimentacao"] in ("127V", "220V") for p in produtos)
    if com_fio and not intencao.voltagem_informada:  # G20
        linhas.append("Essas ferramentas são com fio: confirme a voltagem da sua tomada (127 V ou 220 V) "
                      "antes de comprar. Posso filtrar por voltagem se você me disser.")
        guardrails.append("G20:confirmar_voltagem")
    linhas.append(AVISO_DEMO)
    return RespostaDados("\n".join(linhas), "catalogo", [produto_publico(p) for p in produtos], guardrails)


def detectar_loja(pergunta: str) -> str | None:
    texto = normalizar(pergunta)
    if EXCLUI_LOJA.search(texto):
        return None
    for nome, padrao in INTENCOES_LOJA.items():
        if padrao.search(texto):
            return nome
    return None


def responder_loja(intencao: str, repo: LojaRepository) -> RespostaDados:
    if intencao == "horario":
        linhas = ["Nossos horários:"] + [f"• {u['nome']}: {repo.horario_legivel(u['horarios'])}." for u in repo.unidades()]
        if all(0 not in [h["dia_semana"] for h in u["horarios"]] for u in repo.unidades()):
            linhas.append("Aos domingos as lojas ficam fechadas.")
    elif intencao == "endereco":
        linhas = ["Nossas unidades:"] + [
            f"• {u['nome']}: {u['logradouro']}, {u['numero']}, {u['bairro']}, {u['cidade']}/{u['uf']}, CEP {u['cep']}."
            + (f" Mapa: {u['link_mapa']}" if u["link_mapa"] else "")
            for u in repo.unidades()
        ]
    else:  # pagamento
        formas = repo.formas_pagamento()
        politica = repo.politica("pagamento")
        linhas = [f"Aceitamos: {', '.join(formas[:-1])} e {formas[-1]}." if len(formas) > 1 else f"Aceitamos: {formas[0]}."]
        if politica:
            linhas.append(politica["texto"])
        linhas.append("Não peço dados de cartão ou pagamento neste chat.")
    linhas.append("(Dados fictícios de demonstração.)")
    return RespostaDados("\n".join(linhas), "loja")
