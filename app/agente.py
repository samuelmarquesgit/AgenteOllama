"""Regras do agente.

Fluxo de cada pergunta:
1. Saudação                 -> apresentação fixa.
2. Busca no banco SQLite    -> achou com nota boa? responde com a resposta do banco.
3. Não achou                -> pergunta ao agente de IA (Ollama, local).
4. Agente respondeu         -> grava pergunta+resposta no banco (pendente de validação)
                               e na próxima vez a resposta já vem do banco.
5. Ollama fora do ar / pergunta fora do assunto -> mensagem padrão, nada é gravado.
"""

import os
import sqlite3
from dataclasses import dataclass

from app import banco
from app.busca import Faq, buscar, eh_saudacao, montar_faqs, nota_combinada, tokens

NOTA_MINIMA = 0.5       # abaixo disso a pergunta "não existe" no banco
NOTA_CONFIANTE = 0.75   # abaixo disso responde, mas pede para confirmar
MARGEM_EMPATE = 0.1     # 2ª resposta quase tão boa quanto a 1ª -> sugere as duas

MODELO = os.getenv("OLLAMA_MODELO", "qwen2.5:3b")
FORA_DO_ESCOPO = "FORA_DO_ESCOPO"

APRESENTACAO = (
    "Olá! Sou o assistente virtual da loja de ferramentas. Posso tirar dúvidas "
    "sobre ferramentas elétricas, brocas, discos, baterias, medição e segurança. "
    "Ainda não consulto preços nem estoque. Como posso ajudar?"
)

FALLBACK = (
    "Desculpe, não tenho informação suficiente para responder isso com segurança. "
    "Você pode reformular a pergunta com mais detalhes (ferramenta, material, uso) "
    "ou falar com um atendente da loja."
)

RESPOSTA_FORA_DO_ESCOPO = (
    "Só consigo ajudar com dúvidas sobre ferramentas, acessórios e atendimento da loja. "
    "Quer perguntar algo sobre isso?"
)

INSTRUCAO_LLM = (
    "Você é o assistente virtual de uma loja de ferramentas elétricas e eletrônicas no Brasil. "
    "Responda em português do Brasil, de forma cordial, clara e em no máximo 4 frases, "
    "respondendo diretamente à pergunta com orientações gerais e tecnicamente corretas. "
    "Regras obrigatórias: nunca invente preços, estoque, promoções, prazos de entrega ou "
    "garantias (só nesses casos diga que um atendente confirma); "
    "nunca afirme compatibilidade sem modelo e especificações; "
    "inclua alertas de segurança quando houver risco (eletricidade, discos, proteções); "
    "nunca peça CPF, endereço ou dados de pagamento. "
    f"Se a pergunta NÃO tiver relação com ferramentas, acessórios ou a loja, responda apenas: {FORA_DO_ESCOPO}"
)


def usar_ollama() -> bool:
    return os.getenv("USAR_OLLAMA", "true").lower() in ("1", "true", "sim", "yes")


@dataclass
class Resposta:
    answer: str
    matchedFaqId: str | None
    confidence: float
    origem: str  # "banco" | "agente" | "fallback" | "saudacao" | "fora_do_escopo"

    def para_dict(self) -> dict:
        return self.__dict__.copy()


def perguntar_ao_ollama(pergunta: str) -> str | None:
    """Resposta do modelo local, ou None se o Ollama não estiver disponível."""
    try:
        import ollama

        r = ollama.chat(
            model=MODELO,
            messages=[
                {"role": "system", "content": INSTRUCAO_LLM},
                {"role": "user", "content": pergunta},
            ],
            options={"temperature": 0.2},
        )
        return r["message"]["content"].strip() or None
    except Exception:
        return None


class Agente:
    def __init__(self, con: sqlite3.Connection | None = None, perguntar=perguntar_ao_ollama):
        self.con = con if con is not None else banco.conectar()
        self.perguntar = perguntar
        self.recarregar()

    def recarregar(self):
        self.faqs: list[Faq] = montar_faqs(banco.listar(self.con))

    def responder(self, pergunta: str) -> Resposta:
        pergunta = pergunta.strip()
        if eh_saudacao(pergunta):
            return Resposta(APRESENTACAO, None, 1.0, "saudacao")

        resposta = self._responder_pelo_banco(pergunta)
        if resposta:
            return resposta
        return self._responder_pelo_agente(pergunta)

    # ---- 1) banco de dados -------------------------------------------------
    def _responder_pelo_banco(self, pergunta: str) -> Resposta | None:
        resultados = buscar(pergunta, self.faqs)
        if not resultados:
            return None

        melhor = resultados[0]
        if melhor.nota < NOTA_MINIMA:
            # Pergunta comercial "mista" (ex.: marca + preço + estoque): junta as
            # respostas comerciais se, somadas, elas cobrem bem a pergunta.
            comerciais = [r.faq for r in resultados if r.faq.comercial]
            nota = nota_combinada(pergunta, comerciais)
            if melhor.faq.comercial and nota >= NOTA_MINIMA:
                texto = " ".join(f.resposta for f in comerciais)
                return Resposta(texto, comerciais[0].id, nota, "banco")
            return None

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

    # ---- 2) agente de IA ---------------------------------------------------
    def _responder_pelo_agente(self, pergunta: str) -> Resposta:
        if not usar_ollama():
            return Resposta(FALLBACK, None, 0.0, "fallback")
        texto = self.perguntar(pergunta)
        if not texto:
            return Resposta(FALLBACK, None, 0.0, "fallback")
        if FORA_DO_ESCOPO in texto:
            return Resposta(RESPOSTA_FORA_DO_ESCOPO, None, 0.0, "fora_do_escopo")

        # Completa a base: a próxima pergunta igual já sai do banco.
        chaves = sorted(tokens(pergunta))
        novo_id = banco.inserir_aprendida(self.con, pergunta, texto, chaves)
        self.recarregar()
        return Resposta(texto, novo_id, 0.0, "agente")
