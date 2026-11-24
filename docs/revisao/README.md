# Revisão humana da base de conhecimento (P1.7 / T-025)

A planilha [`planilha_revisao_faq.csv`](planilha_revisao_faq.csv) traz **todas as 41 FAQs de risco alto** e mais **30 FAQs sorteadas** entre as demais, com semente fixa: 71 linhas no total. Ela abre direto no Excel, com separador `;` e acentos em UTF-8.

## Como revisar

1. Para cada linha, leia a `pergunta` e a `resposta` e preencha:
   - `decisao`: `aprovar`, `ajustar` ou `rejeitar`;
   - `resposta_corrigida`: obrigatória quando a decisão for `ajustar`;
   - `revisor`: suas **iniciais** (não use o nome completo nem o e-mail);
   - `data`: no formato `AAAA-MM-DD`;
   - `observacoes`: opcional, por exemplo "confirmar com o manual do fabricante".
2. Priorize as linhas de risco **alto** (eletricidade, discos, solda, baterias) e as respostas do CDC (trocas e garantia), que também precisam de revisão jurídica (T-032).
3. Salve no mesmo formato e aplique:

```powershell
.venv\Scripts\python -m app.db.planilha_revisao resumo     # quantas linhas já têm decisão
.venv\Scripts\python -m app.db.planilha_revisao importar   # aplica no knowledge/faq.json
```

- `aprovar` muda o status para `validado` e grava `revisado_em`.
- `ajustar` troca a resposta e também marca como `validado`.
- `rejeitar` marca como `inativo`: a FAQ sai da busca, mas continua no histórico.
- Linhas sem decisão são ignoradas. Se **qualquer** linha preenchida tiver erro, nada é alterado e o comando lista o que corrigir.
- Reinicie a API depois de importar: o seed sincroniza o banco pelo hash do arquivo.
- O chat mostra "conteúdo ainda não revisado por especialista" para tudo que não é `validado`.

Para gerar a planilha de novo depois de mudar a base: `python -m app.db.planilha_revisao gerar`. Isso apaga as decisões ainda não importadas.
