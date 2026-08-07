# Proposed Repository Structure

| Estado atual | Estado proposto | Motivo | Risco | Compatibilidade | Sprint |
|---|---|---|---|---|---|
| `acd/` | pacote canônico preservado | contrato de packaging | alto se movido | manter imports | futura |
| `tests/` | espelho de áreas produtivas | descoberta de pytest | baixo | manter paths | futura |
| `docs/` tópico/histórico | índices em `docs/` e `docs/repository/` | localização sem movimentação | baixo | links preservados | E |
| `scripts/` | scripts oficiais em `scripts/`; wrappers locais fora dele | comandos estáveis | médio | manter `quality_gate.ps1` | F |
| `constraints/`, `quality/` | configuração e baselines versionáveis | reprodutibilidade/governança | baixo | n/a | E |
| dados, banco e screenshots | estado local ignorado | privacidade e runtime | alto | DatabaseBootstrap recria schema | E |
| raw evidence na raiz | `.local/artifacts/{quality-gates,coverage,logs,diagnostics}` | auditoria sem ruído | médio | mover somente com hashes | futura |
| build/dist/wheel/sdist | artefatos reproduzíveis ignorados | não são fonte | baixo | build oficial | E |
| `domain/agent` e `domain/agents` | consolidação com adaptadores explícitos | reduzir ambiguidade | alto | preservar tabelas/imports | F |
| ORM em `domain/` | modelos de persistência e mappers fora do domínio | ADR-028 target zero | alto | preservar 92 tabelas | persistence-boundary |

Sprint E performs no broad source, test, or documentation moves.
