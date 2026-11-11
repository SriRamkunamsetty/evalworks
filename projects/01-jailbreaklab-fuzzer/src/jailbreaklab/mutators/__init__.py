from jailbreaklab.models import MutationType
from jailbreaklab.mutators.base import BaseMutator
from jailbreaklab.mutators.delimiter import DelimiterInjectionMutator
from jailbreaklab.mutators.encoding import Base64Mutator, HexMutator, LeetspeakMutator
from jailbreaklab.mutators.persona import HypotheticalFrameMutator, PersonaHijackMutator
from jailbreaklab.mutators.perturbation import PrefixInjectionMutator, ZeroWidthObscurationMutator

MUTATOR_REGISTRY: dict[MutationType, BaseMutator] = {
    MutationType.BASE64: Base64Mutator(),
    MutationType.HEX: HexMutator(),
    MutationType.LEETSPEAK: LeetspeakMutator(),
    MutationType.DELIMITER_INJECTION: DelimiterInjectionMutator(),
    MutationType.PERSONA_HIJACK: PersonaHijackMutator(),
    MutationType.HYPOTHETICAL_FRAME: HypotheticalFrameMutator(),
    MutationType.ZERO_WIDTH_OBSCURATION: ZeroWidthObscurationMutator(),
    MutationType.PREFIX_INJECTION: PrefixInjectionMutator(),
}


def get_mutator(mutation_type: MutationType) -> BaseMutator:
    mutator = MUTATOR_REGISTRY.get(mutation_type)
    if not mutator:
        raise ValueError(f"Unknown mutator: {mutation_type}")
    return mutator


def list_mutators() -> list[BaseMutator]:
    return list(MUTATOR_REGISTRY.values())


__all__ = [
    "MUTATOR_REGISTRY",
    "BaseMutator",
    "Base64Mutator",
    "DelimiterInjectionMutator",
    "HexMutator",
    "HypotheticalFrameMutator",
    "LeetspeakMutator",
    "PersonaHijackMutator",
    "PrefixInjectionMutator",
    "ZeroWidthObscurationMutator",
    "get_mutator",
    "list_mutators",
]
