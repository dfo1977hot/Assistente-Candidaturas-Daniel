# ADR-006 - AI Core Consolidation

## Status

Aceito

## Data

2026-07-22

## Contexto

O ACD já possuía contrato de provider, mock local, builder de prompts,
repositório SQLite e casos de uso de geração distribuídos nas camadas atuais.

## Problema

A criação de uma nova arquitetura de IA paralela duplicaria contratos e
introduziria caminhos concorrentes de persistência e montagem de prompts.

## Alternativas avaliadas

1. Criar novo AI Core paralelo.
2. Mover todos os componentes existentes entre camadas nesta Sprint.
3. Consolidar os componentes existentes como núcleo canônico.

## Decisão

Adotar a alternativa 3. `AIProvider`, `MockAIProvider`, `PromptBuilder` e
`PromptRepository` permanecem os únicos componentes canônicos de suas
responsabilidades. Não serão adicionados providers externos, chamadas HTTP ou
credenciais.

## Consequências

Extensões futuras devem implementar o contrato existente e ser injetadas nos
serviços de geração. A topologia atual permanece compatível durante esta Sprint.

## Benefícios

- Evita contratos e repositórios duplicados.
- Preserva testes, SQLite e injeção de dependência existentes.
- Mantém uma fronteira de extensão explícita para providers futuros.

## Impactos

Nenhum comportamento de negócio ou API pública é alterado.

## Compatibilidade

As importações, construtores dos serviços, persistência SQLite, mock provider e
casos de uso existentes são preservados.

## Componentes reutilizados

`AIProvider`, `MockAIProvider`, `PromptBuilder`, `PromptContext`,
`PromptRepository`, `PromptTemplate`, `AIPrompt`, `AIGeneration`,
`ResumeGenerationService`, `CoverLetterGenerationService` e os use cases de
`application/ai`.

## Componentes adaptados

Nenhum.

## Componentes candidatos à depreciação

Nenhum.

## Próximos passos

Quando houver autorização para provider real, implementar um adaptador que
satisfaça `AIProvider`, mantendo o mock e a injeção de dependência existentes.
