# ADR-014: Monotonic Coverage Baseline

## Status

Accepted

## Contexto

O Full Quality Gate validou 69,74437237695535% de cobertura global, acima do
baseline de 68,15%, mas abaixo do milestone de 70%. A politica anterior so
atualizava o baseline ao atingir um milestone, permitindo que uma regressao
entre esses valores permanecesse aprovada.

## Decisao

O baseline de cobertura passa a ser monotônico. Apos um Full Quality Gate
aprovado, o gate promove automaticamente a cobertura global e de branches que
superarem os valores registrados. O baseline nunca diminui.

Milestones de 70%, 75%, 80% e 85% permanecem metas independentes. Eles nao
limitam nem atrasam a promocao do baseline.

## Consequencias

Cada resultado validado passa a elevar imediatamente a protecao contra
regressoes. Por exemplo, 68,15% -> 69,74% -> 70,18% preserva todos os ganhos,
enquanto um resultado posterior de 69,00% e bloqueado.

O gate continua sem threshold independente para branch coverage. Essa metrica
e promovida quando melhora e permanece observavel na governanca.
