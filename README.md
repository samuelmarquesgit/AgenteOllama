# Agente de IA — Loja de Ferramentas (MVP 1)

Assistente virtual que tira dúvidas de clientes sobre ferramentas elétricas e eletrônicas.

## Como funciona

```
Cliente ──► POST /chat ──► 1. procura no banco SQLite (60 FAQs iniciais)
                              │ achou?  ──► responde com a resposta do banco  📚
                              │ não achou
                              ▼
                           2. pergunta ao agente de IA local (Ollama / llama3.2)  🤖
                              │
                              ▼
                           3. grava pergunta + resposta no banco (pendente_validacao)
                              → na próxima vez a resposta já sai do banco
```

Regras de segurança:
- Perguntas comerciais (preço, estoque, frete, pagamento) são sempre respondidas pelo banco e nunca passam pelo LLM.
- Perguntas fora do assunto (ex.: "capital da França") são recusadas e não são gravadas.
- Se o Ollama estiver desligado, o agente admite que não sabe e sugere atendimento humano.

## Pré-requisitos

- Python 3.12+
- [Ollama](https://ollama.com) instalado e aberto, com o modelo baixado: `ollama pull llama3.2`

## Instalação e execução (Windows / PowerShell)

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt

# Chat web + API
.venv\Scripts\python -m uvicorn app.main:app --port 8000
# abra http://127.0.0.1:8000

# ou versão de terminal
.venv\Scripts\python agente.py

```

O banco `data/loja.db` é criado e populado automaticamente na primeira execução
a partir de `knowledge/faq.json`. Para recomeçar do zero, apague `data/loja.db`.

## Endpoints

| Método | Rota      | Descrição |
|--------|-----------|-----------|
| GET    | `/`       | Página de chat |
| GET    | `/health` | `{"status":"ok","faqs":60,"aprendidas":0}` |
| POST   | `/chat`   | Envia `{"message":"Qual broca usar em concreto?"}` e recebe a resposta abaixo |
| GET    | `/faqs`   | Lista as perguntas cadastradas no banco |

Resposta de `/chat`:

```json
{ "answer": "Utilize broca adequada a concreto...", "matchedFaqId": "FAQ-013", "confidence": 1.0, "origem": "banco" }
```

`origem` pode ser `banco`, `agente`, `fallback`, `fora_do_escopo` ou `saudacao`.

## Testes

```powershell
.venv\Scripts\python -m pytest -q        # 355 testes, ~10 s, não precisam do Ollama
```

| Arquivo | O que cobre |
|---------|-------------|
| `tests/test_busca.py` | Normalização, plural, erros de digitação, pontuação, desempate |
| `tests/test_banco.py` | Criação e carga do SQLite, gravação de respostas aprendidas |
| `tests/test_agente.py` | Regras: banco → agente → grava; comercial sem LLM; fora do escopo; Ollama fora do ar |
| `tests/test_api.py` | `/chat`, `/health`, `/faqs`, validação, erro 500 sem detalhes, log sem dados do cliente |
| `tests/test_faq_json.py` | Integridade das 60 FAQs; cada pergunta e cada variação encontram a própria FAQ |
| `tests/test_frontend_e_cli.py` | Página de chat (endpoints, acessibilidade, sem `innerHTML`) e versão de terminal |

O Ollama é substituído por um falso nos testes (`tests/conftest.py`), e cada teste usa um banco temporário.

## Documentação

- [Arquitetura e algoritmo de busca](docs/arquitetura.md)
- [Referência da API](docs/api.md)
- [Manutenção da base de conhecimento](docs/base-de-conhecimento.md)
- [Roteiro de demonstração](docs/roteiro-demo.md)
- [Decisões técnicas](docs/decisions.md) · [Registro de prompts](docs/prompts.md) · [Changelog](CHANGELOG.md)
- [Checklist do projeto](docs/TASKS_AGENTE_LOJA_FERRAMENTAS.md)

## Convenções

- Branches: `feat/...`, `fix/...`, `docs/...`, `test/...`
- Commits e PRs: [Conventional Commits](https://www.conventionalcommits.org/pt-br/) (`feat:`, `fix:`, `docs:`, `test:`...)

## Estrutura

```
app/busca.py      normalização de texto + pontuação por palavras-chave
app/banco.py      SQLite: criação, carga inicial e gravação de respostas aprendidas
app/agente.py     regras: banco → agente IA → grava no banco
app/main.py       API FastAPI
static/index.html página de chat
knowledge/faq.json 60 FAQs iniciais (seed do banco)
tests/            testes automatizados
docs/             documentação, checklist, decisões e registro de prompts
sql/              esquema PostgreSQL planejado para versões futuras (não usado no MVP 1)
```

## Roteiro de demonstração

1. "Qual a diferença entre furadeira e parafusadeira?" → 📚 FAQ-001
2. "Tem uma Bosch por R$ 300?" → 📚 sem inventar preço/estoque
3. "Posso colocar disco maior na esmerilhadeira?" → 📚 resposta de segurança
4. "Qual a diferença entre soprador térmico e secador de cabelo?" → 🤖 agente responde e grava (FAQ-061)
5. Repita a pergunta 4 → agora vem do 📚 banco (o contador de perguntas sobe)
6. "Qual a capital da França?" → ⚠️ fora do assunto, nada é gravado
