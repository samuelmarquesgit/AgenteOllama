import ollama

MODELO = "llama3.2"

instrucao = (
    "Você é um agente de IA que atende clientes e fornecedores da nossa "
    "oficina mecânica. Responda em português, de forma educada e objetiva. "
    "Se não souber algo (preço, prazo, disponibilidade), diga que vai "
    "verificar com a equipe em vez de inventar."
)

historico = [{"role": "system", "content": instrucao}]

print("Agente pronto!!! Digite 'sair' para encerrar.")

while True:
    pergunta = input("\nVocê: ").strip()
    if pergunta.lower() == "sair":
        break
    if not pergunta:
        continue

    historico.append({"role": "user", "content": pergunta})

    try:
        resposta = ollama.chat(model=MODELO, messages=historico)
    except Exception as erro:
        print("Erro ao falar com o Ollama:", erro)
        print("Verifique se o Ollama está aberto e se rodou: ollama pull", MODELO)
        historico.pop()
        continue

    texto = resposta["message"]["content"]
    historico.append({"role": "assistant", "content": texto})
    print("Agente:", texto)
