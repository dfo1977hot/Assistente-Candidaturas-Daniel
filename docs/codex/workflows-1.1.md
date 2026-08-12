# Codex Task — Workflows 1.1: Integração com serviços reais

## Objetivo

Evoluir a página Workflows da Sprint 1.0 para que as etapas executem os serviços produtivos já existentes do ACD, sem duplicar regras de negócio e sem reintroduzir automação Gupy.

Antes de alterar código:

1. Leia `AGENTS.md`.
2. Leia `.github/CONSTITUTION.md`.
3. Inspecione a implementação atual de Workflows, Composition Root e os Services disponíveis.
4. Considere o estado atual do worktree como fonte de verdade, não a branch remota desatualizada.

## Regra arquitetural principal

Workflows é um ORQUESTRADOR.

Ele não deve reimplementar:
- pesquisa salarial;
- detecção de URL de candidatura;
- enriquecimento de empresa;
- análise de aderência;
- geração/seleção de currículo;
- geração de carta;
- criação/atualização de candidatura.

Cada etapa deve chamar o Service/Boundary já existente responsável pela operação.

Presentation não pode importar Infrastructure nem criar Services/Repositories.

Toda implementação concreta deve ser injetada pelo Composition Root.

## Escopo funcional da Sprint 1.1

### 1. Contexto de execução

Antes de `Executar agora`, o workflow deve ter um contexto de execução explícito.

Adicionar na página Workflows, de forma compacta:

- Vaga alvo;
- Candidatura alvo, quando aplicável;
- Currículo alvo, quando aplicável.

Regras:
- O usuário deve conseguir selecionar uma Vaga.
- Ao selecionar uma vaga, preencher/filtrar candidatura relacionada quando existir.
- Currículo pode ser preenchido automaticamente pelo fluxo ou selecionado manualmente.
- Não executar etapas dependentes de vaga sem `job_id`.
- Exibir mensagem amigável se faltar contexto obrigatório.

Persistir no `WorkflowExecution.context` somente IDs e dados serializáveis necessários.

### 2. Registry de handlers

Criar/ajustar uma camada de handlers/adapters de Workflow, preferencialmente fora da Presentation.

Exemplo conceitual:

`WorkflowStepRegistry`
- `verify_job`
- `detect_application_url`
- `enrich_company`
- `research_salary`
- `analyze_fit`
- `select_resume`
- `generate_resume`
- `generate_cover_letter`
- `register_application`
- `review_application`
- `check_follow_up`
- `classify_closed_job`

O `WorkflowService` deve resolver o handler pelo `command` da etapa.

Não usar grandes blocos `if/elif` com lógica de negócio dentro de `WorkflowService`.

### 3. Etapas produtivas prioritárias

Conectar nesta Sprint, no mínimo, as etapas abaixo aos Services reais:

#### `verify_job`
- carregar a vaga;
- validar existência;
- se houver mecanismo atual e seguro para verificar disponibilidade, reutilizá-lo;
- nunca classificar como encerrada apenas porque a URL de candidatura não foi resolvida;
- retornar resultado estruturado.

#### `detect_application_url`
- reutilizar exatamente o resolver atual de LinkedIn;
- respeitar Configurações para execução em segundo plano;
- salvar URL encontrada na Vaga;
- preservar Easy Apply com tracking relevante;
- não abrir automaticamente a candidatura externa;
- Gupy continua manual-only.

#### `enrich_company`
- usar o mesmo serviço de `Buscar dados` da página Empresas;
- usar chaves salvas em Configurações;
- persistir dados obtidos;
- permanecer determinístico em testes sem chave.

#### `research_salary`
- usar o mesmo SalaryResearchService da página Vagas;
- `salary_min` continua Remuneração oferecida;
- `salary_max` continua Remuneração ideal;
- pesquisa de mercado NÃO pode sobrescrever remuneração oferecida;
- persistir Remuneração ideal.

#### `analyze_fit`
- usar o serviço real de aderência de currículo;
- usar a descrição/notas da vaga segundo a regra atual do ACD;
- registrar score e metadados existentes;
- não inventar novo algoritmo se já houver serviço disponível.

#### `select_resume`
- reutilizar a lógica atual de seleção do currículo mais aderente;
- atualizar `context.curriculum_id`.

#### `generate_resume`
- reutilizar o fluxo atual de currículo otimizado/versionado;
- nunca sobrescrever versão anterior;
- atualizar `context.curriculum_id` para a versão gerada quando aplicável.

