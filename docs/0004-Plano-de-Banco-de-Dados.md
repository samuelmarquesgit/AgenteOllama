# 0004 — Plano de banco de dados (ToolExpert AI)

> **Instrução para agente de IA de desenvolvimento:** execute as tarefas na ordem, marque `[x]` somente após validar o critério de aceite, e registre evidências (comando, saída resumida e arquivos alterados) em `docs/db/EXECUTION_LOG.md`. Não presuma credenciais, não apague bancos existentes e não execute comandos destrutivos fora de um banco de desenvolvimento explicitamente autorizado.

## 0. Contrato de execução

- [ ] Inspecionar o repositório e identificar stack, gerenciador de pacotes, infraestrutura e convenções existentes.
- [ ] Confirmar se já existe banco PostgreSQL ou migrações; preservar estruturas existentes e propor alterações incrementais.
- [ ] Criar branch `feature/toolexpert-database` se o projeto usar Git; não sobrescrever alterações locais.
- [ ] Definir PostgreSQL 16+ como referência, usando versão compatível com o ambiente existente.
- [ ] Definir ambiente `development` isolado; obter configuração via variáveis `DATABASE_URL` ou `PGHOST`, `PGPORT`, `PGDATABASE`, `PGUSER`, `PGPASSWORD`.
- [ ] Garantir que segredos estejam em `.env` ignorado pelo Git; criar `.env.example` sem credenciais reais.
- [ ] Definir nomenclatura `snake_case`, PK `bigint generated ... as identity`, datas `timestamptz`, valores monetários `numeric(12,2)` e UTF-8.
- [ ] Documentar comandos para aplicar, reverter e validar migrações; escolher uma única ferramenta de migração (Prisma, TypeORM ou SQL versionado) conforme stack existente.
- [ ] Criar `docs/db/EXECUTION_LOG.md` e registrar decisões e bloqueios. Em caso de ambiguidade que possa causar perda de dados, parar e solicitar confirmação.

**Aceite:** configuração reproduzível e nenhum segredo versionado.

## 1. Estrutura de diretórios

- [ ] Criar `database/migrations/`, `database/seeds/`, `database/tests/` e `docs/db/` (adaptar se o projeto já tiver padrão).
- [ ] Criar `docs/db/README.md` com pré-requisitos e execução local.
- [ ] Criar `docs/db/DER.md` com entidades, cardinalidades e decisões de normalização.
- [ ] Criar `docs/db/DATA_DICTIONARY.md` com coluna, tipo, nulidade, regra e origem.
- [ ] Criar `docs/db/SEED_CATALOG.md` com contagens e características dos dados fictícios.
- [ ] Criar `docs/db/SECURITY.md` com política de acesso e retenção de conversas.

**Aceite:** estrutura documentada e adequada ao repositório.

## 2. Modelagem 3FN — MVP FAQ (implementar primeiro)

- [ ] Criar tabela `faq_categorias`: `id`, `nome` único, `descricao`, `ativo`, `criado_em`, `atualizado_em`.
- [ ] Criar tabela `faq_perguntas`: `id`, `categoria_id` FK, `pergunta`, `resposta`, `ativo`, `criado_em`, `atualizado_em`.
- [ ] Criar tabela `faq_variacoes`: `id`, `pergunta_id` FK, `variacao`, `criado_em`.
- [ ] Criar unicidade de `(pergunta_id, variacao)`; evitar duplicações semânticas no seed.
- [ ] Criar índices em `faq_perguntas(categoria_id, ativo)` e `faq_variacoes(pergunta_id)`.
- [ ] Definir `ON DELETE CASCADE` para variações quando uma pergunta for removida; para categorias, preferir `RESTRICT`.
- [ ] Implementar atualização consistente de `atualizado_em` na aplicação ou trigger, documentando a escolha.
- [ ] Criar migração inicial e migração de reversão ou mecanismo de rollback testável.
- [ ] Validar FKs, constraints, exclusão e atualização em testes automatizados.

**Aceite:** FAQ consultável, íntegro e com migração idempotente pelo mecanismo escolhido (não reaplicar SQL bruto cegamente).

## 3. Modelagem 3FN — catálogo de produtos (fase seguinte)

