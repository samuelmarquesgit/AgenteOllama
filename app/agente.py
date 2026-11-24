"""Regras do agente.

Fluxo de cada pergunta (os guardrails ficam em app/guardrails/):
1. Guardrails de entrada    -> tamanho, dados pessoais mascarados, prompt injection bloqueado.
2. Saudação                 -> apresentação fixa.
3. Continuação da conversa? -> ("e para metal?") o Ollama reescreve como pergunta
                               completa usando o histórico ("Qual broca usar em metal?").
4. Busca no banco SQLite    -> achou com nota boa? responde com a resposta do banco.
5. Assunto comercial        -> responde com os textos fixos; NUNCA chama o LLM.
6. Não achou                -> pergunta ao agente de IA (Ollama, local), com o histórico.
7. Guardrails de saída      -> resposta com preço/estoque/prazo inventado, conselho
                               perigoso etc. é descartada.
8. Guardrails de aprendizado-> grava a pergunta COMPLETA + resposta no banco
                               (pendente de validação); na próxima vez vem do banco.
"""

import logging
import os
import sqlite3
from dataclasses import dataclass, field

from app import banco
from app.busca import Faq, buscar, eh_saudacao, montar_faqs, normalizar, nota_combinada, pontuar, tokens
from app.guardrails.entrada import remover_rotulos
from app.guardrails.aprendizado import resposta_incerta
from app.guardrails import (
    eh_fora_do_escopo,
    limpar_reescrita,
    pode_gravar,
    pode_usar_llm,
    verificar_entrada,
    verificar_saida,
)
from app.guardrails.prompts import (
    APRESENTACAO,
    AVISO_DADOS_PESSOAIS,
    FALLBACK,
    FORA_DO_ESCOPO,
    INSTRUCAO_LLM,
    INSTRUCAO_REESCRITA,
    RESPOSTA_BLOQUEADA_ENTRADA,
    RESPOSTA_BLOQUEADA_SAIDA,
    RESPOSTA_FORA_DO_ESCOPO,
)
from app.db.conexao import ConexoesPorThread
from app.db.repositorios import CatalogoRepository, LojaRepository
from app.intencoes import detectar_loja, detectar_produto, responder_loja, responder_produto
from app.memoria import Troca

__all__ = [
    "APRESENTACAO", "FALLBACK", "FORA_DO_ESCOPO", "INSTRUCAO_LLM", "INSTRUCAO_REESCRITA",
    "RESPOSTA_BLOQUEADA_ENTRADA", "RESPOSTA_BLOQUEADA_SAIDA", "RESPOSTA_FORA_DO_ESCOPO",
    "Agente", "Resposta",
]

NOTA_MINIMA = 0.5       # abaixo disso a pergunta "não existe" no banco
NOTA_CONFIANTE = 0.75   # abaixo disso responde, mas pede para confirmar
MARGEM_EMPATE = 0.1     # 2ª resposta quase tão boa quanto a 1ª -> sugere as duas
NOTA_COMERCIAL = 0.25   # sinal comercial a partir do qual o LLM não é chamado
NOTA_SUGESTAO = 0.9     # sugestões não revisadas só respondem perguntas praticamente iguais...
COBERTURA_REVERSA_SUGESTAO = 0.75  # ...e que contenham a maior parte das palavras da sugestão
CATEGORIA_SUGESTAO = "aprendida"

MODELO = os.getenv("OLLAMA_MODELO", "llama3.2")

# Indícios de que a mensagem depende da anterior ("e para metal?", "e essa?", "quanto dura ela?").
INICIOS_CONTINUACAO = ("e ", "e se ", "mas ", "entao ", "tambem ", "agora ", "so que ", "ainda ")
REFERENCIAS = {
    "isso", "isto", "esse", "essa", "esses", "essas", "este", "esta", "ele", "ela", "eles",
    "elas", "dele", "dela", "nele", "nela", "deles", "delas", "mesmo", "mesma", "outro",
    "outra", "anterior", "aquele", "aquela", "ai", "tambem",
}
MAX_TOKENS_CONTINUACAO = 2  # mensagens muito curtas com histórico ("para metal?") também

