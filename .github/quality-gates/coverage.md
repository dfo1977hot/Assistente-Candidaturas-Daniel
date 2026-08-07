# Coverage Gate

## Politica

A meta arquitetural global e `>= 85%`, preservada no `pyproject.toml`.
O projeto possui divida historica aprovada; o Full Quality Gate verifica que a
cobertura global nao fique abaixo do baseline versionado em
`quality/coverage-baseline.json`.

Codigo novo ou modificado deve buscar `>= 85%` quando a cobertura de diff for
tecnicamente mensuravel. Coverage e um indicador de risco: nao sao aceitos
omits artificiais, pragmas indiscriminados ou testes sem assertions relevantes.

## Gates

- Fast: Ruff, compileall e testes direcionados.
- Full: suite completa, branch coverage e verificacao de nao regressao.

Consulte `docs/architecture/coverage_governance.md` para milestones, atualizacao
do baseline e politicas de excecao.
