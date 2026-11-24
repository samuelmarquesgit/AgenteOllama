# 0017 — Registro de prompts

## P001 — Planejar e executar o MVP básico (2026-11-19)
**Prompt (resumo):** planejar e executar um projeto básico e simples de agente de IA
para uma loja de ferramentas eletrônicas, seguindo `docs/0003-Requisitos-do-Produto.md`.

## P002 — Ajuste de escopo para demo em 30 minutos (2026-11-19)
**Prompt (resumo):** como especialista em frontend, um front básico e didático para
demonstração; como especialista em backend, perguntas e respostas em SQLite com uma
API básica que consulta o banco; se a pergunta não existir, consultar o agente e ir
completando a base de dados.

**Resultado:** API FastAPI (`/chat`, `/health`, `/faqs`), banco SQLite com 60 FAQs,
fallback para Ollama (llama3.2) que grava as novas respostas, página de chat com selo
de origem (📚 banco / 🤖 agente) e contador da base, 23 testes automatizados.

## P003 — Documentação completa e publicação (2026-11-19)
**Prompt (resumo):** criar toda a documentação e subir o que foi feito no GitHub.

**Resultado:** `docs/0011-Arquitetura-Atual.md`, `docs/0012-Referencia-da-API.md`, `docs/0014-Base-de-Conhecimento.md`,
`docs/0015-Roteiro-de-Demonstracao.md`, `CHANGELOG.md`, README com índice e checklist atualizado.

## P004 — Suíte de testes (2026-11-19)
**Prompt (resumo):** criar todos os testes necessários para o projeto.

**Resultado:** 355 testes em 6 arquivos (busca, banco, agente, API, integridade da FAQ,
frontend e terminal). A suíte encontrou e corrigiu 2 bugs de busca (desempate de pergunta
idêntica e voltagens sem unidade).

## P005 — Commit e PR semânticos (2026-11-19)
**Prompt (resumo):** criar um commit semântico com uma PR semântica e subir para o GitHub.

## P006 — Contexto da conversa (2026-11-19)
**Prompt (resumo):** a IA não está continuando no contexto anterior; o que podemos fazer para que ela continue a conversa no contexto?

**Resultado:** `conversationId` + memória em RAM + reescrita da pergunta de continuação pelo Ollama;
o agente recebe o histórico e o banco grava só perguntas completas.

## P007 — Pasta de guardrails (2026-11-19)
**Prompt (resumo):** preciso de uma pasta somente com todos os guardrails para não ocorrer problemas; planeje e faça.

**Resultado:** `app/guardrails/` com 19 guardrails (G01–G19) em 6 módulos, `docs/0013-Guardrails.md` e testes
nos dois sentidos (bloqueia o que deve e não bloqueia o legítimo, incluindo as 60 respostas oficiais).

## P008 — Commit e PR (2026-11-19)
**Prompt (resumo):** subir as mudanças de contexto e guardrails no GitHub com commit semântico.


## P009 — Replanejamento para profissionalização (2026-11-19)
**Prompt (resumo):** depois da demonstração do MVP, profissionalizar o projeto: ler
`0003-Requisitos-do-Produto.md` e `0004-Plano-de-Banco-de-Dados.md`, replanejar tudo
e criar uma identidade visual para o atendente.

**Resultado:** `docs/0005-Plano-de-Profissionalizacao.md` (diagnóstico, 11 decisões para aprovar,
arquitetura alvo, fases F0–F8 com aceite, processo de trabalho, riscos) e
`docs/0009-Identidade-Visual.md` com o atendente **Tork** (avatar, logo, favicon em `static/brand/`,
paleta verificada para WCAG AA, tipografia e tom de voz).

## P010 — Plano v2: o que os clientes perguntam (2026-11-23)
**Prompt (resumo):** melhorar e revisar o plano, pesquisar o que as pessoas perguntam em chats de lojas de
ferramentas e incorporar um roteiro de chatbot (boas-vindas, menu, fluxos, respostas rápidas, encerramento).

**Resultado:** plano v2 (`0005`), `0008-Desenho-Conversacional.md` (25 intenções, 5 fluxos, escalonamento,
métricas, regras do CDC, pesquisa com fontes) e `0010-Stack-e-Ferramentas.md`.

## P011 — Documentação numerada, análise crítica e tasks de reinício (2026-11-23)
**Prompt (resumo):** ler todo o contexto e a documentação, numerar (0001-Contexto, 0002-Indice…) deixando o mais
profissional possível, e criar um arquivo de tasks como se o projeto fosse reiniciado, aplicando a todas as tasks
11 perguntas críticas (pontos fracos, motivos de fracasso, suposições, alternativas, mais simples × mais robusta,
outras áreas, dados contrários, notas de custo/tempo/risco, o que falta, denominador comum, sem concordar por educação).

