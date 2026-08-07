# Candidate Decision Actions

Candidate Decision Actions orientam o usuário para fluxos já existentes; elas
não aplicam, persistem ou automatizam decisões. O painel renderiza ações
descritas por `CandidateDecisionAction` e emite um sinal somente após clique.

As ações disponíveis reutilizam destinos registrados no `Router`:

- **Revisar gaps** → `career`;
- **Preparar currículo** → `curricula`;
- **Preparar entrevista** → `interviews`.

`ApplicationPage` encaminha o evento explícito ao callback recebido e
`MainWindow` realiza apenas a navegação. Nenhuma ação usa score, estado de
decisão, ATS, Infrastructure ou persistência. As ações “prosseguir com
candidatura” e “revisar candidatura” não foram implementadas porque não há
destino funcional equivalente no fluxo atual.
