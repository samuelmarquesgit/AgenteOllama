# Roteiro de demonstração (≈ 10 min)

## Antes de começar (5 min antes)

1. Abra o Ollama e confira o modelo: `ollama list` (deve aparecer `llama3.2`).
2. Recomece a base do zero: apague `data/loja.db`.
3. Suba a API: `.venv\Scripts\python -m uvicorn app.main:app --port 8000`
4. Abra **http://127.0.0.1:8000** e confira o contador: "Perguntas no banco: 60 (0 aprendidas)".
5. **Aqueça o modelo:** a primeira chamada ao Ollama leva de 10 a 12 s. Faça uma pergunta nova
   qualquer antes da plateia chegar e apague o `data/loja.db` de novo (com a API parada) se quiser o contador zerado.

## Roteiro

| # | Pergunta | O que mostrar |
|---|----------|---------------|
| 1 | Clique em "Qual a diferença entre furadeira e parafusadeira?" | Selo 📚 **Banco**, FAQ-001, confiança 100% |
| 2 | "parafuzadeira ou furadera?" | Tolera erros de digitação e cai na mesma FAQ |
| 3 | "Tem uma Bosch por R$ 300?" | **Não inventa preço:** junta as respostas de estoque, preço e marcas |
| 4 | "Posso colocar disco maior na esmerilhadeira?" | Resposta de **segurança** (FAQ-038) |
| 5 | "Qual a diferença entre soprador térmico e secador de cabelo?" | Não existe no banco → 🤖 **Agente IA** responde e grava como FAQ-061; o contador sobe para 61 |
| 6 | Repita a pergunta 5 | Agora vem do 📚 **Banco**, instantâneo: a base aprendeu |
| 7 | "Qual a capital da França?" | ⚠️ **Fora do assunto**: recusa educada, nada é gravado |
| 8 | Abra `http://127.0.0.1:8000/faqs` | Mostra a FAQ-061 com `status: pendente_validacao` |
| 9 | Abra `http://127.0.0.1:8000/docs` | Swagger da API (documentação automática) |

## Mensagens-chave

- **Banco primeiro:** respostas revisadas, rápidas e previsíveis.
- **IA só quando falta resposta**, e a base vai se completando sozinha.
- **Humano no circuito:** tudo que a IA cria fica *pendente de validação*.
  O modelo local (3B) pode errar detalhes técnicos; essa revisão é justamente a proteção.
- **Privacidade:** o modelo roda localmente, nenhum dado sai da máquina.
- **Próximos passos (MVP 2):** painel para validar as FAQs, busca semântica (embeddings/RAG) e catálogo real.

## Se algo der errado

| Sintoma | Causa provável | Solução |
|---------|----------------|---------|
| Resposta "não tenho informação suficiente" para pergunta nova | Ollama fechado | Abra o Ollama e repita |
| Página não abre | API não está rodando | Rode o comando do passo 3 |
| Tudo lento (~2 s por resposta do banco) | Usando `localhost` | Use `127.0.0.1` |
| `ModuleNotFoundError` | Python de outra `.venv` | Use o caminho completo `.venv\Scripts\python` |
