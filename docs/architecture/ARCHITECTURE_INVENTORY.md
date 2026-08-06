# Inventário da Arquitetura do ACD

Data da geração: 2026-07-21

## Performance, capacidade e responsividade verificadas na Sprint K

- `tests/performance` é a convenção oficial para medições sintéticas e determinísticas.
- Startup, bootstrap, composição, UI, backup/restore temporário, OpenAI falso e plugin sintético possuem budgets tolerantes.
- O único `LongRunningTaskExecutor` possui capacidade 1, backlog zero e rejeição observável quando saturado.
- A listagem crítica de 50 candidaturas, incluindo empresa e vaga, executa uma única instrução SQL e não apresenta N+1.
- Não foi adicionada baseline temporal rígida, cache, paginação, índice ou paralelismo sem evidência estável.
- Recursos Qt, SQLAlchemy, logging, plugin e cliente falso possuem teardown verificável; profiles permanecem fora do wheel.

## Finalidade e método

Este documento é uma linha de base para auditorias arquiteturais. Foi gerado por
uma varredura somente leitura dos arquivos Python em `acd/`, com análise AST dos
imports iniciados por `acd.`. As contagens incluem `__init__.py` e representam o
estado do worktree na data acima.

Este é um inventário descritivo: ele registra relações observadas, mas não avalia
conformidade ou propõe correções. Essa avaliação pertence à tarefa de validação de
dependências.

## Camadas e módulos

| Área | Arquivos Python | Responsabilidade observada |
| --- | ---: | --- |
| `acd/application` | 79 | Casos de uso, orquestração e serviços de aplicação. |
| `acd/domain` | 114 | Entidades, regras e tipos de domínio. |
| `acd/infrastructure` | 72 | Repositórios, integrações, parsers e adaptadores. |
| `acd/presentation` | 43 | Páginas, modelos de apresentação e ViewModels Qt. |
| `acd/services` | 44 | Serviços de negócio e orquestrações legadas. |
| `acd/core` | 20 | Kernel, exceções, eventos e serviços compartilhados. |
| `acd/models` | 3 | Modelos de persistência. |
| `acd/database` | 4 | Configuração e inicialização de banco. |
| `acd/repositories` | 2 | Repositório legado. |
| `acd/engineering` | 40 | Ferramentas de engenharia e análise arquitetural. |
| `acd/config` | 6 | Configuração. |
| `acd/ui` | 6 | Casca de interface e widgets legados. |
| `acd/ai` | 2 | Integrações de IA. |
| `acd/automation` | 1 | Automação. |
| `acd/utils` | 1 | Utilitário. |

Também existem os pacotes `resources`, `templates`, `tools` e `shared`; eles não
possuem arquivos Python inventariados nesta varredura.

## Dependências internas observadas

Os números abaixo são ocorrências de import entre áreas, não quantidade de
módulos únicos. Relações não listadas não foram observadas.

| Origem | Destino | Ocorrências |
| --- | --- | ---: |
| Application | Domain | 20 |
| Application | Infrastructure | 40 |
| Application | Models | 3 |
| Application | Services | 31 |
| Core | Config | 1 |
| Core | Services | 2 |
| Database | Config | 1 |
| Database | Models | 1 |
| Domain | Core | 67 |
| Domain | Models | 86 |
| Infrastructure | Database | 16 |
| Infrastructure | Domain | 91 |
| Infrastructure | Models | 2 |
| Models | Core | 1 |
| Presentation | Application | 12 |
| Presentation | Infrastructure | 9 |
| Presentation | Services | 19 |
| Repositories | Core | 1 |
| Repositories | Database | 1 |
| Repositories | Domain | 1 |
| Services | Application | 1 |
| Services | Core | 9 |
| Services | Domain | 38 |
| Services | Infrastructure | 55 |
| Services | Models | 1 |
| UI | Core | 1 |
| UI | Presentation | 14 |
| UI | Services | 5 |

## Serviços

Os módulos abaixo seguem a convenção de nome `*service*.py`.

### Application

- `application/job/service.py`
- `application/job_description_analysis_service.py`
- `application/platform/services/audit_service.py`
- `application/platform/services/backup_service.py`
- `application/platform/services/configuration_service.py`
- `application/platform/services/health_service.py`
- `application/platform/services/metrics_service.py`
- `application/platform/services/restore_service.py`
- `application/release/services/installation_service.py`
- `application/release/services/migration_service.py`
- `application/release/services/update_service.py`

### Services

