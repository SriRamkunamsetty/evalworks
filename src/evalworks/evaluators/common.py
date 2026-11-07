from typing import Any


def required_text(payload: dict[str, Any], key: str, max_length: int = 8000) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"'{key}' must be a non-empty string")
    if len(value) > max_length:
        raise ValueError(f"'{key}' exceeds {max_length} characters")
    return value.strip()


def required_list(payload: dict[str, Any], key: str, max_items: int = 100) -> list:
    value = payload.get(key)
    if not isinstance(value, list) or not value:
        raise ValueError(f"'{key}' must be a non-empty list")
    if len(value) > max_items:
        raise ValueError(f"'{key}' exceeds {max_items} items")
    return value


def human_review(
    note: str = "Human review is required for the final quality or safety judgment.",
) -> dict:
    return {"human_review_required": True, "review_note": note}
