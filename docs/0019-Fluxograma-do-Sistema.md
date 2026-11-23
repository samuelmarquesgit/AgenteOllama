# 0019 — Fluxograma do sistema

> **Versão:** 1.0 · **Data:** 2026-11-23 · **Escopo:** o Tork como será entregue em 29/11 ([`0018`](0018-Plano-de-Entrega-29-11.md), itens P0 e P1).
> Os diagramas usam [Mermaid](https://mermaid.js.org/) e aparecem renderizados no GitHub e no VS Code (com extensão de preview Mermaid).

## Legenda de cores

| Cor | Significado |
|-----|-------------|
| 🟧 Laranja | Cliente e interface |
| 🟥 Vermelho | Guardrail (proteção) |
| 🟩 Verde | Banco de dados e respostas revisadas |
| 🟦 Azul | Inteligência artificial (Ollama) |
| 🟨 Amarelo | Dados configurados da loja e fluxos guiados |
| ⬜ Cinza | Montagem da resposta, memória e métricas |

---

## 1. Fluxograma completo: o caminho de uma mensagem

```mermaid
flowchart TD
    %% ================= ENTRADA =================
    U(["👤 Cliente"]) --> UI["Chat web do Tork"]
    UI -->|"POST /chat: mensagem + conversationId"| VAL{"G01 · mensagem válida?<br/>1 a 500 caracteres"}
    VAL -- "não" --> E422["HTTP 422<br/>mensagem inválida"]
    VAL -- "sim" --> PII["G02 · mascara dados pessoais<br/>CPF, cartão, e-mail, telefone, CEP"]
    PII --> INJ{"G03 · tentativa de<br/>prompt injection?"}
    INJ -- "sim" --> BLQ1["🛡️ Recusa educada<br/>não chama a IA"]
    INJ -- "não" --> SAUD{"É saudação?"}
    SAUD -- "sim" --> BV["👋 Boas-vindas + menu"]
    SAUD -- "não" --> MENU{"Botão do menu ou<br/>resposta rápida?"}

    %% ================= MENU =================
    MENU -- "🔎 Encontrar produto" --> MPROD["Ainda não consulto o catálogo:<br/>ofereço ajuda para escolher ou atendente"]
    MENU -- "📦 Pedido ou entrega" --> MPED["Ainda não consulto pedidos:<br/>link Meus pedidos ou atendente"]
    MENU -- "💳 Pagamento · 🕐 Horário · 📍 Endereço" --> LOJA["Dados configurados da loja<br/>loja.yaml"]
    MENU -- "🔁 Trocas e garantia" --> FTROCA[["F-TROCA<br/>CDC + política da loja"]]
    MENU -- "👤 Falar com atendente" --> FHUM[["F-HUMANO<br/>resumo + consentimento"]]
    MENU -- "🛠️ Ajuda para escolher ou texto livre" --> CTX

    %% ================= CONTEXTO =================
    CTX{"Há histórico e a mensagem<br/>parece continuação?<br/>ex.: e para metal?"}
    CTX -- "não" --> BUSCA
    CTX -- "sim" --> RW["🤖 Ollama reescreve como<br/>pergunta completa"]
    RW --> G15{"G15 · reescrita válida?"}
    G15 -- "sim: usa a reescrita" --> BUSCA
    G15 -- "não: usa a original" --> BUSCA

    %% ================= BANCO =================
    BUSCA[("Busca parametrizada no PostgreSQL<br/>perguntas + variações<br/>unaccent · trigram · palavras-chave")]
    BUSCA --> NOTA{"Nota da melhor<br/>FAQ ≥ 0,5?"}
    NOTA -- "sim" --> RFAQ["📚 Resposta revisada da FAQ<br/>+ sugestão se houver empate<br/>+ pede detalhes se nota abaixo de 0,75"]
    RFAQ --> G20{"G20 · indica ferramenta com fio<br/>sem voltagem confirmada?"}
    G20 -- "sim" --> VOLT["Acrescenta: 127 V, 220 V ou bivolt?"]
    G20 -- "não" --> SAIDA
    VOLT --> SAIDA
    NOTA -- "não" --> COM{"G04 · assunto comercial?<br/>preço, estoque, frete"}
    COM -- "sim" --> RCOM["📚 Textos comerciais fixos<br/>nunca passa pela IA"]
    RCOM --> SAIDA
    COM -- "não" --> OLL{"Ollama disponível?"}

    %% ================= IA =================
    OLL -- "não" --> FB["⚠️ Fallback: não tenho<br/>informação segura"]
    FB --> ESC{"G21 · quantos fallbacks<br/>seguidos?"}
    ESC -- "1º: pede para reformular" --> SAIDA
    ESC -- "2º: mostra o menu" --> SAIDA
    ESC -- "3º: oferece atendente" --> FHUM
    OLL -- "sim" --> LLM["🤖 Ollama responde<br/>prompt com regras + histórico"]
    LLM --> FORA{"G05 · fora do escopo?"}
    FORA -- "sim" --> RFORA["⚠️ Recusa educada<br/>nada é gravado"]
    FORA -- "não" --> GS{"G06–G14 · a resposta inventa<br/>preço, estoque, prazo, garantia,<br/>conselho perigoso ou link?"}
    GS -- "sim" --> BLQ2["🛡️ Resposta descartada"]
    GS -- "não" --> GA{"G16–G18 · pode gravar?<br/>tem assunto e não tinha<br/>dado pessoal"}
    GA -- "sim" --> SUG[("faq_sugestoes<br/>status: pendente")]
    GA -- "não" --> RIA
    SUG --> RIA["🤖 Resposta do Tork IA"]
    RIA --> SAIDA

    %% ================= SAÍDA =================
    FTROCA --> SAIDA
    FHUM --> HUM[("atendimentos_humanos")]
    HUM --> SAIDA
    MPROD --> SAIDA
    MPED --> SAIDA
    LOJA --> SAIDA
    BV --> SAIDA
    BLQ1 --> SAIDA
    BLQ2 --> SAIDA
    RFORA --> SAIDA
    SAIDA["Monta a resposta<br/>texto · origem · FAQ-ID · guardrails acionados"]
    SAIDA --> MEM["Memória da conversa<br/>só respostas úteis, sem dado pessoal"]
    MEM --> LOG["Log de métricas<br/>sem o texto do cliente"]
    LOG --> UI2["Chat mostra a resposta com selo<br/>📚 Banco · 🤖 Tork IA · 🛡️ Guardrail"]
    UI2 --> FIM{"Cliente encerrou?"}
    FIM -- "não: nova mensagem" --> UI
    FIM -- "sim" --> CSAT["Encerramento + avaliação 👍 👎"]

    %% ================= CURADORIA =================
    SUG -.-> REV{"Revisor humano aprova?"}
    REV -- "sim" --> FAQNOVA[("Vira FAQ oficial<br/>faq_perguntas")]
    REV -- "não" --> DESC["Rejeitada ou corrigida"]
    FAQNOVA -.->|"a próxima pergunta igual vem do banco"| BUSCA

    %% ================= ESTILOS =================
    classDef cliente fill:#FFEDD5,stroke:#C2410C,color:#1C2128
    classDef guard fill:#FEE2E2,stroke:#B91C1C,color:#1C2128
    classDef banco fill:#DCFCE7,stroke:#166534,color:#1C2128
    classDef ia fill:#DBEAFE,stroke:#1D4ED8,color:#1C2128
    classDef loja fill:#FEF9C3,stroke:#A16207,color:#1C2128
    classDef saida fill:#F3F4F6,stroke:#4B5563,color:#1C2128
    class U,UI,UI2,BV,CSAT,FIM cliente
    class VAL,E422,PII,INJ,BLQ1,G15,G20,VOLT,COM,ESC,FORA,RFORA,GS,BLQ2,GA guard
    class BUSCA,NOTA,RFAQ,RCOM,SUG,FAQNOVA,REV,DESC,HUM banco
    class RW,OLL,LLM,RIA,FB ia
    class MENU,MPROD,MPED,LOJA,FTROCA,FHUM,SAUD,CTX loja
    class SAIDA,MEM,LOG saida
```

---

## 2. Visão de componentes

```mermaid
flowchart LR
    subgraph Navegador
      CHAT["Chat web do Tork<br/>HTML · CSS · JS"]
    end
    subgraph API["API FastAPI"]
      ROTAS["Rotas<br/>/chat · /health · /faqs · /conversas"]
      GR["Guardrails<br/>G01–G21"]
      AG["Agente<br/>menu · contexto · fluxos"]
      REPO["Repositório<br/>SQL parametrizado"]
      CFG["loja.yaml<br/>horário · endereço · políticas"]
    end
    subgraph Docker["Docker Compose"]
      PG[("PostgreSQL 17")]
    end
    OL["Ollama local<br/>modelo via .env"]

    CHAT -->|HTTP JSON| ROTAS
    ROTAS --> GR --> AG
    AG --> REPO --> PG
    AG --> CFG
    AG -->|"só quando a FAQ não responde"| OL
```

---

## 3. Fluxos guiados

### 3.1 F-TROCA: trocas e garantia

```mermaid
flowchart TD
    A["Tork: É desistência da compra,<br/>defeito ou produto errado?"] --> B{"Motivo"}
    B -- "Desistência" --> C{"Comprou online<br/>ou na loja física?"}
    C -- "Online ou telefone" --> D["Até 7 dias após receber:<br/>direito de arrependimento<br/>CDC art. 49"]
    C -- "Loja física" --> E["Segue a política da loja<br/>loja.yaml"]
    B -- "Defeito" --> F["Garantia legal de 90 dias<br/>+ garantia do fabricante<br/>CDC art. 26"]
    F --> G["Leve a nota fiscal à<br/>assistência técnica autorizada"]
    B -- "Produto ou voltagem errada" --> H["Troca prioritária"]
    H --> I[["F-HUMANO"]]
    D --> J["Como solicitar:<br/>link de trocas ou atendente"]
    E --> J
    G --> J
```

### 3.2 F-HUMANO: falar com um atendente

```mermaid
flowchart TD
    A["Tork: Em uma frase,<br/>o que você precisa?"] --> B["Cliente descreve"]
    B --> C{"G23 · consente compartilhar<br/>o resumo com a equipe?"}
    C -- "não" --> D["Mostra o contato oficial da loja<br/>nada é gravado"]
    C -- "sim" --> E[("Registra atendimento<br/>resumo · motivo · prioridade")]
    E --> F{"Dentro do horário<br/>de atendimento?"}
    F -- "sim" --> G["Um atendente continua<br/>em instantes"]
    F -- "não" --> H["Atendimento humano funciona em<br/>horário configurado; retornamos<br/>assim que abrir"]
```

### 3.3 Escada de fallback e escalonamento (G21)

```mermaid
flowchart LR
    M["Mensagem sem<br/>resposta adequada"] --> C{"Contador de<br/>fallbacks"}
    C -- "1" --> R1["Pede para reformular<br/>com mais detalhes"]
    C -- "2" --> R2["Mostra o menu"]
    C -- "3" --> R3["Oferece atendente"]
    X["Pedido explícito, frustração,<br/>atraso, produto errado,<br/>risco elétrico ou compra PJ"] --> R3
    R3 --> H[["F-HUMANO"]]
    OK["Resposta bem-sucedida"] -->|zera o contador| C
```

---

## 4. Ciclo de vida de uma resposta

```mermaid
stateDiagram-v2
    [*] --> Rascunho: escrita pelo time (YAML)
    [*] --> Pendente: gerada pela IA e aprovada nos guardrails
    Rascunho --> Revisada: revisor técnico ou jurídico aprova
    Pendente --> Revisada: revisor aprova (vira FAQ oficial)
    Pendente --> Rejeitada: revisor rejeita
    Revisada --> Ativa: entra no seed ou no banco
    Ativa --> Inativa: desativada (conteúdo desatualizado)
    Inativa --> Ativa: reativada após revisão
    Rejeitada --> [*]
```

---

## 5. Dados: do YAML ao PostgreSQL

```mermaid
flowchart LR
    Y["database/seeds/data/faq.yaml<br/>150 perguntas · 450 variações<br/>revisado em PR"] --> S["seed_mvp_faq.py<br/>UPSERT idempotente · SEED=2026"]
    M["database/migrations<br/>0001_up.sql / 0001_down.sql ..."] --> R["Script de migração<br/>registra versões aplicadas"]
    R --> PG[("PostgreSQL 17<br/>faq_categorias · faq_perguntas<br/>faq_variacoes · faq_sugestoes")]
    S --> PG
    PG --> V{"Verificador de contagens<br/>8 · 150 · 450?"}
    V -- "sim" --> OK["✅ Base pronta"]
    V -- "não" --> ERR["❌ Falha: corrigir o seed"]
    PG --> APP["Tork: busca parametrizada"]
```

---

## 6. Fluxo de trabalho do time

```mermaid
flowchart LR
    I["Issue com<br/>critério de aceite"] --> B["Branch<br/>feature/nº-descricao"]
    B --> C["Commits semânticos<br/>feat: · fix: · docs:"]
    C --> P["Pull Request<br/>o quê · por quê · como testar"]
    P --> CI{"CI verde?<br/>pytest + Ruff + Postgres"}
    CI -- "não" --> C
    CI -- "sim" --> RV{"Revisão aprovada?"}
    RV -- "não" --> C
    RV -- "sim" --> MG["Merge na main"]
    MG --> T["Tag de versão<br/>v0.3.0 na entrega"]
```

---

## 7. Cronograma da entrega

```mermaid
gantt
    title Entrega ToolExpert AI — prazo 29/11/2026 00:00
    dateFormat YYYY-MM-DD
    axisFormat %d/%m
    section Organização
    Decidir, dividir e consolidar PRs        :a1, 2026-11-23, 1d
    section Banco (P0)
    Postgres, migrações e 60 FAQs no banco   :b1, 2026-11-24, 1d
    Testes de banco e docs/db                :b2, 2026-11-27, 1d
    section Conteúdo (P0)
    150 FAQs e 450 variações                 :c1, 2026-11-25, 1d
    Revisão humana da amostra                :c2, 2026-11-26, 1d
    section Experiência e conversa (P1)
    Identidade do Tork no chat               :d1, 2026-11-25, 1d
    Menu, loja, F-TROCA, F-HUMANO, G20       :d2, 2026-11-26, 1d
    section Entrega
    Congelar às 18h e corrigir               :milestone, e0, 2026-11-27, 0d
    Ensaio, vídeo de reserva e v0.3.0        :e1, 2026-11-28, 1d
    Prazo oficial                            :milestone, e2, 2026-11-29, 0d
    Reserva (só com extensão)                :e3, 2026-11-29, 2d
```
