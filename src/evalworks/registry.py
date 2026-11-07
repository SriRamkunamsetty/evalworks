from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Project:
    slug: str
    name: str
    purpose: str
    evaluator: Callable[[dict[str, Any]], dict[str, Any]]
