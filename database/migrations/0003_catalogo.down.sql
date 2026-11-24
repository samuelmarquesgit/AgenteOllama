DROP VIEW IF EXISTS vw_preco_atual;
DROP TABLE IF EXISTS estoques;
DROP TRIGGER IF EXISTS tg_produtos_atualizado;
DROP TRIGGER IF EXISTS tg_produto_precos_sem_sobreposicao_upd;
DROP TRIGGER IF EXISTS tg_produto_precos_sem_sobreposicao_ins;
DROP TABLE IF EXISTS produto_precos;
DROP TABLE IF EXISTS produto_imagens;
DROP TABLE IF EXISTS produto_especificacoes;
DROP TABLE IF EXISTS especificacoes;
DROP TABLE IF EXISTS produtos;
DROP TABLE IF EXISTS marcas;
-- categorias referencia a si mesma (pai) com RESTRICT: desfazer a hierarquia antes do DROP,
-- senão a exclusão implícita das linhas viola a FK num banco com dados.
UPDATE categorias SET categoria_pai_id = NULL;
DROP TABLE IF EXISTS categorias;
