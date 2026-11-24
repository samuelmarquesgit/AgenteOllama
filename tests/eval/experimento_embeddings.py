"""RT-009: experimento ISOLADO de busca semântica/híbrida com embeddings (não altera o Tork).

Roda o mesmo conjunto da avaliação RT-008 (100 perguntas) pelo agente real, trocando apenas a função de
busca DENTRO deste processo:
  - textual   : busca atual (palavras-chave + radical + tolerância a erro de digitação)
  - semantica : só similaridade de cosseno entre embeddings (nomic-embed-text via Ollama)
  - hibrida   : textual primeiro; se a nota textual ficar abaixo do mínimo, aceita a FAQ semântica
                com cosseno >= limiar

Precisa do Ollama com `nomic-embed-text` (ollama pull nomic-embed-text). Não roda no pytest/CI.

Uso:  python -m tests.eval.experimento_embeddings            # escreve docs/eval/experimento-embeddings.md
"""

import math
import os
import statistics
import sys
import tempfile
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))
os.environ.setdefault("BANCO_SQLITE", str(Path(tempfile.mkdtemp()) / "experimento.db"))

import ollama  # noqa: E402

from app import agente as modulo_agente  # noqa: E402
from app.busca import Resultado, buscar as buscar_textual  # noqa: E402
from tests.eval import avaliar as avaliacao  # noqa: E402

MODELO_EMBEDDING = "nomic-embed-text"
LIMIARES = (0.60, 0.65, 0.70, 0.75, 0.80)
RELATORIO = RAIZ / "docs" / "eval" / "experimento-embeddings.md"
cliente = ollama.Client(host=os.getenv("OLLAMA_HOST") or None, timeout=60)


def _normalizado(v: list[float]) -> list[float]:
    n = math.sqrt(sum(x * x for x in v)) or 1.0
    return [x / n for x in v]


def embed(textos: list[str], prefixo: str) -> list[list[float]]:
    r = cliente.embed(model=MODELO_EMBEDDING, input=[prefixo + t for t in textos])
    return [_normalizado(v) for v in r["embeddings"]]


class IndiceSemantico:
    """Um vetor por pergunta cadastrada e por variação; a nota da FAQ é o maior cosseno."""

    def __init__(self, faqs):
        self.itens = []  # (faq, vetor)
        textos, donos = [], []
        for f in faqs:
            for t in (f.pergunta, *f.variacoes):
                textos.append(t)
                donos.append(f)
        for i in range(0, len(textos), 64):
            for faq, vetor in zip(donos[i:i + 64], embed(textos[i:i + 64], "search_document: ")):
                self.itens.append((faq, vetor))
        self.ids = {f.id for f in faqs}
        self.latencias_ms: list[float] = []

    def ranking(self, pergunta: str, faqs, limite: int) -> list[Resultado]:
        inicio = time.perf_counter()
        [q] = embed([pergunta], "search_query: ")
        self.latencias_ms.append((time.perf_counter() - inicio) * 1000)
        permitidas = {f.id for f in faqs}
        melhor: dict[str, tuple[float, object]] = {}
        for faq, vetor in self.itens:
            if faq.id in permitidas:
                cos = sum(a * b for a, b in zip(q, vetor))
                if cos > melhor.get(faq.id, (-1.0, None))[0]:
                    melhor[faq.id] = (cos, faq)
        ordem = sorted(melhor.values(), key=lambda x: x[0], reverse=True)[:limite]
        return [Resultado(faq, round(cos, 3)) for cos, faq in ordem]


def rodar(nome: str, buscar_substituta) -> dict:
    original = modulo_agente.buscar
    modulo_agente.buscar = buscar_substituta
    try:
        inicio = time.perf_counter()
        resultados = avaliacao.avaliar()
        duracao = (time.perf_counter() - inicio) * 1000 / len(resultados)
    finally:
        modulo_agente.buscar = original
    s = avaliacao.resumo(resultados)
    s.update(nome=nome, ms_por_pergunta=round(duracao, 1),
             erros=[f"{r.id} ({r.motivo})" for r in resultados if not r.acertou or r.perigosa])
    return s


