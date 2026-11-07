# EvalWorks

**A human-centered AI evaluation workbench.** EvalWorks brings ten focused chatbot testing applications into one modular platform: conversation review, prompt probing, judge calibration, memory checks, evidence review, Indic language quality, safety triage, accessibility signals, multimodal grounding, and incident-to-regression workflows.

The core evaluators are deliberately transparent and deterministic. They prepare evidence and review structure; they do not claim to automatically determine truth, cultural quality, accessibility, or safety. An optional LLM agent drafts adversarial test prompts, and every draft is marked for human approval.

## Start locally

Requires Python 3.12+. No model credentials are needed for the local demo or test suite.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
Copy-Item .env.example .env
python -m alembic upgrade head
uvicorn evalworks.main:app --app-dir src --reload
```

Open http://localhost:8000. Compose starts the API, a background evaluation worker, and private Redis for shared rate limits. For the local demo, the development API key is `local-dev-key-change-me`; change it in `.env` before using the app outside your own machine. Interactive API docs are at `/docs`.

To create the first authenticated workspace administrator, apply migrations and run:

```powershell
python -m evalworks.cli create-admin --workspace "My review team" --email you@example.com
```

The CLI prompts for a password and stores only an Argon2 hash. Sign in from the workspace UI. New deployments have no default user or public sign-up route. Keep the data-encryption key stable while jobs are queued; rotate it only after draining the queue.

When running the API directly instead of Compose, start a second process with `python -m evalworks.worker` to process durable evaluation jobs. `POST /api/v1/jobs` requires an `Idempotency-Key` header and returns a job ID; read progress at `GET /api/v1/jobs/{job_id}`. Job inputs are encrypted while queued and erased after completion; only a redacted evaluation result is added to run history.

## Run with Docker

Copy `.env.example` to `.env`, change `API_KEY`, then run:

```powershell
docker compose up --build
```

The container runs as a non-root user, drops Linux capabilities, uses a read-only root filesystem, and persists its local database in a named volume. Docker is not required to run the application or tests.

## Projects

| App | Purpose | API slug |
|---|---|---|
| HumanEval Studio | Rubric-led conversation review | `human-eval-studio` |
| ProbeFleet | Challenge prompt management | `probefleet` |
| JudgeBench | Human/LLM score comparison | `judgebench` |
| Conversation Memory Bench | Recall and forgetting checks | `memory-bench` |
| EvidenceCheck | Claim and source review | `evidencecheck` |
| IndicEval | Language and code-switching review | `indiceval` |
| Safety Scenario Lab | Safety and injection triage | `safety-lab` |
| Accessibility Reviewer | Readability measurements and human checklist | `accessibility-reviewer` |
| Multimodal Grounding QA | Human comparison against media observations | `multimodal-qa` |
| EvalSRE | Incident-to-regression-case workflow | `evalsre` |

See [the architecture](docs/ARCHITECTURE.md) and [project catalog](docs/PROJECT_CATALOG.md) for trust boundaries, current scope, and the recommended build sequence.

All API requests are versioned under `/api/v1`. Development can use `X-API-Key`; production uses authenticated user sessions. Synchronous evaluation inputs are not stored; queued inputs are encrypted at rest and erased on completion. Run history stores a keyed HMAC fingerprint, redacted result summary, allowlisted reproducibility metadata, and reviewer feedback. Runs and feedback are scoped to a workspace. Roles are `admin`, `reviewer`, and read-only `viewer`; only admins delete runs. Browser sessions use HttpOnly cookies and CSRF protection.

## Optional LLM agent

Set `LLM_BASE_URL`, `LLM_API_KEY`, and `LLM_MODEL` to an OpenAI-compatible chat-completions endpoint. Then call `POST /api/v1/agents/probe-plan` for drafts. Authorized reviewers can run up to five approved cases per request with `POST /api/v1/projects/probefleet/execute`; the server uses only the configured provider, never a caller-supplied target URL, and persists redacted run results for human review.

## Test and quality checks

```powershell
python -m ruff check .
python -m pytest -q
```

GitHub Actions runs lint, tests, dependency auditing, compilation, and a Docker image build on pushes and pull requests. Tests use an isolated in-memory database and do not call external model APIs.

Publishing a version tag (`vX.Y.Z`) builds and publishes an SBOM- and provenance-enabled container image to GitHub Container Registry. Kubernetes templates are in `deploy/kubernetes`; replace the sample image name and create the referenced secrets with a managed PostgreSQL URL, TLS Redis URL, API key, session secret, data HMAC key, and data encryption key before applying them. Apply the worker template to run the job processor. Run `python -m alembic upgrade head` as a release step before deploying a new version.

## Security and deployment notes

- Never commit `.env`, API keys, private conversations, or personal data.
- The development API key is supported only outside production. Production mode rejects SQLite, the development API key, weak or reused secrets, insecure cookies, and non-TLS Redis URLs. Set `APP_ENV=production`, independent random `API_KEY`, `SESSION_SECRET`, `DATA_HMAC_KEY`, and `DATA_ENCRYPTION_KEY` values (each at least 32 characters), `COOKIE_SECURE=true`, `REDIS_URL=rediss://…`, and a managed database URL. For model calls, use HTTPS and configure the provider hostname in `LLM_ALLOWED_HOSTS`.
- Redis-backed login and general rate limits are shared across API replicas. Set correct client IP forwarding only at a trusted ingress and retain gateway-level abuse controls.
- Add organization-specific retention, deletion, and consent controls before using real user conversations.
- Do not treat heuristic measurements or LLM judgments as ground truth. Record reviewer rationale and uncertainty.

## Open-source contribution path

The architecture is split into independent evaluators and a small API orchestration layer so a contributor can add one evaluation capability without changing every app. Potential upstream integrations include import/export formats, evaluation adapters, CI reporting, and annotation interoperability. For GSoC, choose an organization that is accepted in the target year, follow its contributor instructions, and scope work with its mentors; this personal repository alone is not a GSoC project.

## Current limitations

The repository has ten structured evaluation workflows, including authorized ProbeFleet execution against an allowlisted server-configured provider. It includes workspace-scoped storage, session authentication and roles, encrypted durable jobs with retry leases, shared rate limits, a reviewer UI, CI, container builds, and database migrations. It is a production-oriented reference implementation, not a hosted service or a claim of independently certified security. Cloud-specific managed-service automation, SSO/MFA, account recovery, organization-specific retention/consent workflows, and external evaluation integrations remain follow-up work before exposing it to sensitive real-world workloads.
