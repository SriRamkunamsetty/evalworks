from typing import Any

from evalworks.evaluators.common import human_review, required_text


def evaluate(payload: dict[str, Any]) -> dict[str, Any]:
    language = required_text(payload, "language", 80)
    prompt = required_text(payload, "prompt", 4000)
    answer = required_text(payload, "answer", 8000)
    non_ascii = sum(ord(char) > 127 for char in answer)
    return {
        "language": language,
        "prompt_characters": len(prompt),
        "answer_characters": len(answer),
        "non_ascii_character_ratio": round(non_ascii / max(1, len(answer)), 4),
        "review_dimensions": [
            "meaning",
            "code_switching",
            "register",
            "cultural_context",
            "respect",
        ],
        **human_review(
            "Character scripts do not establish language, fluency, or cultural correctness."
        ),
    }
