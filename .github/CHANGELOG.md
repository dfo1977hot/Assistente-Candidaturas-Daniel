# Changelog

Todas as alterações relevantes deste projeto serão documentadas neste arquivo.

Este projeto segue o padrão **Keep a Changelog** e utiliza **Versionamento Semântico (SemVer)**.

---

## [0.1.0] - 2026-07-04

### Added

- Arquitetura em camadas (Presentation, Services, Repositories e Domain).
- CRUD completo de Empresas.
- CRUD completo de Vagas.
- CRUD completo de Candidaturas.
- Repository Pattern para os principais módulos.
- ApplicationService.
- CompanyService.
- JobService.
- Testes automatizados do ApplicationService.
- Documentação inicial da arquitetura.

### Changed

- Refatoração completa da estrutura do projeto.
- Consolidação dos serviços.
- Organização dos repositórios.

### Fixed

- Recuperação do bootstrap da aplicação.
- Correção da criação do banco de dados.
- Correção do carregamento das empresas nas vagas.
- Correção do carregamento das candidaturas.
- Correção do DetachedInstanceError utilizando eager loading (`joinedload`).

### Security

- Nenhuma alteração.

---

## Próxima versão

### 0.2.0

Planejada para:

- Consolidação arquitetural.
- Planner IA.
- Organização definitiva dos módulos Agent e Agents.