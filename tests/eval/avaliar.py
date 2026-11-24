"""RT-008 — avaliação do roteamento do Tork com o conjunto de 100 perguntas.

A IA generativa é substituída por um marcador: medimos PARA ONDE cada pergunta vai (FAQ certa, catálogo,
loja, fallback ou IA), de forma determinística. A qualidade do texto gerado pela IA é avaliada à parte (T-048).

Uso:
    python -m tests.eval.avaliar                 # imprime o resumo
    python -m tests.eval.avaliar --relatorio     # grava docs/eval/avaliacao-roteamento.md
"""

import json
import os
import sys
import tempfile
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
ARQ_CONJUNTO = Path(__file__).with_name("conjunto_avaliacao.json")
ARQ_RELATORIO = RAIZ / "docs" / "eval" / "avaliacao-roteamento.md"
MARCADOR_IA = "<<RESPOSTA GERADA PELA IA>>"


@dataclass
class Resultado:
    id: str
    grupo: str
    pergunta: str
    origem: str
    faq: str | None
    acertou: bool
    foi_para_ia: bool
    perigosa: bool
    motivo: str


def _julgar(item: dict, resposta, foi_para_ia: bool) -> Resultado:
    faqs, origens = item.get("faqs", []), item.get("origens", [])
    acertou = (resposta.matchedFaqId in faqs) or (resposta.origem in origens)
    perigosa, motivo = False, ""
    if item.get("nunca_ia") and foi_para_ia:
        perigosa, motivo = True, "pergunta comercial/de segurança respondida pela IA sem verificação"
    for trecho in item.get("proibido", []):
        if trecho.lower() in resposta.answer.lower():
            perigosa, motivo = True, f"contém trecho proibido: {trecho!r}"
    if not acertou and not motivo:
        esperado = ", ".join(faqs + origens)
        motivo = f"esperado {esperado}; obtido {resposta.origem} {resposta.matchedFaqId or ''}".strip()
    return Resultado(item["id"], item["grupo"], item["pergunta"], resposta.origem, resposta.matchedFaqId,
                     acertou, foi_para_ia, perigosa, motivo)


def avaliar(con=None) -> list[Resultado]:
    """Roda o conjunto inteiro. Sem `con`, usa um banco temporário recém-populado."""
    os.environ.setdefault("BANCO_SQLITE", str(Path(tempfile.mkdtemp()) / "avaliacao.db"))
    sys.path.insert(0, str(RAIZ))
    from app import banco
    from app.agente import Agente

    if con is None:
        con = banco.conectar(Path(tempfile.mkdtemp()) / "avaliacao.db")
    chamadas = []

    def ia_falsa(pergunta, historico=None):
        chamadas.append(pergunta)
        return MARCADOR_IA

    os.environ["USAR_OLLAMA"] = "true"
    agente = Agente(con, perguntar=ia_falsa, reescrever=lambda p, h: None)
    conjunto = json.loads(ARQ_CONJUNTO.read_text(encoding="utf-8"))["perguntas"]
    resultados = []
    for item in conjunto:
        antes = len(chamadas)
        agente.sugestoes = []  # cada pergunta é avaliada sem aprender com as anteriores
        resposta = agente.responder(item["pergunta"])
        resultados.append(_julgar(item, resposta, foi_para_ia=len(chamadas) > antes))
        con.execute("DELETE FROM faq_sugestoes")
    return resultados


def resumo(resultados: list[Resultado]) -> dict:
    por_grupo = defaultdict(list)
    for r in resultados:
        por_grupo[r.grupo].append(r)
    return {
        "total": len(resultados),
        "acertos": sum(r.acertou for r in resultados),
        "perigosas": sum(r.perigosa for r in resultados),
        "foi_para_ia": sum(r.foi_para_ia for r in resultados),
        "fallback": sum(r.origem == "fallback" for r in resultados),
        "origens": Counter(r.origem for r in resultados),
        "grupos": {g: (sum(r.acertou for r in rs), len(rs)) for g, rs in por_grupo.items()},
    }


def relatorio_markdown(resultados: list[Resultado]) -> str:
    s = resumo(resultados)
    linhas = [
        "# Avaliação de roteamento do Tork (RT-008)",
        "",
        "> Gerado por `python -m tests.eval.avaliar --relatorio`. A IA é substituída por um marcador: mede-se para onde",
        "> cada pergunta vai (FAQ certa, catálogo, loja, fallback ou IA). **O gabarito ainda precisa de revisão humana (T-025).**",
        "",
        "## Resumo",
        "",
        "| Métrica | Valor |",
        "|---------|-------|",
        f"| Acerto geral | **{s['acertos']}/{s['total']} ({100 * s['acertos'] / s['total']:.0f}%)** |",
        f"| Respostas perigosas | **{s['perigosas']}** |",
        f"| Perguntas que iriam para a IA | {s['foi_para_ia']} |",
        f"| Fallback (\"não tenho informação segura\") | {s['fallback']} |",
        "",
        "| Grupo | Acerto |",
        "|-------|--------|",
    ]
    for g, (ok, n) in s["grupos"].items():
        linhas.append(f"| {g} | {ok}/{n} ({100 * ok / n:.0f}%) |")
    linhas += ["", "| Origem | Respostas |", "|--------|-----------|"]
    linhas += [f"| {o} | {n} |" for o, n in s["origens"].most_common()]
    erros = [r for r in resultados if not r.acertou or r.perigosa]
    linhas += ["", f"## Perguntas fora do gabarito ({len(erros)})", "", "| ID | Grupo | Pergunta | Motivo |", "|----|-------|----------|--------|"]
    linhas += [f"| {r.id} | {r.grupo} | {r.pergunta} | {'⚠️ ' if r.perigosa else ''}{r.motivo} |" for r in erros]
    return "\n".join(linhas) + "\n"


def main(argv: list[str]) -> int:
    resultados = avaliar()
    s = resumo(resultados)
    print(f"Acerto: {s['acertos']}/{s['total']} | perigosas: {s['perigosas']} | IA: {s['foi_para_ia']} | fallback: {s['fallback']}")
    for g, (ok, n) in s["grupos"].items():
        print(f"  {g:16} {ok}/{n}")
    if "--relatorio" in argv:
        ARQ_RELATORIO.parent.mkdir(parents=True, exist_ok=True)
        ARQ_RELATORIO.write_text(relatorio_markdown(resultados), encoding="utf-8")
        print(f"Relatório: {ARQ_RELATORIO}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
