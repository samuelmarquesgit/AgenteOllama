# Segurança e privacidade do banco

## Acesso

| Item | Situação nesta entrega (SQLite) | Na migração para o PostgreSQL |
|------|----------------------------------|-------------------------------|
| Onde fica | Arquivo local `data/loja.db`, fora do Git (`.gitignore`) | Servidor em rede privada, nunca exposto à internet |
| Quem acessa | O processo da API e o terminal | Papel `toolexpert_app` (SELECT na FAQ/catálogo, INSERT em sugestões, atendimentos e avaliações) |
| Alterações de estrutura | Só por migração versionada | Papel separado `toolexpert_migrator` |
| Credenciais | Não há (arquivo local) | Só em `.env` (ignorado) / secrets do CI; `.env.example` sem valores reais |
| SQL injection | Todas as consultas são parametrizadas; termos de busca normalizados (curingas `%`/`_` sem efeito) | Idem |

Testes que comprovam: `test_busca_faq_resiste_a_sql_injection_e_curingas`, `test_checks_rejeitam_dados_invalidos`, `test_nenhum_registro_orfao`.

## Dados pessoais

| Regra | Como é garantida |
|-------|------------------|
| O chat não guarda CPF, cartão, e-mail, telefone ou CEP | Guardrail G02 mascara antes de qualquer gravação; G18 impede gravar sugestões de mensagens que tinham dado pessoal |
| Atendimento humano sem identificação pessoal | `atendimentos_humanos` só tem `conversa_ref` (ID aleatório do navegador), resumo e motivo |
| Consentimento antes de registrar atendimento | `CHECK (consentimento = 1)` na tabela (G23) |
| Logs sem o texto do cliente | O log da API registra só FAQ-ID, nota, origem e guardrails |
| Seeds 100% sintéticos | Nenhum dado real de pessoa ou loja |

## Retenção

| Dado | Retenção proposta | Situação |
|------|-------------------|----------|
| Histórico de conversa | Só em memória (some ao reiniciar a API) | Em vigor |
| `faq_sugestoes` | Até a revisão; rejeitadas podem ser apagadas após 30 dias | Proposta (sem rotina automática ainda) |
| `atendimentos_humanos` | 90 dias após encerrado, depois anonimizar o resumo | Proposta (fase de histórico, DB §4) |
| `avaliacoes` | Indefinida (não tem dado pessoal) | Em vigor |

As bases legais e os prazos definitivos devem ser validados com um responsável jurídico antes de uso real (DB §9).

## Backup

Desenvolvimento: o banco é recriável a partir dos seeds; só as `faq_sugestoes` não estão em arquivo.
Para preservá-las: `sqlite3 data/loja.db ".backup data/backup.db"` (ou copiar o arquivo com a API parada).
Ambiente persistente: backup diário + teste de restauração (DB §9), a definir na migração para o PostgreSQL.
