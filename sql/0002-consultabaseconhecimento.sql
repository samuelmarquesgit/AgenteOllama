SELECT
    f.id,
    f.pergunta,
    f.resposta,
    c.nome AS categoria
FROM faq_perguntas f
JOIN faq_categorias c
    ON c.id = f.categoria_id
LEFT JOIN faq_variacoes v
    ON v.pergunta_id = f.id
WHERE f.ativo = TRUE
  AND (
      f.pergunta ILIKE '%furadeira%'
      OR v.variacao ILIKE '%furadeira%'
  )
GROUP BY
    f.id,
    f.pergunta,
    f.resposta,
    c.nome;