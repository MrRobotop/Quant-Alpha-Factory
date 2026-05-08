"""Factor registry."""

from __future__ import annotations

from src.factors.base import FactorSpec


class FactorRegistryError(ValueError):
    """Raised when factor registry operations fail."""


class FactorRegistry:
    """In-memory registry for versioned factor specifications."""

    def __init__(self) -> None:
        self._factors: dict[str, FactorSpec] = {}

    def register(self, factor: FactorSpec) -> None:
        """Register a factor after validating required metadata."""
        validate_factor_spec(factor)
        if factor.identifier in self._factors:
            raise FactorRegistryError(f"Factor already registered: {factor.identifier}")
        self._factors[factor.identifier] = factor

    def get(self, name: str, version: str | None = None) -> FactorSpec:
        """Retrieve a factor by name and optional version."""
        if version is not None:
            identifier = f"{name}:{version}"
            try:
                return self._factors[identifier]
            except KeyError as exc:
                raise FactorRegistryError(f"Factor not found: {identifier}") from exc

        matches = [factor for factor in self._factors.values() if factor.name == name]
        if not matches:
            raise FactorRegistryError(f"Factor not found: {name}")
        if len(matches) > 1:
            raise FactorRegistryError(
                f"Multiple versions exist for factor '{name}'. Specify version."
            )
        return matches[0]

    def list(self) -> list[FactorSpec]:
        """List registered factors in deterministic order."""
        return [self._factors[key] for key in sorted(self._factors)]


def validate_factor_spec(factor: FactorSpec) -> None:
    """Validate non-negotiable factor metadata fields."""
    required_text_fields = {
        "name": factor.name,
        "version": factor.version,
        "description": factor.description,
        "economic_rationale": factor.economic_rationale,
        "leakage_notes": factor.leakage_notes,
    }
    missing = [field for field, value in required_text_fields.items() if not value.strip()]
    if missing:
        raise FactorRegistryError(f"Factor missing required metadata: {', '.join(missing)}")
    if not factor.required_columns:
        raise FactorRegistryError("Factor must declare required_columns.")
    if factor.horizon <= 0:
        raise FactorRegistryError("Factor horizon must be positive.")
    if factor.implementation_type == "qlib_expression" and not factor.qlib_expression:
        raise FactorRegistryError("Qlib expression factors must include qlib_expression.")
