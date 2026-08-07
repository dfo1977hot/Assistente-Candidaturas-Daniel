# ADR-013 - Coverage Governance and Incremental Quality Gates

## Status

Aceito

## Contexto e problema

O ACD possui meta arquitetural de 85%, mas a cobertura historica medida esta
abaixo dela. Aplicar essa meta como bloqueio absoluto em toda alteracao pequena
impede evolucao incremental sem reduzir o risco do codigo existente.

## Decisao

Manter 85% como meta arquitetural e registrar um baseline versionado. O Fast
Quality Gate executa Ruff, compileall e testes direcionados. O Full Quality Gate
executa a suite completa com branch coverage e bloqueia regressao abaixo do
baseline aprovado.

## Alternativas consideradas

1. Reduzir `fail_under` para o baseline historico.
2. Excluir codigo legado da medicao.
3. Exigir 85% global em toda alteracao.
4. Preservar a meta e introduzir baseline incremental.

Foi escolhida a alternativa 4. As demais mascaram risco ou tornam a evolucao
normal do projeto impraticavel.

## Consequencias

O baseline so pode crescer e a cobertura de codigo novo deve buscar 85% quando
mensuravel. Diff coverage nao recebe dependencia nova nesta Sprint; sua
automacao depende de um diff confiavel fornecido pela CI.
