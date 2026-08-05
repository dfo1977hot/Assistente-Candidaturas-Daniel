# Plugin security policy

Plugins are disabled by default. A plugin is eligible only from an explicitly
trusted canonical root and explicit name allowlist, with a bounded UTF-8 JSON
manifest, safe identifier, matching manifest name, simple `module:Class` entry
point, compatible metadata and `PluginInterface` subclass. Invalid discovery or
load fails closed and logs only the sanitized technical name/error type.

Arbitrary user module names, external paths and `sys.path` mutation are not
allowed. A plugin cannot replace the Composition Root, database, logger or
secret provider through the supplied context. Authorized plugins still execute
inside the desktop process with the user's permissions: there is no sandbox,
signature verification or capability enforcement. This is a documented high
residual risk; only reviewed local plugins may be allowlisted.

