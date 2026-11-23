# 0006 — Análise crítica do projeto

> **Versão:** 1.0 · **Data:** 2026-11-23 · **Escopo:** o projeto inteiro e o [plano v2](0005-Plano-de-Profissionalizacao.md)
> **Método:** 11 perguntas de pensamento crítico definidas pelo time, respondidas sem concordar por educação.
> A mesma análise é aplicada **a cada épico e a cada task** em [`0007-Tasks-Reinicio-do-Projeto.md`](0007-Tasks-Reinicio-do-Projeto.md).
>
> **Escala das notas:** 1 = ótimo (barato, rápido, risco baixo) · 5 = péssimo (caro, demorado, risco alto).

---

## Veredito direto

A parte técnica está bem encaminhada: guardrails, testes e contexto funcionam. **O maior risco não é técnico:**
- não existe loja real, cliente real, dono do produto nem prazo definido;
- o plano v2 tem escopo de uma equipe de produto em tempo integral, para 4 pessoas cuja disponibilidade não está comprovada.

Sem **definir o objetivo e cortar escopo**, a chance de o projeto parar no meio é alta. A recomendação final (pergunta 10) corta o plano v2 em cerca de 40% e acrescenta uma fase de descoberta.

---

## 1. Os 5 principais pontos fracos

| # | Ponto fraco | Por que é grave |
|---|-------------|-----------------|
| 1 | **Não há loja nem cliente real.** Catálogo, políticas, pedidos e unidades são fictícios | Sem usuários, as métricas (CSAT, contenção) não têm dado; os fluxos de pedido e estoque nunca serão de verdade; existe o risco de construir algo que ninguém usa |
| 2 | **Escopo desproporcional ao time.** O plano v2 tem 10 fases, 27 decisões e cerca de 15 ferramentas novas | A estimativa até o Gate é de **~70 dias-pessoa**. Com 4 pessoas a ~10 h/semana, são **3,5 a 4,5 meses**, e a disponibilidade não está comprovada: houve 1 contribuição externa, de 1 linha, em 4 dias |
| 3 | **Busca por palavras-chave escritas à mão não escala** | Manter palavras-chave para 150 FAQs e 450 variações é artesanal. Com 60 FAQs já há empates ("broca para porcelanato" empata 3 FAQs com nota 0,5). O plano adia embeddings para a F7 por uma regra (sem pgvector no MVP) que **pode estar errada** |
| 4 | **LLM local pequeno erra conteúdo técnico, e os guardrails não pegam isso** | Na demo, o llama3.2 descreveu errado o soprador térmico. Regex bloqueia preço e "retire a proteção", mas não um erro técnico. A "IA que aprende" alimenta uma fila que depende de um revisor especialista que **não existe** |
| 5 | **Conteúdo de segurança e jurídico sem responsável** | 90 FAQs novas, textos do CDC e orientações sobre eletricidade e discos de corte: um erro tem consequência física ou jurídica real. Ninguém do time foi designado para revisar |

## 2. Se fracassar em seis meses, por quê? (do mais ao menos provável)

1. **O time se dispersou.** Sem dono por frente e sem cadência, o trabalho voltou para uma pessoa só (*bus factor* = 1).
2. **A infraestrutura engoliu o prazo.** F0 e F1 (uv, CI, Postgres, migrações) consumiram semanas sem nenhuma melhoria visível ao usuário, e a motivação caiu.
3. **Uma resposta errada e perigosa numa demonstração** destruiu a confiança no produto.
4. **Não havia loja para integrar.** A F8 nunca começou; o projeto ficou "pronto" sem uso.
5. **A hospedagem gratuita falhou** (PC desligado, VM da Oracle reciclada) e ninguém de fora conseguiu usar.
6. **Mudança externa:** licença de modelo ou plano gratuito alterado.

## 3. Suposições perigosas ou otimistas demais

| Suposição | Realidade |
|-----------|-----------|
| "Grátis para sempre, inclusive em produção" | Servidor gratuito 24 h com LLM praticamente não existe. A Oracle exige cartão e pode recuperar VMs ociosas; o PC do time desliga |
| "Temos 4 pessoas" | Ainda não há evidência de disponibilidade nem de divisão de trabalho |
| "Um modelo de 3–8B é bom o bastante" | Ainda não foi medido; o único dado (a demo) é negativo |
| "O cliente quer um chat no site" | No Brasil, o cliente de loja está no **WhatsApp**; chat web isolado costuma ter pouco tráfego |
| "As respostas aprendidas serão revisadas" | Fila sem dono só cresce |
| "Palavras-chave manuais escalam" | Já mostram limite com 60 FAQs |
| "Vai existir um ERP para integrar" | Não existe loja |
| "O Postgres é necessário agora" | Para 150 FAQs, o SQLite aguenta. O Postgres só se justifica se o plano de banco for **entrega obrigatória** (confirmar) ou pelas fases futuras |
| "A IA pode escrever as 90 FAQs" | Pode rascunhar; sem revisão técnica, vira risco |