log = logging.getLogger("agente")


def usar_ollama() -> bool:
    return os.getenv("USAR_OLLAMA", "true").lower() in ("1", "true", "sim", "yes")


@dataclass
class Resposta:
    answer: str
    matchedFaqId: str | None
    confidence: float
    origem: str  # "banco" | "catalogo" | "loja" | "agente" | "fallback" | "saudacao" | "fora_do_escopo" | "bloqueado"
    perguntaInterpretada: str | None = None   # preenchida quando a pergunta foi reescrita
    guardrails: list[str] = field(default_factory=list)  # guardrails acionados
    produtos: list[dict] = field(default_factory=list)   # cards do catálogo (origem = "catalogo")

    def para_dict(self) -> dict:
        d = self.__dict__.copy()
        d["guardrails"] = list(self.guardrails)
        d["produtos"] = list(self.produtos)
        return d


def _mensagens_do_historico(historico: list[Troca]) -> list[dict]:
    mensagens = []
    for troca in historico:
        mensagens.append({"role": "user", "content": troca.pergunta})
        mensagens.append({"role": "assistant", "content": troca.resposta})
    return mensagens


def _chat_ollama(mensagens: list[dict], temperatura: float) -> str | None:
    """Chama o Ollama; devolve None se ele não estiver disponível ou responder vazio."""
    try:
        import ollama

        r = ollama.chat(model=MODELO, messages=mensagens, options={"temperature": temperatura})
        return r["message"]["content"].strip() or None
    except Exception:
        return None


def perguntar_ao_ollama(pergunta: str, historico: list[Troca] | None = None) -> str | None:
    """Resposta do modelo local, considerando o histórico da conversa."""
    mensagens = [{"role": "system", "content": INSTRUCAO_LLM}]
    mensagens += _mensagens_do_historico(historico or [])
    mensagens.append({"role": "user", "content": pergunta})
    return _chat_ollama(mensagens, temperatura=0.2)


def reescrever_com_ollama(pergunta: str, historico: list[Troca]) -> str | None:
    """Transforma uma continuação ("e para metal?") numa pergunta independente."""
    contexto = "\n".join(f"Cliente: {t.pergunta}\nAssistente: {t.resposta}" for t in historico)
    texto = _chat_ollama(
        [
            {"role": "system", "content": INSTRUCAO_REESCRITA},
            {"role": "user", "content": f"HISTÓRICO:\n{contexto}\n\nÚLTIMA MENSAGEM: {pergunta}"},
        ],
        temperatura=0.0,
    )
    return limpar_reescrita(texto)


def parece_continuacao(pergunta: str) -> bool:
    """Heurística: a mensagem só faz sentido junto com a anterior?"""
    texto = normalizar(pergunta)
    if not texto:
        return False
    if texto.startswith(INICIOS_CONTINUACAO) or texto == "e":
        return True
    if set(texto.split()) & REFERENCIAS:
        return True
    return len(tokens(pergunta)) <= MAX_TOKENS_CONTINUACAO and not eh_saudacao(pergunta)


