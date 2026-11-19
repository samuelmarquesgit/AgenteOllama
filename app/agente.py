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
from app.busca import Faq, buscar, eh_saudacao, montar_faqs, normalizar, nota_combinada, tokens
from app.guardrails.entrada import remover_rotulos
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
    origem: str  # "banco" | "agente" | "fallback" | "saudacao" | "fora_do_escopo" | "bloqueado"
    perguntaInterpretada: str | None = None   # preenchida quando a pergunta foi reescrita
    guardrails: list[str] = field(default_factory=list)  # guardrails acionados

    def para_dict(self) -> dict:
        d = self.__dict__.copy()
        d["guardrails"] = list(self.guardrails)
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
    ):
        self.con = con if con is not None else banco.conectar()
        self.perguntar = perguntar
        self.reescrever = reescrever
        self.recarregar()

    def recarregar(self):
        self.faqs: list[Faq] = montar_faqs(banco.listar(self.con))

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
                self._responder_pelo_banco(independente)
                or self._responder_comercial(independente)
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

    # ---- 1) banco de dados -------------------------------------------------
    def _responder_pelo_banco(self, pergunta: str) -> Resposta | None:
        resultados = buscar(pergunta, self.faqs)
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
        resultados = buscar(pergunta, self.faqs, limite=5)
        comerciais = [r.faq for r in resultados if not pode_usar_llm(r.faq.categoria) and r.nota >= NOTA_COMERCIAL]
        if not comerciais:
            return None
        texto = " ".join(f.resposta for f in comerciais[:3])
        nota = nota_combinada(pergunta, comerciais)
        return Resposta(texto, comerciais[0].id, nota, "banco", guardrails=["escopo:comercial_sem_llm"])

    # ---- 3) agente de IA ---------------------------------------------------
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
        if not pode_gravar(pergunta, saida.permitido, tinha_dados_pessoais):
            return Resposta(saida.texto, None, 0.0, "agente", guardrails=["aprendizado:nao_gravado"])
        novo_id = banco.inserir_aprendida(self.con, pergunta, saida.texto, sorted(tokens(pergunta)))
        self.recarregar()
        return Resposta(saida.texto, novo_id, 0.0, "agente")
