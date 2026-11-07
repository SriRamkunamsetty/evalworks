# Security policy

## Supported version

Security reports should target the latest version on the default branch.

## Reporting a vulnerability

Do not post secrets, private transcripts, or exploitable details in a public issue. Once this repository is published, use GitHub's private vulnerability reporting feature. Until then, contact the repository owner privately through the hosting provider.

## Scope and current limitations

The current browser UI uses a shared API key and is intended only for a trusted local or private network. Do not expose it to the public internet. Public multi-user operation requires user authentication, role-based access, distributed rate limiting, managed secret storage, and deployment-specific review.