#### `generate_cover_letter`
- usar `CoverLetterService`;
- vincular vaga, currículo e candidatura quando disponíveis;
- gerar nova versão, nunca sobrescrever versão anterior;
- atualizar `context.cover_letter_id`/versão;
- a barra de progresso específica da página Cartas continua fora do escopo desta Sprint; o progresso do Workflow deve funcionar normalmente.

#### `register_application`
- criar candidatura se não existir;
- atualizar candidatura relacionada quando já existir;
- evitar duplicatas;
- preservar:
  - Salário esperado = Remuneração ideal (`salary_max`);
  - Salário oferecido = remuneração anunciada (`salary_min`) ou A combinar;
  - Data resposta em branco quando não houver resposta;
- atualizar `context.application_id`.

### 4. Ação manual final

`manual_submit_application` deve continuar retornando:

`Aguardando usuário`

Não automatizar submissão.

Para Gupy:
- abrir somente `/candidates/signin` quando a ação manual apropriada for disparada pelo usuário;
- não automatizar passwordless;
- não preencher perguntas;
- não submeter candidatura.

### 5. Resultado estruturado por etapa

Padronizar resultado de handler, por exemplo:

```python
{
    "status": "Concluída",
    "message": "...",
    "context_updates": {...},
}
```

Statuses aceitos:
- `Concluída`
- `Ignorada`
- `Falhou`
- `Aguardando usuário`

O WorkflowService deve incorporar `context_updates` ao contexto da execução e persistir o contexto atualizado após cada etapa.

### 6. Idempotência e reexecução

`Reexecutar etapa que falhou` não deve criar duplicatas.

Regras mínimas:
- `register_application`: localizar antes de criar;
- `generate_cover_letter`: somente criar nova versão quando a etapa efetivamente for executada novamente por decisão explícita;
- enriquecimento/salário: atualizar o mesmo registro;
- detecção de link: atualizar a vaga existente.

### 7. Progresso e histórico

Manter o comportamento da Sprint 1.0:
- barra de progresso;
- etapa atual;
- status;
- cancelamento cooperativo;
- histórico;
- logs;
- reexecução de falha.

Melhorar o log para registrar:
- command;
- entidade alvo (`job_id`, `application_id`, `curriculum_id`) quando relevante;
- resultado resumido;
- duração da etapa.

Não registrar:
- chaves de API;
- tokens;
- senhas;
- conteúdo sensível desnecessário.

### 8. UX

Na tabela/listagem de Workflows, preservar o mesmo registro após:
- Salvar;
- Executar;
- abrir/fechar Histórico.

Durante execução:
- desabilitar ações conflitantes;
- manter `Cancelar` disponível;
- restaurar os controles ao terminar/falhar/cancelar.

Mensagens ao usuário devem ser em português e amigáveis.

## Testes obrigatórios

Criar/atualizar testes para:

1. Registry resolve handlers corretos.
2. Workflow persiste `context_updates`.
3. Falta de `job_id` bloqueia etapa dependente de vaga.
4. Salary handler altera apenas `salary_max`.
5. Application handler usa `salary_max` como esperado e `salary_min` como oferecido.
6. Data resposta permanece vazia.
7. Register application é idempotente.
8. Cover letter cria versão nova sem sobrescrever.
9. Gupy permanece manual-only.
10. Presentation não importa Infrastructure.
11. Presentation não instancia Service/Repository.
12. Composition Root injeta handlers/dependências.
13. Falha de uma etapa interrompe fluxo e pode ser reexecutada.
14. `Aguardando usuário` interrompe o fluxo sem marcar como erro.
15. Cancelamento mantém histórico consistente.

## Gates

Executar inicialmente testes direcionados.

Depois obrigatoriamente:

`C:\Projetos\.venv\Scripts\python.exe -m ruff check .`

e:

`C:\Projetos\.venv\Scripts\python.exe -m pytest -q`

Não fazer commit se qualquer gate estiver vermelho.

## Entrega esperada do Codex

Ao concluir, responder com:

1. arquivos alterados;
2. arquitetura implementada;
3. handlers realmente conectados;
4. handlers ainda pendentes, se houver;
5. resultado dos testes direcionados;
6. resultado do Ruff global;
7. resultado do pytest global;
8. `APPROVED` ou `BLOCKED` para commit.

## Não fazer

- Não reintroduzir automação Gupy.
- Não duplicar lógica dos Services nas páginas ou no WorkflowService.
- Não mudar Salário esperado para média/max.
- Não sobrescrever Remuneração oferecida com pesquisa de mercado.
- Não preencher Data resposta automaticamente.
- Não enfraquecer testes arquiteturais para permitir acoplamento Presentation -> Infrastructure.
- Não commitar antes dos gates globais verdes.
