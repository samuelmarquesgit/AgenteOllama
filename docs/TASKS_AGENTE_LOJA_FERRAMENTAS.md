# Checklist de desenvolvimento — Agente de IA para loja de ferramentas

> **Fase atual (atualizado em 2026-11-19 — v0.1.0 entregue):** MVP 1 — agente simples de perguntas e respostas (FAQ).  
> **Objetivo:** responder dúvidas frequentes de clientes sobre ferramentas elétricas, eletrônicas, acessórios, compra e pós-venda, sem integração com ERP, estoque, pagamentos ou WhatsApp.  
> **Convenção:** marque `[x]` quando a tarefa estiver concluída. Todas começam pendentes.

## 0. Escopo e critérios de sucesso

- [ ] Definir nome provisório do agente e da loja.
- [ ] Definir público-alvo (iniciante, profissional, ambos).
- [x] Definir idioma inicial: português brasileiro.
- [x] Definir canal inicial: chat web local, sem autenticação de cliente.
- [x] Definir o que o MVP **faz**: recebe perguntas, encontra respostas na FAQ e responde de forma clara.
- [x] Definir o que o MVP **não faz**: consultar preços/estoque reais, prometer entrega, realizar compras, abrir garantias ou executar ações externas.
- [x] Definir critérios de aceite: responder corretamente às perguntas cadastradas, pedir esclarecimentos quando necessário e admitir desconhecimento.
- [ ] Definir responsável por validar respostas técnicas e políticas comerciais.

## 1. Preparação do projeto

- [x] Criar repositório Git.
- [x] Criar `README.md` com objetivo, pré-requisitos e comandos de execução.
- [x] Criar `.gitignore` para Node, Python, `.env`, logs e arquivos temporários.
- [x] Criar `.env.example` com variáveis sem segredos.
- [ ] Definir licença e política de contribuição, se necessário.
- [ ] Criar pastas `frontend/`, `backend/`, `knowledge/`, `tests/`, `docs/`. — *parcial: estrutura `app/`, `static/`, `knowledge/`, `tests/`, `docs/`, `sql/` (ver D001)*
- [x] Definir convenção de branches e commits.
- [x] Registrar decisões técnicas em `docs/decisions.md`.

## 2. Arquitetura mínima

- [x] Escolher frontend simples (sugestão: Next.js/React). — *HTML único em `static/index.html` (ver D001)*
- [x] Escolher backend (sugestão: NestJS/Node.js). — *FastAPI/Python (ver D001)*
- [x] Criar endpoint `POST /chat` que recebe `{ "message": "..." }`.
- [x] Criar resposta padronizada `{ "answer": "...", "matchedFaqId": "...", "confidence": 0 }`.
- [x] Definir fonte inicial da FAQ em `knowledge/faq.json` (sem banco de dados). — *seed em `knowledge/faq.json`, servido via SQLite (ver D002)*
- [x] Implementar normalização de texto (maiúsculas/minúsculas, acentos e espaços).
- [x] Implementar busca simples por perguntas, palavras-chave e sinônimos.
- [x] Definir limiar de correspondência e fallback para dúvidas não encontradas.
- [x] Não enviar dados para um modelo externo nesta primeira versão, salvo decisão explícita. — *LLM roda localmente via Ollama*
- [x] Documentar como substituir futuramente a busca simples por embeddings/RAG.

## 3. Base de conhecimento — FAQ

- [x] Criar esquema de cada FAQ: `id`, `categoria`, `pergunta`, `variacoes`, `palavras_chave`, `resposta`, `fonte`, `revisado_em`, `status`.
- [x] Transformar as perguntas da seção **Banco inicial de perguntas e respostas** em registros `knowledge/faq.json`.
- [x] Cadastrar variações de linguagem (ex.: “parafusadeira”, “aparafusadora”; “furar parede”, “furar concreto”).
- [x] Separar conteúdo técnico de regras específicas da loja.
- [x] Marcar como `pendente_validacao` toda resposta que depende de política comercial, catálogo ou fabricante.
- [ ] Revisar especificações com manuais oficiais antes de recomendar modelos específicos.
- [x] Definir processo para adicionar, revisar, desativar e versionar FAQs.
- [x] Definir resposta padrão quando não houver correspondência confiável.
- [ ] Definir resposta padrão para perguntas ambíguas: fazer 1–3 perguntas de esclarecimento.
- [ ] Revisar conteúdo de segurança com especialista técnico.

