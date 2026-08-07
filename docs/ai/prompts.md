# Prompts

## Construção

`PromptBuilder` constrói prompts determinísticos para currículo e carta de
apresentação a partir de `PromptContext`. O contexto contém dados da vaga,
pontuação ATS, competências ausentes, resumo profissional, objetivos e idioma.

## Persistência e versionamento

`PromptRepository` persiste registros de prompt e gerações em SQLite.
`PromptTemplate` e `AIPrompt` mantêm nome de template, versão e conteúdo.
O repositório atual também preserva versões de currículo e carta geradas.

## Convenções

- O builder não executa prompts.
- O provider não altera prompts.
- O repositório não interpreta o conteúdo dos prompts.
- Novas categorias de prompt devem reutilizar `PromptRepository` e manter o
  campo de versão explícito.
