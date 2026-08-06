# Technical Debt List

Este arquivo registra dividas tecnicas nao bloqueantes detectadas no Architecture Inventory.

## Politica
- Toda divida deve ter ID unico.
- Toda divida deve conter impacto e prioridade.
- Itens bloqueantes nao entram aqui: devem bloquear sprint no inventario.

## Itens
- TD-001 | Dashboard sem testes de integracao completos | prioridade: media | status: aberto
- TD-002 | Automation Engine com acoplamento acima do alvo | prioridade: media | status: aberto
- TD-003 | UI com widgets monoliticos em alguns fluxos | prioridade: baixa | status: aberto
- TD-004 | Nove basetemps/caches inacessiveis geram Permission denied | impacto: ruido operacional | prioridade: alta | recomendacao: ignorar e remover apenas com autorizacao | Sprint: operacional
- TD-005 | 178 artefatos de Gate na raiz (aprox. 9,96 MB) | impacto: auditoria | prioridade: media | recomendacao: futura migracao SHA-256 para `.local/artifacts` | Sprint: futura
- TD-006 | Banco real e dados pessoais locais coexistem com source | impacto: privacidade | prioridade: alta | recomendacao: futura retirada do tracking sem apagar | Sprint: futura
- TD-007 | `domain/agent` e `domain/agents` sao contextos produtivos distintos com tabelas diferentes | impacto: nomes confundem manutencao | prioridade: baixa | recomendacao: manter e documentar; eventual rename exige compatibilidade | status: classificado
- TD-008 | Wizard e ApplicationFacade experimentais permanecem testados fora do runtime | impacto: superficie experimental | prioridade: media | recomendacao: manter isolados ate decisao de produto | status: classificado
- TD-009 | `scripts/quality_gate.py` vazio e sem consumidor foi removido; Gate oficial permanece `quality_gate.ps1` | impacto: resolvido | prioridade: baixa | status: fechado
- TD-010 | ResourceWarnings SQLite/SQLAlchemy no Full Gate | impacto: ruido/recursos | prioridade: media | Sprint: futura
- TD-011 | Worktree acumulado sem commits consolidados | impacto: revisao/recuperacao | prioridade: alta | recomendacao: plano de versionamento | Sprint: futura
- TD-012 | Schema versionado via `PRAGMA user_version`, mas a trilha de migrations ainda e incremental | impacto: upgrades futuros | prioridade: alta | recomendacao: adotar `DatabaseMigrationRunner` para cada nova revisao e manter backup pre-migracao | Sprint: G
- TD-013 | Backup/restore legado em `application/platform/services` usa copia de arquivo e defaults relativos | impacto: risco se reativado | prioridade: alta | recomendacao: migrar consumidores para `SQLiteDatabaseLifecycle`; manter fora do runtime ate entao | Sprint: futura
- TD-014 | Hooks globais de excecao de Python/Qt nao foram instalados para evitar duplicidade e interferencia no shutdown | impacto: excecoes fora dos limites desktop/task podem depender do stderr padrao | prioridade: baixa | recomendacao: reavaliar apenas com ownership e teardown testaveis | Sprint: futura
- TD-015 | Retencao de logs e diagnosticos depende de rotacao local e exclusao manual dos exports | impacto: acumulacao local limitada mas nao centralmente expirada | prioridade: media | recomendacao: definir expiracao opt-in sem apagar evidencia ativa | Sprint: futura
- TD-016 | Plugins autorizados executam no processo e sem assinatura criptografica | impacto: codigo de plugin possui permissoes do usuario | prioridade: alta | recomendacao: assinatura, capability model e isolamento de processo antes de marketplace | Sprint: futura
- TD-017 | Validacao de URL bloqueia IP literal local, mas nao elimina DNS rebinding | impacto: futuro cliente generico pode atingir rede local apos resolucao | prioridade: media | recomendacao: resolver/revalidar IP por conexao e redirect | Sprint: futura
- TD-018 | Segredos permanecem no ambiente do processo, sem cofre do sistema operacional | impacto: processo comprometido pode le-los | prioridade: alta | recomendacao: avaliar Windows Credential Manager com migracao explicita | Sprint: futura
- TD-019 | ConfigurationProvider JSON legado aceita path explicito do chamador | impacto: consumidor reativado pode ler/escrever configuracao fora de raiz | prioridade: media | recomendacao: exigir AuthorizedPathPolicy no ponto de composicao | Sprint: futura
- TD-020 | Timeout de plugin in-process nao pode ser imposto com seguranca | impacto: plugin autorizado pode bloquear a thread chamadora | prioridade: alta | recomendacao: isolamento em processo antes de timeout/capabilities | Sprint: futura
- TD-021 | Shutdown desktop nao coordena todas as operacoes opcionais por supervisor unico | impacto: tarefa nao cooperativa pode atrasar encerramento | prioridade: media | recomendacao: compor supervisor quando houver multiplas tarefas produtivas simultaneas | Sprint: futura
- TD-022 | Checkpoints do pipeline permanecem apenas em memoria | impacto: reinicio nao retoma pipeline | prioridade: media | recomendacao: definir schema versionado e privacidade antes de persistir | Sprint: futura
- TD-023 | Lista produtiva de candidaturas ainda retorna o conjunto completo | impacto: crescimento extremo pode aumentar memoria e latencia | prioridade: media | recomendacao: definir UX de paginacao e volume representativo antes de limitar | Sprint: futura
- TD-024 | Baseline temporal de performance nao possui runner CI controlado | impacto: comparacao fina sofreria ruido de maquina/cache | prioridade: media | recomendacao: coletar distribuicao multi-run e criar promotor automatico antes de versionar baseline | Sprint: futura
- TD-025 | Medicao de memoria Python nao cobre integralmente alocacoes nativas Qt/SQLite | impacto: vazamentos nativos pequenos podem escapar ao tracemalloc | prioridade: baixa | recomendacao: usar ferramenta nativa apenas sobre caso sintetico reproduzivel | Sprint: futura
- TD-026 | 85 modulos em `acd/domain` importam SQLAlchemy e hospedam mapeamentos ORM | evidencia: `quality/domain-sqlalchemy-baseline.json` e ADR-028 | impacto: dominio hibrido acoplado ao framework | prioridade: alta | recomendacao: migracao incremental por contexto com mappers e modelos de persistencia, sem alterar as 92 tabelas | Sprint: persistence-boundary
- TD-027 | Basetemps pytest e diretorios `acd-*` gerados permanecem inacessiveis e geram Permission denied | evidencia: inventario Sprint E em 2026-08-04 | impacto: ruido operacional e inventario incompleto | prioridade: alta | recomendacao: manter ignore especifico, nao elevar privilegios, e tratar limpeza somente por acao administrativa aprovada | Sprint: operacional
- TD-028 | Evidencias historicas de Quality Gate permanecem na raiz ate migracao com hashes | evidencia: 205 arquivos `.sprint-*`, 1,372,601 bytes | impacto: worktree ruidoso e risco de versionamento acidental | prioridade: media | recomendacao: migrar para `.local/artifacts` somente com hash antes/depois e manifest atualizado | Sprint: repository-hygiene
- TD-029 | Componentes legacy e experimentais possuem consumidores ainda ativos ou exigem contrato de retirada | evidencia: inventario e politica de aposentadoria da Sprint F | impacto: risco de quebra por remocao prematura | prioridade: alta | recomendacao: manter Kernel/container isolados, contextos `agent`/`agents` distintos e wizard/facade experimentais ate evidencia de retirada | Sprint: futura | status: classificado
- TD-030 | `DatabaseMigrationRunner` existe como contrato controlado, mas ainda depende de adocao produtiva futura | impacto: upgrades futuros | prioridade: media | recomendacao: ligar o runner ao fluxo de release quando a primeira migration real for aprovada | Sprint: G
- TD-031 | Contato nao existe como entidade, pagina ou servico de primeira classe no runtime produtivo | impacto: o texto de Sprint H cita contato como esperado, mas o produto atual nao expõe esse fluxo | prioridade: media | recomendacao: classificar como ausente no MVP ou criar backlog dedicado antes de prometer suporte | Sprint: H