## 4. Backend

- [ ] Inicializar projeto NestJS. — *substituído por FastAPI (D001)*
- [x] Configurar validação de entrada (mensagem não vazia, limite de caracteres).
- [x] Implementar carregamento da FAQ do arquivo JSON.
- [x] Implementar serviço `FaqSearchService`. — *`app/busca.py`*
- [x] Implementar serviço `ChatService`. — *`app/agente.py`*
- [x] Implementar endpoint `GET /health`.
- [x] Implementar endpoint `POST /chat`.
- [x] Retornar resposta encontrada com ID da FAQ para auditoria.
- [x] Implementar fallback quando nenhuma resposta for adequada.
- [x] Tratar erros sem expor detalhes internos.
- [ ] Configurar CORS restrito ao frontend. — *não necessário: página servida pela própria API (mesma origem)*
- [ ] Adicionar limite básico de requisições.
- [x] Registrar métricas técnicas sem armazenar dados pessoais desnecessários.

## 5. Frontend

- [ ] Inicializar projeto Next.js. — *substituído por HTML estático (D001)*
- [x] Criar página de chat responsiva.
- [x] Exibir apresentação: “Sou o assistente virtual da loja de ferramentas”.
- [x] Exibir aviso de que o agente está em versão inicial e não consulta estoque/preços reais.
- [x] Criar campo de mensagem e botão Enviar.
- [x] Exibir mensagens do cliente e do agente em balões distintos.
- [x] Exibir estado “Respondendo...” durante requisições.
- [x] Exibir sugestões de perguntas frequentes clicáveis.
- [x] Exibir mensagem amigável em caso de falha na API.
- [x] Permitir iniciar uma nova conversa.
- [x] Garantir navegação por teclado e rótulos acessíveis.
- [ ] Testar layout em celular e desktop.

## 6. Regras de comportamento

- [x] Responder em português claro, cordial e objetivo.
- [ ] Distinguir orientação geral de especificação de produto.
- [x] Nunca inventar preços, disponibilidade, promoções, garantia ou prazo de entrega.
- [ ] Nunca afirmar compatibilidade sem modelo e especificações suficientes.
- [ ] Perguntar material, frequência de uso, orçamento e alimentação quando relevantes.
- [ ] Não recomendar retirada de proteções ou uso de acessórios incompatíveis.
- [ ] Alertar sobre desligar/desenergizar equipamentos antes de manutenção, quando aplicável.
- [ ] Encaminhar dúvidas de risco elétrico, reparos perigosos ou uso profissional especializado a profissional habilitado.
- [x] Quando não souber, dizer que não tem informação suficiente e sugerir atendimento humano.
- [x] Não solicitar CPF, endereço ou dados de pagamento no MVP.

## 7. Testes e qualidade

- [x] Criar testes unitários da normalização de texto.
- [x] Criar testes unitários da busca por FAQ.
- [x] Testar perguntas com erros ortográficos simples.
- [x] Testar sinônimos e perguntas formuladas de modo diferente.
- [x] Testar perguntas sem resposta cadastrada.
- [ ] Testar perguntas com múltiplos significados.
- [x] Testar limite de tamanho de mensagem e entradas vazias.
- [ ] Testar respostas para situações de risco e incompatibilidade.
- [x] Criar teste de integração para `POST /chat`.
- [x] Criar teste de integração para `GET /health`.
- [ ] Testar frontend em celular e desktop.
- [ ] Validar manualmente todas as FAQs com especialista.
- [ ] Definir meta de acerto nas perguntas conhecidas (sugestão: >= 95% na bateria de testes).
- [ ] Registrar dúvidas não respondidas para expansão futura, sem coletar dados pessoais indevidos.

