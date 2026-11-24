# 0014 — Base de conhecimento: manutenção

## De onde vêm as respostas

| Origem | Onde fica | Quem cria |
|--------|-----------|-----------|
| Carga inicial (60 FAQs) | `knowledge/faq.json`, copiado para o banco na 1ª execução | Equipe (a partir de `docs/0003-Requisitos-do-Produto.md`) |
| Respostas aprendidas | Banco `data/loja.db`, `origem='agente'` | Ollama, quando a pergunta não existia |

> O arquivo `data/loja.db` **não vai para o Git** (está no `.gitignore`). Ele é recriado
> a partir do `faq.json` sempre que for apagado.

## Formato de uma FAQ (`knowledge/faq.json`)

```json
{
  "id": "FAQ-013",
  "categoria": "brocas_discos_acessorios",
  "pergunta": "Qual broca usar em concreto?",
  "variacoes": ["broca para parede", "broca de concreto"],
  "palavras_chave": ["broca", "concreto", "sds", "sds plus", "sds max", "videa", "alvenaria"],
  "resposta": "Utilize broca adequada a concreto/alvenaria e compatível com a máquina. ...",
  "fonte": "docs/0003-Requisitos-do-Produto.md",
  "revisado_em": null,
  "status": "rascunho"
}
```

| Campo | Regra |
|-------|-------|
| `id` | Único, formato `FAQ-NNN` |
| `categoria` | Uma das 8 categorias abaixo. `atendimento_comercial` **nunca** passa pelo LLM |
| `variacoes` | Frases que o cliente costuma usar. Se a pergunta for idêntica a uma delas, a nota é 1,0 |
| `palavras_chave` | Termos (sem acento, tanto faz) que identificam o assunto. Valem mais que o texto da pergunta |
| `status` | `rascunho` → `pendente_validacao` → `validado`; `inativo` desliga a FAQ |

Categorias: `escolha_de_ferramentas`, `brocas_discos_acessorios`, `baterias_alimentacao`,
`medicao_eletronica`, `soldagem_compressores_limpeza`, `uso_manutencao_seguranca`,
`atendimento_comercial`, `diagnostico_comparacao` (e `aprendida`, só no banco).

## Como adicionar ou corrigir uma FAQ

1. Edite `knowledge/faq.json`.
2. Apague `data/loja.db` (as respostas aprendidas ainda não validadas serão perdidas).
3. Rode `.venv\Scripts\python -m pytest -q` para garantir que as perguntas da demo continuam certas.
4. Reinicie a API.

**Dica:** se uma pergunta cair na FAQ errada, inclua as palavras dela nas `palavras_chave`
da FAQ correta ou cadastre a frase em `variacoes`.

## Como revisar as respostas aprendidas pelo agente

Listar as pendentes:

```powershell
.venv\Scripts\python -c "import sqlite3; c=sqlite3.connect('data/loja.db'); [print(r) for r in c.execute(\"SELECT id, pergunta, resposta FROM faq WHERE origem='agente' AND status='pendente_validacao'\")]"
```

Aprovar, corrigir ou desativar (exemplo para `FAQ-061`):

```sql
UPDATE faq SET status = 'validado' WHERE id = 'FAQ-061';
UPDATE faq SET resposta = 'Texto corrigido...', status = 'validado' WHERE id = 'FAQ-061';
UPDATE faq SET status = 'inativo' WHERE id = 'FAQ-061';
```

> Respostas aprovadas que devam fazer parte da base oficial devem ser copiadas para
> `knowledge/faq.json`, já que o banco local não é versionado.
> O painel administrativo para isso está no backlog do MVP 2.