## 4. Três alternativas completamente diferentes

| Alternativa | Como funciona | Ganha | Perde |
|-------------|---------------|-------|-------|
| **A. Plataforma de atendimento pronta (Chatwoot, open source)** | Chatwoot como caixa de entrada multicanal (web, WhatsApp, e-mail), com handoff humano nativo; o nosso FAQ entra como "bot" via webhook | Handoff, fila, métricas e WhatsApp quase prontos | Controle da interface; mais um sistema para operar |
| **B. Sem chatbot** | Central de ajuda estática com busca (MkDocs + busca no navegador) + **WhatsApp Business** (app gratuito) com respostas rápidas e catálogo | Custo e risco quase zero; resolve a maioria das dúvidas repetidas | Não exercita IA nem banco relacional (objetivo de aprendizado e portfólio) |
| **C. RAG puro** | FAQ + manuais indexados por embeddings; o LLM sempre responde **citando a fonte**; humanos revisam por amostragem | Menos curadoria por pergunta; cobre perguntas novas melhor | Mais risco de alucinação; exige modelo melhor e avaliação forte |

## 5. Mais simples e barata × mais robusta

| | Mais simples e barata | Mais robusta |
|---|---|---|
| **O que é** | Manter a v0.2 (SQLite + FAQ + guardrails), chegar a 150 FAQs revisadas, menu e respostas da loja em JSON, publicar por Cloudflare Tunnel | Plano v2 inteiro: Postgres, ports e adapters, handoff real (Chatwoot), avaliação contínua, RAG, WhatsApp, observabilidade, VPS paga (US$ 5–20/mês) ou GPU |
| **Esforço** | ~10–15 dias-pessoa | ~6 meses de time |
| **Quando escolher** | Objetivo é demonstrar e aprender rápido | Existe uma loja real disposta a usar |

## 6. Como especialistas de outras áreas resolveriam

| Especialista | Abordagem |
|--------------|-----------|
| **Engenheiro de segurança do trabalho** | Tratar as orientações de segurança como *procedimento controlado*: conteúdo de risco só a partir de fontes normativas (NR-12, NR-10, manuais do fabricante), com revisão registrada e matriz de risco por FAQ (baixo, médio, alto → alto exige humano) |
| **Gestor financeiro** | Calcular o custo por conversa e o valor por conversa resolvida. Sem loja, não há receita: o retorno é **educacional e de portfólio**, então otimizar para aprender e demonstrar, não para operar |
| **Psicólogo / pesquisador de UX** | Clientes desconfiam de bots: deixar claro que é um assistente virtual, com saída para humano sempre visível e menos texto. **Testar com 5 pessoas reais** revela a maioria dos problemas de usabilidade, mais do que 500 testes automatizados |
| **Gerente de produto** | Descoberta antes de construção: entrevistar vendedores de loja sobre as perguntas reais, priorizar pelo volume e pelo custo de errar, e só então decidir a arquitetura |

## 7. Dados e fatos que contrariam o plano