## 8. Documentação e entrega do MVP 1

- [x] Documentar instalação e execução local.
- [x] Documentar formato e manutenção do `faq.json`.
- [x] Documentar endpoints com exemplos de requisição/resposta.
- [x] Criar roteiro de demonstração com 10 perguntas reais.
- [ ] Fazer revisão final de segurança e privacidade.
- [ ] Publicar versão `v0.1.0` em ambiente de homologação.
- [ ] Homologar respostas com responsável da loja.
- [ ] Registrar feedback e bugs encontrados.
- [ ] Aprovar ou reprovar avanço para o MVP 2.

## 9. Backlog futuro — fora do escopo atual

- [ ] MVP 2: adicionar modelo de linguagem para respostas mais flexíveis.
- [ ] MVP 2: implementar RAG com manuais e fichas técnicas validadas.
- [ ] MVP 2: criar painel administrativo para gerenciar FAQs.
- [ ] MVP 2: persistir histórico de conversa com regras de privacidade.
- [ ] MVP 3: integrar catálogo real de produtos.
- [ ] MVP 3: integrar preço e estoque por API.
- [ ] MVP 3: recomendar produtos e acessórios compatíveis.
- [ ] MVP 3: comparar produtos com especificações verificadas.
- [ ] MVP 4: integrar WhatsApp Business Platform.
- [ ] MVP 4: integrar carrinho e e-commerce.
- [ ] MVP 4: consultar pedidos e frete com autorização.
- [ ] MVP 4: transferir atendimento para vendedor humano.
- [ ] MVP 5: adicionar métricas de conversão e satisfação.
- [ ] MVP 5: adicionar autenticação, permissões e auditoria avançada.
- [ ] MVP 5: avaliar arquitetura multiempresa (SaaS), se aplicável.

---

# Banco inicial de perguntas e respostas

> **Uso:** conteúdo inicial para a FAQ do MVP. As respostas são orientações gerais; não representam estoque, preço, política de uma loja específica nem especificações de um modelo. Cada item deve ser revisado antes da publicação.

## A. Escolha de ferramentas

### FAQ-001 — Qual a diferença entre furadeira e parafusadeira?
**Resposta:** A furadeira é voltada principalmente à perfuração de materiais. A parafusadeira é otimizada para apertar e soltar parafusos, normalmente com controle de torque. Alguns modelos combinam as duas funções.

### FAQ-002 — Qual a diferença entre furadeira comum e furadeira de impacto?
**Resposta:** A furadeira de impacto acrescenta uma ação de percussão, útil em alvenaria conforme o modelo e a broca. Para concreto mais resistente ou uso intenso, um martelete adequado pode ser mais indicado.

### FAQ-003 — Quando devo usar um martelete?
**Resposta:** Marteletes são indicados para determinadas perfurações em concreto e alvenaria. Alguns modelos também fazem rompimento leve. Verifique o tipo de encaixe, a energia de impacto e as aplicações permitidas no manual.

### FAQ-004 — Qual é melhor: ferramenta com fio ou a bateria?
**Resposta:** Modelos com fio dispensam recarga e são úteis em trabalhos prolongados com tomada disponível. Modelos a bateria oferecem mobilidade. A escolha depende de potência, autonomia, peso, frequência de uso e ambiente.

### FAQ-005 — Parafusadeira 12V ou 20V: qual escolher?
**Resposta:** Modelos de 12V tendem a ser compactos para tarefas leves. Plataformas de tensão maior podem atender trabalhos exigentes, mas tensão sozinha não define torque ou desempenho. Compare especificações e aplicação.

