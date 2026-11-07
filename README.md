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

Open http://localhost:8000. For the local demo, the development API key is `local-dev-key-change-me`; change it in `.env` before using the app outside your own machine. Interactive API docs are at `/docs`.

To create the first authenticated workspace administrator, apply migrations and run:

```powershell
python -m evalworks.cli create-admin --workspace "My review team" --email you@example.com
```

The CLI prompts for a password and stores only an Argon2 hash. Sign in from the workspace UI. New deployments have no default user or public sign-up route.

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

All API requests are versioned under `/api/v1`. Development can use `X-API-Key`; production uses authenticated user sessions. Evaluation inputs are returned to the reviewer but are not stored. The database stores a keyed HMAC fingerprint, redacted result summary, allowlisted reproducibility metadata, and reviewer feedback. Runs and feedback are scoped to a workspace. Roles are `admin`, `reviewer`, and read-only `viewer`; only admins delete runs. Browser sessions use HttpOnly cookies and CSRF protection.

## Optional LLM agent

Set `LLM_BASE_URL`, `LLM_API_KEY`, and `LLM_MODEL` to an OpenAI-compatible chat-completions endpoint. Then call `POST /api/v1/agents/probe-plan`. The agent returns draft scenarios only; it does not run them against a target or silently add them to a benchmark.

## Test and quality checks

```powershell
python -m ruff check .
python -m pytest -q
```

GitHub Actions runs lint, tests, and a Docker image build on pushes and pull requests. Tests use an isolated in-memory database and do not call external model APIs.

Publishing a version tag (`vX.Y.Z`) builds and publishes a container image to GitHub Container Registry. A private Kubernetes deployment template is in `deploy/kubernetes`; replace the sample image name and create the referenced secret with a managed PostgreSQL URL (`postgresql+psycopg://…`) and strong API key before applying it. Run `python -m alembic upgrade head` as a release step before deploying a new version.

## Security and deployment notes

- Never commit `.env`, API keys, private conversations, or personal data.
- The development API key is supported only outside production. Production mode rejects SQLite, the development API key, weak session secrets, and insecure cookies. Set `APP_ENV=production`, a random `API_KEY`, a random `SESSION_SECRET` (at least 32 characters), `COOKIE_SECURE=true`, and a managed database URL.
- Login and general request limits are in-process and per instance. Put a trusted gateway/WAF with distributed rate limiting in front of a multi-replica deployment.
- Add organization-specific retention, deletion, and consent controls before using real user conversations.
- Do not treat heuristic measurements or LLM judgments as ground truth. Record reviewer rationale and uncertainty.

## Open-source contribution path

The architecture is split into independent evaluators and a small API orchestration layer so a contributor can add one evaluation capability without changing every app. Potential upstream integrations include import/export formats, evaluation adapters, CI reporting, and annotation interoperability. For GSoC, choose an organization that is accepted in the target year, follow its contributor instructions, and scope work with its mentors; this personal repository alone is not a GSoC project.

## Current limitations

The repository has ten working structured evaluation flows, workspace-scoped storage, session authentication and roles, a reviewer UI, CI, a container build, and database migrations. It is a production-oriented reference implementation, not a hosted service or a claim of independently certified security. Durable background queues, cloud-specific managed-service modules, SSO/MFA, account recovery, organization-specific retention/consent workflows, and external evaluation integrations remain follow-up work before exposing it to sensitive real-world workloads.