- [ ] Criar `categorias`: `id`, `nome`, `categoria_pai_id` FK nullable, `ativo`; impedir autorreferência e ciclos hierárquicos por validação adequada.
- [ ] Criar `marcas`: `id`, `nome` único, `ativo`.
- [ ] Criar `produtos`: `id`, `categoria_id` FK, `marca_id` FK, `sku` único, `nome`, `descricao`, `ativo`, timestamps.
- [ ] Criar `especificacoes`: `id`, `nome`, `unidade` nullable, `tipo_valor` (`texto`, `numero`, `booleano`); documentar validação de valores.
- [ ] Criar `produto_especificacoes`: `produto_id` FK, `especificacao_id` FK, `valor_texto` ou representação tipada definida no projeto, PK composta.
- [ ] Criar `produto_imagens`: `id`, `produto_id` FK, `url`, `texto_alternativo`, `ordem`; usar URLs fictícias locais ou placeholders sem dependência externa.
- [ ] Criar `produto_precos`: `id`, `produto_id` FK, `preco`, `inicio_vigencia`, `fim_vigencia` nullable; CHECK preço >= 0 e período válido; impedir vigências sobrepostas por produto na regra de negócio/constraint.
- [ ] Criar índices para busca por `sku`, categoria, marca e nome.
- [ ] Documentar que marca/modelo/compatibilidade só são fatos quando baseados em documentação validada; seeds são demonstrações fictícias.

**Aceite:** produtos sem preços duplicados conflitantes e especificações normalizadas.

## 4. Modelagem 3FN — atendimento e histórico (fase posterior)

- [ ] Criar `clientes`: `id`, `nome_exibicao` nullable, `email` nullable, `telefone` nullable, timestamps; usar somente dados sintéticos.
- [ ] Criar `canais_atendimento`: `id`, `codigo` único (`web`, `whatsapp`, `api`), `nome`.
- [ ] Criar `conversas`: `id`, `cliente_id` FK nullable, `canal_id` FK, `status`, `iniciada_em`, `encerrada_em` nullable.
- [ ] Criar `mensagens`: `id`, `conversa_id` FK, `papel` (`usuario`, `assistente`, `sistema`, `ferramenta`), `conteudo`, `criada_em`, `faq_pergunta_id` FK nullable.
- [ ] Criar índices por conversa e data; definir política de retenção e anonimização.
- [ ] Não registrar segredos, tokens, dados de pagamento nem dados pessoais desnecessários em mensagens.

**Aceite:** histórico consistente e segregação lógica de conversas.

## 5. Modelagem 3FN — comercial (somente evolução futura)

- [ ] Criar `locais_estoque`: `id`, `codigo` único, `nome`.
- [ ] Criar `estoques`: PK (`produto_id`, `local_id`), `quantidade` CHECK >= 0, `atualizado_em`.
- [ ] Criar `pedidos`: `id`, `cliente_id` FK, `status`, `criado_em`, `atualizado_em`; não persistir total derivável sem necessidade justificada.
- [ ] Criar `pedido_itens`: `id`, `pedido_id` FK, `produto_id` FK, `quantidade` CHECK > 0, `preco_unitario` CHECK >= 0; guardar preço histórico da transação.
- [ ] Criar índices nas FKs e testar integridade em cancelamentos e exclusões.
- [ ] Não implementar pagamento nem baixa automática de estoque no MVP.

**Aceite:** pedidos e estoque fictícios coerentes, sem operações financeiras reais.

## 6. Seeds fictícios e reprodutíveis

- [ ] Criar seed determinístico com `SEED=2026`, usando gerador local (ex.: Faker pt_BR) e identificadores estáveis ou UPSERT seguro.
- [ ] Popular 8 categorias de FAQ: furadeiras, parafusadeiras, serras, esmerilhadeiras, baterias, medição, segurança e atendimento comercial.
- [ ] Popular **150 FAQs** com respostas técnicas úteis, revisáveis e sem inventar capacidades de modelos reais.
- [ ] Popular **450 variações** (3 por pergunta), com frases naturais em português brasileiro.
- [ ] Cobrir dúvidas sobre aplicações, diferença entre impacto e martelete, torque, potência, bateria, brocas, discos, EPI, manutenção, compatibilidade, garantia, entrega e devolução.
- [ ] Garantir que respostas comerciais fictícias não afirmem preço, estoque ou prazo como se fossem reais; orientar consulta ao sistema quando necessário.
- [ ] Popular **25 categorias de produtos**, **15 marcas** e **300 produtos fictícios** com SKU `FAKE-0001` etc.; evitar associar especificações inventadas a modelos comerciais identificáveis.
- [ ] Popular **40 tipos de especificação** e **1.500 associações** produto-especificação coerentes com categorias.
- [ ] Popular preços positivos para todos os produtos, com vigências não sobrepostas.
- [ ] Popular **100 clientes sintéticos**, **500 conversas**, **2.000 mensagens**, **200 pedidos**, **500 itens de pedido** e estoques não negativos, apenas nas fases correspondentes.
- [ ] Separar seeds em `seed_mvp_faq`, `seed_catalogo`, `seed_atendimento` e `seed_comercial`.
- [ ] Tornar execução repetida segura: não duplicar registros; documentar procedimento de reset **apenas em ambiente isolado e autorizado**.
- [ ] Criar script que compare contagens esperadas com contagens reais e falhe em divergências.

**Aceite:** dados sintéticos, consistentes, reprodutíveis e sem dependência de internet.

## 7. Consultas e acesso para o agente MVP

