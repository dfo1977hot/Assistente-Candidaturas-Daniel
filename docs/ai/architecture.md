# Arquitetura do AI Core

## Decisão

O AI Core é consolidado sobre os componentes existentes. Não há um segundo
contrato de provider, repositório ou mecanismo de construção de prompts.

## Componentes canônicos

| Responsabilidade | Componente | Camada |
| --- | --- | --- |
| Contrato de geração | `AIProvider` | Infrastructure |
| Implementação local para testes | `MockAIProvider` | Infrastructure |
| Construção determinística de prompts | `PromptBuilder` e `PromptContext` | Application |
| Persistência de prompts e gerações | `PromptRepository` | Infrastructure |
| Orquestração de geração | `ResumeGenerationService` e `CoverLetterGenerationService` | Services |
| Entradas de aplicação | funções em `application/ai` | Application |

## Fluxo

```text
Application use case
        |
        v
Generation service -- PromptBuilder --> texto de prompt
        |
        +-- AIProvider --> MockAIProvider
        |
        +-- PromptRepository --> SQLite
```

O provider recebe dados já preparados e retorna texto. Ele não conhece
persistência, UI ou casos de uso. O `MockAIProvider` não realiza chamadas de
rede e é o provider padrão para desenvolvimento e testes.

## Limites

- Não há provider externo nesta arquitetura.
- Não há chamadas HTTP, chaves de API ou seleção de modelo remoto.
- A interface `AIProvider` é a extensão futura para adaptadores externos.
- A persistência SQLite e as APIs públicas existentes são preservadas.