def main() -> int:
    from app import banco
    from app.busca import montar_faqs
    from app.db.repositorios import FaqRepository

    con = banco.conectar()
    faqs = montar_faqs(FaqRepository(con).listar_para_busca())
    con.close()
    t0 = time.perf_counter()
    indice = IndiceSemantico(faqs)
    tempo_indice = time.perf_counter() - t0
    print(f"índice: {len(indice.itens)} vetores em {tempo_indice:.1f} s")

    def so_semantica(pergunta, lista, limite=3):
        if not lista or not ({f.id for f in lista} <= indice.ids):
            return buscar_textual(pergunta, lista, limite)  # listas fora do índice (ex.: sugestões)
        return indice.ranking(pergunta, lista, limite)

    def hibrida(limiar):
        def buscar(pergunta, lista, limite=3):
            textual = buscar_textual(pergunta, lista, limite)
            if (textual and textual[0].nota >= modulo_agente.NOTA_MINIMA) or not lista \
                    or not ({f.id for f in lista} <= indice.ids):
                return textual
            semantica = [r for r in indice.ranking(pergunta, lista, limite) if r.nota >= limiar]
            # nota "textual equivalente": entra no banco como resposta que pede confirmação
            return [Resultado(r.faq, modulo_agente.NOTA_MINIMA) for r in semantica[:1]] or textual
        return buscar

    execucoes = [rodar("textual (atual)", buscar_textual), rodar("semântica pura", so_semantica)]
    execucoes += [rodar(f"híbrida, cosseno ≥ {lim:.2f}", hibrida(lim)) for lim in LIMIARES]
    RELATORIO.write_text(relatorio(execucoes, indice, tempo_indice), encoding="utf-8")
    for e in execucoes:
        print(f"{e['nome']:<28} acertos {e['acertos']:>3}  perigosas {e['perigosas']}  {e['ms_por_pergunta']} ms")
    print(f"Relatório: {RELATORIO}")
    return 0


def relatorio(execucoes: list[dict], indice: IndiceSemantico, tempo_indice: float) -> str:
    grupos = list(execucoes[0]["grupos"])
    linhas = [
        "# RT-009 — Experimento de busca semântica/híbrida",
        "",
        f"> Gerado por `python -m tests.eval.experimento_embeddings` em {time.strftime('%Y-%m-%d %H:%M')}. "
        f"Modelo `{MODELO_EMBEDDING}` via Ollama local; mesmo conjunto de 100 perguntas da RT-008; "
        "o agente real é usado com a IA generativa substituída por um marcador. **Experimento isolado: o Tork "
        "continua usando a busca textual.**",
        "",
        f"Índice: {len(indice.itens)} vetores (pergunta + variações de cada FAQ) em {tempo_indice:.1f} s. "
        f"Latência do embedding por pergunta: mediana {statistics.median(indice.latencias_ms):.0f} ms, "
        f"p95 {sorted(indice.latencias_ms)[int(0.95 * len(indice.latencias_ms))]:.0f} ms.",
        "",
        "| Busca | Acertos | Perigosas | Foi para a IA | " + " | ".join(grupos) + " | ms/pergunta |",
        "|---|---|---|---|" + "---|" * len(grupos) + "---|",
    ]
    for e in execucoes:
        g = " | ".join(f"{a}/{t}" for a, t in e["grupos"].values())
        linhas.append(f"| {e['nome']} | **{e['acertos']}** | {e['perigosas']} | {e['foi_para_ia']} | {g} | "
                      f"{e['ms_por_pergunta']} |")
    linhas += ["", "## Erros por configuração", ""]
    for e in execucoes:
        linhas.append(f"- **{e['nome']}:** " + ("; ".join(e["erros"]) or "nenhum"))
    linhas += ["", "## Cuidados de leitura", "",
               "- O limiar da híbrida foi varrido **no próprio conjunto de avaliação**: o melhor valor tende a "
               "superestimar o ganho real. Uma decisão de adoção exige um conjunto de validação separado.",
               "- \"Perigosas\" conta respostas comerciais/de segurança que foram para a IA sem verificação ou "
               "com trecho proibido (mesma regra da RT-008).", ""]
    return "\n".join(linhas)


if __name__ == "__main__":
    sys.exit(main())
