# ACD Constitution

Este documento define as regras maximas de governanca do projeto.
Nenhuma skill, agente, sprint ou mudanca pode violar esta constituicao.

## Artigo 1 - Arquitetura
- A arquitetura oficial do ACD e Clean Architecture.
- Dependencias devem apontar para o centro.
- O dominio nunca depende de infraestrutura, UI ou framework externo de interface.

## Artigo 2 - Banco de dados
- Existe apenas uma DeclarativeBase.
- Existe apenas um engine.
- Existe apenas uma SessionLocal.
- E proibida recriacao destrutiva de banco em fluxo regular.

## Artigo 3 - Estrutura
E proibido criar estruturas paralelas ou duplicadas como:
- agent e agents
- repository e repositories
- service e services
- entity e entities

## Artigo 4 - Refatoracao e ADR
- Nenhuma sprint funcional pode modificar arquitetura sem ADR.
- Toda mudanca estrutural deve ser registrada em docs/architecture/adr/.
- ADR deve ser indexado em docs/architecture/adr/ADR-INDEX.md.

## Artigo 5 - Qualidade
Toda alteracao deve:
- passar ruff
- passar black
- passar mypy
- passar testes
- atualizar documentacao quando necessario

## Artigo 6 - Gate obrigatorio
- Architecture Inventory e etapa obrigatoria pre-sprint.
- Se status for BLOCKED, nenhuma sprint pode iniciar.
- Quality Gates devem aprovar antes de merge e release.

## Artigo 7 - Pipeline de agentes
Pipeline obrigatorio de validacao sequencial:
Architecture Agent -> Implementation Agent -> Refactoring Agent -> Testing Agent -> Documentation Agent -> Release Agent

Cada agente so inicia com aprovacao explicita da etapa anterior.

## Artigo 8 - Agent Framework e Handoff
- Todo agente deve seguir o contrato de .github/agents/base/AGENT_SPEC.md.
- Novos agentes devem ser gerados a partir de .github/agents/base/AGENT_TEMPLATE.md.
- Relatorios devem seguir .github/agents/base/REPORT_TEMPLATE.md.
- Handoff entre agentes e obrigatorio e deve seguir .github/agents/base/HANDOFF_TEMPLATE.md.
- Sem handoff aprovado, e proibido iniciar a proxima etapa do pipeline.

## Artigo 9 - Agent SDK
- O Agent SDK oficial esta em .github/agent-sdk/.
- Schemas, templates e validadores do SDK sao a fonte canonica para evolucao de agentes.
- Agente sem certificacao do SDK nao pode entrar no pipeline.

## Artigo 10 - Governance Freeze v1.0
- Baseline de governanca: Governance v1.0 (Milestone M0).
- Nenhuma nova regra de governanca pode ser adicionada sem RFC aprovada.
- Artefatos congelados sob controle de RFC:
	- .github/CONSTITUTION.md
	- .github/ADLC.md
	- .github/agent-sdk/
	- .github/skills/architecture-inventory/
	- .github/quality-gates/
	- docs/project/ENGINEERING_HANDBOOK.md
	- docs/architecture/adr/
	- docs/rfc/
	- .github/agent-sdk/capability-registry.yaml
	- docs/project/DECISION_MATRIX.md
