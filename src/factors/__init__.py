"""Factor registry and evaluation modules."""

from src.factors.base import FactorSpec
from src.factors.evaluation import FactorICResult, evaluate_factor_ic
from src.factors.library import baseline_factors, build_default_registry
from src.factors.registry import FactorRegistry, FactorRegistryError, validate_factor_spec

__all__ = [
    "FactorICResult",
    "FactorRegistry",
    "FactorRegistryError",
    "FactorSpec",
    "baseline_factors",
    "build_default_registry",
    "evaluate_factor_ic",
    "validate_factor_spec",
]
