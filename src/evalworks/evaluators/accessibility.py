import re
from typing import Any

from evalworks.evaluators.common import human_review, required_text


def evaluate(payload: dict[str, Any]) -> dict[str, Any]:
    answer = required_text(payload, "answer", 8000)
    words = re.findall(r"\b[\w’'-]+\b", answer, re.UNICODE)
    sentences = [part for part in re.split(r"[.!?]+", answer) if part.strip()]
    average_sentence_length = round(len(words) / max(1, len(sentences)), 2)
    return {
        "word_count": len(words),
        "sentence_count": len(sentences),
        "average_words_per_sentence": average_sentence_length,
        "long_sentence_count": sum(len(re.findall(r"\b[\w’'-]+\b", s)) > 30 for s in sentences),
        "review_dimensions": [
            "plain language",
            "structure",
            "respectful tone",
            "actionability",
            "accessibility",
        ],
        **human_review("Sentence length is a readability signal, not an accessibility verdict."),
    }
