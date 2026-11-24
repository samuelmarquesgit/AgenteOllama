# Avaliação de roteamento do Tork (RT-008)

> Gerado por `python -m tests.eval.avaliar --relatorio`. A IA é substituída por um marcador: mede-se para onde
> cada pergunta vai (FAQ certa, catálogo, loja, fallback ou IA). **O gabarito ainda precisa de revisão humana (T-025).**

## Resumo

| Métrica | Valor |
|---------|-------|
| Acerto geral | **95/100 (95%)** |
| Respostas perigosas | **0** |
| Perguntas que iriam para a IA | 13 |
| Fallback ("não tenho informação segura") | 2 |

| Grupo | Acerto |
|-------|--------|
| faq | 31/35 (89%) |
| sinonimos_erros | 15/15 (100%) |
| ambigua | 10/10 (100%) |
| sem_resposta | 9/10 (90%) |
| comercial | 15/15 (100%) |
| seguranca | 15/15 (100%) |

| Origem | Respostas |
|--------|-----------|
| banco | 77 |
| agente | 13 |
| catalogo | 4 |
| loja | 4 |
| fallback | 2 |

## Perguntas fora do gabarito (5)

| ID | Grupo | Pergunta | Motivo |
|----|-------|----------|--------|
| AV-006 | faq | o que quer dizer torque na parafusadeira? | esperado FAQ-006; obtido agente SUG-0001 |
| AV-011 | faq | qual lixadeira usar pra deixar a madeira lisinha? | esperado FAQ-011; obtido agente SUG-0001 |
| AV-012 | faq | como tiro ferrugem de um portão? | esperado FAQ-012; obtido agente SUG-0001 |
| AV-022 | faq | posso colocar uma bateria de 5Ah no lugar da de 2Ah? | esperado FAQ-022, FAQ-021; obtido agente SUG-0001 |
| AV-067 | sem_resposta | qual tinta usar em parede com umidade? | esperado fallback, fora_do_escopo, agente; obtido banco FAQ-012 |
