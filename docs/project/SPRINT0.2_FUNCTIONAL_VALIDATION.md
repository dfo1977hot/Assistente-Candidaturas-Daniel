# ACD - Sprint 0.2

## Projeto
Assistente de Candidaturas do Daniel (ACD)

## Versao
v0.1.1-alpha

## Titulo
Functional Validation & UI Stabilization

## Epic
Platform Stabilization

## Prioridade
Critica

## Estimativa
3 dias

## Dependencias
- Sprint -1 (Governanca)
- Sprint -0.5 (Agent SDK)
- Sprint 0.1A (SQLAlchemy)
- Sprint 0.1B (Database)
- Sprint 0.1C (Bootstrap)

## Objetivo
Validar funcionalmente todas as telas existentes do ACD, eliminando erros de navegacao, renderizacao e inicializacao da interface.

Nao serao implementadas novas funcionalidades nesta sprint.

## Fora do Escopo
- Novos modulos
- IA
- ATS
- Playwright
- Novas tabelas
- Refatoracoes arquiteturais amplas
- Mudancas na governanca

## Escopo de Validacao
1. Sidebar: cada item deve abrir, renderizar, trocar de pagina e nao gerar traceback.
2. Dashboard: KPIs, layout, responsividade basica e widgets sem quebra.
3. Empresas, Vagas, Candidaturas e Entrevistas: abertura, tabela, toolbar, filtros e botoes.
4. Curriculos e Cartas: abertura da pagina sem excecao.
5. Analytics: graficos vazios, renderizacao e layout.
6. Planejamento de Carreira, Agentes e Configuracoes: validacao de abertura e navegacao.

## Criterio de Validacao
Cada tela recebe status PASS ou FAIL.

## Relatorio Obrigatorio
Arquivo: `docs/project/SPRINT0.2_REPORT.md`

Formato:
| Tela | Status | Bugs | Severidade |
|---|---|---|---|
| Dashboard | PASS | 0 | - |
| Empresas | FAIL | 2 | Medio |
| Analytics | PASS | 0 | - |

## Severidade
- Critico: impede iniciar a aplicacao.
- Alto: impede utilizar a tela.
- Medio: funcionalidade parcial.
- Baixo: problema visual.

## Logging
Toda excecao deve ser registrada em `logs/functional_validation.log`.

## Testes
Adicionar testes para:
- abertura da MainWindow;
- troca de paginas;
- criacao das paginas;
- renderizacao dos widgets principais.

Cobertura minima: 85% para a camada `presentation`.

Estrutura esperada:
- `tests/presentation/test_main_window.py`
- `tests/presentation/test_sidebar.py`
- `tests/presentation/test_dashboard.py`
- `tests/presentation/test_pages.py`

## Melhorias Permitidas
Apenas correcoes de `__init__`, sinais e slots, layouts, imports, widgets quebrados e erros de renderizacao.

Qualquer outra alteracao exige ADR.

## Criterios de Aceite
- Todas as telas abrem sem excecao.
- Sidebar navega corretamente.
- Dashboard renderiza.
- Nao existem tracebacks durante a navegacao.
- Relatorio `SPRINT0.2_REPORT.md` gerado.
- Bugs classificados por severidade.

## Commit da Sprint
`test(ui): validate application screens and navigation`

## Definition of Done
- Todas as paginas existentes podem ser abertas.
- Nenhum erro critico na UI.
- Navegacao funcional.
- Relatorio gerado.
- Testes executados.
- Quality Gate aprovado.
