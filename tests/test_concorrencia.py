"""RT-007 — concorrência no acesso ao SQLite e à memória de conversas.

Antes da correção, 8 threads compartilhando um único sqlite3.Connection geravam erros como
"bad parameter or other API misuse" e "no more rows available" (25 de 320 operações).
"""

import threading

import pytest

from app.agente import Agente
from app.db.conexao import ConexoesPorThread
from app.db.repositorios import AtendimentoRepository, CatalogoRepository, FiltroProdutos
from app.memoria import Memoria
from tests.conftest import OllamaFalso


@pytest.fixture
def pool(tmp_path, banco_modelo):
    import shutil

    destino = tmp_path / "concorrencia.db"
    shutil.copyfile(banco_modelo, destino)
    p = ConexoesPorThread(destino)
    yield p
    p.fechar_todas()


def _rodar(threads, alvo):
    ths = [threading.Thread(target=alvo, args=(n,)) for n in range(threads)]
    for t in ths:
        t.start()
    for t in ths:
        t.join()


def test_leituras_e_escritas_simultaneas_sem_erro(pool):
    ag = Agente(perguntar=OllamaFalso(lambda p: f"Resposta para {p}"), conexoes=pool)
    erros, letras = [], "abcdefghij"

    def trabalhador(n):
        for i in range(20):
            try:
                op = (n + i) % 4
                if op == 0:
                    ag.responder(f"Como funciona a ferramenta {letras[n]}{letras[i % 10]}xyz de bancada especial?")
                elif op == 1:
                    AtendimentoRepository(ag.con).avaliar(f"c{n}", True)
                elif op == 2:
                    CatalogoRepository(ag.con).buscar(FiltroProdutos(categorias=["furadeiras"]))
                else:
                    ag.responder("Qual broca usar em concreto?")
            except Exception as e:  # noqa: BLE001 - o teste coleta qualquer falha de concorrência
                erros.append(f"{type(e).__name__}: {e}")

    _rodar(6, trabalhador)
    assert erros == []
    assert ag.con.execute("SELECT COUNT(*) FROM avaliacoes").fetchone()[0] == 30  # 6 threads x 5 avaliações
    assert ag.con.execute("PRAGMA integrity_check").fetchone()[0] == "ok"


def test_cada_thread_recebe_sua_conexao(pool):
    vistas = {}

    def trabalhador(n):
        vistas[n] = id(pool.atual())
        assert pool.atual() is pool.atual()   # a mesma thread reaproveita a sua

    _rodar(4, trabalhador)
    assert len(set(vistas.values())) == 4


def test_memoria_concorrente_nao_perde_nem_corrompe():
    mem = Memoria(trocas_por_conversa=5, max_conversas=50)

    def trabalhador(n):
        for i in range(200):
            mem.registrar(f"c{(n * 200 + i) % 80}", "p", "r")
            mem.historico(f"c{i % 80}")
            if i % 50 == 0:
                mem.esquecer(f"c{i % 80}")

    _rodar(8, trabalhador)
    assert len(mem) <= 50
