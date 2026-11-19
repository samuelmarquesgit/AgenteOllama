"""API do agente.

GET  /          -> página de chat
GET  /health    -> status e quantidade de perguntas no banco
POST /chat      -> {"message": "..."} -> {"answer", "matchedFaqId", "confidence", "origem"}
GET  /faqs      -> perguntas cadastradas (para mostrar a base crescendo na demo)
"""

import logging
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

from app.agente import Agente

PASTA_STATIC = Path(__file__).resolve().parent.parent / "static"
LIMITE_CARACTERES = 500

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("agente")
app = FastAPI(title="Agente da loja de ferramentas", version="0.1.0")
agente = Agente()


class Pergunta(BaseModel):
    message: str = Field(min_length=1, max_length=LIMITE_CARACTERES)


class RespostaChat(BaseModel):
    answer: str
    matchedFaqId: str | None
    confidence: float
    origem: str


@app.exception_handler(Exception)
async def erro_generico(request: Request, exc: Exception):
    # Não expõe detalhes internos para o cliente.
    log.exception("Erro inesperado em %s", request.url.path)
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
    resposta = agente.responder(pergunta.message)
    # Métrica técnica sem guardar o texto do cliente no log.
    log.info("chat faq=%s nota=%.2f origem=%s", resposta.matchedFaqId, resposta.confidence, resposta.origem)
    return resposta.para_dict()


@app.get("/faqs")
def faqs():
    return [
        {"id": f.id, "categoria": f.categoria, "pergunta": f.pergunta, "status": f.status}
        for f in agente.faqs
    ]


@app.get("/")
def pagina():
    return FileResponse(PASTA_STATIC / "index.html")
