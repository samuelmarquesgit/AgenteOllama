"""Busca simples na FAQ: normalização de texto + pontuação por palavras-chave.

Sem banco de dados e sem embeddings. Cada FAQ recebe uma nota de 0 a 1 que
mede quanto da pergunta do cliente foi "coberta" pelas palavras da FAQ.
"""

import json
import re
import unicodedata
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from pathlib import Path

CAMINHO_FAQ = Path(__file__).resolve().parent.parent / "knowledge" / "faq.json"

# Palavras que não ajudam a identificar o assunto da pergunta.
STOPWORDS = {
    "a", "o", "as", "os", "um", "uma", "uns", "umas", "de", "da", "do", "das", "dos",
    "em", "no", "na", "nos", "nas", "para", "pra", "pro", "por", "com", "e", "ou",
    "que", "qual", "quais", "quando", "onde", "como", "porque", "se", "eu", "me", "mim",
    "meu", "minha", "meus", "minhas", "voce", "voces", "vcs", "vc", "ele", "ela", "isso",
    "esse", "essa", "este", "esta", "isto", "aqui", "ai", "la", "ja", "nao", "sim", "muito",
    "mais", "menos", "bem", "tambem", "so", "ser", "sao", "estar", "esta", "ter",
    "posso", "pode", "podem", "devo", "deve", "usar", "uso", "utilizar", "preciso",
    "quero", "queria", "gostaria", "fazer", "faco", "sobre", "favor", "ola", "oi",
    "bom", "boa", "dia", "tarde", "noite", "obrigado", "obrigada", "tudo", "algum",
    "alguma", "ferramenta", "ferramentas", "coisa", "entre", "ao", "aos", "saber",
}

SAUDACOES = {"oi", "ola", "bom dia", "boa tarde", "boa noite", "e ai", "opa", "hello"}


def normalizar(texto: str) -> str:
    """Minúsculas, sem acentos, só letras/números e espaços simples."""
    texto = texto.lower().replace("r$", " reais ")
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    texto = re.sub(r"[^a-z0-9]+", " ", texto)
    return " ".join(texto.split())


def _radical(palavra: str) -> str:
    """Stemming bem leve: tira plural simples ("brocas" -> "broca")."""
    if len(palavra) > 4 and palavra.endswith("oes"):
        return palavra[:-3] + "ao"
    if len(palavra) > 3 and palavra.endswith("s") and not palavra.endswith("ss"):
        return palavra[:-1]
    return palavra


VOLTAGENS = {"110", "127", "220", "380"}


def tokens(texto: str) -> set[str]:
    """Palavras relevantes (sem stopwords e sem números soltos como "300").

    Voltagens comuns escritas sem a unidade ("220") viram "220v".
    """
    resultado = set()
    for p in normalizar(texto).split():
        if p in VOLTAGENS:
            resultado.add(p + "v")
        elif p not in STOPWORDS and not p.isdigit():
            resultado.add(_radical(p))
    return resultado


def _parecido(a: str, b: str) -> bool:
    """Tolera erros simples de digitação em palavras de 5+ letras."""
    if a == b:
        return True
    if len(a) < 5 or len(b) < 5:
        return False
    return SequenceMatcher(None, a, b).ratio() >= 0.84


def _bate(token: str, conjunto: set[str]) -> bool:
    return token in conjunto or any(_parecido(token, t) for t in conjunto)


@dataclass
class Faq:
    id: str
    categoria: str
    pergunta: str
    resposta: str
    palavras_chave: list[str]
    variacoes: list[str] = field(default_factory=list)
    status: str = "rascunho"
    nivel_risco: str = "baixo"
    # calculados
    tokens_chave: set[str] = field(default_factory=set)
    tokens_texto: set[str] = field(default_factory=set)

    def __post_init__(self):
        for chave in self.palavras_chave:
            self.tokens_chave |= tokens(chave)
        self.tokens_texto = tokens(" ".join([self.pergunta, *self.variacoes]))

    @property
    def comercial(self) -> bool:
        return self.categoria == "atendimento_comercial"


@dataclass
class Resultado:
    faq: Faq
    nota: float


def montar_faqs(dados: list[dict]) -> list[Faq]:
    """Converte linhas do banco (ou do JSON) em objetos Faq."""
    campos = Faq.__dataclass_fields__
    return [
        Faq(**{k: v for k, v in item.items() if k in campos and k not in ("tokens_chave", "tokens_texto")})
        for item in dados
        if item.get("status") != "inativo"
    ]


def carregar_faq(caminho: Path = CAMINHO_FAQ) -> list[Faq]:
    return montar_faqs(json.loads(caminho.read_text(encoding="utf-8")))


def pesos(pergunta: str, faq: Faq) -> dict[str, float]:
    """Quanto cada palavra da pergunta foi coberta pela FAQ (1 = palavra-chave)."""
    cobertura = {}
    for t in tokens(pergunta):
        if _bate(t, faq.tokens_chave):
            cobertura[t] = 1.0
        elif _bate(t, faq.tokens_texto):
            cobertura[t] = 0.6
    return cobertura


def eh_identica(pergunta: str, faq: Faq) -> bool:
    """A pergunta é exatamente a pergunta cadastrada ou uma das variações?"""
    return normalizar(pergunta) in (normalizar(faq.pergunta), *map(normalizar, faq.variacoes))


def pontuar(pergunta: str, faq: Faq) -> float:
    """Nota 0..1: fração da pergunta coberta pela FAQ (palavra-chave vale mais)."""
    q = tokens(pergunta)
    if not q:
        return 0.0
    if eh_identica(pergunta, faq):
        return 1.0
    return round(sum(pesos(pergunta, faq).values()) / len(q), 3)


def nota_combinada(pergunta: str, faqs: list[Faq]) -> float:
    """Cobertura da pergunta somando várias FAQs (cada palavra conta uma vez)."""
    q = tokens(pergunta)
    if not q:
        return 0.0
    melhor: dict[str, float] = {}
    for f in faqs:
        for t, p in pesos(pergunta, f).items():
            melhor[t] = max(melhor.get(t, 0.0), p)
    return round(sum(melhor.values()) / len(q), 3)


def buscar(pergunta: str, faqs: list[Faq], limite: int = 3) -> list[Resultado]:
    q = tokens(pergunta)
    resultados = [Resultado(f, pontuar(pergunta, f)) for f in faqs]
    resultados = [r for r in resultados if r.nota > 0]
    # Empate: pergunta idêntica à cadastrada primeiro; depois FAQ comercial (evita
    # parecer que informamos preço/estoque); depois a que cobriu mais palavras-chave.
    resultados.sort(
        key=lambda r: (r.nota, eh_identica(pergunta, r.faq), r.faq.comercial, len(q & r.faq.tokens_chave)),
        reverse=True,
    )
    return resultados[:limite]


def eh_saudacao(pergunta: str) -> bool:
    return normalizar(pergunta) in SAUDACOES
