# Network security policy

The OpenAI SDK is the only productive network client found. External base URLs
must use HTTPS, contain no credentials, and must not be localhost, loopback,
link-local, private or reserved IP literals. Default certificate verification
is never disabled. Calls require a positive timeout and bounded retries; errors
are sanitized and response use is schema/size bounded.

There is no productive generic download flow or web server, so downloads,
redirect handling, HTTP security headers and inbound request controls are not
applicable. Literal-host validation does not prevent DNS rebinding; a future
generic downloader would require DNS/IP revalidation, redirect limits and
streamed response-size enforcement.

