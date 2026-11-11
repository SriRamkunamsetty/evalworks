import base64

from visionjailbreak.generator.image_gen import generate_typographic_image
from visionjailbreak.models import PerturbationType


def test_generate_typographic_image_plain():
    payload = generate_typographic_image("TEST_PROMPT", PerturbationType.PLAIN_TYPOGRAPHIC)
    assert payload.width == 512
    assert payload.height == 256
    assert payload.embedded_text == "TEST_PROMPT"
    # Valid Base64 check
    decoded = base64.b64decode(payload.image_base64)
    assert len(decoded) > 100
    assert decoded[:8] == b"\x89PNG\r\n\x1a\n"  # PNG magic bytes


def test_generate_all_perturbations():
    for pert in PerturbationType:
        payload = generate_typographic_image("TEST_PERT", pert)
        decoded = base64.b64decode(payload.image_base64)
        assert len(decoded) > 100
        assert decoded[:8] == b"\x89PNG\r\n\x1a\n"