**Resultado:** 17 documentos numerados com índice; `0006-Analise-Critica.md` (plano v2 com nota 9–11/15,
recomendação de cortar ~40% e criar a fase de descoberta); `0007-Tasks-Reinicio-do-Projeto.md` (10 épicos com as 11
perguntas, 55 tasks com crítica compacta e nota C/T/R, ~70 dias-pessoa, cortes por prazo).

## P012 — Prazo de entrega (2026-11-23)
**Prompt (resumo):** prazo final em 29/11 até 00:00, com possibilidade de estender até 30/11/2026 às 22:00.

**Resultado:** `0018-Plano-de-Entrega-29-11.md`. O `0007` (~70 dias-pessoa) não cabe em ~5 dias; o plano de entrega
fica com o núcleo do DB §10 (Postgres, 150/450, busca parametrizada, testes, `docs/db/`) como P0, a identidade e o menu
como P1, cronograma diário até sábado 28/11, extensão só como reserva e as 11 perguntas aplicadas.

## P013 — Fluxograma completo em Mermaid (2026-11-23)
**Prompt (resumo):** criar primeiro um fluxograma completo com o Mermaid.

**Resultado:** `0019-Fluxograma-do-Sistema.md` com o caminho completo de uma mensagem (entrada, guardrails, menu,
contexto, banco, IA, aprendizado, curadoria e resposta) e diagramas de componentes, F-TROCA, F-HUMANO, escada de
fallback, ciclo de vida da resposta, pipeline de dados, fluxo de trabalho e cronograma (Gantt).

## P014 — Banco normalizado e base fake de produtos (2026-11-23)
**Prompt (resumo):** deixar no SQLite por enquanto (Docker depois); entrega no repositório do GitHub; começar
imediatamente, com o banco todo normalizado; criar uma base totalmente fake de produtos e preços para apresentação,
pegando na internet uma lista pronta.

**Resultado:** 19 tabelas em 3FN (4 migrações up/down), seeds idempotentes, repositórios com SQL parametrizado,
catálogo fictício de 300 produtos com preços e estoque, respostas de produto e loja no chat (com cards), `docs/db/`
e 687 testes. Não havia lista pronta e licenciada na internet (Mercado Livre exige autenticação; raspar varejistas
viola os termos), então o catálogo foi gerado com marcas inventadas e preços em faixas realistas (D028).

## P015 — Falha do SonarCloud na PR #2 (2026-11-23)
**Prompt (resumo):** o último commit falhou no SonarCloud (Security Rating C), mas o Sonar nunca foi configurado no projeto.

**Resultado:** a análise vem do aplicativo SonarQube Cloud instalado na conta do GitHub (não há configuração no
repositório). O projeto no SonarCloud é privado, então os detalhes exigem login. Endurecidos os dois candidatos mais
prováveis: ID de conversa com `crypto.getRandomValues` e log de erro sem o caminho bruto da requisição.


## P016 — PR do banco fora da main e Quality Gate reprovado (2026-11-23)
**Prompt (resumo):** não consigo realizar a PR; ler o ambiente do projeto no GitHub e ajudar a resolver.

**Diagnóstico:** a PR #3 (empilhada) foi mergeada na branch `docs/replanejamento-profissionalizacao` depois que a
#2 já tinha ido para a `main`, então o banco ficou fora da `main` e não havia PR aberta. O SonarQube Cloud (aplicativo
do GitHub) reprovava por segurança E (falso positivo de SQL injection no executor de migrações, mais SQL montado com
f-string) e confiabilidade C (regras de PL/SQL/Oracle aplicadas a migrações SQLite).

**Resultado:** PR #4 para a `main` com o banco + correções: SQL parametrizado e validação de arquivo no executor,
`.sonarcloud.properties` (produção × testes, exclusão dos `.sql`), refatorações de complexidade. Quality Gate aprovado.
Sugestão: ativar "Automatically delete head branches" para PRs empilhadas apontarem sozinhas para a `main`.

## P017 — Duas perguntas diferentes, a mesma resposta (2026-11-23)
**Prompt (resumo):** "gostaria de saber sobre parafusos brocantes" gerou uma resposta da IA; "escreve-se brocantes ou
blocantes?" devolveu a mesma resposta, como se viesse do banco. Preciso melhorar isso.

**Diagnóstico:** (1) o llama3.2 inventou o conteúdo; (2) sugestões não revisadas eram buscadas como FAQ oficial, com
todas as palavras como palavra-chave e tolerância a erro de digitação ("blocantes" ≈ "brocantes"), passando do limite
de 50%; (3) o selo dizia "Banco de dados"; (4) FAQs novas não entravam em bancos existentes.

**Resultado:** reaproveitamento estrito de sugestões com selo próprio, FAQ-061 (autobrocante), sincronização dos
seeds por hash, comando de revisão, G25 (incerteza não é gravada) e prompt contra definições inventadas. 718 testes.

