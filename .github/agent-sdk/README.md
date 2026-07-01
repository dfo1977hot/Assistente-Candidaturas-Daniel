# Agent SDK

Este SDK padroniza criacao, validacao e evolucao de agentes do ACD.

## Componentes
- schemas/: contratos de mission, handoff, report e capability.
- templates/: moldes oficiais de agente, handoff e report.
- validators/: validadores de contrato, handoff e exigencia de ADR.
- examples/: contratos de referencia por tipo de agente.
- capability-registry.yaml: registro legivel por maquina.

## Fluxo recomendado
1. Criar contrato a partir de templates/AGENT_TEMPLATE.md.
2. Registrar capacidade no capability-registry.yaml.
3. Validar contrato com validators/validate_agent.py.
4. Validar handoff com validators/validate_handoff.py.
5. Executar validators/validate_adr_requirement.py em mudancas estruturais.
