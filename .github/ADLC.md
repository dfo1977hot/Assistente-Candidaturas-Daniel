# ACD Development Lifecycle (ADLC)

Documento normativo relacionado: .github/CONSTITUTION.md
SDK normativo de agentes: .github/agent-sdk/

## Fluxo obrigatorio para toda mudanca
Ideia -> Architecture Inventory -> ADR -> Planejamento da Sprint -> Implementacao -> Refatoracao -> Testes -> Quality Gate -> Release -> Documentacao

## Regra central
Nenhuma sprint pode pular etapas do ADLC.
Nenhuma etapa pode violar a constituicao do projeto.
Nenhum agente pode operar fora do contrato definido em .github/agents/base/AGENT_SPEC.md.

## Politica de execucao
1. Architecture Inventory e obrigatorio antes de qualquer sprint.
2. Sem APPROVED no gate de arquitetura, a sprint fica BLOCKED.
3. Mudanca estrutural exige ADR antes de implementacao.
4. Merge e release dependem dos quality gates aprovados.
5. Mudanca de governanca exige RFC aprovada (Governance Freeze v1.0).

## Bootstrap recomendado antes da Sprint 0
1. Architecture Inventory
2. Quality Gate
3. Architecture Score
4. Iniciar Sprint 0 em lotes pequenos

## Pipeline obrigatorio entre agentes
Fluxo sequencial de aprovacao:
1. Architecture Agent
2. Implementation Agent
3. Refactoring Agent
4. Testing Agent
5. Documentation Agent
6. Release Agent

Cada agente so pode iniciar apos aprovacao explicita da etapa anterior.
Se qualquer etapa reprovar, o fluxo retorna para correcao e nova validacao.
Toda comunicacao entre agentes deve ocorrer por handoff padronizado, sem troca direta informal.
Formato de handoff deve seguir .github/agents/base/HANDOFF_TEMPLATE.md.

## Responsaveis por etapa
- Architecture Agent: inventario, dependencia e aprovacao arquitetural.
- Implementation Agent: implementacao de escopo aprovado.
- Refactoring Agent: melhoria estrutural sem feature nova.
- Testing Agent: qualidade por testes e cobertura.
- Documentation Agent: sincronizacao de ADR e docs tecnicas.
- Release Agent: versao, build, migracao e release notes.
