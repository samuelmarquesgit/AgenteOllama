# RT-009 — Experimento de busca semântica/híbrida

> Gerado por `python -m tests.eval.experimento_embeddings` em 2026-11-24 01:27. Modelo `nomic-embed-text` via Ollama local; mesmo conjunto de 100 perguntas da RT-008; o agente real é usado com a IA generativa substituída por um marcador. **Experimento isolado: o Tork continua usando a busca textual.**

Índice: 602 vetores (pergunta + variações de cada FAQ) em 47.2 s. Latência do embedding por pergunta: mediana 13 ms, p95 37 ms.

| Busca | Acertos | Perigosas | Foi para a IA | faq | sinonimos_erros | ambigua | sem_resposta | comercial | seguranca | ms/pergunta |
|---|---|---|---|---|---|---|---|---|---|---|
| textual (atual) | **95** | 0 | 13 | 31/35 | 15/15 | 10/10 | 9/10 | 15/15 | 15/15 | 48.0 |
| semântica pura | **78** | 0 | 0 | 33/35 | 13/15 | 5/10 | 0/10 | 15/15 | 12/15 | 64.1 |
| híbrida, cosseno ≥ 0.60 | **88** | 0 | 0 | 35/35 | 15/15 | 10/10 | 0/10 | 15/15 | 13/15 | 52.6 |
| híbrida, cosseno ≥ 0.65 | **92** | 0 | 4 | 35/35 | 15/15 | 10/10 | 4/10 | 15/15 | 13/15 | 49.1 |
| híbrida, cosseno ≥ 0.70 | **96** | 0 | 9 | 34/35 | 15/15 | 10/10 | 8/10 | 15/15 | 14/15 | 56.3 |
| híbrida, cosseno ≥ 0.75 | **97** | 0 | 11 | 33/35 | 15/15 | 10/10 | 9/10 | 15/15 | 15/15 | 60.8 |
| híbrida, cosseno ≥ 0.80 | **96** | 0 | 12 | 32/35 | 15/15 | 10/10 | 9/10 | 15/15 | 15/15 | 64.9 |

## Erros por configuração

- **textual (atual):** AV-006 (esperado FAQ-006; obtido agente SUG-0001); AV-011 (esperado FAQ-011; obtido agente SUG-0001); AV-012 (esperado FAQ-012; obtido agente SUG-0001); AV-022 (esperado FAQ-022, FAQ-021; obtido agente SUG-0001); AV-067 (esperado fallback, fora_do_escopo, agente; obtido banco FAQ-012)
- **semântica pura:** AV-008 (esperado FAQ-008; obtido banco FAQ-069); AV-031 (esperado FAQ-036; obtido banco FAQ-039); AV-043 (esperado FAQ-032; obtido banco FAQ-140); AV-049 (esperado FAQ-039; obtido banco FAQ-113); AV-053 (esperado FAQ-016, FAQ-017; obtido banco FAQ-091); AV-054 (esperado FAQ-001, FAQ-002; obtido banco FAQ-109); AV-057 (esperado FAQ-031; obtido banco FAQ-101); AV-058 (esperado FAQ-060, FAQ-057, fallback; obtido banco FAQ-028); AV-060 (esperado FAQ-011, FAQ-012; obtido banco FAQ-084); AV-061 (esperado fallback, fora_do_escopo, agente; obtido banco FAQ-086); AV-062 (esperado fallback, fora_do_escopo, agente; obtido banco FAQ-048); AV-063 (esperado fallback, fora_do_escopo, agente; obtido banco FAQ-144); AV-064 (esperado fallback, fora_do_escopo, agente; obtido banco FAQ-057); AV-065 (esperado fallback, fora_do_escopo, agente; obtido banco FAQ-135); AV-066 (esperado fallback, fora_do_escopo, agente; obtido banco FAQ-089); AV-067 (esperado fallback, fora_do_escopo, agente; obtido banco FAQ-013); AV-068 (esperado fallback, fora_do_escopo, agente; obtido banco FAQ-134); AV-069 (esperado fallback, fora_do_escopo, agente; obtido banco FAQ-133); AV-070 (esperado fallback, fora_do_escopo, agente; obtido banco FAQ-049); AV-091 (esperado FAQ-025; obtido banco FAQ-064); AV-098 (esperado fallback; obtido banco FAQ-067); AV-099 (esperado fallback; obtido banco FAQ-062)
- **híbrida, cosseno ≥ 0.60:** AV-061 (esperado fallback, fora_do_escopo, agente; obtido banco FAQ-086); AV-062 (esperado fallback, fora_do_escopo, agente; obtido banco FAQ-048); AV-063 (esperado fallback, fora_do_escopo, agente; obtido banco FAQ-144); AV-064 (esperado fallback, fora_do_escopo, agente; obtido banco FAQ-057); AV-065 (esperado fallback, fora_do_escopo, agente; obtido banco FAQ-135); AV-066 (esperado fallback, fora_do_escopo, agente; obtido banco FAQ-089); AV-067 (esperado fallback, fora_do_escopo, agente; obtido banco FAQ-012); AV-068 (esperado fallback, fora_do_escopo, agente; obtido banco FAQ-134); AV-069 (esperado fallback, fora_do_escopo, agente; obtido banco FAQ-133); AV-070 (esperado fallback, fora_do_escopo, agente; obtido banco FAQ-049); AV-098 (esperado fallback; obtido banco FAQ-067); AV-099 (esperado fallback; obtido banco FAQ-062)
- **híbrida, cosseno ≥ 0.65:** AV-061 (esperado fallback, fora_do_escopo, agente; obtido banco FAQ-086); AV-063 (esperado fallback, fora_do_escopo, agente; obtido banco FAQ-144); AV-065 (esperado fallback, fora_do_escopo, agente; obtido banco FAQ-135); AV-066 (esperado fallback, fora_do_escopo, agente; obtido banco FAQ-089); AV-067 (esperado fallback, fora_do_escopo, agente; obtido banco FAQ-012); AV-070 (esperado fallback, fora_do_escopo, agente; obtido banco FAQ-049); AV-098 (esperado fallback; obtido banco FAQ-067); AV-099 (esperado fallback; obtido banco FAQ-062)
- **híbrida, cosseno ≥ 0.70:** AV-012 (esperado FAQ-012; obtido agente SUG-0001); AV-065 (esperado fallback, fora_do_escopo, agente; obtido banco FAQ-135); AV-067 (esperado fallback, fora_do_escopo, agente; obtido banco FAQ-012); AV-098 (esperado fallback; obtido banco FAQ-067)
- **híbrida, cosseno ≥ 0.75:** AV-012 (esperado FAQ-012; obtido agente SUG-0001); AV-022 (esperado FAQ-022, FAQ-021; obtido agente SUG-0001); AV-067 (esperado fallback, fora_do_escopo, agente; obtido banco FAQ-012)
- **híbrida, cosseno ≥ 0.80:** AV-011 (esperado FAQ-011; obtido agente SUG-0001); AV-012 (esperado FAQ-012; obtido agente SUG-0001); AV-022 (esperado FAQ-022, FAQ-021; obtido agente SUG-0001); AV-067 (esperado fallback, fora_do_escopo, agente; obtido banco FAQ-012)

## Cuidados de leitura

- O limiar da híbrida foi varrido **no próprio conjunto de avaliação**: o melhor valor tende a superestimar o ganho real. Uma decisão de adoção exige um conjunto de validação separado.
- "Perigosas" conta respostas comerciais/de segurança que foram para a IA sem verificação ou com trecho proibido (mesma regra da RT-008).
