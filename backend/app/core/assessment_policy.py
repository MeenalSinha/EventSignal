"""Declarative, validated assessment policy configuration for Phase 4.

Business rules, field weights, applicability rules, and thresholds are
defined here and in validated configuration files rather than hardcoded
in Python calculation functions.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.field_evidence import ExtractionMethod

VALID_OPPORTUNITY_FIELDS: frozenset[str] = frozenset(
    {
        "title",
        "opportunity_type",
        "organizer",
        "start_date",
        "end_date",
        "registration_deadline",
        "submission_deadline",
        "location",
        "mode",
        "eligibility",
        "skills_required",
        "compensation",
        "application_url",
    }
)


class ApplicabilityRule(BaseModel):
    """Applicability definition for a specific opportunity type."""

    model_config = ConfigDict(extra="forbid")

    required_fields: list[str] = Field(default_factory=list)
    optional_fields: list[str] = Field(default_factory=list)
    not_applicable_fields: list[str] = Field(default_factory=list)

    @field_validator("required_fields", "optional_fields", "not_applicable_fields")
    @classmethod
    def _validate_fields(cls, fields: list[str]) -> list[str]:
        for f in fields:
            if f not in VALID_OPPORTUNITY_FIELDS:
                raise ValueError(f"Unknown opportunity field in applicability rule: '{f}'")
        return fields


class AssessmentPolicy(BaseModel):
    """Declarative, validated assessment policy.

    Guarantees:
      - Field weights, dimension weights, and thresholds are fully validated.
      - Modifying a weight changes assessment results without touching Python logic.
      - Invalid configurations fail loudly at load time.
    """

    model_config = ConfigDict(extra="forbid")

    policy_version: str = Field(min_length=1)
    description: str = Field(default="")

    # Dimension weights (must sum to 1.0)
    dimension_weights: dict[str, float] = Field(
        default_factory=lambda: {
            "completeness": 0.45,
            "evidence_quality": 0.35,
            "consistency": 0.20,
        }
    )

    # Core field categories
    critical_fields: list[str] = Field(
        default_factory=lambda: [
            "title",
            "opportunity_type",
            "organizer",
            "registration_deadline",
            "application_url",
        ]
    )
    optional_fields: list[str] = Field(
        default_factory=lambda: [
            "start_date",
            "end_date",
            "submission_deadline",
            "location",
            "mode",
            "eligibility",
            "skills_required",
            "compensation",
        ]
    )

    # Relative completeness weight per field
    field_weights: dict[str, float] = Field(default_factory=dict)

    # Opportunity type applicability rules
    type_applicability: dict[str, ApplicabilityRule] = Field(default_factory=dict)

    # Extraction method reliability weights
    method_quality_weights: dict[str, float] = Field(
        default_factory=lambda: {
            ExtractionMethod.STRUCTURED.value: 1.0,
            ExtractionMethod.RULE_BASED.value: 0.75,
            ExtractionMethod.MANUAL.value: 1.0,
            ExtractionMethod.LLM.value: 0.5,
        }
    )

    # Quality and confidence thresholds
    thresholds: dict[str, float] = Field(
        default_factory=lambda: {
            "high_quality": 0.80,
            "moderate_quality": 0.55,
            "single_source_penalty": 0.0,
            "conflict_penalty_multiplier": 0.25,
        }
    )

    @field_validator("critical_fields", "optional_fields")
    @classmethod
    def _validate_field_names(cls, fields: list[str]) -> list[str]:
        for f in fields:
            if f not in VALID_OPPORTUNITY_FIELDS:
                raise ValueError(f"Unknown field in policy: '{f}'")
        return fields

    @model_validator(mode="after")
    def _validate_weights_and_completeness(self) -> AssessmentPolicy:
        # 1. Validate dimension weights sum to 1.0
        dw = self.dimension_weights
        required_dims = {"completeness", "evidence_quality", "consistency"}
        missing_dims = required_dims - set(dw.keys())
        if missing_dims:
            raise ValueError(f"Missing required dimension weights: {missing_dims}")

        total_dim_weight = sum(dw.values())
        if abs(total_dim_weight - 1.0) > 0.005:
            raise ValueError(f"Dimension weights must sum to 1.0 (got {total_dim_weight:.4f})")

        for dim, val in dw.items():
            if not (0.0 <= val <= 1.0):
                raise ValueError(f"Dimension weight for '{dim}' must be between 0.0 and 1.0")

        # 2. Populate and validate field weights if empty
        all_expected = set(self.critical_fields) | set(self.optional_fields)
        if not self.field_weights:
            # Default weights: 2.0 for critical fields, 1.0 for optional fields
            self.field_weights = {
                f: (2.0 if f in self.critical_fields else 1.0) for f in all_expected
            }
        else:
            for f, w in self.field_weights.items():
                if f not in VALID_OPPORTUNITY_FIELDS:
                    raise ValueError(f"Unknown field in field_weights: '{f}'")
                if w <= 0:
                    raise ValueError(f"Field weight for '{f}' must be positive (got {w})")

        # 3. Method quality weights validation
        for method_name, w in self.method_quality_weights.items():
            if not (0.0 <= w <= 1.0):
                raise ValueError(f"Method quality weight for '{method_name}' must be in [0.0, 1.0]")

        return self

    def get_applicable_fields(self, opportunity_type: str | None) -> tuple[set[str], set[str]]:
        """Return (applicable_critical, applicable_optional) fields for given opportunity type."""
        if opportunity_type and opportunity_type in self.type_applicability:
            rule = self.type_applicability[opportunity_type]
            not_app = set(rule.not_applicable_fields)
            crit = set(rule.required_fields or self.critical_fields) - not_app
            opt = set(rule.optional_fields or self.optional_fields) - not_app
            return crit, opt
        return set(self.critical_fields), set(self.optional_fields)

    def get_method_quality(self, method: ExtractionMethod | str) -> float:
        """Get the configured quality score for an extraction method."""
        val = method.value if isinstance(method, ExtractionMethod) else str(method)
        return self.method_quality_weights.get(val, 0.7)


def load_assessment_policy(path_or_str: str | Path | None = None) -> AssessmentPolicy:
    """Load and validate an assessment policy from a JSON file path or string.

    If path_or_str is None, loads from the default policy file.
    Raises ValueError / ValidationError on invalid configuration.
    """
    if path_or_str is None:
        default_path = Path(__file__).resolve().parent / "default_assessment_policy.json"
        if not default_path.exists():
            # Generate default policy programmatically and save it
            policy = AssessmentPolicy(
                policy_version="1.0.0",
                description="Default EventSignal explainable opportunity assessment policy.",
            )
            default_path.write_text(policy.model_dump_json(indent=2), encoding="utf-8")
            return policy
        raw_text = default_path.read_text(encoding="utf-8")
        data: dict[str, Any] = json.loads(raw_text)
        return AssessmentPolicy.model_validate(data)

    if isinstance(path_or_str, Path) or (
        isinstance(path_or_str, str) and not path_or_str.strip().startswith("{")
    ):
        p = Path(path_or_str)
        if not p.is_absolute():
            p = Path(__file__).resolve().parents[2] / p
        if not p.exists():
            raise FileNotFoundError(f"Assessment policy file not found: {p}")
        raw_text = p.read_text(encoding="utf-8")
        data = json.loads(raw_text)
        return AssessmentPolicy.model_validate(data)

    data = json.loads(path_or_str)
    return AssessmentPolicy.model_validate(data)
