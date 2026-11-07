# Project catalog and build sequence

The ten cards are independent evaluation workflows inside one repository. The current code is an initial vertical slice for each, not ten fully independent SaaS products. Build each workflow deeper after validating it with users and an upstream open-source community.

| App | Current vertical slice | Next high-value increment |
|---|---|---|
| HumanEval Studio | Conversation transcript, rubric dimensions, evidence and feedback fields | Persistent annotation queues, multiple reviewers, adjudication, rubric versioning |
| ProbeFleet | Objective plus prompt scenarios with approval status | Model adapter runner, safe concurrency, replay, scenario tagging and result comparison |
| JudgeBench | Human/judge score gap and normalized agreement | Multi-rater agreement statistics, bias slices, confidence intervals, calibration datasets |
| Conversation Memory Bench | Literal recall and unwanted-recall checks | Multi-turn fixtures, paraphrase-aware evaluation, explicit correction and consent cases |
| EvidenceCheck | Claim/source review fields and reviewer verdicts | Source snapshots, provenance, citation validation and reviewer workflow |
| IndicEval | Language/context rubric and script-character signal | Human-reviewed language suites, code-switch dimensions, dataset governance and language slices |
| Safety Scenario Lab | Prompt-injection pattern triage and review dimensions | Risk taxonomy, controlled test harness, finding deduplication and red-team reporting |
| Accessibility Reviewer | Sentence-length signals and human review dimensions | Screen-reader testing, plain-language rubric, user research and accessible UI checks |
| Multimodal Grounding QA | Modalities and expected-observation checklist | Safe media upload, vision/audio adapter, input evidence anchoring and retention controls |
| EvalSRE | Incident report into a regression-case draft | Approval state machine, benchmark promotion, regression runner and release comparison |

## Recommended sequence

1. Deepen HumanEval Studio, ProbeFleet, and JudgeBench first. These directly demonstrate chatbot testing and evaluation judgment.
2. Ship provider execution with timeouts and model comparison. Add it behind adapters so tests remain deterministic and credential-free.
3. Improve the annotations and data model, then publish a reproducible public sample benchmark with documented consent and limitations.
4. Contribute a small compatibility feature or bug fix upstream. Only propose a GSoC-sized change after an accepted mentoring organization confirms the need and scope.