### FAQ-006 — O que significa torque em uma parafusadeira?
**Resposta:** Torque é o momento de força de rotação, normalmente indicado em N·m. A necessidade depende do parafuso, material e tarefa. O ajuste de torque ajuda a evitar aperto excessivo em aplicações compatíveis.

### FAQ-007 — O que significa potência em watts?
**Resposta:** Watts (W) indicam potência. Em ferramentas elétricas, o valor informado nem sempre equivale à potência útil entregue no eixo. Para comparar desempenho, considere também rotação, torque e aplicação.

### FAQ-008 — Qual ferramenta usar para montar móveis?
**Resposta:** Uma parafusadeira com ajuste de torque e bits adequados costuma ser útil. Para móveis delicados, prefira controle fino e evite aperto excessivo. Qual material e tipo de montagem você fará?

### FAQ-009 — Qual ferramenta usar para cortar madeira?
**Resposta:** Depende do corte: serra circular para muitos cortes retos, serra tico-tico para curvas e recortes, e serra de esquadria para cortes angulares repetitivos. Informe espessura e tipo de madeira.

### FAQ-010 — Qual ferramenta usar para cortar metal?
**Resposta:** Depende do metal, espessura e acabamento. Podem ser usados equipamentos específicos, como serras apropriadas ou esmerilhadeiras com acessórios compatíveis. Nunca use discos inadequados ou retire proteções.

### FAQ-011 — Qual ferramenta usar para lixar madeira?
**Resposta:** Lixadeira orbital ou roto-orbital costuma ser adequada para acabamento; lixadeira de cinta remove material mais rapidamente. A escolha depende da área, acabamento e tipo de peça.

### FAQ-012 — Qual ferramenta usar para remover tinta ou ferrugem?
**Resposta:** Pode envolver lixamento, escovação ou métodos químicos específicos, conforme superfície e revestimento. Verifique os riscos de poeira, vapores e materiais antigos antes de iniciar.

## B. Brocas, discos e acessórios

### FAQ-013 — Qual broca usar em concreto?
**Resposta:** Utilize broca adequada a concreto/alvenaria e compatível com a máquina. Para marteletes, confirme o encaixe exigido, como SDS-plus ou SDS-max, conforme o equipamento.

### FAQ-014 — Qual broca usar em madeira?
**Resposta:** Brocas próprias para madeira, como as de ponta centralizadora, ajudam na precisão. O tipo depende do diâmetro, profundidade e acabamento desejado.

### FAQ-015 — Qual broca usar em metal?
**Resposta:** Use broca indicada para o metal e a máquina. Ajuste rotação, fixação da peça e lubrificação conforme o material e as instruções do fabricante.

### FAQ-016 — Posso usar qualquer disco na esmerilhadeira?
**Resposta:** Não. O disco deve ser apropriado à operação, ao material, ao diâmetro, ao encaixe e à rotação máxima da máquina. Utilize a proteção indicada e siga o manual.

### FAQ-017 — Qual a diferença entre disco de corte e disco de desbaste?
**Resposta:** Discos de corte são projetados para cortar; discos de desbaste, para remover material. Não use disco de corte para desbastar lateralmente, salvo autorização expressa do fabricante para aquela aplicação.

### FAQ-018 — Como saber se uma bateria serve na minha ferramenta?
**Resposta:** Verifique marca, plataforma, modelo, tensão nominal e lista oficial de compatibilidade. Baterias visualmente parecidas podem não ser compatíveis.

### FAQ-019 — Bits de parafusadeira são universais?
**Resposta:** Muitos bits usam encaixes padronizados, mas é necessário conferir tipo, tamanho e compatibilidade com porta-bits e parafuso. Usar bit errado pode danificar a cabeça do parafuso.

### FAQ-020 — Posso usar adaptadores entre encaixes diferentes?
**Resposta:** Somente adaptadores aprovados para o equipamento e a aplicação. Adaptadores inadequados podem comprometer fixação, rotação e segurança.

## C. Baterias e alimentação

