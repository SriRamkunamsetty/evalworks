# Architecture

EvalWorks is a modular monolith. It is small enough for a new contributor to understand while keeping evaluation logic separated from HTTP, persistence, and model-provider concerns.

```mermaid
flowchart LR
    Reviewer[Reviewer browser] -->|Session cookie + CSRF| API[FastAPI v1]
    API --> Modules[Ten evaluation modules]
    API --> Tenant[Workspace scoped access]
    Tenant --> Store[(SQLAlchemy database)]
    API --> Provider[Configured OpenAI-compatible provider]
    Modules --> Redactor[Keyed input fingerprint + result redaction]
    Redactor --> Store
    CI[GitHub Actions] --> Quality[Ruff + pytest + migration checks]
    CI --> Image[Container build]
    Tag[Version tag] --> Publish[GHCR container publish]
```

## Request lifecycle

1. Request-size limits and basic in-process rate limiting run before the API route.
2. Production routes load an active user from a signed session, then enforce role and workspace scope. Local development can use the development API key.
3. Pydantic validates the request shape; each evaluator applies its own domain limits.
4. Deterministic evaluators prepare structured signals and always mark subjective work for human review.
5. The API returns the working result to the reviewer. Persistence records a keyed fingerprint and recursively redacts prompt, answer, claim, and evidence fields.
6. Reviewer feedback attaches to a run. A run and its feedback can be deleted together.

The optional model adapter only uses the configured server-side endpoint. The probe planner returns drafts and requires human review; it does not execute prompts against targets. The chat endpoint does not persist chat content.

## Trust boundaries

- **Browser to API:** HttpOnly, SameSite session cookie; state-changing requests also require a matching CSRF token. Production requires TLS-secure cookies.
- **Workspace access:** every run and feedback query includes the authenticated workspace ID. Admin user provisioning creates accounts only inside the current workspace.
- **API to model provider:** requests contain conversation text. Only use a provider whose data-handling terms fit your use case.
- **API to database:** evaluation source text is not persisted by the run path; reviewer-entered rationales may still contain sensitive content.
- **Generated test prompts:** model output is untrusted. Review before execution or publishing to a shared test set.

## Current scaling profile

One API process, synchronous model calls, SQLAlchemy pooling, and local rate limiting are appropriate for local development or a private single-instance demo. The current release includes user sessions and tenant isolation, but not durable background jobs, shared rate limiting, SSO/MFA, account recovery, or full retention/consent workflows. A multi-replica deployment needs a distributed rate limiter and managed database; asynchronous workloads need a durable queue with retries, idempotency, and explicit data-retention rules.
