# API — referência

Base: `http://127.0.0.1:8000`. A documentação interativa (Swagger) gerada pelo FastAPI fica em `/docs`.

> No Windows, use `127.0.0.1` em vez de `localhost`: o `localhost` tenta IPv6 primeiro e
> acrescenta cerca de 2 s a cada requisição.

## `GET /health`

Mostra se a API está no ar e o tamanho da base.

```json
{ "status": "ok", "faqs": 60, "aprendidas": 0 }
```

## `POST /chat`

Envia a pergunta do cliente.

**Requisição**
```json
{ "message": "Qual broca usar em concreto?" }
```

**Resposta 200**
```json
{
  "answer": "Utilize broca adequada a concreto/alvenaria e compatível com a máquina. ...",
  "matchedFaqId": "FAQ-013",
  "confidence": 1.0,
  "origem": "banco"
}
```

| Campo | Descrição |
|-------|-----------|
| `answer` | Texto para mostrar ao cliente |
| `matchedFaqId` | ID da FAQ usada (para auditoria); `null` em fallback, saudação ou fora do escopo |
| `confidence` | Nota da busca, de 0 a 1 (`0` quando a resposta veio do agente) |
| `origem` | `banco`, `agente`, `fallback`, `fora_do_escopo` ou `saudacao` |

**Exemplos de `origem`**

| Pergunta | origem | matchedFaqId |
|----------|--------|--------------|
| "Qual a diferença entre furadeira e parafusadeira?" | `banco` | `FAQ-001` |
| "Tem uma Bosch por R$ 300?" | `banco` | `FAQ-041` (junta estoque + preço + marcas) |
| "Qual a diferença entre soprador térmico e secador de cabelo?" (1ª vez) | `agente` | `FAQ-061` (recém-criada) |
| A mesma pergunta (2ª vez) | `banco` | `FAQ-061` |
| "Qual a capital da França?" | `fora_do_escopo` | `null` |
| "oi" | `saudacao` | `null` |

**Erros**

| Código | Quando |
|--------|--------|
| 422 | `message` ausente, vazia, só com espaços ou com mais de 500 caracteres |
| 500 | Erro inesperado: `{"detail": "Erro interno. Tente novamente."}` |

**Exemplo em PowerShell**
```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/chat `
  -ContentType "application/json; charset=utf-8" `
  -Body ([Text.Encoding]::UTF8.GetBytes('{"message":"Qual broca usar em concreto?"}'))
```

## `GET /faqs`

Lista as perguntas do banco (útil na demo, para mostrar a base crescendo).

```json
[
  { "id": "FAQ-001", "categoria": "escolha_de_ferramentas", "pergunta": "Qual a diferença entre furadeira e parafusadeira?", "status": "rascunho" },
  { "id": "FAQ-061", "categoria": "aprendida", "pergunta": "Qual a diferença entre soprador térmico e secador de cabelo?", "status": "pendente_validacao" }
]
```

## `GET /`

Serve a página de chat (`static/index.html`).