### FAQ-021 — O que significa Ah na bateria?
**Resposta:** Ampère-hora (Ah) é uma medida de capacidade elétrica. Dentro da mesma plataforma e condições de uso, maior capacidade costuma permitir mais autonomia, mas também pode aumentar peso e tempo de carga.

### FAQ-022 — Posso usar bateria de maior Ah?
**Resposta:** Em muitos sistemas, sim, desde que a bateria pertença à mesma plataforma e seja aprovada pelo fabricante para a ferramenta e carregador. Confirme a compatibilidade exata.

### FAQ-023 — Quanto tempo dura a bateria?
**Resposta:** Depende da capacidade, ferramenta, carga de trabalho, temperatura e estado da bateria. Para estimar, informe o modelo da ferramenta, a bateria e a tarefa.

### FAQ-024 — Posso carregar uma bateria em qualquer carregador?
**Resposta:** Não. Utilize carregador compatível e aprovado pelo fabricante para a bateria. Carregadores inadequados podem causar aquecimento, danos ou incêndio.

### FAQ-025 — Ferramenta 220V funciona em tomada 127V?
**Resposta:** Em geral, uma ferramenta projetada apenas para 220V não deve ser ligada diretamente em 127V. Verifique a etiqueta e o manual; modelos bivolt têm regras próprias. Não improvise adaptações elétricas.

### FAQ-026 — Como guardar baterias de ferramentas?
**Resposta:** Siga o manual do fabricante. Em geral, armazene em local seco, fresco e protegido de calor, umidade e objetos metálicos nos terminais. Evite baterias danificadas.

## D. Medição e eletrônica

### FAQ-027 — Qual a diferença entre multímetro e alicate amperímetro?
**Resposta:** O multímetro mede grandezas como tensão e resistência; alguns também medem corrente por pontas de prova. O alicate amperímetro mede corrente por uma garra, conforme o tipo e as especificações.

### FAQ-028 — Qual multímetro escolher?
**Resposta:** Considere as grandezas a medir, precisão, faixa de tensão, categoria de medição (CAT), ambiente e recursos. Para instalações elétricas, escolha equipamento adequado e siga procedimentos de segurança.

### FAQ-029 — Posso medir tomada com qualquer multímetro?
**Resposta:** Não. Medições em rede elétrica exigem instrumento, pontas e categoria de segurança adequados, além de conhecimento técnico. Se não tiver qualificação, procure profissional habilitado.

### FAQ-030 — O que é detector de tensão sem contato?
**Resposta:** É um instrumento que pode indicar presença de campo elétrico em determinadas condições. Não deve ser usado sozinho para comprovar ausência de tensão; siga procedimentos e instrumentos adequados.

## E. Soldagem, compressores e limpeza

### FAQ-031 — Qual a diferença entre solda MIG/MAG, TIG e eletrodo revestido?
**Resposta:** MIG/MAG usa arame alimentado continuamente; TIG usa eletrodo de tungstênio; eletrodo revestido utiliza varetas consumíveis. A escolha depende do material, espessura, acabamento e experiência.

### FAQ-032 — Qual compressor preciso para pintar?
**Resposta:** Compare a vazão de ar efetiva exigida pela pistola, pressão de trabalho e ciclo de serviço do compressor. O volume do reservatório, isoladamente, não determina a capacidade de pintura.

### FAQ-033 — Qual lavadora de alta pressão escolher?
**Resposta:** Avalie pressão, vazão, frequência de uso e superfície. Pressão excessiva pode danificar pintura, rejuntes e materiais delicados. Informe o que pretende limpar.

### FAQ-034 — Posso usar qualquer detergente na lavadora?
**Resposta:** Não. Use somente produtos autorizados pelo fabricante da lavadora e adequados à superfície. Produtos incompatíveis podem danificar componentes e causar riscos.

## F. Uso, manutenção e segurança

### FAQ-035 — Como escolher equipamento para uso profissional?
**Resposta:** Considere frequência, ciclo de trabalho, ergonomia, desempenho, assistência técnica, disponibilidade de peças e acessórios. Informe a atividade e quantas horas por dia utilizará.

