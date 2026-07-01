---
name: acd-sprint-0-foundation-refactoring
description: "Executa a Sprint 0 de refatoracao da fundacao do ACD com inventario arquitetural obrigatorio, consolidacao de camadas, deduplicacao de modulos/models/tabelas, unificacao SQLAlchemy (Base/engine/SessionLocal), compatibilidade temporaria com deprecacao, governanca por ADR e bloqueio de sprint quando houver inconsistencias estruturais."
argument-hint: "Escopo da execucao (full, dry-run, ou foco em dominio/banco/bootstrap)"
user-invocable: true
disable-model-invocation: false
---

# ACD Sprint 0 - Foundation Refactoring & Architecture Consolidation

## Resultado esperado
Esta skill conduz uma refatoracao estrutural bloqueante para deixar o projeto com arquitetura unica, inicializacao estavel e base de dados consistente.

Ao final, deve entregar:
- Aplicacao iniciando sem erros.
- Interface principal abrindo via python app.py.
- SQLite operacional sem apagar base existente.
- Uma unica arquitetura canonica.
- Modulos, entidades, modelos e tabelas duplicadas eliminados.
- Imports circulares eliminados.
- Configuracao, logging e DI padronizados.
- Relatorio final tecnico com decisoes e evidencias.
- Registro de decisoes estruturais em ADR.

## Quando usar
Use esta skill quando houver sinais de deriva arquitetural:
- Pastas paralelas com o mesmo papel (ex.: agent vs agents).
- Repositorios/servicos dispersos em mais de uma camada.
- Mais de uma Base declarativa, metadata, engine ou SessionLocal.
- Erros de inicializacao, import circular ou conflito de tablename.
- Necessidade de preparar release de estabilizacao antes de evolutivas.

## Entradas
- Escopo: full, dry-run, domain-only, db-only, bootstrap-only.
- Politica de migracao: copiar, corrigir imports, validar, remover antigo.
- Politica de exclusao: mover para deprecated antes de remover definitivo.
- Cobertura: 95% obrigatorio para modulos de nucleo e flexivel para legado/UI com justificativa.

## Workflow

### Fase 00 - Gate obrigatorio de governanca (antes de qualquer sprint)
1. Executar obrigatoriamente a skill architecture-inventory antes de iniciar qualquer sprint.
2. Respeitar status de gate:
   - APPROVED: sprint pode iniciar.
   - BLOCKED: sprint deve ser interrompida e seguir para consolidacao arquitetural.
3. Verificar e bloquear sprint quando houver qualquer inconsistencia em:
   - modulos duplicados.
   - classes duplicadas.
   - tabelas duplicadas.
   - imports circulares.
   - Base duplicadas.
   - engine duplicados.
   - SessionLocal duplicadas.
4. Gerar relatorio de conflitos antes de qualquer geracao de novo codigo.
5. Sem relatorio de inventario aprovado, a sprint nao pode continuar.

### Fase 0 - Regras de seguranca
1. Nao quebrar funcionalidade existente sem registrar compensacao.
2. Preferir migrar e adaptar imports antes de excluir codigo.
3. Toda exclusao deve entrar no relatorio final com justificativa.
4. Evitar alteracoes cosméticas fora do escopo.
5. Nunca apagar imediatamente artefatos legados: mover primeiro para deprecated/.
6. Nunca mover diretamente: copiar, ajustar imports, testar, validar app, remover antigo.
7. Nunca apagar acd.db para corrigir incompatibilidade; usar migration.

### Fase 1 - Inventario estrutural completo
1. Mapear arvore de diretorios de codigo-fonte.
2. Identificar duplicacoes de nome e responsabilidade:
   - domain/agent vs domain/agents.
   - infrastructure/agent vs infrastructure/agents.
   - repositories/ vs infrastructure/repositories/.
   - services/ vs application/ (servico de dominio vs caso de uso).
3. Identificar artefatos redundantes:
   - Modelos SQLAlchemy duplicados.
   - __tablename__ repetidos.
   - mais de uma Base/metadata/engine/SessionLocal.
4. Produzir lista de candidatos a mover, renomear e remover.
5. Registrar no relatorio qual estrutura viola o padrao definitivo de camadas.

### Fase 2 - Definir arquitetura canonica
Aplicar destino unico por responsabilidade:
- acd/application/: casos de uso.
- acd/domain/: regras de negocio e contratos.
- acd/infrastructure/: adaptadores tecnicos e repositorios concretos.
- acd/presentation/: UI.
- acd/database/: bootstrap e conexao de banco.
- acd/models/: modelos persistentes compartilhando a mesma Base.
- acd/core/: configuracao transversal e inicializacao.
- acd/resources/: ativos e recursos estaticos.
- acd/ui/: componentes de interface.
- acd/utils/: utilitarios compartilhados.
- tests/: testes automatizados.
- docs/: documentacao e ADR.

Decisoes obrigatorias desta sprint:
- Manter domain/agents e eliminar domain/agent.
- Manter infrastructure/agents e eliminar infrastructure/agent.
- Consolidar repositorios em infrastructure/repositories/.
- Proibir surgimento de novas duplicidades sem passar por inventario arquitetural.

### Fase 3 - Consolidacao fisica de modulos
1. Copiar arquivos para o destino canonico (nao mover diretamente).
2. Atualizar imports progressivamente para evitar quebras em cascata.
3. Resolver colisao de nomes (ex.: agent/agents) com convencao unica.
4. Aplicar camada de compatibilidade durante Sprint 0 usando wrappers e DeprecationWarning.
5. Mover diretorios legados para deprecated/ (ex.: deprecated/domain/agent/).
6. Somente apos validacao e aprovacao, remover legado de forma definitiva.

