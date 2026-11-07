# Contributing

Thanks for helping improve EvalWorks. The project is designed around clear, small evaluation modules and explainable human review.

## Before opening a pull request

1. Open or find an issue describing the problem or proposed change.
2. Keep changes focused. New evaluators belong in `src/evalworks/evaluators/` and should be registered in `src/evalworks/projects.py`.
3. Add tests for valid input, invalid input, and the limitation of any heuristic.
4. Never include private conversations, API keys, or personal data in fixtures or screenshots.
5. Run `python -m ruff check .` and `python -m pytest -q`.

## Evaluator design

- Be explicit about what is deterministic, approximate, or subjective.
- Return structured evidence and uncertainty; do not present a heuristic as a truth or safety verdict.
- Bound text lengths and collection sizes.
- Keep provider calls behind `evalworks.llm`; tests must use mock responses and never require paid credentials.
- Ask for human approval before executing generated test scenarios.

## GSoC contributors

This repository is a practice project, not a promise of GSoC participation. Follow the current program rules and the selected mentoring organization's application and AI-use policies. Upstream work should be discussed with that project's maintainers and implemented in the organization's repository when accepted.
