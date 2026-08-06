# Filesystem security policy

Authorized logical roots are per-user data, logs, backups, diagnostics, exports
and controlled temporary directories. Production defaults must not write to
site-packages, system directories or the repository root. Legacy database
compatibility is the documented exception and is not expanded.

Untrusted relative paths are resolved beneath an explicit canonical root and
must remain there. Absolute, UNC, different-drive and traversal inputs are
rejected. Existing symlink/junction components are resolved and must remain
inside the same root. Creation uses validated parents and exclusive/atomic
operations where supported. Canonical validation reduces but cannot eliminate
TOCTOU against a hostile same-user process. Windows ACLs are inherited; access
denial fails safely. Sprint I does not run `takeown` or `icacls`.

