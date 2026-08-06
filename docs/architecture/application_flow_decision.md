# Application Flow Decision — Sprint B

## Decision

**DESCONTINUAR FORMALMENTE** o wizard de nova candidatura como fluxo
produtivo. `ApplicationPage` permanece a única rota oficial para gestão e
criação de candidaturas: `applications`.

## Context and factual comparison

| Capacidade | ApplicationPage | Wizard novo | Observação |
|---|---|---|---|
| Criar candidatura | Sim | Não | O wizard apenas inicia sessão temporária. |
| Editar e excluir | Sim | Não | Operações disponíveis apenas no fluxo oficial. |
| Vincular empresa e vaga | Sim | Apenas texto | O wizard não produz IDs de empresa/vaga. |
| Currículo e recursos posteriores | Sim | Não | O wizard não alcança esse fluxo. |
| Status inicial e filtros | Sim | Não | O wizard não expõe esses campos. |
| Persistência | `ApplicationService` | Não | `ApplicationSession.application_id` nunca é definido. |
| Validação | Dados e regras do serviço | Campos textuais mínimos | Etapas aceitam dados incompletos de domínio. |
| Cancelamento/retorno | Gestão no mesmo fluxo | Apenas limpar estado | Não há rota, callback ou retorno produtivo. |
| Uso produtivo | Sim, rota `applications` | Não | O root não o compõe nem registra. |
| Testes | UI, arquitetura e serviço | Unitários de estado/UI | Testes do wizard não comprovam persistência. |

`ApplicationFacade` é uma fachada de sessão em memória: coordena
`StartApplicationUseCase` e `ApplicationOrchestrator`, mas não chama serviços
injetados, não cria empresa/vaga/candidatura, não persiste e não usa um port de
Application aprovado. O wizard depende dessa fachada e encerra chamando
`start_application`; portanto, ele não conclui uma candidatura válida.

Há sobreposição na coleta de empresa, vaga e descrição, mas o valor adicional
do wizard não compensa o risco de apresentar dois caminhos de criação com
resultados distintos. Integrá-lo exigiria contrato de persistência, validação
de domínio, navegação de sucesso/cancelamento e atualização da lista — um
redesign fora do escopo da Sprint B.

## Consequences

- O runtime tem uma única verdade: `applications` → `ApplicationPage`.
- `NewApplicationPage`, `application_wizard`, `NewApplicationViewModel` e
  `ApplicationFacade` permanecem experimentais, fora do runtime produtivo e
  disponíveis somente para seus testes isolados.
- Não há rota `applications/new`, entrada na sidebar, composição no
  `DesktopCompositionRoot` ou importação produtiva desses componentes.
- Uma futura evolução deve estender o fluxo oficial ou aprovar um novo
  contrato persistente antes de reavaliar a integração.

## Deferred items

Uma eventual integração do wizard, persistência coordenada por contratos de
Application, autosave e renovação da experiência de criação ficam adiados. Não
fazem parte desta decisão nem desta Sprint.
