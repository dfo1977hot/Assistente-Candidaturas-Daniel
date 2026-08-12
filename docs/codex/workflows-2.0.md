# Codex Task — Workflows 2.0: Condições, gatilhos automáticos e agendamento

## Objetivo
Evoluir o módulo Workflows do ACD a partir da Sprint 1.1, adicionando condições `SE/ENTÃO`, gatilhos automáticos, agendamento, retomada segura e rastreabilidade, sem duplicar regras dos Services existentes.

## Antes de alterar código
1. Leia `AGENTS.md`.
2. Leia `.github/CONSTITUTION.md`.
3. Leia `docs/codex/workflows-1.1.md`.
4. Inspecione o worktree atual de Workflows, Composition Root, EventBus e Services conectados.
5. Use o worktree local validado como fonte de verdade.

## Regras arquiteturais
- Workflows continua sendo apenas ORQUESTRADOR.
- Presentation não importa Infrastructure.
- Presentation não instancia Service/Repository.
- Dependências concretas são criadas no Composition Root.
- Condições e gatilhos são avaliados em Services/Domain.
- Não usar `eval()`.
- Não criar retries infinitos ou `except: pass`.
- Logs não podem expor segredos.
- Gupy permanece manual-only.
- Salário esperado permanece igual à Remuneração ideal (`salary_max`).
- Data resposta permanece vazia quando não houver resposta real.

## 1. Condições SE / ENTÃO / SENÃO
Permitir condição opcional por etapa.

Exemplo:
SE `fit_score >= 75`
ENTÃO executar a etapa
SENÃO ignorar e continuar, ou encerrar conforme configuração.

Operadores iniciais:
- `==`
- `!=`
- `>`
- `>=`
- `<`
- `<=`
- `contém`
- `não contém`
- `está vazio`
- `não está vazio`

Campos devem vir do contexto estruturado:
- `job_id`
- `application_id`
- `curriculum_id`
- `fit_score`
- `salary_ideal`
- `salary_offered`
- `application_url`
- `company_id`
- `application_status`

Criar avaliador seguro e testável. Quando condição for falsa:
- status da etapa = `Ignorada`;
- registrar motivo;
- por padrão continuar;
- permitir opção explícita `Encerrar workflow`.

## 2. Gatilhos automáticos
Conectar gatilhos reais para:
- Vaga criada;
- Vaga importada;
- Candidatura criada;
- Mudança de status da candidatura;
- Execução manual.

Não duplicar eventos dentro das Pages. Preferir EventBus/Application Service hooks já existentes.

## 3. Proteção contra duplicidade
Evitar duas execuções equivalentes disparadas pelo mesmo evento. Criar chave idempotente baseada em workflow_id, event_type, entity_id e occurrence/event id quando existir.

## 4. Agendamento
Adicionar gatilho `Agendado`.

Suportar:
- uma vez;
- diariamente;
- semanalmente;
- mensalmente.

Campos:
- data;
- hora;
- recorrência;
- ativo/inativo;
- `last_run_at`;
- `next_run_at`.

Não criar Windows Service ou tarefa do sistema nesta Sprint. Ao abrir o ACD, verificar execuções vencidas; enquanto aberto, executar próximos vencimentos. Documentar claramente essa limitação.

## 5. WorkflowSchedulerService
Criar Service dedicado para:
- listar agendamentos ativos;
- calcular próxima execução;
- identificar vencidos;
- disparar workflow;
- atualizar `last_run_at` e `next_run_at`;
- impedir duplicidade;
- executar sem bloquear UI.

Injetar pelo Composition Root.

## 6. UI Workflows
Manter layout compacto.

Ao selecionar uma etapa, permitir configurar:
- Campo da condição;
- Operador;
- Valor;
- comportamento se condição falsa.

Quando gatilho = `Agendado`, mostrar Data, Hora e Recorrência.
Quando gatilho = `Mudança de status`, mostrar Status alvo.

## 7. Retomada
Se etapa retornar `Aguardando usuário`:
- interromper workflow;
- persistir checkpoint;
- não executar etapas seguintes.

Adicionar ação `Retomar workflow`:
- retomar da etapa seguinte ao checkpoint resolvido;
- não repetir etapas concluídas;
- reutilizar contexto persistido;
- preservar idempotência.

Para falha, manter `Reexecutar etapa` e adicionar `Retomar a partir desta etapa`.

## 8. Histórico e logs
Registrar origem manual/evento/agendada, gatilho, condição avaliada, valor esperado, valor observado, resultado, motivo de etapa ignorada, IDs relevantes e duração. Não registrar segredos.

## 9. Templates
Atualizar templates para aceitar condições. No template `Preparação da candidatura`, permitir um limiar configurável de aderência. Não transformar 75 em regra global fixa.

## 10. API para Dashboard futuro
Preparar métodos de consulta para workflows ativos, execuções em andamento, falhas recentes, aguardando usuário e próxima execução agendada. Não implementar o Dashboard completo nesta Sprint.

## Testes obrigatórios
Criar/atualizar testes para:
1. avaliador de condição sem `eval`;
2. todos os operadores suportados;
3. condição falsa gera `Ignorada`;
4. opção de encerrar em condição falsa;
5. Vaga criada dispara workflow compatível;
6. Vaga importada dispara workflow compatível;
7. Candidatura criada dispara workflow compatível;
8. Mudança de status respeita status alvo;
9. execução manual continua funcionando;
10. mesma ocorrência não dispara workflow duplicado;
11. cálculo de próxima execução única;
12. cálculo diário;
13. cálculo semanal;
14. cálculo mensal;
15. workflow vencido roda ao iniciar ACD;
16. scheduler não bloqueia UI;
17. `Aguardando usuário` cria checkpoint;
18. `Retomar workflow` não repete etapas concluídas;
19. retry de falha continua idempotente;
20. logs não expõem secrets;
21. Presentation não importa Infrastructure;
22. Presentation não instancia Service/Repository;
23. Composition Root injeta scheduler e trigger dispatcher;
24. Gupy continua manual-only;
25. regras de remuneração permanecem intactas.

## Gates obrigatórios
Execute testes direcionados primeiro.

Depois:

`C:\Projetos\.venv\Scripts\python.exe -m ruff check .`

`C:\Projetos\.venv\Scripts\python.exe -m pytest -q`

Não fazer commit se qualquer gate estiver vermelho.

## Entrega esperada
Ao concluir, responder com:
1. arquivos alterados;
2. arquitetura implementada;
3. condições disponíveis;
4. gatilhos realmente conectados;
5. comportamento do scheduler;
6. comportamento de retomada;
7. testes direcionados;
8. Ruff global;
9. pytest global;
10. `APPROVED` ou `BLOCKED`.

## Não fazer
- não usar `eval()`;
- não automatizar Gupy;
- não duplicar lógica de Services;
- não criar Windows Service nesta Sprint;
- não alterar regra salarial;
- não preencher Data resposta automaticamente;
- não enfraquecer testes arquiteturais;
- não commitar antes dos gates globais verdes.
