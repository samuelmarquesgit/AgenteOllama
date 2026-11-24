"""API do agente.

GET    /                       -> página de chat
GET    /health                 -> status e quantidade de perguntas no banco
POST   /chat                   -> {"message": "...", "conversationId": "..."} -> resposta
DELETE /conversas/{id}         -> esquece o histórico de uma conversa
GET    /faqs                   -> perguntas cadastradas (para mostrar a base crescendo na demo)
GET    /produtos               -> catálogo fictício (filtros: categoria, alimentacao, marca, preco_max, limite)
GET    /produtos/{sku}         -> detalhes, especificações e estoque por unidade
GET    /loja                   -> unidades, horários, formas de pagamento e políticas
"""

import logging
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.agente import Agente
from app.guardrails import LIMITE_CARACTERES, mascarar_dados_pessoais
from app.db.repositorios import CatalogoRepository, FiltroProdutos, LojaRepository
from app.intencoes import produto_publico
from app.memoria import Memoria

PASTA_STATIC = Path(__file__).resolve().parent.parent / "static"
ORIGENS_COM_CONTEXTO = {"banco", "agente", "catalogo", "loja"}

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("agente")
app = FastAPI(title="Agente da loja de ferramentas", version="0.3.0")
agente = Agente()
memoria = Memoria()
app.mount("/static", StaticFiles(directory=PASTA_STATIC), name="static")


class Pergunta(BaseModel):
    message: str = Field(min_length=1, max_length=LIMITE_CARACTERES)
    conversationId: str | None = Field(default=None, max_length=64, pattern=r"^[A-Za-z0-9_-]+$")


class RespostaChat(BaseModel):
    answer: str
    matchedFaqId: str | None
    confidence: float
    origem: str
    perguntaInterpretada: str | None = None
    guardrails: list[str] = []
    produtos: list[dict] = []


@app.exception_handler(Exception)
async def erro_generico(request: Request, exc: Exception):
    # Não expõe detalhes internos para o cliente.
    # Registra a rota (modelo fixo), nunca o caminho bruto enviado pelo cliente (evita log injection).
    rota = getattr(request.scope.get("route"), "path", "desconhecida")
    log.exception("Erro inesperado em %s %s", request.method, rota)
    return JSONResponse(status_code=500, content={"detail": "Erro interno. Tente novamente."})


@app.get("/health")
def health():
    total = len(agente.faqs)
    aprendidas = sum(1 for f in agente.faqs if f.categoria == "aprendida")
    return {"status": "ok", "faqs": total, "aprendidas": aprendidas}


@app.post("/chat", response_model=RespostaChat)
def chat(pergunta: Pergunta):
    if not pergunta.message.strip():
        return JSONResponse(status_code=422, content={"detail": "Mensagem vazia."})

    historico = memoria.historico(pergunta.conversationId)
    resposta = agente.responder(pergunta.message, historico)

    # Só respostas úteis entram no contexto; nunca com dados pessoais.
    if resposta.origem in ORIGENS_COM_CONTEXTO:
        pergunta_segura = resposta.perguntaInterpretada or mascarar_dados_pessoais(pergunta.message.strip())[0]
        memoria.registrar(pergunta.conversationId, pergunta_segura, resposta.answer)

    # Métrica técnica sem guardar o texto do cliente no log.
    log.info(
        "chat faq=%s nota=%.2f origem=%s contexto=%d reescrita=%s guardrails=%s",
        resposta.matchedFaqId, resposta.confidence, resposta.origem, len(historico),
        resposta.perguntaInterpretada is not None, ",".join(resposta.guardrails) or "-",
    )
    return resposta.para_dict()


@app.delete("/conversas/{conversa_id}", status_code=204)
def esquecer_conversa(conversa_id: str):
    memoria.esquecer(conversa_id)


@app.get("/faqs")
def faqs():
    return [
        {"id": f.id, "categoria": f.categoria, "pergunta": f.pergunta, "status": f.status}
        for f in agente.faqs
    ]


@app.get("/produtos")
def produtos(
    categoria: list[str] = Query(default=[]),
    alimentacao: list[str] = Query(default=[]),
    marca: str | None = None,
    preco_max: float | None = Query(default=None, ge=0),
    limite: int = Query(default=20, ge=1, le=100),
):
    filtro = FiltroProdutos(categorias=categoria, alimentacao=alimentacao, marca=marca,
                            preco_max_centavos=int(preco_max * 100) if preco_max is not None else None, limite=limite)
    return [produto_publico(p) for p in CatalogoRepository(agente.con).buscar(filtro)]


@app.get("/produtos/{sku}", responses={404: {"description": "Produto não encontrado."}})
def produto(sku: str):
    p = CatalogoRepository(agente.con).obter(sku)
    if not p:
        raise HTTPException(status_code=404, detail="Produto não encontrado.")
    return p


@app.get("/loja")
def loja():
    repo = LojaRepository(agente.con)
    return {
        "aviso": "Dados fictícios de demonstração.",
        "unidades": repo.unidades(),
        "formas_pagamento": repo.formas_pagamento(),
        "politicas": [repo.politica(c) for c in ("pagamento", "troca", "garantia", "frete", "retirada", "atendimento_humano")],
    }


@app.get("/")
def pagina():
    return FileResponse(PASTA_STATIC / "index.html")
