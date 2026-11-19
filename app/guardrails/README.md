# app/guardrails

Todos os guardrails do agente. Catálogo completo (G01–G19), diagrama e exemplos:
**[docs/guardrails.md](../../docs/guardrails.md)**.

| Arquivo | Camada | Guardrails |
|---------|--------|------------|
| `entrada.py` | Entrada | G01 tamanho · G02 dados pessoais · G03 prompt injection |
| `escopo.py` | Escopo | G04 comercial sem LLM · G05 fora do escopo |
| `prompts.py` | Prompt | regras do prompt de sistema e mensagens padrão |
| `saida.py` | Saída | G06–G13 conteúdo proibido · G14 tamanho |
| `reescrita.py` | Reescrita | G15 pergunta de continuação válida |
| `aprendizado.py` | Aprendizado | G16–G18 o que pode ser gravado no banco |

Regra de ouro: **todo guardrail novo precisa de testes nos dois sentidos** (o que deve
bloquear e o que não pode bloquear) em `tests/test_guardrails.py`.
