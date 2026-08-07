# Candidate Decision Presentation

`CandidateDecisionViewModel` is the Presentation boundary for Candidate
Decision Support. It receives `CandidateDecisionUseCase`, calls `load` with an
application identifier, and exposes immutable `CandidateDecisionViewState`.

The state preserves score, confidence, reasons, strengths, risks, gaps, and
recommendations. Deterministic headlines and summaries only render the decision
already produced by Application. `INSUFFICIENT_DATA` is a valid UI state, not a
technical error.

The ViewModel does not access CandidateDecisionService, composition services,
query ports, repositories, or Infrastructure. Future Qt screens may consume
this contract without learning the Application internals.
