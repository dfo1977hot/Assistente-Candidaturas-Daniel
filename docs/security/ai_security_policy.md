# AI security policy

Only the official Infrastructure adapter may call OpenAI. It receives the API
key through the centralized secret provider, uses the official SDK with TLS
defaults, positive timeout and bounded retries, and returns a strict typed
schema. Authentication, timeout, provider and validation failures become safe
typed results; prompts, responses, credentials and personal content are not
logged or audited.

Only data required for the explicit resume-generation action is sent. External
job/resume content is bounded and enclosed as untrusted data; instructions say
it cannot change policy, request tools, reveal secrets or authorize filesystem,
database, network or command actions. Model output is never SQL, code, command,
path, module or configuration. It is schema-validated before application use.
No real request is made by Sprint I tests.

