"""Revisão humana das respostas geradas pela IA (fila `faq_sugestoes`).

Uso:
    python -m app.db.revisao                                   # lista as sugestões pendentes
    python -m app.db.revisao rejeitar SUG-0006 "resposta errada"
    python -m app.db.revisao aprovar SUG-0007 brocas_discos_acessorios
    python -m app.db.revisao categorias                        # categorias válidas para aprovar

Reinicie a API depois de revisar: ela carrega a base na inicialização.
"""

import getpass
import sys

from app.db.conexao import abrir
from app.db.repositorios import FaqRepository, SugestaoRepository


def main(argv: list[str]) -> int:
    con = abrir()
    repo = SugestaoRepository(con)
    revisor = getpass.getuser()
    try:
        if not argv:
            pendentes = repo.listar_pendentes()
            if not pendentes:
                print("Nenhuma sugestão pendente.")
            for s in pendentes:
                print(f"\n{s['codigo']} ({s['criado_em']})\n  P: {s['pergunta']}\n  R: {s['resposta']}")
        elif argv[0] == "categorias":
            for c in FaqRepository(con).listar_categorias():
                print(f"{c['codigo']:32} {c['nome']}")
        elif argv[0] == "rejeitar" and len(argv) >= 2:
            repo.rejeitar(argv[1], " ".join(argv[2:]) or "rejeitada na revisão", revisor)
            print(f"{argv[1]} rejeitada.")
        elif argv[0] == "aprovar" and len(argv) == 3:
            print(f"{argv[1]} aprovada como {repo.aprovar(argv[1], argv[2], revisor)}.")
        else:
            print(__doc__)
            return 2
    except ValueError as erro:
        print(f"Erro: {erro}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
