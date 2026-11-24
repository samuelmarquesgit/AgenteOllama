# Catálogo dos seeds

> **Todos os dados de loja e catálogo são FICTÍCIOS**, para demonstração. Marcas, modelos, preços, estoques,
> endereços e telefones foram inventados; qualquer semelhança com marcas ou lojas reais é coincidência.

## Contagens (conferidas pelo verificador `python -m app.db.seeds`)

| Tabela | Registros | Fonte |
|--------|----------:|-------|
| faq_categorias | 8 | `knowledge/faq.json` |
| faq_perguntas | 60 | `knowledge/faq.json` |
| faq_variacoes | 77 | `knowledge/faq.json` |
| faq_palavras_chave | 321 | `knowledge/faq.json` |
| unidades | 2 | `database/seeds/data/loja.json` |
| unidade_horarios | 12 | `loja.json` (seg–sáb, domingo fechado) |
| formas_pagamento | 4 | `loja.json` |
| politicas | 6 | `loja.json` |
| categorias | 25 | `catalogo.json` (6 categorias-pai + 19 folhas) |
| marcas | 15 | `catalogo.json` (todas `ficticia = 1`) |
| produtos | 300 | `catalogo.json` (`FAKE-0001` a `FAKE-0300`) |
| especificacoes | 45 | `catalogo.json` |
| produto_especificacoes | 1.500 | 5 por produto |
| produto_precos | 600 | 2 vigências por produto (anterior e atual) |
| produto_imagens | 300 | placeholder local `/static/produtos/placeholder.svg` |
| estoques | 600 | 2 unidades × 300 produtos; ~16% zerados |

O plano de banco pede **150 FAQs e 450 variações**: a base atual tem 60 e 77. A complementação de conteúdo é a próxima tarefa do plano de entrega (`0018`, P0.4).

## Como o catálogo foi gerado

`database/seeds/gerar_catalogo.py`, com `SEED=2026` (determinístico: o mesmo arquivo a cada execução).

- **Por que não uma lista pronta da internet:** não foi encontrada uma lista aberta e licenciada de ferramentas com preços em reais. A API pública do Mercado Livre exige autenticação (HTTP 403), e coletar páginas de varejistas violaria os termos de uso. Datasets encontrados no Kaggle e no Hugging Face tinham licença indefinida ou eram pagos.
- **Preços:** sorteados dentro de **faixas aproximadas do varejo brasileiro de 2026** por tipo de produto, escaladas pela potência ou capacidade (referência informal, **não** é cotação de nenhuma loja). Terminam em ",90".
- **Coerência:** potência, encaixe (SDS-plus × SDS-max), diâmetro de disco, rotação máxima etc. são compatíveis com a categoria.

| Categoria | Produtos | Faixa de preço (R$) |
|-----------|---------:|---------------------|
| Furadeiras | 20 | 109,90 – 419,90 |
| Furadeiras de impacto | 22 | 159,90 – 689,90 |
| Marteletes | 16 | 559,90 – 2.469,90 |
| Parafusadeiras (bateria) | 24 | 299,90 – 1.019,90 |
| Esmerilhadeiras | 20 | 149,90 – 1.249,90 |
| Serras circulares | 16 | 379,90 – 1.089,90 |
| Serras tico-tico | 14 | 139,90 – 739,90 |
| Lixadeiras | 14 | 159,90 – 559,90 |
| Brocas (jogos) | 22 | 29,90 – 279,90 |
| Discos | 22 | 9,90 – 139,90 |
| Bits e pontas | 14 | 19,90 – 339,90 |
| Lâminas de serra | 12 | 19,90 – 249,90 |
| Baterias | 14 | 149,90 – 919,90 |
| Carregadores | 10 | 159,90 – 569,90 |
| Multímetros | 12 | 109,90 – 1.109,90 |
| Trenas e níveis a laser | 10 | 189,90 – 1.839,90 |
| EPI | 18 | 9,90 – 79,90 |
| Compressores | 10 | 339,90 – 3.189,90 |
| Lavadoras de alta pressão | 10 | 379,90 – 2.149,90 |

## Marcas fictícias

Torqmax · Voltrix · Ferrabraz · Brutus Pro · Metalix · Prumo · Agilis · Rochedo · Faiscar · Nivela · Serrano · Hexabit · Granitto · Bravon · Kalibra

## Repetir a execução com segurança

Os seeds usam **UPSERT pela chave natural** (`codigo`, `sku`, `nome`): rodar de novo atualiza, não duplica.
Variações, palavras-chave, especificações, preços e horários espelham o arquivo de origem (o que saiu do arquivo sai do banco).
Isso é verificado pelo teste `test_seed_e_idempotente`.
