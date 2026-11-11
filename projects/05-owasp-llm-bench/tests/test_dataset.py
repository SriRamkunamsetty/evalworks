from collections import Counter

from owaspbench.dataset.catalog import get_all_benchmark_items, get_items_by_category
from owaspbench.models import OWASPCategory


def test_dataset_size_and_coverage():
    items = get_all_benchmark_items()
    assert len(items) == 30
    counts = Counter(it.category for it in items)
    assert len(counts) == 10
    for cat in OWASPCategory:
        assert counts[cat] == 3


def test_get_items_by_category():
    inj_items = get_items_by_category(OWASPCategory.LLM01_PROMPT_INJECTION)
    assert len(inj_items) == 3
    for it in inj_items:
        assert it.category == OWASPCategory.LLM01_PROMPT_INJECTION


def test_item_attributes_valid():
    for item in get_all_benchmark_items():
        assert item.item_id.startswith("LLM")
        assert len(item.title) > 0
        assert len(item.user_prompt) > 0
        assert len(item.description) > 0
