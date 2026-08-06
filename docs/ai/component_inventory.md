# Inventário de Componentes do AI Core

| Componente | Camada | Responsabilidade | Dependências | Consumidores | Estado | Classificação |
| --- | --- | --- | --- | --- | --- | --- |
| `AIProvider` | Infrastructure | Contrato de geração textual | `typing.Protocol` | Serviços de geração, testes | Único contrato | Reutilizar |
| `MockAIProvider` | Infrastructure | Resposta simulada local | `AIProvider` | Serviços de geração, testes | Sem rede | Reutilizar |
| `PromptBuilder` | Application | Montagem determinística de prompts | `PromptContext` | Serviços de geração, testes | Dois tipos de prompt | Reutilizar |
| `PromptContext` | Application | Dados para prompt | `dataclasses` | `PromptBuilder`, serviços | DTO local | Reutilizar |
| `PromptRepository` | Infrastructure | Persistência de prompts, gerações e versões | SQLite/SQLAlchemy | Serviços de geração | API pública existente | Reutilizar |
| `PromptTemplate` | Domain model | Template versionado | SQLAlchemy | `PromptRepository` | Persistido | Reutilizar |
| `AIPrompt` | Domain model | Prompt executado | SQLAlchemy | `PromptRepository` | Persistido | Reutilizar |
| `AIGeneration` | Domain model | Geração registrada | SQLAlchemy | `PromptRepository` | Persistido | Reutilizar |
| `ResumeGenerationService` | Services | Orquestra geração de currículo | Provider, repository, builder, ATS | Use cases e testes | Compatível | Reutilizar |
| `CoverLetterGenerationService` | Services | Orquestra geração de carta | Provider, repository, builder, ATS | Use cases e testes | Compatível | Reutilizar |
| Funções em `application/ai` | Application | Entradas de caso de uso | Serviços de geração | Aplicação | Compatíveis | Reutilizar |

## Componentes adaptados

Nenhum. Não há duplicação a eliminar sem mover responsabilidades entre camadas
ou alterar APIs públicas.

## Candidatos à depreciação

Nenhum. Os componentes inventariados possuem consumidores identificados e são
parte da compatibilidade que esta Sprint preserva.
