import pytest

from indirectinject.engine.poisoner import TEMPLATES, embed_poison_into_document
from indirectinject.models import PoisonStrategy


def test_all_templates_registered():
    assert len(TEMPLATES) == len(PoisonStrategy)
    for strat in PoisonStrategy:
        assert strat in TEMPLATES
        assert TEMPLATES[strat].sample_payload


@pytest.mark.parametrize("strat", list(PoisonStrategy))
def test_embed_poison_inserts_adversarial_chunk(strat):
    base_text = "Paragraph 1: Intro\n\nParagraph 2: Outro"
    poisoned_text, indices = embed_poison_into_document(
        base_text,
        strat,
        trigger_keyword="return refunds",
    )

    assert len(indices) == 1
    assert "return refunds" in poisoned_text
    chunks = [p.strip() for p in poisoned_text.split("\n\n") if p.strip()]
    assert len(chunks) == 3
    assert indices[0] == 1