- `services/agents/supervisor_service.py`
- `services/ai_execution_service.py`
- `services/ai_generation_service.py`
- `services/analytics_service.py`
- `services/application_service.py`
- `services/ats_service.py`
- `services/automation_service.py`
- `services/career_planning_service.py`
- `services/career_simulation_service.py`
- `services/company_service.py`
- `services/connector_discovery_service.py`
- `services/connector_mapping_service.py`
- `services/connector_transformation_service.py`
- `services/connector_validation_service.py`
- `services/curriculum_service.py`
- `services/export_service.py`
- `services/field_resolver_service.py`
- `services/gap_analysis_service.py`
- `services/import_service.py`
- `services/interview_service.py`
- `services/job_analysis_service.py`
- `services/job_service.py`
- `services/knowledge_service.py`
- `services/learning/approval_service.py`
- `services/learning/knowledge_reuse_service.py`
- `services/learning/learning_service.py`
- `services/planner/planner_service.py`
- `services/profile_service.py`
- `services/schema_service.py`
- `services/trend_analysis_service.py`
- `services/workflow_service.py`
- `services/workflow_template_service.py`

### Infrastructure, Core e Engineering

- `core/kernel/service_loader.py`
- `core/kernel/service_registry.py`
- `engineering/architecture/services/dependency_graph_service.py`
- `engineering/architecture/services/graph_analysis_service.py`
- `engineering/architecture/services/metrics_service.py`
- `engineering/architecture/services/module_service.py`
- `engineering/architecture/services/report_service.py`
- `infrastructure/agents/capability_service.py`
- `infrastructure/platform/migration_service.py`
- `infrastructure/release/feature_flag_service.py`

## Entidades de domínio

As entidades estão concentradas em `domain/entities/`:

`ai_generation`, `ai_prompt`, `analytics_recommendation`, `analytics_snapshot`,
`answer_template`, `application`, `ats_score`, `automation_log`,
`automation_result`, `automation_session`, `browser_profile`, `certification`,
`connector_setting`, `cover_letter_version`, `curriculum`, `curriculum_version`,
`education`, `experience`, `generation_log`, `interview`, `job`, `job_profile`,
`keyword`, `language`, `metric`, `profile`, `profile_version`, `project`,
`prompt_template`, `publication`, `recommendation`, `report`, `resume_version`,
`score_detail`, `skill`, `skill_gap`, `social_link`, `timeline_event`, `trend`,
`workflow`, `workflow_event`, `workflow_execution`, `workflow_log`,
`workflow_step` e `workflow_template`.

Além desse pacote, o domínio contém agregados e componentes especializados em
`domain/agent`, `domain/agents`, `domain/analytics`, `domain/automation`,
`domain/career`, `domain/connector`, `domain/learning`, `domain/planner`,
`domain/platform`, `domain/release` e `domain/workflow`.

## Repositórios

### Infrastructure

`agent/agent_repository`, `agents/agent_repository`, `analytics_repository`,
`application_repository`, `ats_repository`, `career_repository`,
`company_repository`, `connector_repository`, `curriculum_repository`,
`interview_repository`, `job_profile_repository`, `job_repository`,
`learning/learning_repository`, `platform/platform_repository`,
`profile_repository`, `prompt_repository`, `release/release_repository`,
`skill_repository` e `workflow_repository`.

### Repositório legado

- `repositories/applicatrion_repository.py`

## Casos de uso

Os módulos que seguem a convenção `*use_case*.py` são:

- `application/learning/learning_use_cases.py`
- `application/platform/platform_use_cases.py`
- `application/profile/profile_use_cases.py`
- `application/start_application_use_case.py`

Há ainda casos de uso organizados por operação dentro de subpacotes de
`application`, como `application/agent`, `application/company`, `application/ai`
e `application/job`.

## Presenters e apresentação

Nenhum módulo de produção segue a convenção `*presenter*.py`. A adaptação para a
interface está distribuída em `presentation/pages`, `presentation/models`,
`presentation/platform` e nos ViewModels, incluindo
`presentation/pages/new_application_view_model.py`.

## Fonte de verificação

- Estrutura de dependências: `tests/architecture/test_layer_dependencies.py`
- Inventário legível anterior: `docs/architecture/ARCHITECTURE_INVENTORY.md`
- Scanner existente: `acd/tools/architecture_inventory.py`

## Runtime, packaging e estado local verificados na Sprint E

- Entry point oficial: `acd = acd.desktop:main`.
- `DesktopCompositionRoot` e o unico Composition Root produtivo.
- `DatabaseBootstrap` usa o Registry ORM explicito de 92 tabelas.
- `pyproject.toml` governa versao `0.1.0`, dependencias e QSS empacotado.
- `scripts/quality_gate.ps1` usa basetemp exclusivo sob `%TEMP%/acd-pytest`.
- Bancos, coverage, logs, caches e artefatos de Gate sao estado local conforme
  `docs/repository/local_files_policy.md`.
- `domain/agent`, `domain/agents`, Kernel/Bootstrap antigos, wizard e facade
  permanecem candidatos de investigacao; nenhuma aposentadoria foi realizada.

