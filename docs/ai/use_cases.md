# Casos de Uso de IA

## Disponíveis

| Caso de uso | Entrada | Serviço orquestrador | Saída |
| --- | --- | --- | --- |
| Gerar currículo | `Curriculum`, `JobProfile`, idioma | `ResumeGenerationService` | Conteúdo, versão e explicação |
| Otimizar currículo | `Curriculum`, `JobProfile`, idioma | `ResumeGenerationService` | Conteúdo, versão e explicação |
| Gerar carta | `Curriculum`, `JobProfile`, idioma | `CoverLetterGenerationService` | Conteúdo, versão e explicação |

As entradas públicas estão em `acd.application.ai`. Os serviços recebem o
provider, repositório, builder e serviço ATS por injeção de dependência.

## Limites atuais

Análise de vaga, análise ATS, sugestões de melhoria, gap analysis e career
intelligence não recebem novos casos de uso nesta Sprint. Qualquer expansão
deve reutilizar o contrato `AIProvider`, `PromptBuilder` e `PromptRepository`.
