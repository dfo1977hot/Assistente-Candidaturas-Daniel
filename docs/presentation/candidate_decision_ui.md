# Candidate Decision UI

`ApplicationPage` is the visual point for a decision because it already owns
the selected `application_id`. The desktop composition root constructs
`CandidateDecisionViewModel`, passes it to `MainWindow`, and `MainWindow`
forwards it to `ApplicationPage` through constructor injection.

`ApplicationPage` calls `load(application_id)` only after the existing table
selection flow provides a valid identifier. It supplies the resulting immutable
`CandidateDecisionViewState` to `CandidateDecisionPanel`, a passive widget that
renders decision, score, confidence, headline, summary, reasons, strengths,
risks, gaps, and recommendations when present.

The panel displays a neutral empty state when no application is selected.
`INSUFFICIENT_DATA` is rendered as the functional ViewState supplied by the
ViewModel, not as a technical error. Future unknown decisions are also rendered
as neutral textual content.

Neither `ApplicationPage` nor `CandidateDecisionPanel` imports or accesses the
Candidate Decision use case or service, composition services, repositories,
Infrastructure, Query Ports, Query Adapters, or the dependency container.
There is no timer, polling, background refresh, or visual mapping of decision
semantics. A future dashboard can consume the same ViewModel without changing
this boundary.

## UI Validation

The desktop startup path creates the panel without loading a decision before a
valid application is selected. Empty state, valid selections, supported decision
states, `INSUFFICIENT_DATA`, replacement of a previous selection, empty lists,
and unknown states are covered by the Presentation tests. Long values use the
existing page-level vertical scroll area, so the panel remains reachable without
nested scrolling. The panel uses textual labels and does not rely on color.

The current interaction is synchronous and follows the existing selection flow.
Performance and technical errors remain subject to the existing Presentation
behavior; this validation does not introduce retries, workers, or error masking.

Candidate Decision Actions provide explicit navigation to existing gaps,
curriculum, and interview pages; see `candidate_decision_actions.md`.
