"""Planilha de revisão humana da base de conhecimento (P1.7 / T-025).

Amostra = TODAS as FAQs de risco alto + 30 FAQs sorteadas (semente fixa) entre as demais.
O revisor preenche `decisao` (aprovar | ajustar | rejeitar), `resposta_corrigida` (se ajustar),
`revisor` (iniciais) e `data` (AAAA-MM-DD). A importação aplica as decisões no `knowledge/faq.json`;
na próxima inicialização o seed sincroniza o banco (hash do arquivo).

Uso:
    python -m app.db.planilha_revisao gerar      # escreve docs/revisao/planilha_revisao_faq.csv
    python -m app.db.planilha_revisao importar   # aplica as linhas preenchidas no faq.json
    python -m app.db.planilha_revisao resumo     # quantas linhas já foram revisadas
"""

import csv
import json
import random
import re
import sys
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
FAQ_JSON = RAIZ / "knowledge" / "faq.json"
PLANILHA = RAIZ / "docs" / "revisao" / "planilha_revisao_faq.csv"
TAMANHO_AMOSTRA = 30
SEMENTE = 20261124
COLUNAS = ["id", "categoria", "nivel_risco", "status_atual", "pergunta", "resposta", "fonte",
           "decisao", "resposta_corrigida", "revisor", "data", "observacoes"]
DECISOES = {"aprovar", "ajustar", "rejeitar"}
DATA = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _carregar() -> list[dict]:
    return json.loads(FAQ_JSON.read_text(encoding="utf-8"))


def amostra(faqs: list[dict]) -> list[dict]:
    """Risco alto (todas) + 30 sorteadas entre as outras, em ordem de id."""
    altas = [f for f in faqs if f.get("nivel_risco") == "alto"]
    demais = [f for f in faqs if f.get("nivel_risco") != "alto"]
    sorteadas = random.Random(SEMENTE).sample(demais, min(TAMANHO_AMOSTRA, len(demais)))
    return sorted(altas + sorteadas, key=lambda f: f["id"])


def gerar(destino: Path = PLANILHA) -> int:
    linhas = amostra(_carregar())
    destino.parent.mkdir(parents=True, exist_ok=True)
    # utf-8-sig: o Excel abre com acentos corretos; ";" é o separador padrão do Excel em pt-BR
    with destino.open("w", encoding="utf-8-sig", newline="") as arq:
        escritor = csv.DictWriter(arq, fieldnames=COLUNAS, delimiter=";")
        escritor.writeheader()
        for f in linhas:
            escritor.writerow({"id": f["id"], "categoria": f["categoria"], "nivel_risco": f.get("nivel_risco", ""),
                               "status_atual": f.get("status", ""), "pergunta": f["pergunta"],
                               "resposta": f["resposta"], "fonte": f.get("fonte", "")})
    return len(linhas)


def _ler(origem: Path) -> list[dict]:
    with origem.open(encoding="utf-8-sig", newline="") as arq:
        return list(csv.DictReader(arq, delimiter=";"))


def validar_linha(linha: dict) -> str | None:
    """Devolve o motivo do erro, ou None se a linha preenchida é válida."""
    decisao = (linha.get("decisao") or "").strip().lower()
    if decisao not in DECISOES:
        return f"decisão inválida: {decisao!r}"
    if not (linha.get("revisor") or "").strip():
        return "revisor não informado"
    if not DATA.match((linha.get("data") or "").strip()):
        return "data deve ser AAAA-MM-DD"
    if decisao == "ajustar" and not (linha.get("resposta_corrigida") or "").strip():
        return "ajustar exige resposta_corrigida"
    return None


def importar(origem: Path = PLANILHA, faq_json: Path = FAQ_JSON) -> dict:
    faqs = json.loads(faq_json.read_text(encoding="utf-8"))
    por_id = {f["id"]: f for f in faqs}
    resultado = {"aprovadas": 0, "ajustadas": 0, "rejeitadas": 0, "ignoradas": 0, "erros": []}
    for linha in _ler(origem):
        if not (linha.get("decisao") or "").strip():
            resultado["ignoradas"] += 1
            continue
        erro = validar_linha(linha) or (None if linha["id"] in por_id else "id não existe")
        if erro:
            resultado["erros"].append(f"{linha.get('id')}: {erro}")
            continue
        faq, decisao = por_id[linha["id"]], linha["decisao"].strip().lower()
        if decisao == "rejeitar":
            faq["status"] = "inativo"          # sai da busca, mas fica registrado
            resultado["rejeitadas"] += 1
        else:
            if decisao == "ajustar":
                faq["resposta"] = linha["resposta_corrigida"].strip()
                resultado["ajustadas"] += 1
            else:
                resultado["aprovadas"] += 1
            faq["status"] = "validado"
        faq["revisado_em"] = linha["data"].strip()
        faq["fonte"] = f"{faq.get('fonte', '')} · revisado por {linha['revisor'].strip()} em {linha['data'].strip()}"
    if not resultado["erros"]:
        faq_json.write_text(json.dumps(faqs, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return resultado


def resumo(origem: Path = PLANILHA) -> dict:
    linhas = _ler(origem)
    preenchidas = [linha for linha in linhas if (linha.get("decisao") or "").strip()]
    return {"linhas": len(linhas), "revisadas": len(preenchidas),
            "risco_alto": sum(1 for linha in linhas if linha["nivel_risco"] == "alto")}


def main(argv: list[str]) -> int:
    comando = argv[0] if argv else "resumo"
    if comando == "gerar":
        print(f"{gerar()} FAQs na planilha {PLANILHA.relative_to(RAIZ)} ({date.today()})")
    elif comando == "importar":
        r = importar()
        if r["erros"]:
            print("Nada foi alterado. Corrija a planilha:\n  " + "\n  ".join(r["erros"]))
            return 1
        print(f"aprovadas {r['aprovadas']} · ajustadas {r['ajustadas']} · rejeitadas {r['rejeitadas']} · "
              f"sem decisão {r['ignoradas']}. Reinicie a API para carregar a base.")
    elif comando == "resumo":
        print(resumo())
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