class Agente:
    def __init__(
        self,
        con: sqlite3.Connection | None = None,
        perguntar=perguntar_ao_ollama,
        reescrever=reescrever_com_ollama,
        conexoes: ConexoesPorThread | None = None,
    ):
        """`con`: conexão única (testes, terminal). Sem `con`, usa uma conexão por thread (servidor, RT-007)."""
        self._con_fixa = con
        if con is None:
            self._conexoes = conexoes or ConexoesPorThread()
            banco.conectar(self._conexoes.caminho).close()  # migra e popula uma vez, antes de atender
        self.perguntar = perguntar
        self.reescrever = reescrever
        self.marcas_catalogo = self.catalogo.marcas()
        self.recarregar()

    @property
    def con(self) -> sqlite3.Connection:
        return self._con_fixa if self._con_fixa is not None else self._conexoes.atual()

    @property
    def catalogo(self) -> CatalogoRepository:
        return CatalogoRepository(self.con)

    @property
    def loja(self) -> LojaRepository:
        return LojaRepository(self.con)

    def recarregar(self):
        # Monta as listas novas e só então as publica (troca de referência): threads que estão
        # respondendo continuam com a versão anterior, sem ver uma lista pela metade.
        faqs = montar_faqs(banco.listar(self.con))
        oficiais = [f for f in faqs if f.categoria != CATEGORIA_SUGESTAO]
        sugestoes = [f for f in faqs if f.categoria == CATEGORIA_SUGESTAO]
        self.faqs, self.oficiais, self.sugestoes = faqs, oficiais, sugestoes   # oficiais + sugestões (para /faqs e /health)

    def responder(self, pergunta: str, historico: list[Troca] | None = None) -> Resposta:
        historico = historico or []

        # ---- guardrails de entrada (G01–G03) ----
        entrada = verificar_entrada(pergunta)
        acionados = [f"dados_pessoais:{t}" for t in entrada.dados_pessoais]
        if not entrada.permitido:
            texto = RESPOSTA_BLOQUEADA_ENTRADA if entrada.motivo == "injecao" else FALLBACK
            return Resposta(texto, None, 0.0, "bloqueado", guardrails=acionados + [f"entrada:{entrada.motivo}"])
        pergunta = remover_rotulos(entrada.texto) if entrada.dados_pessoais else entrada.texto

        if eh_saudacao(pergunta):
            resposta = Resposta(APRESENTACAO, None, 1.0, "saudacao")
        else:
            independente = self._interpretar(pergunta, historico)
            resposta = (
                self._responder_por_dados(independente)
                or self._responder_pelo_banco(independente)
                or self._responder_comercial(independente)
                or self._responder_por_sugestao(independente)
                or self._responder_pelo_agente(independente, historico, bool(entrada.dados_pessoais))
            )
            if independente != pergunta:
                resposta.perguntaInterpretada = independente

        resposta.guardrails = acionados + resposta.guardrails
        if entrada.dados_pessoais:
            resposta.answer = f"{AVISO_DADOS_PESSOAIS}\n\n{resposta.answer}"
        return resposta

    # ---- 0) contexto -------------------------------------------------------
    def _interpretar(self, pergunta: str, historico: list[Troca]) -> str:
        """Pergunta completa a ser usada na busca e na gravação."""
        if not historico or not usar_ollama() or not parece_continuacao(pergunta):
            return pergunta
        return self.reescrever(pergunta, historico) or pergunta

    # ---- 1) dados da loja e do catálogo (nunca passam pelo LLM) -----------
    def _responder_por_dados(self, pergunta: str) -> Resposta | None:
        intencao_loja = detectar_loja(pergunta)
        if intencao_loja:
            r = responder_loja(intencao_loja, self.loja)
            return Resposta(r.texto, None, 1.0, r.origem, guardrails=r.guardrails)
        intencao_produto = detectar_produto(pergunta, self.marcas_catalogo)
        if intencao_produto:
            r = responder_produto(intencao_produto, self.catalogo)
            return Resposta(r.texto, None, 1.0, r.origem, guardrails=r.guardrails, produtos=r.produtos)
        return None

    # ---- 2) banco de FAQ ---------------------------------------------------
    def _responder_pelo_banco(self, pergunta: str) -> Resposta | None:
        resultados = buscar(pergunta, self.oficiais)
        if not resultados or resultados[0].nota < NOTA_MINIMA:
            return None

        melhor = resultados[0]
        faq = melhor.faq
        texto = faq.resposta
        if len(resultados) > 1:
            segunda = resultados[1]
            if segunda.nota >= NOTA_MINIMA and melhor.nota - segunda.nota <= MARGEM_EMPATE:
                if faq.comercial and segunda.faq.comercial:
                    texto += " " + segunda.faq.resposta
                else:
                    texto += f"\n\nTalvez também ajude: \"{segunda.faq.pergunta}\""
        if melhor.nota < NOTA_CONFIANTE and not faq.comercial:
            texto += "\n\nSe não era bem isso, me conte mais detalhes (ferramenta, material e tipo de uso)."
        return Resposta(texto, faq.id, melhor.nota, "banco")

    # ---- 2) comercial: textos fixos, nunca LLM (G04) -----------------------
    def _responder_comercial(self, pergunta: str) -> Resposta | None:
        resultados = buscar(pergunta, self.oficiais, limite=5)
        comerciais = [r.faq for r in resultados if not pode_usar_llm(r.faq.categoria) and r.nota >= NOTA_COMERCIAL]
        if not comerciais:
            return None
        texto = " ".join(f.resposta for f in comerciais[:3])
        nota = nota_combinada(pergunta, comerciais)
        return Resposta(texto, comerciais[0].id, nota, "banco", guardrails=["escopo:comercial_sem_llm"])

    # ---- 3) agente de IA ---------------------------------------------------
    # ---- 4) resposta aprendida, ainda não revisada --------------------------
    def _responder_por_sugestao(self, pergunta: str) -> Resposta | None:
        """Reaproveita uma resposta gerada pela IA SÓ se a pergunta for praticamente a mesma.

        Sugestões não passaram por revisão humana: não podem "pegar" perguntas parecidas como a
        FAQ oficial faz. Exige nota alta nos dois sentidos (a pergunta cobre a sugestão e vice-versa).
        """
        q = tokens(pergunta)
        melhor, nota_melhor = None, 0.0
        for sug in self.sugestoes:
            nota = pontuar(pergunta, sug)
            if nota < NOTA_SUGESTAO or not sug.tokens_chave:
                continue
            reversa = sum(1 for t in sug.tokens_chave if t in q) / len(sug.tokens_chave)
            if reversa >= COBERTURA_REVERSA_SUGESTAO and nota > nota_melhor:
                melhor, nota_melhor = sug, nota
        if not melhor:
            return None
        return Resposta(melhor.resposta, melhor.id, nota_melhor, "sugestao", guardrails=["aprendizado:nao_revisada"])

    def _responder_pelo_agente(self, pergunta: str, historico: list[Troca], tinha_dados_pessoais: bool = False) -> Resposta:
        if not usar_ollama():
            return Resposta(FALLBACK, None, 0.0, "fallback")
        texto = self.perguntar(pergunta, historico)
        if not texto:
            return Resposta(FALLBACK, None, 0.0, "fallback")
        if eh_fora_do_escopo(texto):
            return Resposta(RESPOSTA_FORA_DO_ESCOPO, None, 0.0, "fora_do_escopo", guardrails=["escopo:fora_do_escopo"])

        # ---- guardrails de saída (G06–G14) ----
        saida = verificar_saida(texto)
        if not saida.permitido:
            log.warning("resposta do LLM bloqueada: %s", ",".join(saida.violacoes))
            return Resposta(RESPOSTA_BLOQUEADA_SAIDA, None, 0.0, "bloqueado",
                            guardrails=[f"saida:{v}" for v in saida.violacoes])

        # ---- guardrails de aprendizado (G16–G19) ----
        if resposta_incerta(saida.texto):  # G25
            texto = f"{saida.texto}\n\nPara uma resposta segura, posso encaminhar você a um atendente da loja."
            return Resposta(texto, None, 0.0, "agente", guardrails=["aprendizado:resposta_incerta"])
        if not pode_gravar(pergunta, saida.permitido, tinha_dados_pessoais):
            return Resposta(saida.texto, None, 0.0, "agente", guardrails=["aprendizado:nao_gravado"])
        novo_id = banco.inserir_aprendida(self.con, pergunta, saida.texto)
        self.recarregar()
        return Resposta(saida.texto, novo_id, 0.0, "agente")
