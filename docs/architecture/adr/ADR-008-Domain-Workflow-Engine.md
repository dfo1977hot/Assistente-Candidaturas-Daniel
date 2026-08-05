# ADR-008 - Domain Workflow Engine

## Status

Aceito

## Data

2026-07-23

## Contexto

O ACD possui fluxos de negócio para candidatura, entrevista, carreira,
currículo e ATS. A execução existente baseada em persistência e comandos não
fornecia um modelo de domínio para descrever, validar e descobrir esses
processos de forma consistente.

## Decisão

Adotar um Domain Workflow Engine composto por:

- `WorkflowDefinition` e `WorkflowStep` para representar processos;
- `WorkflowRegistry` e `WorkflowCatalog` para descoberta;
- `WorkflowValidator` para integridade estrutural;
- `WorkflowExecutor` que delega capacidades a handlers injetados;
- eventos de ciclo de vida baseados no Kernel;
- observabilidade em memória por execução.

## Responsabilidades

O domínio descreve e valida o processo. Handlers injetados orquestram as
capacidades existentes; `CommandDispatcherStepHandler` é o adaptador de
Infrastructure inicial para os comandos legados. A Presentation não acessa o
executor ou Infrastructure diretamente.

## Alternativas avaliadas

1. Expandir diretamente o executor ORM/JSON existente.
2. Criar um novo executor acoplado a comandos de Infrastructure.
3. Criar um núcleo de domínio com handlers injetados.

Foi escolhida a alternativa 3 para preservar as dependências de camada e
evitar duplicação de capacidades de negócio.

## Impactos

O novo engine não substitui o workflow legado nem persiste definições ou
execuções. Integrações são opt-in por handlers, permitindo evolução gradual e
compatível.

## Estratégia futura

Adicionar adaptadores para os demais serviços existentes, publicar os eventos
no barramento do Kernel e adicionar persistência por portas, sem mover regras
do domínio para Infrastructure ou Presentation.
