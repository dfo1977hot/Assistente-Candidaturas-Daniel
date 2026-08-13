# ACD 1.0 Readiness — Consolidação arquitetural

## Objetivo

Congelar um baseline estável antes de novas integrações externas.

## Baseline estável

O último gate global integralmente aprovado antes da experiência de e-mail foi:

- Ruff global: verde
- Pytest: 1756 passed, 1 skipped
- Follow-up 1.0: aprovado
- Workflows 2.0: aprovado
- Dashboard & Analytics 1.1: aprovado
- Cartas 1.1: aprovado

## Estado das comunicações

A integração Gmail/IMAP foi tratada como experimento e não faz parte do baseline estável.
A tentativa Microsoft Graph também não deve ser incorporada nesta fase.

O contrato estável é:

`CommunicationsService -> MailMessageReader`

O Service:
- associa mensagens reais a candidaturas;
- registra `Retorno recebido` na timeline;
- preserva idempotência;
- não conhece autenticação ou API do provedor;
- não envia, responde, exclui, move ou marca mensagens.

Adapters de provedor ficam em Infrastructure e serão adicionados em Sprints específicas.

## Próximo adapter recomendado

Outlook Classic via COM, somente após este baseline ficar globalmente verde.

Requisitos futuros:
- Windows + Outlook Classic instalado;
- adapter isolado em Infrastructure;
- inicialização COM apropriada no worker;
- nenhuma senha armazenada;
- leitura somente;
- testes com adapter fake/mocks COM;
- fallback amigável quando Outlook Classic não estiver disponível.

## Fora de escopo desta consolidação

- Outlook Classic;
- Microsoft Graph;
- Gmail;
- envio automático de mensagens;
- sincronização contínua em background;
- calendário/Teams;
- IA lendo caixa postal.

## Gate de saída

A consolidação só está pronta com:

- compileall direcionado;
- Ruff direcionado e global;
- testes direcionados;
- pytest global verde;
- worktree sem adapters experimentais ativos no runtime.
