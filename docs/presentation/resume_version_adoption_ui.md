# Resume Version Adoption UI

The review panel distinguishes the version currently visualized from the source
adopted for the selected application. It renders “Currículo usado nesta
candidatura” as either `Original` or the matching persisted version label.

Only explicit clicks can adopt the visualized version or return to the original
curriculum. Changing the selector, generating a version, and performing transient
ATS evaluation do not write adoption state. The controls are synchronous local
writes, guarded against repeated clicks, and do not use threads.

The review contract propagates the source and selected identifier from
`ApplicationContext`; Presentation performs no database lookup. On application
change, the panel renders the new review state and clears the prior context.