- [ ] Criar consulta parametrizada de FAQs ativas por categoria.
- [ ] Criar consulta parametrizada por termo em pergunta e variações, com `ILIKE` e ordenação simples por relevância.
- [ ] Evitar SQL concatenado; usar parâmetros/prepared statements.
- [ ] Criar camada de repositório/serviço com métodos `listarCategorias`, `buscarPerguntas`, `obterRespostaPorId`.
- [ ] Definir resposta de fallback quando não houver correspondência suficiente: solicitar reformulação ou atendimento humano.
- [ ] Definir formato de retorno `{id, pergunta, resposta, categoria, score?}`; score somente se calculado.
- [ ] Não adicionar LLM, embeddings, pgvector ou RAG nesta fase.

**Aceite:** API ou script local retorna respostas corretas às perguntas de teste sem acessar serviços externos.

## 8. Testes automatizados e qualidade

- [ ] Testar migrações em banco PostgreSQL vazio.
- [ ] Testar rollback em banco descartável e reaplicação das migrações.
- [ ] Testar integridade referencial de todas as FKs.
- [ ] Testar unicidade de SKU, marca, categoria FAQ e variações por pergunta.
- [ ] Testar CHECKs de preço, quantidade e datas.
- [ ] Testar que nenhuma FAQ ativa tenha pergunta ou resposta vazia.
- [ ] Testar contagens exatas dos seeds e ausência de duplicação após segunda execução.
- [ ] Testar buscas com acentos, maiúsculas/minúsculas, termos inexistentes e tentativa de SQL injection.
- [ ] Validar amostra de 30 FAQs com revisão humana/técnica; não afirmar validação especializada sem revisão real.
- [ ] Rodar `EXPLAIN (ANALYZE, BUFFERS)` em ambiente de desenvolvimento para consultas principais e registrar resultados.
- [ ] Verificar que testes não dependem de dados pessoais reais.

**Aceite:** suíte de testes passa e evidências constam no log.

## 9. Segurança e operação

- [ ] Criar usuário de aplicação com permissões mínimas (`SELECT` para FAQ se o MVP for somente leitura); migrações usam papel separado.
- [ ] Não expor PostgreSQL diretamente à internet; configurar rede privada/local.
- [ ] Garantir backups e restauração testados para ambientes persistentes.
- [ ] Documentar retenção de mensagens, exclusão/anônimização e bases legais aplicáveis sob orientação responsável.
- [ ] Habilitar logs de erro sem registrar credenciais ou conteúdos sensíveis desnecessários.
- [ ] Criar health check de conectividade e instruções de troubleshooting.

**Aceite:** credenciais segregadas, privilégios mínimos e recuperação documentada.

## 10. Entrega e definição de pronto

- [ ] Entregar migrações versionadas e seeds separados por fase.
- [ ] Entregar `docs/db/DER.md`, `DATA_DICTIONARY.md`, `README.md`, `SECURITY.md` e `EXECUTION_LOG.md`.
- [ ] Entregar `.env.example` e comandos de instalação, migração, seed e teste.
- [ ] Gerar relatório final com tabelas criadas, registros por tabela, testes executados e pendências.
- [ ] Garantir que o **MVP 1** funcione somente com FAQ, sem depender de catálogo, clientes ou pedidos.
- [ ] Marcar como concluídas apenas tarefas efetivamente executadas e verificadas; manter as demais `[ ]`.

**Definição de pronto do MVP 1:** PostgreSQL acessível em desenvolvimento, três tabelas FAQ normalizadas, 150 perguntas com respostas, 450 variações, busca parametrizada, testes passando e documentação para reprodução.

## 11. Ordem operacional sugerida ao agente executor

1. Executar seções **0 → 1 → 2 → 6 (somente FAQ) → 7 → 8 (testes FAQ) → 9 (mínimo necessário) → 10 (entrega MVP)**.
2. **Parar e apresentar resultado do MVP 1** antes de iniciar catálogo, atendimento e comercial.
3. Após aprovação explícita, executar seções **3**, depois **4** e **5**, com os respectivos seeds e testes.
4. Em cada etapa, executar migração, seed, testes e registrar evidências. Se falhar, corrigir e repetir a validação sem mascarar erros.

## 12. Prompt de execução para IA de programação

> Você é engenheiro de dados sênior especializado em PostgreSQL e normalização relacional. Leia este arquivo integralmente e implemente **somente o MVP 1** na ordem estabelecida. Primeiro inspecione o repositório, preserve código existente e explique decisões. Crie migrações, seeds determinísticos, consultas parametrizadas, testes e documentação. Execute comandos apenas em banco de desenvolvimento autorizado. Não invente resultados de testes. Marque `[x]` exclusivamente nas tarefas concluídas e comprovadas. Ao final, informe os arquivos criados, comandos de reprodução, contagens reais, testes e pendências. Não inicie catálogo ou módulos comerciais sem aprovação.