### Fase 4 - Unificacao SQLAlchemy
1. Garantir uma unica Base declarativa em acd/models/base.py.
2. Garantir um unico registry/metadata efetivo.
3. Garantir um unico engine e uma unica SessionLocal.
4. Corrigir create_database.py para:
   - criar engine.
   - criar SessionLocal.
   - importar Base.
   - registrar todos os modelos.
   - executar Base.metadata.create_all(engine) sem apagar banco existente.
5. Eliminar tabelas/modelos repetidos e conflitos de tablename.
6. Quando houver incompatibilidade de schema, gerar migration em vez de recriar banco.

### Fase 5 - Imports circulares e bootstrap
1. Detectar ciclos de import entre camadas.
2. Aplicar lazy import somente quando necessario.
3. Reorganizar dependencias para fluxo unidirecional.
4. Garantir fluxo de inicializacao:
   main -> load config -> logger -> database -> theme -> DI container -> main window.

### Fase 6 - Padroes transversais
1. Centralizar configuracoes em config.py.
2. Unificar logging em um logger raiz.
3. Implementar container de DI com encadeamento:
   Container -> Database -> Repositories -> Services -> UseCases.
4. Padronizar type hints, docstrings e PEP8.

### Fase 7 - Qualidade e higiene
1. Remover __pycache__ versionados.
2. Garantir existencia e consistencia de:
   - .vscode/settings.json
   - .env.example
   - .pre-commit-config.yaml
3. Garantir ferramentas de qualidade ativas:
   - ruff
   - black
   - isort
   - mypy
4. Criar/atualizar testes de:
   - banco
   - configuracao
   - inicializacao
   - models
   - repositories
5. Em dry-run, limitar alteracoes a criacao/validacao dos arquivos auxiliares obrigatorios:
    - .env.example
    - .vscode/settings.json
    - .pre-commit-config.yaml
6. Em dry-run, nao alterar codigo-fonte, imports, models, banco nem estrutura de modulos.

### Fase 7.1 - Politica de cobertura (regra obrigatoria)
1. Exigir cobertura minima de 95% para:
    - core
    - database
    - models
    - dependency injection
    - repositories
    - configuration
    - bootstrap
    - logging
2. Permitir cobertura abaixo de 95% somente com justificativa explicita para:
    - UI
    - widgets
    - temas
    - recursos graficos
    - codigo legado
3. Gerar tabela obrigatoria no relatorio final com colunas:
    - modulo
    - cobertura
    - status
    - justificativa
4. Exemplo de formato:
    - Core | 98% | OK | -
    - Database | 100% | OK | -
    - Models | 97% | OK | -
    - UI | 71% | Justificado | baixa testabilidade de camada visual

### Fase 8 - Validacao e aceite
Executar checks finais:
1. python app.py abre Dashboard, Sidebar e StatusBar sem erro.
2. Banco SQLite inicializa corretamente sem recriacao destrutiva de acd.db.
3. Nao ha model duplicado.
4. Nao ha tablename repetido.
5. Nao ha import circular.
6. Suite de testes passando com politica de cobertura aplicada por modulo.
7. Compatibilidade temporaria ativa para caminhos legados com DeprecationWarning.

## Pontos de decisao
- Se houver duplicidade com comportamento divergente:
   preservar primeiro o modulo arquiteturalmente correto.
- Em caso de empate arquitetural:
   preservar o modulo mais coeso, com menor acoplamento e maior cobertura.
- Somente se ainda houver empate:
   preservar o mais utilizado.
- Compatibilidade temporal:
   Sprint 0: compatibilidade ativa.
   Sprint 0.1: compatibilidade com aviso reforcado.
   Sprint 1: remocao definitiva.

## Definicao de pronto
- Arquitetura consolidada e consistente.
- Banco funcional com criacao automatica.
- Inicializacao estavel da aplicacao e UI operacional.
- Codigo organizado e documentado.
- Testes passando com cobertura acordada.
- Nenhuma inconsistencia estrutural pendente no inventario.

## Regras permanentes de nomenclatura
E proibido introduzir novamente duplicidades sem Architecture Inventory e aprovacao:
- agent e agents simultaneamente.
- repository e repositories simultaneamente.
- service e services simultaneamente.
- entity e entities simultaneamente.

## Saidas obrigatorias
Gerar relatorio final contendo:
1. Arquivos removidos, renomeados e movidos.
2. Decisoes arquiteturais e racional tecnico.
3. Problemas encontrados e resolucao aplicada.
4. Resultado dos testes e cobertura.
5. Confirmacao de execucao do app sem erros.
6. Tabela de cobertura por modulo com status e justificativa.
7. Lista do que foi movido para deprecated/ aguardando aprovacao de exclusao.
8. Relacao de ADRs criados/atualizados.

## Architecture Governance (ADR obrigatorio)
Toda alteracao estrutural desta skill deve registrar um ADR em docs/architecture/adr/.

Padrao sugerido:
- ADR-001.md - Padronizacao da camada Domain
- ADR-002.md - Unificacao do SQLAlchemy Base
- ADR-003.md - Migracao de agent para agents
- ADR-004.md - Estrategia de Dependency Injection

Cada ADR deve conter:
1. Contexto
2. Decisao
3. Consequencias
4. Alternativas consideradas
5. Status (proposto, aceito, substituido)

## Comando de commit sugerido
refactor(core): consolidate architecture and remove duplicated modules

## Extensao recomendada (proxima etapa)
Criar Sprint 0.1 - Arquitetura Modular com contratos para repositories, services, connectors e agents, permitindo troca de implementacoes sem refatoracao profunda.
