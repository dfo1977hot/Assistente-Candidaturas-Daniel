# Candidate Decision Support

`CandidateDecisionService` produz uma recomendacao deterministica para uma
candidatura existente. O consumidor fornece somente o identificador da
candidatura; o servico obtem o `InterviewContext` pelo
`InterviewContextService` ja registrado na Composition Layer.

## Evidencias utilizadas

- curriculo e competencias da vaga para confirmar a completude minima;
- resultado ATS previamente persistido como score normalizado de 0 a 100;
- gaps ATS previamente persistidos;
- recomendacoes ATS previamente persistidas.

O servico nao executa ATS, Gap Analysis, IA ou persistencia. Dados ausentes
produzem `INSUFFICIENT_DATA` ou reduzem a confidence; nunca sao interpretados
como evidencia negativa sobre o candidato.

## Politica inicial

- `STRONG_APPLY`: ATS >= 80 e no maximo um gap persistido;
- `APPLY`: ATS >= 65 e no maximo tres gaps persistidos;
- `LOW_PRIORITY`: ATS < 50 ou seis ou mais gaps persistidos;
- `REVIEW`: demais casos, inclusive gaps nao persistidos;
- `INSUFFICIENT_DATA`: candidatura, curriculo, ATS ou competencias da vaga
  indisponiveis.

O resultado e imutavel e serializavel. `reasons`, `strengths`, `risks`,
`gaps` e `recommendations` apresentam somente evidencias persistidas ou a
consequencia explicita da ausencia delas.
