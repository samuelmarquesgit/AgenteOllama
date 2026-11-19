"""Versão de terminal do agente (mesmo banco e mesmas regras da API).

Uso:  .venv\\Scripts\\python agente.py
"""

from app.agente import Agente

ORIGEM = {
    "banco": "📚 banco",
    "agente": "🤖 agente IA (salvo no banco)",
    "fallback": "⚠️ sem resposta",
    "fora_do_escopo": "⚠️ fora do assunto",
    "saudacao": "👋",
}

agente = Agente()
print(f"Agente da loja de ferramentas pronto! ({len(agente.faqs)} perguntas no banco)")
print("Digite 'sair' para encerrar.")

while True:
    pergunta = input("\nVocê: ").strip()
    if pergunta.lower() == "sair":
        break
    if not pergunta:
        continue
    r = agente.responder(pergunta)
    print(f"Agente [{ORIGEM.get(r.origem, r.origem)}]:", r.answer)
