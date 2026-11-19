"""Versão de terminal do agente (mesmo banco, mesmas regras e guardrails da API).

Uso:  .venv\\Scripts\\python agente.py
"""

from app.agente import Agente
from app.guardrails import mascarar_dados_pessoais
from app.memoria import Memoria

ORIGEM = {
    "banco": "📚 banco",
    "agente": "🤖 agente IA (salvo no banco)",
    "fallback": "⚠️ sem resposta",
    "fora_do_escopo": "⚠️ fora do assunto",
    "saudacao": "👋",
    "bloqueado": "🛡️ bloqueado",
}
CONVERSA = "terminal"

agente = Agente()
memoria = Memoria()
print(f"Agente da loja de ferramentas pronto! ({len(agente.faqs)} perguntas no banco)")
print("Digite 'sair' para encerrar ou 'nova' para começar outra conversa.")

while True:
    pergunta = input("\nVocê: ").strip()
    if pergunta.lower() == "sair":
        break
    if pergunta.lower() == "nova":
        memoria.esquecer(CONVERSA)
        print("(nova conversa)")
        continue
    if not pergunta:
        continue
    r = agente.responder(pergunta, memoria.historico(CONVERSA))
    if r.origem in ("banco", "agente"):
        memoria.registrar(CONVERSA, r.perguntaInterpretada or mascarar_dados_pessoais(pergunta)[0], r.answer)
    if r.perguntaInterpretada:
        print(f"(entendi como: {r.perguntaInterpretada})")
    print(f"Agente [{ORIGEM.get(r.origem, r.origem)}]:", r.answer)