- **A maior reclamação do setor é atraso de entrega** ([Reclame Aqui](https://www.reclameaqui.com.br/empresa/maxi-ferramentas)), e o Tork não resolve isso sem integração real. O valor do chat técnico pode ser menor do que o plano supõe.
- **Os assistentes de referência (Home Depot, Lowe's) usam modelos grandes com catálogos enormes** ([Customer Experience Dive](https://www.customerexperiencedive.com/news/home-depot-lowes-ai-assistants-share-common-goal-approaches-differ/832056/)). Com um modelo de 3B e sem catálogo, a experiência fica abaixo da que o cliente conhece.
- **A própria demo:** o llama3.2 errou o conteúdo técnico de uma pergunta simples.
- **A busca já mostra limite:** empates com 60 FAQs.
- **O time:** em 4 dias após a demo, 1 commit externo de 1 linha, e com um modelo sem licença comercial.

## 8. Notas: custo, tempo e risco de erro

| Proposta | Custo | Tempo | Risco | **Total /15** | Comentário |
|----------|:-----:|:-----:|:-----:|:-------------:|------------|
| Plano v2 completo (F0–F9) | 2 | 5 | 4 | **11** | Ferramentas grátis, mas muitas horas; risco de abandono alto |
| Plano v2 até o Gate (F0–F4) | 2 | 4 | 3 | **9** | Ainda grande para o time atual |
| **Recomendação (pergunta 10)** | 1 | 3 | 2 | **6** | Corta ~40%, mantém o aprendizado de banco e IA |
| Alternativa A (Chatwoot) | 2 | 2 | 3 | **7** | Boa quando houver atendente real |
| Alternativa B (sem chatbot) | 1 | 1 | 2 | **4** | Melhor custo-benefício, mas **não cumpre** o objetivo de aprender IA e banco |
| Alternativa C (RAG puro) | 2 | 3 | 4 | **9** | Risco de alucinação alto com modelo pequeno |

O plano v2 escrito até agora **tira 9 a 11**. Isso é ruim, e é o motivo da recomendação abaixo.

## 9. O que está faltando e ninguém perguntou

1. **Qual é o objetivo e qual é o prazo?** Trabalho acadêmico (com banca e data), portfólio ou produto para uma loja real? Muda tudo.
2. **Quem é o dono do produto**, que decide prioridades e aceita entregas?
3. **Quem revisa** o conteúdo técnico e o jurídico?
4. **Critério de sucesso do projeto** (não só do bot): nota, demonstração, usuários, contratação?
5. **Teste com usuários reais** antes de investir em infraestrutura.
6. **Responsabilidade por orientação errada:** aviso de uso, termos e limites do assistente.
7. **Canal:** WhatsApp é onde o cliente brasileiro está; o chat web pode ser só a vitrine.
8. **Manutenção depois do semestre:** quem cuida da base e da fila de sugestões?
9. **Bus factor = 1:** só uma pessoa conhece o projeto inteiro.
10. **Direito autoral:** copiar FAQs ou trechos de manuais de fabricantes pode violar direitos; escrever com fonte citada e texto próprio.

## 10. Prós e contras → denominador comum

| Opção | Prós | Contras |
|-------|------|---------|
| Simples (v0.2 + conteúdo) | Rápida, barata, visível | Não cumpre o plano de banco; dívida técnica |
| Plano v2 completo | Profissional, completo | Grande demais; risco de abandono |
| Chatwoot | Handoff e WhatsApp prontos | Mais um sistema; menos aprendizado de código |
| RAG puro | Menos curadoria | Alucinação com modelo pequeno |

### Recomendação (denominador comum)

1. **E0 — Descoberta (1 semana):** definir objetivo, prazo, dono do produto e revisores; entrevistar 3 a 5 vendedores ou clientes; congelar o escopo.
2. **Manter a stack** (Python + FastAPI) e migrar para o **Postgres porque o plano de banco é uma entrega pedida**. Se não for obrigatório, adiar e ficar no SQLite.
3. **Antecipar um teste rápido de embeddings locais** (2 dias): comparar embeddings, palavras-chave e trigram no conjunto-ouro. Se os embeddings ganharem, **eliminam a tabela de palavras-chave** e simplificam a F1. Isso contraria o "sem pgvector no MVP" do plano de banco, e é intencional.
4. **Cortar do MVP:** Langfuse, MkDocs, Oracle, Release Please, Presidio, SonarQube e F7–F9. O painel admin fica mínimo.
5. **Fluxos só onde não há integração:** menu, F-ESCOLHA, F-TROCA, F-HUMANO e respostas da loja. F-PROD e F-PEDIDO com mensagem honesta.
6. **Handoff:** uma tabela simples primeiro; avaliar o Chatwoot quando houver atendente humano real.
7. **Conteúdo com revisão obrigatória:** nenhuma FAQ nova entra sem revisor; matriz de risco por FAQ.
8. **Testar com 5 pessoas reais** antes do Gate.
9. **Cadência:** um dono por frente, uma entrega visível por semana, demonstração às sextas.

## 11. Sem concordar por educação: o que eu descartaria

| Ideia | Decisão | Motivo |
|-------|---------|--------|
| Pedir CPF no chat (roteiro original) | **Descartar** | LGPD, risco de vazamento, conflita com o G02 |
| Mostrar produtos com preço e link sem integração | **Descartar até haver catálogo real** | Seria preço inventado ou fictício apresentado como real |
| "Grátis para sempre" também em produção 24 h | **Trocar** por "grátis para desenvolver e demonstrar; até US$ 10/mês em produção, se houver loja" | A premissa atual não se sustenta |
| Palavras-chave manuais como estratégia de longo prazo | **Substituir se o teste de embeddings ganhar** | Manutenção artesanal |
| IA escrevendo as 90 FAQs sem revisor | **Descartar** | Risco técnico e de segurança |
| Modelo `qwen2.5:3b` | **Descartar** | Licença sem uso comercial |
| Fazer F0 inteira antes de qualquer melhoria visível | **Intercalar** | Motivação do time; entregar valor toda semana |
