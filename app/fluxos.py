"""Fluxos guiados (P1.4 / T-032, T-033, T-039): F-TROCA e F-HUMANO, conforme docs/0008 §5.

Um fluxo é uma conversa curta, de passos fixos, sem IA generativa: os textos vêm das políticas da
loja (tabela `politicas`) e de mensagens revisáveis deste módulo. O estado fica só em memória, por
conversa (precisa de conversationId). "cancelar", "sair" ou "menu" encerram o fluxo a qualquer momento.

F-TROCA:  motivo (desistência | defeito | produto errado) -> [online | loja física] -> orientação.
          Produto ou voltagem errada é troca prioritária: segue para o F-HUMANO com prioridade alta.
F-HUMANO: resumo em uma frase (dados pessoais mascarados, G02) -> consentimento explícito (G23) ->
          registro em `atendimentos_humanos` -> mensagem dentro/fora do horário de atendimento.
          Não pede nome, telefone nem CPF. Sem consentimento, nada é gravado.
"""

import re
import threading
from collections import OrderedDict
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime

from app.busca import normalizar
from app.db.repositorios import AtendimentoRepository, LojaRepository
from app.guardrails import mascarar_dados_pessoais

ORIGEM = "fluxo"
LIMITE_RESUMO = 300
MAX_CONVERSAS = 1000
MAX_TENTATIVAS = 2  # respostas não entendidas no mesmo passo antes de sair do fluxo

INICIO_HUMANO = re.compile(
    r"\b((falar|falo|conversar|chamar|chama|passa\w*|transfer\w*)\b.{0,20}\b(atendente|humano|pessoa|vendedor)"
    r"|(quero|preciso de) (um |uma )?(atendente|humano|vendedor)|atendimento humano)\b")
# "como trocar o disco?" é dúvida técnica, não troca de compra: "trocar" só abre o fluxo junto de produto/pedido.
INICIO_TROCA = re.compile(
    r"\b((posso|quero|preciso|como) (devolver|(fazer|faco|faz) (uma )?(troca|devolucao))"
    r"|(posso|quero|preciso|como) trocar\b.{0,15}\b(produto|pedido|compra|item|mercadoria)"
    r"|trocas? e garantia|trocar ou devolver)\b")
SAIR = {"cancelar", "sair", "menu", "parar", "esquece", "deixa pra la", "nao quero mais falar"}

DESISTENCIA = re.compile(r"\b(desist\w*|arrepend\w*|nao (quero|gostei|serv\w*)|mudei de ideia|desistencia)\b")
DEFEITO = re.compile(r"\b(defeito\w*|quebr\w*|nao (liga|funciona|carrega)|parou|estragad\w*)\b")
ERRADO = re.compile(r"\b(errad\w*|trocad\w*|diferente|outro produto|voltagem)\b")
ONLINE = re.compile(r"\b(online|on line|site|internet|app|aplicativo|telefone|whatsapp|zap|entrega)\b")
LOJA = re.compile(r"\b(loja|fisica|presencial|balcao|unidade)\b")
SIM = re.compile(r"^(sim|s|ok|pode|claro|pode sim|autorizo|concordo|tudo bem|beleza|isso|uhum|aham)\b")
NAO = re.compile(r"^(nao|n|nao quero|melhor nao|prefiro nao|nao autorizo)\b")

OP_MOTIVO = ["Desisti da compra", "Produto com defeito", "Veio errado ou na voltagem errada"]
OP_CANAL = ["Comprei online", "Comprei na loja física"]
OP_CONSENTIMENTO = ["Sim, pode compartilhar", "Não"]

TEXTO = {
    "troca_inicio": "Posso ajudar! É desistência da compra, produto com defeito ou produto errado?",
    "troca_canal": "Entendi. Você comprou online (site, telefone, WhatsApp) ou na loja física?",
    "troca_online": ("Em compras feitas fora da loja física você pode desistir em até 7 dias após receber o produto "
                     "(direito de arrependimento, art. 49 do CDC). Guarde a nota fiscal e a embalagem. Para solicitar, "
                     "fale com um atendente: é só pedir por aqui."),
    "troca_defeito": ("{garantia} Não abra nem tente consertar o produto antes, para não perder a garantia. "
                      "Se quiser, posso chamar um atendente para orientar o encaminhamento."),
    "troca_errado": "Lamento pelo transtorno! Produto ou voltagem errada é tratado como troca prioritária.",
    "humano_inicio": ("Vou chamar um atendente. Para ele já começar ajudando, me diga em uma frase o que você precisa "
                      "(sem CPF, telefone ou endereço)."),
    "humano_consentimento": ("Vou compartilhar este resumo com a nossa equipe para dar continuidade ao atendimento: "
                             "\"{resumo}\". Ele fica registrado só para esse fim. Pode ser?"),
    "humano_dentro": "Pronto! Registrei seu pedido (protocolo {protocolo}). Um atendente vai continuar por aqui em instantes.",
    "humano_fora": ("Nosso atendimento humano funciona {horario}. Registrei seu pedido (protocolo {protocolo}) "
                    "e retornaremos assim que abrir."),
    "humano_recusado": ("Tudo bem, não registrei nada. Se preferir, fale direto com a loja: {contato}. "
                        "Posso ajudar em mais alguma coisa?"),
    "nao_entendi": "Desculpe, não entendi. {pergunta}",
    "saiu": "Tudo bem, encerrei esse atendimento. Pode perguntar o que quiser ou digitar \"menu\".",
    "desistiu_fluxo": "Vamos fazer diferente: me conte sua dúvida com outras palavras ou peça para falar com um atendente.",
}

