---
name: architecture-inventory
description: "Executa um inventario arquitetural somente leitura antes de qualquer sprint para detectar degradacao estrutural, duplicacoes, violacoes de camadas, problemas SQLAlchemy, imports circulares, gaps de cobertura e ADR pendente. Use para decidir APPROVED ou BLOCKED antes de implementar qualquer funcionalidade."
argument-hint: "Escopo da inspecao (full, quick, domain, sqlalchemy, imports, coverage, adr)"
user-invocable: true
disable-model-invocation: false
---

# Architecture Inventory (Gate Pre-Sprint)

## Objetivo
Esta skill e obrigatoria antes de qualquer sprint.

Ela nunca altera codigo-fonte.
Ela apenas inspeciona e produz diagnostico arquitetural.

Perguntas que esta skill responde:
- O projeto continua integro?
- Houve degradacao arquitetural?
- Posso iniciar a nova sprint?

## Regra de uso
Fluxo obrigatorio:
1. Executar Architecture Inventory.
2. Se status for APPROVED, a sprint pode iniciar.
3. Se status for BLOCKED, interromper sprint e executar plano de consolidacao arquitetural.

## Modo de operacao (somente leitura)
Permite:
- listar diretorios e arquivos.
- analisar imports, dependencias e metadados.
- executar testes/checks em modo leitura.
- gerar artefatos de relatorio e diagrama em docs/architecture/.

Nao permite:
- editar modulos de producao.
- mover, renomear ou apagar codigo de aplicacao.
- alterar schema de banco ou migracoes.

## Verificacoes obrigatorias

### 1) Estrutura
Detectar:
- diretorios duplicados.
- modulos redundantes.
- camadas fora do padrao.
- arquivos orfaos.

### 2) SQLAlchemy
Validar unicidade de:
- Base declarativa.
- engine.
- SessionLocal.

### 3) Models
Detectar __tablename__ duplicado e conflito de model.

### 4) Imports
Analisar:
- import circular.
- import morto.
- dependencia quebrada.

### 5) Clean Architecture
Validar dependencias proibidas entre camadas.
Exemplo de violacao: UI dependendo diretamente de Infrastructure.

### 6) Pureza de Domain
Falhar se dominio depender de bibliotecas de infraestrutura/UI, incluindo:
- Qt
- PySide
- SQLAlchemy

### 7) Dependency Graph
Gerar diagrama em docs/architecture/dependency-graph/dependency_graph.svg.

### 8) Complexity
Medir por modulo:
- tamanho.
- acoplamento.
- coesao.

### 9) Cobertura
Gerar Coverage Report por camada.

### 10) ADR
Se houver mudanca estrutural detectada desde a ultima baseline:
- verificar existencia de ADR em docs/architecture/adr/.
- sem ADR correspondente, bloquear sprint.

## Estrutura canonica esperada
- acd/application/
- acd/domain/
- acd/infrastructure/
- acd/presentation/
- acd/database/
- acd/models/
- acd/core/
- acd/resources/
- acd/ui/
- acd/utils/
- tests/
- docs/

## Criterios de decisao
Status APPROVED:
- sem duplicacao critica de modulos/camadas.
- sem import circular bloqueante.
- sem Base/engine/SessionLocal duplicado.
- sem conflito de __tablename__.
- sem dependencia proibida de dominio.
- sem ADR pendente para mudanca estrutural.

Status BLOCKED:
- qualquer violacao critica acima.
- ou tendencia de degradacao sem plano de remediacao.

## Architecture Score (obrigatorio)
Ao final da execucao, calcular Architecture Score de 0 a 100.

Pesos padrao:
- Clean Architecture: 25
- Duplicacoes: 20
- Imports e dependencias: 10
- Testes e cobertura: 20
- ADR e governanca: 10
- Logging: 5
- Configuracao: 10

Regra de pontuacao:
- Score >= 85 e sem violacao critica: APPROVED.
- Score < 85 ou qualquer violacao critica: BLOCKED.

Exemplo de saida:
Architecture Score: 97/100
Architectural Risk: muito baixo
Release Ready: YES
Status: APPROVED

## Saidas obrigatorias
1. Relatorio em docs/architecture/decisions/architecture-inventory-report.md.
2. Diagrama em docs/architecture/dependency-graph/dependency_graph.svg.
3. Sumario de cobertura por camada em docs/architecture/decisions/coverage-by-layer.md.
4. Lista de ADR pendente em docs/architecture/decisions/adr-pending.md.
5. Score detalhado em docs/architecture/decisions/architecture-score.md.
6. Registro de divida tecnica nao bloqueante em docs/architecture/technical-debt.md.

## Formato minimo de relatorio
Usar tabela de status com campos:
- Data
- Versao
- Sprint atual
- Estrutura
- Duplicacoes
- Imports circulares
- Models duplicados
- SQLAlchemy
- Coverage
- ADR pendentes
- Architecture Score
- Architectural Risk
- Release Ready
- Status final (APPROVED ou BLOCKED)

Exemplo de linha:
Architecture Inventory | 2026-07-01 | v0.0.1-refactor | Sprint X | Estrutura OK | Duplicacoes 0 | Circulares 0 | Models 0 | SQLAlchemy OK | Core 98% / UI 73% | ADR pendente 0 | Score 97/100 | Risk muito baixo | Release Ready YES | APPROVED

## Technical Debt List
Quando encontrar problemas nao bloqueantes:
1. Registrar em docs/architecture/technical-debt.md.
2. Incluir ID unico (TD-XXX), impacto, prioridade e status.
3. Vincular ao modulo afetado e ao plano de mitigacao.

## Integracao com Sprint 0
Quando BLOCKED, encaminhar para skill de consolidacao arquitetural (Sprint 0) antes de qualquer implementacao funcional.

## Governanca de agentes (recomendado)
Separar responsabilidades em agentes dedicados:
- Architecture Agent: inventario, dependencia, ADR e gate.
- Implementation Agent: funcionalidades aprovadas.
- Refactoring Agent: consolidacao e reducao de divida tecnica.
- Test Agent: estrategia de testes e cobertura.
- Documentation Agent: ADR, diagramas e docs tecnicas.
- Release Agent: versionamento, empacotamento e distribuicao.