## Ciclo de dados local verificado na Sprint G

- `acd.database.local_state` resolve um caminho absoluto sem depender do CWD e
  sem criar arquivos no import.
- O banco legado existente permanece no lugar; instalações novas usam o
  diretório local do usuário, salvo override explícito.
- `SQLiteDatabaseLifecycle` implementa backup online consistente, SHA-256,
  manifesto, integridade, compatibilidade mínima e restauração com backup
  preventivo e substituição atômica.
- O manifesto de 92 tabelas segue como autoridade temporária de schema; tabelas
  extras são preservadas e Alembic permanece adiado.

## Observabilidade local verificada na Sprint H

- `acd/observability` centraliza configuração, contexto, sanitização e
  diagnósticos sem efeito colateral de import.
- `acd.desktop` possui o ciclo explícito de configuração e teardown; nenhum
  módulo de Presentation cria handlers.
- Eventos estruturados cobrem startup, bootstrap, backup/restore e tarefas
  longas com correlação e duração monotônica.
- Diagnósticos consultam SQLite somente em modo read-only e exportam metadata
  sanitizada, determinística e acompanhada de SHA-256.
- Logs rotativos e exports de diagnóstico são estado local, não telemetria e
  não pertencem ao wheel.

## Limites de segurança verificados na Sprint I

- `acd/security` centraliza segredos, paths, arquivos externos, URLs, envelopes
  de IA e manifestos de plugin sem side effects de import.
- O provider OpenAI não lê segredo diretamente e valida endpoint, timeout,
  retries, input não confiável e resposta tipada.
- O loader legado é deny-by-default, não altera `sys.path` e não recebe sessão
  de banco; plugins autorizados ainda são in-process e não possuem sandbox.
- Importação de currículo valida nome, extensão, tamanho e assinatura antes da
  escrita em raiz controlada.

## Resiliência e modos de falha verificados na Sprint J

- `acd.resilience` centraliza categorias, retry finito, backoff/jitter, deadline
  e cancelamento cooperativo sem nova dependência.
- OpenAI desabilita retry oculto do SDK e repete somente timeout, rate limit,
  conexão e 5xx antes de aceitar qualquer efeito local.
- O único `LongRunningTaskExecutor` possui estados explícitos e nunca aborta a
  thread; conclusão tardia após cancelamento/timeout não vira sucesso.
- SQLite repete apenas `busy/locked` em cópia idempotente; backup parcial e
  restore antes da promoção atômica possuem cleanup/rollback observável.
- Falha de plugin desabilita somente a capacidade opcional. Circuit breaker,
  checkpoint durável e timeout de plugin in-process permanecem adiados.
- Não foram encontrados subprocessos produtivos, `shell=True`, `eval`, `exec`,
  pickle externo, YAML inseguro, servidor web ou downloader genérico.

## Temporary domain ORM exception recorded in Sprint E.0

- The Architecture Inventory confirmed 85 existing modules under `acd/domain`
  that import SQLAlchemy and are loaded by the explicit ORM Registry.
- ADR-028 records this as a temporary hybrid ORM/domain exception. Its
  machine-checked baseline is `quality/domain-sqlalchemy-baseline.json`;
  the policy is monotonic decrease and the final target is zero modules.
- `DatabaseBootstrap`, the explicit Registry, and the 92-table manifest remain
  unchanged. Sprint E may document and inventory this debt but may not migrate
  entities, alter the Registry, or alter the schema.

## Repository hygiene facts recorded in Sprint E

- The worktree is intentionally loaded: 75 tracked modifications, 580
  untracked entries, and 9,224 ignored entries were measured on 2026-08-04.
- Permission denied remains limited to generated pytest/runtime basetemps and
  generated `acd-*` directories. They are operational debt and were neither
  elevated nor removed.
- Root Gate evidence is local by policy. The preservation manifest records the
  final green Sprint C and Sprint D evidence plus Sprint E/E.0 governance
  artifacts; future movement requires SHA-256 verification.
- Legacy `agent`/`agents`, Kernel/Bootstrap compatibility paths, containers,
  the experimental wizard/facade, and historical wrappers remain inventory
  items. Their removal belongs to Sprint F, while ORM decoupling belongs to the
  dedicated ADR-028 migration plan.

## Legacy retirement governance verified in Sprint F

- ADR-029 reconciles the documented and verified containerless productive path:
  `app.py -> acd.desktop:main -> DesktopCompositionRoot`.
- Kernel, Bootstrap, `DependencyContainer`, and query-adapter registration are
  compatibility/test-only and are not composed by the desktop runtime.
- `domain/agent` and `domain/agents` are distinct ORM bounded contexts with
  separate tables; neither is an alias or removal candidate in this Sprint.
- Wizard, new-application views, and facade remain experimental and absent from
  productive routes. No `applications/new` or `new_application` route exists.
