# Project catalog and completion status

EvalWorks ships ten working evaluation workflows in one modular application. “Complete” here means each workflow has a validated API path, persisted run record, redacted storage, human-review signal, and regression coverage. It does not mean ten independently deployable SaaS products or a fully operated public service.

| Project | Shipped workflow | Current status | Further work for full product maturity |
|---|---|---|---|
| HumanEval Studio | Transcript validation, configurable rubric dimensions, feedback and persisted review runs | Working | Reviewer queues, rubric version history, adjudication, accessible annotation UI |
| ProbeFleet | Scenario drafting, explicit authorization, capped configured-provider execution, safety triage and redacted run records | Working | Durable asynchronous jobs, replay, model matrix, cancel/retry, richer threat taxonomy |
| JudgeBench | Human/judge scalar comparison and multi-rater error, agreement and correlation signals | Working | Confidence intervals, ordinal agreement statistics, calibration datasets and slices |
| Conversation Memory Bench | Normalized literal recall, aliases, expected recall and unwanted-recall checks | Working | Multi-turn state fixtures, consent/correction suite and paraphrase-aware semantic evaluation |
| EvidenceCheck | Claim/source checklist, reviewer verdicts, bounded citation metadata and HTTPS-only citation URLs | Working | Source snapshots, provenance and human-verified entailment workflow |
| IndicEval | Unicode script coverage and text-quality warning signals for 13 language labels | Working | Native-speaker datasets, language-specific benchmarks and community governance |
| Safety Scenario Lab | Bounded injection/disclosure patterns and structured human safety review | Working | Curated threat suite, deduplication, calibrated severity and external benchmark adapters |
| Accessibility Reviewer | Reading-level thresholds, sentence/word signals and review checklist | Working | Screen-reader and assistive-technology workflows, usability research and WCAG review |
| Multimodal Grounding QA | Modality checklist with expected observations and evidence identifiers | Working | Secure media ingestion, provider adapters, timestamped evidence and retention controls |
| EvalSRE | Incident-to-regression draft with stable fingerprint and approval requirement | Working | Approved-case promotion state machine, scheduled regression runs and release comparisons |

## Shared platform shipped

- Versioned FastAPI routes and a small browser workbench.
- Provider adapter with bounded response reads and explicit configuration; no request-supplied target URL.
- PostgreSQL-capable schema and Alembic migrations, including workspace scoping, authenticated user sessions, and admin, reviewer, and viewer roles.
- Keyed input fingerprints and recursively redacted persisted evaluator results.
- CI lint and regression suite, Docker image build, tagged GHCR publishing, Compose hardening, and a Kubernetes deployment template.
- Probe execution requires an explicit authorization flag and is limited to five test cases per synchronous request.

## Production completion still needed

This is a portfolio-grade, security-conscious application baseline, not a claim of production operation at scale. Before public multi-tenant service use, add SSO/MFA and account recovery, distributed rate limits, durable job queue and worker isolation, audit logging/metrics/tracing, tested backup/restore and retention policies, deployment-specific secrets and network policy, load testing, and independent security review. Current model calls are synchronous and single-process rate limits do not coordinate across replicas.

For GSoC, treat this repository as a proposal portfolio. Choose an accepted mentoring organization in the target year and agree with its mentors on an upstream-sized deliverable; this repository alone is not a GSoC project.
