# Regras de qualidade do currículo estruturado

`StructuredResumeQualityValidator` valida um `StructuredResumeSnapshot` de modo determinístico e somente leitura.

## Regras implementadas

| Código | Categoria | Severidade | Condição e recomendação |
| --- | --- | --- | --- |
| `IDENTITY_NAME_REQUIRED` | identity | error | Nome ausente; informar o nome completo. |
| `CONTACT_EMAIL_INVALID` | contact | warning | E-mail presente sem formato básico; informar usuário e domínio válidos. |
| `SKILL_EMPTY` | skills | warning | Competência vazia; remover ou preencher. |
| `SKILL_DUPLICATE` | duplication | info | Competência duplicada após normalização; manter uma ocorrência. |
| `EXPERIENCE_COMPANY_REQUIRED` | experience | warning | Empresa ausente; informar a organização. |
| `EXPERIENCE_ROLE_REQUIRED` | experience | warning | Cargo ausente; informar a função. |
| `EXPERIENCE_PERIOD_INVALID` | consistency | warning | Data inicial posterior à final; corrigir o período. |
| `EXPERIENCE_DUPLICATE` | duplication | warning | Empresa, cargo e período duplicados; manter uma ocorrência. |
| `EDUCATION_DUPLICATE` | duplication | warning | Formação duplicada; manter uma ocorrência. |
| `CERTIFICATION_DUPLICATE` | duplication | warning | Certificação duplicada; manter uma ocorrência. |
| `LANGUAGE_DUPLICATE` | duplication | warning | Idioma repetido com mesmo nível; manter uma ocorrência. |
| `LANGUAGE_CONFLICTING_PROFICIENCY` | consistency | warning | Idioma repetido com níveis conflitantes; revisar o nível. |
| `CONTENT_PLACEHOLDER_DETECTED` | structure | warning | Placeholder isolado detectado; substituir por conteúdo profissional. |
| `CONTENT_CONTROL_CHARACTER` | exportability | error | Caractere incompatível com XML/DOCX; removê-lo. |
| `CONTENT_TECHNICAL_ARTIFACT` | structure | warning | Artefato técnico exposto; remover depuração, JSON, caminho local ou segredo. |
| `CHRONOLOGY_ORDER_WARNING` | chronology | warning | Experiências fora de ordem decrescente; ordenar da mais recente. |
| `EXPORT_MINIMUM_CONTENT_REQUIRED` | exportability | error | Falta nome ou seção profissional relevante; preencher ambos. |

## Determinismo

O score começa em 100 e subtrai 20 por erro, 5 por alerta e 1 por informação, limitado a 0–100. `is_valid` é verdadeiro somente na ausência de erros. Os issues são ordenados por severidade, categoria, seção, campo e código. A comparação de duplicidade aplica trim, colapso de espaços e `casefold`; o snapshot não é modificado.

## Limitações

As regras não avaliam aderência à vaga, semântica profissional, autenticidade, rede, IA, provider, persistência ou exportação. Datas são comparadas apenas quando estão em ISO `YYYY-MM` ou `YYYY-MM-DD`.
