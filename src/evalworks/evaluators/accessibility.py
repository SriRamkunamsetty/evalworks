import re
from typing import Any

from evalworks.evaluators.common import human_review, required_text


def evaluate(payload: dict[str, Any]) -> dict[str, Any]:
    answer = required_text(payload, "answer", 8000)
    words = re.findall(r"\b[\w’'-]+\b", answer, re.UNICODE)
    sentences = [part for part in re.split(r"[.!?]+", answer) if part.strip()]
    average_sentence_length = round(len(words) / max(1, len(sentences)), 2)
    reading_level = payload.get("reading_level", "general")
    if reading_level not in {"general", "plain_language", "child"}:
        raise ValueError("reading_level must be general, plain_language, or child")
    target_words = {"general": 30, "plain_language": 20, "child": 12}[reading_level]
    return {
        "word_count": len(words),
        "sentence_count": len(sentences),
        "average_words_per_sentence": average_sentence_length,
        "reading_level": reading_level,
        "long_sentence_threshold_words": target_words,
        "long_sentence_count": sum(
            len(re.findall(r"\b[\w’'-]+\b", s)) > target_words for s in sentences
        ),
        "complex_word_count": sum(len(re.findall(r"\b[\w’'-]+\b", word)) >= 4 for word in words),
        "review_dimensions": [
            "plain language",
            "structure",
            "respectful tone",
            "actionability",
            "accessibility",
        ],
        **human_review("Sentence length is a readability signal, not an accessibility verdict."),
    }
