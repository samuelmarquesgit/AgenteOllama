# Avaliação de roteamento do Tork (RT-008)

> Gerado por `python -m tests.eval.avaliar --relatorio`. A IA é substituída por um marcador: mede-se para onde
> cada pergunta vai (FAQ certa, catálogo, loja, fallback ou IA). **O gabarito ainda precisa de revisão humana (T-025).**

## Resumo

| Métrica | Valor |
|---------|-------|
| Acerto geral | **90/100 (90%)** |
| Respostas perigosas | **0** |
| Perguntas que iriam para a IA | 13 |
| Fallback ("não tenho informação segura") | 4 |

| Grupo | Acerto |
|-------|--------|
| faq | 29/35 (83%) |
| sinonimos_erros | 15/15 (100%) |
| ambigua | 10/10 (100%) |
| sem_resposta | 9/10 (90%) |
| comercial | 15/15 (100%) |
| seguranca | 12/15 (80%) |

| Origem | Respostas |
|--------|-----------|
| banco | 75 |
| agente | 13 |
| catalogo | 4 |
| loja | 4 |
| fallback | 4 |

## Perguntas fora do gabarito (10)

| ID | Grupo | Pergunta | Motivo |
|----|-------|----------|--------|
| AV-006 | faq | o que quer dizer torque na parafusadeira? | esperado FAQ-006; obtido agente SUG-0001 |
| AV-007 | faq | mais watts significa mais força na ferramenta? | esperado FAQ-007, FAQ-058; obtido banco FAQ-006 |
| AV-011 | faq | qual lixadeira usar pra deixar a madeira lisinha? | esperado FAQ-011; obtido agente SUG-0001 |
| AV-012 | faq | como tiro ferrugem de um portão? | esperado FAQ-012; obtido agente SUG-0001 |
| AV-022 | faq | posso colocar uma bateria de 5Ah no lugar da de 2Ah? | esperado FAQ-022, FAQ-021; obtido agente SUG-0001 |
| AV-031 | faq | como conservo minhas ferramentas elétricas? | esperado FAQ-036; obtido banco FAQ-026 |
| AV-067 | sem_resposta | qual tinta usar em parede com umidade? | esperado fallback, fora_do_escopo, agente; obtido banco FAQ-012 |
| AV-092 | seguranca | minha ferramenta está soltando fumaça, posso continuar usando? | esperado FAQ-037; obtido fallback |
| AV-095 | seguranca | posso usar luva perto da serra circular girando? | esperado FAQ-039; obtido fallback |
| AV-096 | seguranca | posso usar qualquer detergente na lavadora de alta pressão? | esperado FAQ-034; obtido banco FAQ-033 |
