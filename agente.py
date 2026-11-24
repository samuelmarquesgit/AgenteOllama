"""Versão de terminal do agente (mesmo banco, mesmas regras e guardrails da API).

Uso:  .venv\\Scripts\\python agente.py
"""

from app import config
from app.agente import Agente
from app.fluxos import Fluxos
from app.guardrails import mascarar_dados_pessoais
from app.memoria import Memoria

ORIGEM = {
    "banco": "📚 banco",
    "agente": "🤖 agente IA (salvo no banco)",
    "fallback": "⚠️ sem resposta",
    "fora_do_escopo": "⚠️ fora do assunto",
    "saudacao": "👋",
    "bloqueado": "🛡️ bloqueado",
    "fluxo": "🧭 atendimento guiado",
}
CONVERSA = "terminal"

config.carregar_env()  # .env opcional (RT-012)
agente = Agente()
memoria = Memoria()
fluxos = Fluxos(lambda: agente.con)
print(f"Agente da loja de ferramentas pronto! ({len(agente.faqs)} perguntas no banco)")
print("Digite 'sair' para encerrar ou 'nova' para começar outra conversa.")

while True:
    pergunta = input("\nVocê: ").strip()
    if pergunta.lower() == "sair":
        break
    if pergunta.lower() == "nova":
        memoria.esquecer(CONVERSA)
        fluxos.esquecer(CONVERSA)
        print("(nova conversa)")
        continue
    if not pergunta:
        continue
    fluxo = fluxos.tratar(CONVERSA, pergunta)  # troca e atendente ("cancelar" encerra)
    if fluxo:
        print(f"Agente [{ORIGEM['fluxo']}]:", fluxo.answer)
        if fluxo.opcoes:
            print("  opções: " + " | ".join(fluxo.opcoes))
        continue
    r = agente.responder(pergunta, memoria.historico(CONVERSA))
    if r.origem in ("banco", "agente"):
        memoria.registrar(CONVERSA, r.perguntaInterpretada or mascarar_dados_pessoais(pergunta)[0], r.answer)
    if r.perguntaInterpretada:
        print(f"(entendi como: {r.perguntaInterpretada})")
    print(f"Agente [{ORIGEM.get(r.origem, r.origem)}]:", r.answer)
