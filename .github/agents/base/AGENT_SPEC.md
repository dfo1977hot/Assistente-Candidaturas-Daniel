# Agent Spec (ACD)

## Objetivo
Definir o contrato obrigatorio para qualquer agente do ACD.

## Campos obrigatorios
1. Mission
2. Responsibilities
3. Restrictions
4. Inputs
5. Outputs
6. Approval Criteria
7. Blocking Criteria
8. Checklist
9. Handoff

## Regras do contrato
- Todo agente deve obedecer .github/CONSTITUTION.md.
- Todo agente deve obedecer .github/ADLC.md.
- Nao e permitido omitir campos obrigatorios.
- Comunicacao entre agentes deve ocorrer por artefato de handoff padronizado.
- Sem handoff aprovado, o proximo agente nao inicia.

## Formato de status
- approved
- blocked
- needs_changes

## Campos minimos de handoff
- status
- score
- risk
- next_agent
- evidence
- timestamp
