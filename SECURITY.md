# Security policy

## Supported version

Security reports should target the latest version on the default branch.

## Reporting a vulnerability

Do not post secrets, private transcripts, or exploitable details in a public issue. Once this repository is published, use GitHub's private vulnerability reporting feature. Until then, contact the repository owner privately through the hosting provider.

## Scope and current limitations

The bundled development API key is supported only outside production. Production uses workspace-scoped authenticated sessions with CSRF protection, Redis-backed shared request limits, encrypted durable evaluation jobs, and distinct API, session, data HMAC, and data encryption secrets. Public multi-user operation still needs deployment-specific review, SSO/MFA, account recovery, audit/observability, and organization-owned retention/consent policies. See `docs/ARCHITECTURE.md` and `docs/PROJECT_CATALOG.md` for details.