AVISO_DEMO = " (Políticas fictícias de demonstração.)"


@dataclass
class Estado:
    fluxo: str            # "troca" | "humano"
    passo: str
    tentativas: int = 0
    motivo: str = "pedido_cliente"
    prioridade: str = "normal"
    resumo: str | None = None
    dados: dict = field(default_factory=dict)


@dataclass
class RespostaFluxo:
    answer: str
    opcoes: list[str] = field(default_factory=list)
    passo: str = ""
    encerrado: bool = False
    protocolo: int | None = None

    def para_dict(self) -> dict:
        return {"answer": self.answer, "matchedFaqId": None, "confidence": 1.0, "origem": ORIGEM,
                "perguntaInterpretada": None, "guardrails": [f"fluxo:{self.passo}"], "produtos": [],
                "statusConteudo": "dados_demonstracao", "opcoes": list(self.opcoes),
                "fluxoAberto": not self.encerrado}


class Fluxos:
    def __init__(self, conexao: Callable, agora: Callable[[], datetime] = datetime.now):
        self._conexao = conexao        # função que devolve a conexão SQLite da thread atual
        self._agora = agora
        self._estados: OrderedDict[str, Estado] = OrderedDict()
        self._trava = threading.Lock()

    # ------------------------------------------------------------------ API
    def ativo(self, conversa_id: str | None) -> bool:
        with self._trava:
            return bool(conversa_id) and conversa_id in self._estados

    def esquecer(self, conversa_id: str | None) -> None:
        with self._trava:
            self._estados.pop(conversa_id, None)

    def tratar(self, conversa_id: str | None, mensagem: str) -> RespostaFluxo | None:
        """Devolve a resposta do fluxo, ou None se a mensagem não é de fluxo (segue para o agente)."""
        if not conversa_id:
            return None
        texto = normalizar(mensagem)
        with self._trava:
            estado = self._estados.get(conversa_id)
        if estado is None:
            return self._iniciar(conversa_id, texto)
        if texto in SAIR:
            self.esquecer(conversa_id)
            return RespostaFluxo(TEXTO["saiu"], passo="saiu", encerrado=True)
        passo = getattr(self, f"_passo_{estado.fluxo}_{estado.passo}")
        return passo(conversa_id, estado, mensagem, texto)

    # ------------------------------------------------------------------ início
    def _iniciar(self, conversa_id: str, texto: str) -> RespostaFluxo | None:
        if INICIO_HUMANO.search(texto):
            return self._abrir_humano(conversa_id, Estado("humano", "resumo"))
        if INICIO_TROCA.search(texto):
            motivo = self._motivo_troca(texto)
            if motivo:  # "quero devolver, veio errado" já diz o motivo
                return self._decidir_troca(conversa_id, Estado("troca", "motivo", motivo="troca"), motivo)
            self._guardar(conversa_id, Estado("troca", "motivo", motivo="troca"))
            return RespostaFluxo(TEXTO["troca_inicio"], OP_MOTIVO, "troca_motivo")
        return None

    def _guardar(self, conversa_id: str, estado: Estado) -> None:
        with self._trava:
            self._estados[conversa_id] = estado
            self._estados.move_to_end(conversa_id)
            while len(self._estados) > MAX_CONVERSAS:
                self._estados.popitem(last=False)

    def _nao_entendi(self, conversa_id: str, estado: Estado, pergunta: str, opcoes: list[str]) -> RespostaFluxo:
        estado.tentativas += 1
        if estado.tentativas >= MAX_TENTATIVAS:
            self.esquecer(conversa_id)
            return RespostaFluxo(TEXTO["desistiu_fluxo"], passo="nao_entendido", encerrado=True)
        return RespostaFluxo(TEXTO["nao_entendi"].format(pergunta=pergunta), opcoes, f"{estado.fluxo}_{estado.passo}")

    # ------------------------------------------------------------------ F-TROCA
    @staticmethod
    def _motivo_troca(texto: str) -> str | None:
        if ERRADO.search(texto):
            return "errado"
        if DEFEITO.search(texto):
            return "defeito"
        if DESISTENCIA.search(texto):
            return "desistencia"
        return None

    def _passo_troca_motivo(self, conversa_id, estado, _mensagem, texto) -> RespostaFluxo:
        motivo = self._motivo_troca(texto)
        if not motivo:
            return self._nao_entendi(conversa_id, estado, TEXTO["troca_inicio"], OP_MOTIVO)
        return self._decidir_troca(conversa_id, estado, motivo)

    def _decidir_troca(self, conversa_id: str, estado: Estado, motivo: str) -> RespostaFluxo:
        loja = LojaRepository(self._conexao())
        if motivo == "desistencia":
            estado.passo, estado.tentativas = "canal", 0
            self._guardar(conversa_id, estado)
            return RespostaFluxo(TEXTO["troca_canal"], OP_CANAL, "troca_canal")
        if motivo == "defeito":
            self.esquecer(conversa_id)
            garantia = (loja.politica("garantia") or {}).get("texto", "")
            return RespostaFluxo(TEXTO["troca_defeito"].format(garantia=garantia) + AVISO_DEMO,
                                 ["Falar com um atendente"], "troca_defeito", encerrado=True)
        # produto ou voltagem errada -> handoff prioritário com resumo pronto
        humano = Estado("humano", "consentimento", motivo="troca", prioridade="alta",
                        resumo="Troca prioritária: produto ou voltagem errada (fluxo de trocas).")
        resposta = self._abrir_humano(conversa_id, humano)
        resposta.answer = f"{TEXTO['troca_errado']} {resposta.answer}"
        return resposta

    def _passo_troca_canal(self, conversa_id, estado, _mensagem, texto) -> RespostaFluxo:
        if ONLINE.search(texto):
            self.esquecer(conversa_id)
            return RespostaFluxo(TEXTO["troca_online"], ["Falar com um atendente"], "troca_online", encerrado=True)
        if LOJA.search(texto):
            self.esquecer(conversa_id)
            politica = (LojaRepository(self._conexao()).politica("troca") or {}).get("texto", "")
            loja_fisica = politica.split("Na loja física, ", 1)[-1]
            return RespostaFluxo(f"Na loja física, {loja_fisica}", ["Falar com um atendente"], "troca_loja",
                                 encerrado=True)
        return self._nao_entendi(conversa_id, estado, TEXTO["troca_canal"], OP_CANAL)

    # ------------------------------------------------------------------ F-HUMANO
    def _abrir_humano(self, conversa_id: str, estado: Estado) -> RespostaFluxo:
        self._guardar(conversa_id, estado)
        if estado.resumo:
            return RespostaFluxo(TEXTO["humano_consentimento"].format(resumo=estado.resumo), OP_CONSENTIMENTO,
                                 "humano_consentimento")
        return RespostaFluxo(TEXTO["humano_inicio"], passo="humano_resumo")

    def _passo_humano_resumo(self, conversa_id, estado, mensagem, texto) -> RespostaFluxo:
        resumo, _ = mascarar_dados_pessoais(" ".join(mensagem.split()))
        if len(texto) < 3:
            return self._nao_entendi(conversa_id, estado, "Em uma frase, o que você precisa?", [])
        if len(resumo) > LIMITE_RESUMO:
            resumo = resumo[: LIMITE_RESUMO - 1].rstrip() + "…"
        estado.resumo, estado.passo, estado.tentativas = resumo, "consentimento", 0
        return self._abrir_humano(conversa_id, estado)

    def _passo_humano_consentimento(self, conversa_id, estado, _mensagem, texto) -> RespostaFluxo:
        if NAO.search(texto):
            self.esquecer(conversa_id)
            return RespostaFluxo(TEXTO["humano_recusado"].format(contato=self._contato()), passo="humano_recusado",
                                 encerrado=True)
        if not SIM.search(texto):
            pergunta = "Posso compartilhar o resumo com a equipe? Responda sim ou não."
            return self._nao_entendi(conversa_id, estado, pergunta, OP_CONSENTIMENTO)
        self.esquecer(conversa_id)
        protocolo = AtendimentoRepository(self._conexao()).registrar(
            conversa_id, estado.resumo, motivo=estado.motivo, prioridade=estado.prioridade, consentimento=True)
        if self._dentro_do_horario():
            texto_final = TEXTO["humano_dentro"].format(protocolo=protocolo)
        else:
            texto_final = TEXTO["humano_fora"].format(protocolo=protocolo, horario=self._horario())
        return RespostaFluxo(texto_final, passo="humano_registrado", encerrado=True, protocolo=protocolo)

    # ------------------------------------------------------------------ horário e contato
    def _unidade(self) -> dict | None:
        unidades = LojaRepository(self._conexao()).unidades()
        return unidades[0] if unidades else None

    def _horario(self) -> str:
        unidade = self._unidade()
        return LojaRepository.horario_legivel(unidade["horarios"]) if unidade else "em horário comercial"

    def _dentro_do_horario(self) -> bool:
        unidade = self._unidade()
        if not unidade:
            return False
        agora = self._agora()
        hora = agora.strftime("%H:%M")
        return any(h["dia_semana"] == agora.isoweekday() and h["abre"] <= hora < h["fecha"]
                   for h in unidade["horarios"])

    def _contato(self) -> str:
        unidade = self._unidade()
        return f"{unidade['nome']}, telefone {unidade['telefone']}" if unidade else "os canais oficiais da loja"
