# Codex Task — Dashboard & Analytics 1.0

## Objetivo
Criar o primeiro Dashboard operacional do ACD usando dados reais de Vagas, Candidaturas, Workflows, Cartas e histórico operacional.

## Antes de alterar código
1. Leia `AGENTS.md`.
2. Leia `.github/CONSTITUTION.md`.
3. Leia `docs/codex/workflows-2.0.md`.
4. Inspecione o worktree atual e qualquer Dashboard/KPI existente.
5. Use o worktree local validado como fonte de verdade.

## Regras arquiteturais
- Presentation não importa Infrastructure.
- Presentation não instancia Service/Repository.
- Agregações ficam em Service dedicado.
- Não duplicar regras de negócio.
- Não executar consultas pesadas na thread principal.
- Reutilizar `LongRunningTaskExecutor` quando necessário.
- Não usar dados fake em produção.

## Escopo

### Dashboard geral
Exibir KPIs:
- Vagas cadastradas;
- Vagas abertas/ativas;
- Candidaturas totais;
- Candidaturas em andamento;
- Entrevistas;
- Ofertas;
- Rejeições/encerradas;
- Taxa candidatura → entrevista;
- Taxa entrevista → oferta;
- Workflows ativos;
- Workflows em andamento;
- Workflows aguardando usuário;
- Falhas recentes;
- Próxima execução agendada;
- Cartas geradas;
- Currículos otimizados, somente se houver dado confiável.

### Funil
Usar apenas status reais do domínio. Mostrar quantidade e conversão por estágio.

### Filtros
- 7 dias
- 30 dias
- 90 dias
- Ano atual
- Todo o período
- Personalizado
- Empresa
- Cargo/texto
- Status da candidatura
- Plataforma/origem, quando disponível

### Tendência temporal
Gráficos para:
- Vagas cadastradas;
- Candidaturas criadas;
- Entrevistas;
- Ofertas.

Granularidade diária, semanal ou mensal conforme período.

### Workflows
Exibir:
- execuções hoje;
- em andamento;
- aguardando usuário;
- falhas recentes;
- próxima execução;
- últimos executados.

### Alertas operacionais
Exibir, quando aplicável:
- workflows aguardando usuário;
- workflows falhos;
- candidaturas sem atualização há X dias;
- vagas com candidatura pendente;
- agendamentos vencidos.

Centralizar qualquer limite de dias.

### AnalyticsService
Criar Service dedicado para:
- filtros;
- KPIs;
- funil;
- séries temporais;
- resumo de Workflows;
- alertas;
- DTOs imutáveis/serializáveis.

Não colocar SQL em Presentation.

### Performance
- consultas pesadas fora da thread principal;
- evitar N+1;
- cache curto permitido;
- preferir agregação em Repository/SQL;
- não carregar textos grandes sem necessidade.

### Atualização
Adicionar botão `Atualizar`.
Atualizar por eventos relevantes quando o EventBus atual permitir.

### UX
Cards compactos, gráficos simples, tabela/resumo operacional, padrão visual atual do ACD.

### Estados vazios
Mostrar `Sem dados no período` quando apropriado.
Erros de consulta não devem derrubar a aplicação.

### Fora de escopo
Preparar Service para futura exportação CSV/Excel/PDF, mas não implementar exportação agora.

## Testes obrigatórios
1. KPIs com base vazia;
2. KPIs com dados reais;
3. taxa candidatura → entrevista;
4. taxa entrevista → oferta;
5. funil usa status reais;
6. filtros de período;
7. empresa;
8. status;
9. plataforma/origem quando disponível;
10. tendência temporal curta;
11. tendência longa;
12. resumo de Workflows;
13. próxima execução;
14. aguardando usuário;
15. falhas recentes;
16. alertas;
17. Dashboard não bloqueia UI;
18. botão Atualizar;
19. atualização por evento quando aplicável;
20. estado vazio;
21. erro de consulta;
22. Presentation não importa Infrastructure;
23. Presentation não instancia Service/Repository;
24. Composition Root injeta AnalyticsService;
25. nenhuma regressão Workflows 2.0;
26. nenhuma regressão salarial;
27. Gupy manual-only.

## Gates
Execute testes direcionados e depois:

`C:\Projetos\.venv\Scripts\python.exe -m ruff check .`

`C:\Projetos\.venv\Scripts\python.exe -m pytest -q`

Não faça commit enquanto algum gate estiver vermelho.

## Entrega
1. arquivos alterados;
2. arquitetura;
3. KPIs;
4. funil;
5. filtros;
6. gráficos;
7. alertas;
8. testes direcionados;
9. Ruff global;
10. pytest global;
11. `APPROVED` ou `BLOCKED`.

## Não fazer
- dados fake em produção;
- status inventados;
- SQL na Presentation;
- bloquear UI;
- enfraquecer arquitetura;
- automatizar Gupy;
- alterar regra de remuneração;
- commitar antes dos gates verdes.