### FAQ-036 — Como conservar minhas ferramentas?
**Resposta:** Mantenha limpas e secas, siga a manutenção do manual, inspecione cabos e acessórios e armazene adequadamente. Desligue e desconecte a fonte de energia antes de procedimentos permitidos de limpeza/manutenção.

### FAQ-037 — Minha ferramenta está esquentando. É normal?
**Resposta:** Algum aquecimento pode ocorrer durante o uso, mas calor excessivo, cheiro de queimado, fumaça ou falhas exigem interromper a operação e procurar assistência autorizada. Não continue utilizando nessas condições.

### FAQ-038 — Posso retirar a proteção da esmerilhadeira para usar disco maior?
**Resposta:** Não. Nunca remova a proteção para instalar disco maior ou incompatível. Use somente dimensões e acessórios autorizados pelo fabricante.

### FAQ-039 — Qual EPI usar com ferramentas elétricas?
**Resposta:** Depende da ferramenta e da atividade. Podem ser necessários proteção ocular, auditiva, respiratória e outros EPIs adequados. Consulte manual, avaliação de riscos e normas aplicáveis; luvas podem ser inadequadas perto de partes rotativas.

### FAQ-040 — Posso usar ferramenta elétrica na chuva?
**Resposta:** Não utilize equipamentos elétricos expostos à água ou chuva, salvo se o fabricante permitir expressamente aquela condição e houver medidas de proteção apropriadas.

## G. Atendimento comercial — respostas condicionais

> **Atenção:** os itens abaixo são modelos de resposta e devem ser adaptados à operação real da loja antes de ativados.

### FAQ-041 — Vocês têm esse produto em estoque?
**Resposta:** Ainda não consigo consultar o estoque em tempo real. Informe o nome ou modelo do produto para que um atendente confirme a disponibilidade.

### FAQ-042 — Qual é o preço dessa ferramenta?
**Resposta:** Ainda não tenho acesso aos preços atualizados. Informe o modelo desejado e consulte um atendente ou o catálogo oficial da loja.

### FAQ-043 — Vocês fazem entrega?
**Resposta:** As opções de entrega dependem da política da loja e da região atendida. Um atendente poderá confirmar as modalidades disponíveis.

### FAQ-044 — Quanto custa o frete?
**Resposta:** Não consigo calcular frete nesta versão. O valor depende de destino, produto, peso e modalidade de envio. Consulte o canal oficial da loja.

### FAQ-045 — Quais são as formas de pagamento?
**Resposta:** As formas de pagamento devem ser confirmadas nos canais oficiais da loja. Não solicito dados de cartão ou pagamento neste chat.

### FAQ-046 — Vocês parcelam?
**Resposta:** O parcelamento depende das condições comerciais vigentes. Consulte o atendimento ou checkout oficial para verificar as opções.

### FAQ-047 — Vocês têm promoção ou desconto?
**Resposta:** Não consulto promoções em tempo real. Verifique as ofertas divulgadas nos canais oficiais da loja.

### FAQ-048 — Posso trocar ou devolver um produto?
**Resposta:** As condições dependem do tipo de compra, motivo e legislação aplicável. Em compras realizadas fora do estabelecimento, o CDC prevê, em regra, direito de arrependimento em até 7 dias, nas condições legais. Consulte a política da loja para orientações específicas.

### FAQ-049 — Qual é a garantia da ferramenta?
**Resposta:** O prazo e a cobertura dependem do produto, fabricante e condições de compra, além dos direitos previstos em lei. Consulte a nota fiscal, o termo de garantia e o atendimento da loja.

### FAQ-050 — Vocês vendem peças de reposição?
**Resposta:** Ainda não consulto o catálogo de peças. Informe a marca, o modelo e a peça desejada para verificação por um atendente.

