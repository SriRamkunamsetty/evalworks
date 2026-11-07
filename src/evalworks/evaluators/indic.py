import unicodedata
from typing import Any

from evalworks.evaluators.common import human_review, required_text

_LANGUAGE_RANGES = {
    "hindi": (0x0900, 0x097F),
    "marathi": (0x0900, 0x097F),
    "nepali": (0x0900, 0x097F),
    "bengali": (0x0980, 0x09FF),
    "punjabi": (0x0A00, 0x0A7F),
    "gujarati": (0x0A80, 0x0AFF),
    "odia": (0x0B00, 0x0B7F),
    "tamil": (0x0B80, 0x0BFF),
    "telugu": (0x0C00, 0x0C7F),
    "kannada": (0x0C80, 0x0CFF),
    "malayalam": (0x0D00, 0x0D7F),
    "sinhala": (0x0D80, 0x0DFF),
    "urdu": (0x0600, 0x06FF),
}


def _language_key(language: str) -> str | None:
    normalized = language.casefold()
    return next((name for name in _LANGUAGE_RANGES if name in normalized), None)


def evaluate(payload: dict[str, Any]) -> dict[str, Any]:
    language = required_text(payload, "language", 80)
    prompt = required_text(payload, "prompt", 4000)
    answer = required_text(payload, "answer", 8000)
    normalized_answer = unicodedata.normalize("NFC", answer)
    letters = [char for char in normalized_answer if char.isalpha()]
    language_key = _language_key(language)
    requested_range = _LANGUAGE_RANGES.get(language_key) if language_key else None
    requested_script_letters = (
        sum(requested_range[0] <= ord(char) <= requested_range[1] for char in letters)
        if requested_range
        else 0
    )
    latin_letters = sum("LATIN" in unicodedata.name(char, "") for char in letters)
    bidi_control_count = sum(
        unicodedata.bidirectional(char) in {"RLO", "LRO", "RLE", "LRE", "PDF"} for char in answer
    )
    return {
        "language": language,
        "prompt_characters": len(prompt),
        "answer_characters": len(answer),
        "detected_script": language_key,
        "letter_count": len(letters),
        "requested_script_letter_ratio": round(requested_script_letters / max(1, len(letters)), 4),
        "latin_letter_ratio": round(latin_letters / max(1, len(letters)), 4),
        "replacement_character_count": answer.count("\ufffd"),
        "bidi_control_count": bidi_control_count,
        "measurement": "Unicode script coverage only; does not measure fluency or correctness.",
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
