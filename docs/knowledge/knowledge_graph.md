# Knowledge Graph e Semantic Memory

## Objetivo

Fornecer uma camada de conhecimento reutilizável que represente entidades e
relações de negócio do ACD. A camada permite consultas determinísticas e a
montagem de contexto para consumidores futuros, inclusive provedores de IA,
sem integrar IA generativa nesta fase.

## Escopo

O Knowledge Graph modela nós, relações, versões e consultas em memória. Ele
não substitui os repositórios transacionais existentes, não introduz banco de
grafos e não altera fluxos de candidatura, carreira, aprendizado ou workflow.

## Componentes

```text
Domain
  KnowledgeNode, KnowledgeRelationship, integridade do grafo
        ↑
Application
  SemanticQueryService, SemanticContextBuilder
        ↑
Port
  KnowledgeRepository
        ↑
Infrastructure
  InMemoryKnowledgeRepository
```

- **KnowledgeNode:** identidade, tipo, atributos e versão de uma entidade de
  conhecimento.
- **KnowledgeRelationship:** ligação tipada e direcionada entre dois nós.
- **KnowledgeRepository:** contrato para escrita, consulta, atualização,
  remoção e versionamento.
- **SemanticQueryService:** consultas determinísticas por relações e tipos.
- **SemanticContextBuilder:** consolida entidades, relações, histórico e
  aprendizados relacionados a uma vaga, currículo e objetivo.

## Fluxo de atualização

1. Um caso de uso obtém uma entidade de domínio já existente.
2. Um adaptador a traduz para um `KnowledgeNode` ou `KnowledgeRelationship`.
3. O repositório valida a integridade antes de gravar a versão em memória.
4. Consultas e o Context Builder leem o grafo sem alterar os dados de origem.

O grafo é uma projeção de conhecimento. A fonte de verdade de cada entidade
continua sendo seu agregado e repositório transacional atuais.

## Estratégia de evolução

O primeiro adaptador será em memória e compatível com o contrato de
repositório. Uma Sprint futura poderá criar adaptadores SQLite ou de banco de
grafos, preservando os casos de uso e as consultas. A integração com IA será
somente consumidora do contexto consolidado; nenhum provedor de IA fará parte
do grafo.

## Regras arquiteturais

- Domain não depende de Application, Infrastructure ou Presentation.
- Application depende apenas do contrato de repositório.
- Infrastructure implementa armazenamento e adaptadores de projeção.
- Presentation acessa contexto semântico somente por casos de uso de
  Application.
