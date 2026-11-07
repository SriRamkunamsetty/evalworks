from evalworks.evaluators import (
    accessibility,
    evidence,
    incidents,
    indic,
    judgebench,
    memory,
    multimodal,
    probes,
    review,
    safety,
)
from evalworks.registry import Project

PROJECTS = [
    Project(
        "human-eval-studio",
        "HumanEval Studio",
        "Structured human review of chatbot conversations",
        review,
    ),
    Project(
        "probefleet", "ProbeFleet", "Design and execute challenging test conversations", probes
    ),
    Project("judgebench", "JudgeBench", "Compare human ratings with AI judge scores", judgebench),
    Project(
        "memory-bench",
        "Conversation Memory Bench",
        "Check recall, corrections, and forgetting",
        memory,
    ),
    Project("evidencecheck", "EvidenceCheck", "Review claims and supporting evidence", evidence),
    Project(
        "indiceval", "IndicEval", "Review language, code-switching, and cultural context", indic
    ),
    Project(
        "safety-lab", "Safety Scenario Lab", "Triage safety and prompt-injection scenarios", safety
    ),
    Project(
        "accessibility-reviewer",
        "Accessibility Reviewer",
        "Inspect clarity and readability signals",
        accessibility,
    ),
    Project(
        "multimodal-qa",
        "Multimodal Grounding QA",
        "Review answers against multimodal inputs",
        multimodal,
    ),
    Project("evalsre", "EvalSRE", "Turn incidents into regression test drafts", incidents),
]
PROJECT_BY_SLUG = {project.slug: project for project in PROJECTS}
