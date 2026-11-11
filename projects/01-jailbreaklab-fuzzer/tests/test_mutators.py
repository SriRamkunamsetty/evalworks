import base64

import pytest

from jailbreaklab.models import MutationType
from jailbreaklab.mutators import MUTATOR_REGISTRY, get_mutator, list_mutators


def test_registry_contains_all_mutators():
    assert len(MUTATOR_REGISTRY) == len(MutationType)
    assert len(list_mutators()) == len(MutationType)


@pytest.mark.parametrize("m_type", list(MutationType))
def test_all_mutators_produce_valid_mutated_prompts(m_type):
    mutator = get_mutator(m_type)
    prompt = "Test security prompt override"
    mutated = mutator.mutate(prompt)

    assert mutated.mutator_id == m_type
    assert mutated.base_prompt == prompt
    assert len(mutated.mutated_prompt) > len(prompt)
    assert mutated.owasp_category.value.startswith("LLM")
    assert "AML." in mutated.mitre_atlas_id


def test_base64_mutator_encodes_accurately():
    mutator = get_mutator(MutationType.BASE64)
    prompt = "Secret instruction 123"
    mutated = mutator.mutate(prompt)

    # Base64 string must be in mutated prompt
    b64_str = base64.b64encode(prompt.encode()).decode()
    assert b64_str in mutated.mutated_prompt


def test_hex_mutator_encodes_accurately():
    mutator = get_mutator(MutationType.HEX)
    prompt = "admin"
    mutated = mutator.mutate(prompt)
    assert prompt.encode().hex() in mutated.mutated_prompt


def test_leetspeak_mutator_substitutes_chars():
    mutator = get_mutator(MutationType.LEETSPEAK)
    prompt = "test"
    mutated = mutator.mutate(prompt)
    # 'e' -> '3', 't' -> '7' => "7357"
    assert "7357" in mutated.mutated_prompt


def test_zero_width_mutator_embeds_unicode():
    mutator = get_mutator(MutationType.ZERO_WIDTH_OBSCURATION)
    prompt = "safe"
    mutated = mutator.mutate(prompt)
    assert "\u200c" in mutated.mutated_prompt
