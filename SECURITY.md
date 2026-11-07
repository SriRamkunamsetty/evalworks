# Security policy

## Supported version

Security reports should target the latest version on the default branch.

## Reporting a vulnerability

Do not post secrets, private transcripts, or exploitable details in a public issue. Once this repository is published, use GitHub's private vulnerability reporting feature. Until then, contact the repository owner privately through the hosting provider.

## Scope and current limitations

The bundled development API key is supported only outside production. Production uses workspace-scoped authenticated sessions with CSRF protection. Public multi-user operation also needs distributed rate limiting, managed secret storage, audit/observability, and deployment-specific review. Configure separate API, session, and data HMAC secrets. See `docs/ARCHITECTURE.md` for scaling limits.