### FAQ-051 — Vocês trabalham com a marca Bosch/Makita/DeWalt?
**Resposta:** Não tenho acesso à lista atualizada de marcas da loja. Um atendente poderá confirmar as marcas disponíveis.

### FAQ-052 — Posso retirar o pedido na loja?
**Resposta:** A retirada depende das opções e horários da unidade. Confirme essa possibilidade com o atendimento oficial antes de se deslocar.

### FAQ-053 — Como acompanho meu pedido?
**Resposta:** Ainda não consigo consultar pedidos. Utilize o canal oficial de acompanhamento ou entre em contato com o atendimento da loja. Não envie dados pessoais sensíveis neste chat.

### FAQ-054 — Vocês emitem nota fiscal?
**Resposta:** A emissão de documentos fiscais segue as regras aplicáveis à operação. Consulte o atendimento da loja para confirmar os procedimentos de compra e emissão.

### FAQ-055 — Posso falar com um vendedor?
**Resposta:** Sim, você pode procurar o canal oficial de atendimento humano da loja. Nesta versão, ainda não faço a transferência automática da conversa.

## H. Perguntas de diagnóstico e comparação

### FAQ-056 — Qual a melhor marca de ferramenta?
**Resposta:** Não existe uma única melhor marca para todas as aplicações. Compare desempenho, assistência, peças, ergonomia, garantia e custo-benefício para o uso desejado.

### FAQ-057 — Qual ferramenta tem melhor custo-benefício?
**Resposta:** Depende do trabalho e da frequência de uso. Diga qual tarefa fará, se o uso é doméstico ou profissional e seu orçamento para eu orientar os critérios de escolha.

### FAQ-058 — Uma ferramenta mais potente é sempre melhor?
**Resposta:** Não. Potência deve ser avaliada junto com controle, ergonomia, eficiência e adequação à aplicação. Uma ferramenta excessiva pode ser menos prática ou segura para tarefas delicadas.

### FAQ-059 — Como comparar duas ferramentas?
**Resposta:** Informe marca e modelo de ambas. Podemos comparar aplicação, torque, potência, rotação, recursos, peso, alimentação e acessórios, usando especificações confirmadas.

### FAQ-060 — Não sei qual ferramenta comprar. Pode me ajudar?
**Resposta:** Claro! Me diga: (1) qual trabalho você fará; (2) em qual material; (3) com que frequência; e (4) qual é seu orçamento aproximado. Assim consigo orientar a escolha.

---

## 10. Perguntas para demonstração do MVP

- [x] “Qual a diferença entre furadeira e parafusadeira?” → FAQ-001.
- [x] “Preciso furar concreto, o que uso?” → FAQ-002 ou FAQ-003, com esclarecimento.
- [x] “Qual broca é boa para metal?” → FAQ-015.
- [x] “Uma bateria de 4 Ah dura mais que uma de 2 Ah?” → FAQ-021, com ressalvas.
- [x] “Posso colocar disco maior na esmerilhadeira?” → FAQ-016/FAQ-038; resposta segura.
- [x] “Como escolher um multímetro?” → FAQ-028.
- [x] “Tem uma Bosch por R$ 300?” → informar falta de preço/estoque, sem inventar.
- [x] “Vocês entregam na minha cidade?” → FAQ-043, sem prometer entrega.
- [x] “Quero devolver uma compra online.” → FAQ-048, com orientação geral.
- [x] “Não sei qual ferramenta comprar.” → FAQ-060, fazendo perguntas de diagnóstico.

## 11. Definição de pronto (Definition of Done)

- [ ] Todas as 60 FAQs revisadas por responsável técnico/comercial.
- [x] API e interface web executam localmente com instruções reproduzíveis.
- [x] As 10 perguntas de demonstração funcionam conforme esperado.
- [ ] O agente não inventa preços, estoque, garantias ou compatibilidades.
- [x] Perguntas desconhecidas geram fallback claro.
- [ ] Testes automatizados e revisão manual aprovados.
- [ ] MVP 1 homologado e documentado.
