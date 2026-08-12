"""Pydantic decision schemas for LLM-augmented agents."""

from pydantic import BaseModel, Field
from typing import Literal


class ManufacturerDecision(BaseModel):
    """Structured decision output from LLM for a manufacturer's monthly step."""

    action: Literal["expand", "maintain", "reduce"] = Field(
        description="Capacity adjustment: expand / maintain / reduce"
    )
    change_percentage: float = Field(
        default=0.0,
        ge=0.0,
        le=0.5,
        description="Magnitude of capacity change [0.0, 0.5]."
    )
    rd_focus: Literal["efficiency", "cost_reduction", "none"] = Field(
        description="R&D priority this tick: efficiency, cost_reduction, or none"
    )
    reasoning: str = Field(
        default="",
        description="Brief economic rationale for the decision"
    )


class AdopterDecision(BaseModel):
    """Structured decision output from LLM for an adopter's monthly step.

    When the LLM returns `will_adopt=true`, the adopter is marked as adopted.
    On failure the TPB formula is used as a deterministic fallback.
    """

    will_adopt: bool = Field(
        description="Whether the agent decides to install PV this month"
    )
    confidence: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Confidence in the decision [0.0, 1.0]"
    )
    key_factor: str = Field(
        default="economic",
        description="Primary driver: economic, environmental, social, or policy"
    )
    reasoning: str = Field(
        default="",
        description="Brief rationale for adoption decision"
    )
