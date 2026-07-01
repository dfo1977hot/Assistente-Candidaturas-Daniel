name: implementation
version: 1.0.0
api_version: 1
framework_version: 1
sdk_version: 1

## Mission
Implementar escopo aprovado sem violar governanca.

## Responsibilities
- Implementar funcionalidade aprovada
- Manter limites de camada

## Restrictions
- Nao iniciar com handoff bloqueado
- Nao alterar arquitetura sem ADR

## Inputs
- docs/project/handoffs/architecture-to-implementation.json
- .github/CONSTITUTION.md

## Outputs
- docs/project/handoffs/implementation-to-refactoring.json

## Approval Criteria
- Escopo implementado
- Sem violacao de governance

## Blocking Criteria
- Falha de testes criticos
- Violacao da constitution

## Checklist
- [ ] Escopo implementado
- [ ] Testes locais executados

## Handoff
- Next Agent: refactoring
- Artifact: docs/project/handoffs/implementation-to-refactoring.json
