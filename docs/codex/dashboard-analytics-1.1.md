# Codex Task — Dashboard & Analytics 1.1: Drill-down e exportação

## Objetivo
Evoluir o Dashboard & Analytics 1.0 já validado, adicionando drill-down operacional e exportação de dados analíticos sem duplicar regras de negócio nem bloquear a UI.

## Antes de alterar código
1. Leia `AGENTS.md`.
2. Leia `.github/CONSTITUTION.md`.
3. Leia `docs/codex/dashboard-analytics-1.0.md`.
4. Inspecione o worktree atual e preserve integralmente a implementação já aprovada.
5. Use o worktree local validado como fonte de verdade.

## Regras arquiteturais
- Presentation não importa Infrastructure.
- Presentation não instancia Service/Repository.
- `AnalyticsService` continua sendo a fonte das métricas e projeções.
- Exportação deve consumir DTOs/resultados do AnalyticsService.
- Não colocar SQL na Presentation.
- Não executar exportações pesadas na thread principal.
- Reutilizar `LongRunningTaskExecutor`.
- Não introduzir dados fake.
- Gupy continua manual-only.
- Salário esperado continua igual à Remuneração ideal.
- Data resposta permanece vazia sem resposta real.

## Escopo funcional

### Drill-down dos KPIs
Permitir abrir os registros que compõem os principais KPIs:
- Vagas cadastradas;
- Vagas abertas/ativas;
- Candidaturas totais;
- Candidaturas em andamento;
- Entrevistas;
- Ofertas;
- Rejeições/encerradas;
- Workflows aguardando usuário;
- Falhas recentes de Workflow;
- Cartas geradas.

Ao clicar/duplo clicar em um KPI:
- abrir lista filtrada;
- preservar filtros atuais;
- permitir navegação para o registro de origem quando a navegação atual suportar isso.
Não acoplar Dashboard diretamente às páginas concretas.

### Drill-down do funil
Ao clicar em um estágio:
- mostrar registros daquele estágio;
- apresentar empresa, cargo, status, data relevante e origem/plataforma quando disponíveis;
- permitir abrir candidatura/vaga relacionada por navegação indireta.
Usar apenas status reais do domínio.

### Tabela analítica
Adicionar visão resumida com:
- Empresa
- Cargo
- Plataforma/origem
- Status da candidatura
- Data de criação
- Última atualização
- Remuneração oferecida
- Remuneração ideal
- Fit score
- Currículo associado
- Carta associada
- Workflow/status operacional

Não carregar textos grandes.

### Exportação CSV
- UTF-8 com BOM para Excel no Windows;
- apenas dados filtrados;
- nome seguro;
- sem alterar banco;
- erro de I/O amigável.

### Exportação XLSX
- reutilizar biblioteca existente;
- adicionar dependência apenas se realmente necessária;
- cabeçalho legível;
- autofiltro;
- primeira linha congelada;
- larguras razoáveis;
- datas como datas;
- valores monetários como números;
- sem secrets.

### Exportação PDF
Implementar apenas se já houver infraestrutura/biblioteca aprovada no projeto. Caso contrário, registrar pendência e não adicionar dependência pesada.

### Progresso e cancelamento
Exportações potencialmente demoradas:
- fora da thread principal;
- progresso real;
- cancelamento cooperativo;
- sem arquivo parcial válido;
- controles restaurados em sucesso/falha/cancelamento.

### AnalyticsExportService
Criar Service dedicado se necessário. Deve receber DTO/projeção filtrada e exportar sem consultar Repositories diretamente quando o AnalyticsService já fornecer os dados.

### Filtros
Preservar período, empresa, cargo, status e plataforma ao entrar/sair de drill-down.
Adicionar `Limpar filtros`.

### UX
Adicionar:
- Exportar CSV
- Exportar Excel
- Exportar PDF somente se suportado
- Voltar
- contador de registros filtrados
Manter layout compacto.

## Testes obrigatórios
1. drill-down de KPI usa mesmos filtros;
2. drill-down do funil usa status reais;
3. retorno preserva filtros;
4. tabela não carrega textos grandes;
5. CSV contém só registros filtrados;
6. CSV UTF-8 compatível;
7. XLSX com cabeçalhos corretos;
8. XLSX preserva tipos;
9. exportação não altera banco;
10. erro de I/O não derruba app;
11. cancelamento não deixa arquivo parcial válido;
12. exportação não bloqueia UI;
13. progresso restaura controles;
14. estado vazio amigável;
15. navegação sem acoplamento indevido;
16. Presentation não importa Infrastructure;
17. Presentation não instancia Service/Repository;
18. Composition Root injeta serviço de exportação;
19. nenhuma regressão Dashboard 1.0;
20. nenhuma regressão Workflows 2.0;
21. nenhuma regressão Cartas 1.1;
22. regras salariais preservadas;
23. Gupy manual-only.

## Gates
Execute testes direcionados e depois:

`C:\Projetos\.venv\Scripts\python.exe -m ruff check .`

`C:\Projetos\.venv\Scripts\python.exe -m pytest -q`

Não faça commit enquanto qualquer gate estiver vermelho.

## Entrega
1. arquivos alterados;
2. arquitetura;
3. drill-downs;
4. exportações;
5. progresso/cancelamento;
6. testes direcionados;
7. Ruff global;
8. pytest global;
9. pendências;
10. `APPROVED` ou `BLOCKED`.

## Não fazer
- duplicar consultas do AnalyticsService;
- SQL em Presentation;
- bloquear UI;
- dados fake;
- dependência pesada de PDF sem necessidade;
- automatizar Gupy;
- alterar regra salarial;
- enfraquecer arquitetura;
- commitar antes dos gates verdes.
