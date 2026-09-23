"""
Adopter agent — potential PV system buyer in Germany.

State variables per Tables SI 1, SI 2, SI 4, SI 6 of the supplementary
information (Nuñez-Jimenez et al., 2022).  LLM-augmented decision with
deterministic TPB fallback.
"""

import asyncio
import json
import random
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Tuple

from openai import AsyncOpenAI
from agents.agent_framework import (
    ConversationMemory,
    create_llm_client,
    extract_json_object,
)
from agents.tools import build_adopter_tools
from schemas import AdopterDecision
from submodels.adoption import AdoptionEvaluation, evaluate_adoption


# ---------------------------------------------------------------------------
# Enums & helpers
# ---------------------------------------------------------------------------


class AdopterType(Enum):
    """Table SI 1: three adopter categories, differentiated by system size."""
    RESIDENTIAL = "residential"
    COMMERCIAL_INDUSTRIAL = "commercial_industrial"
    UTILITY_SCALE = "utility_scale"


# Population counts 1:1,000 scaled (Table SI 1 row 1-3, column 3)
_CATEGORY_POPULATION = {
    AdopterType.RESIDENTIAL: 16_891,
    AdopterType.COMMERCIAL_INDUSTRIAL: 3_853,
    AdopterType.UTILITY_SCALE: 85,
}

_CATEGORY_SYSTEM_SIZE_RANGE = {
    AdopterType.RESIDENTIAL: (0.5, 10.0),
    AdopterType.COMMERCIAL_INDUSTRIAL: (10.0, 40.0),
    AdopterType.UTILITY_SCALE: (40.0, 10_000.0),
}

_CATEGORY_SELF_CONSUMPTION_MEAN = {
    AdopterType.RESIDENTIAL: 0.30,
    AdopterType.COMMERCIAL_INDUSTRIAL: 0.20,
    AdopterType.UTILITY_SCALE: 0.40,
}


# ---------------------------------------------------------------------------
# Adopter
# ---------------------------------------------------------------------------


@dataclass
class Adopter:
    """Potential PV adopter in Germany (domestic region only).

    Table SI 1 — Category-dependent variables:
        adopter_type, system_size, self_consumption_rate,
        electricity_price, discount_rate

    Table SI 2 — Category-independent state variables:
        is_adopted, location, pv_orientation, personal_discount_rate,
        discount_foreign_pv, environmental_awareness

    Table SI 4 — Technology sensing variables:
        pv_performance_ratio, maintenance_cost_ratio, irradiation
    """

    agent_id: int
    adopter_type: AdopterType
    location: Tuple[float, float]
    is_adopted: bool = False
    roof_size: float = 0.0  # usable roof area [m²] (Table SI 1) — bounds system size
    system_size: float = 0.0
    self_consumption_rate: float = 0.0
    electricity_price: float = 0.0
    discount_rate: float = 0.0
    personal_discount_rate: float = 0.0
    discount_foreign_pv: float = 0.0
    pv_orientation: float = 0.9
    environmental_awareness: float = 0.5
    pv_performance_ratio: float = 0.85
    maintenance_cost_ratio: float = 0.015
    irradiation: float = 938.0
    attitude: float = 0.0
    social_norm: float = 0.0
    pbc: float = 0.0
    intention: float = 0.0
    ideation: float = 0.0
    npv_domestic: float = 0.0
    npv_foreign: float = 0.0
    module_choice: Optional[str] = None
    scale_effect: float = 1.0
    peer_radius_km: float = 1.0
    personal_threshold: float = 0.45  # innovator→laggard: ~0.30 → ~0.65
    monthly_consumption_kwh: float = 300.0  # household electricity use
    memory: ConversationMemory = field(default_factory=ConversationMemory)
    _llm_client: Optional[AsyncOpenAI] = field(default=None, repr=False, compare=False)

    # ------------------------------------------------------------------
    # LLM-augmented adoption decision
    # ------------------------------------------------------------------

    async def step_llm(
        self,
        electricity_price: float,
        fit_tariff: float,
        module_price_domestic: float,
        module_price_foreign: float,
        bos_cost: float,
        neighbour_ratio: float,
        market_maturity: float,
        information: float,
        irr: float,
        model_name: str = "gpt-4.1-mini",
    ) -> AdopterDecision:
        """Query an LLM for the adopter's monthly adoption decision.

        On failure the two-stage adoption formula is used as a deterministic
        fallback.
        """
        prompt = self._build_llm_prompt(
            electricity_price, fit_tariff, module_price_domestic,
            module_price_foreign, bos_cost, neighbour_ratio, market_maturity,
            information, irr,
        )

        # Inject conversation memory for multi-turn context
        memory_ctx = self.memory.format_for_prompt()
        full_prompt = memory_ctx + "\n\n" + prompt if self.memory.history else prompt

        # Build tool registry for this decision context
        tools = build_adopter_tools(
            electricity_price=electricity_price,
            fit_tariff=fit_tariff,
            module_price_domestic=module_price_domestic,
            module_price_foreign=module_price_foreign,
            bos_cost=bos_cost,
            market_maturity=market_maturity,
            neighbour_ratio=neighbour_ratio,
            system_size_kw=self.system_size,
            self_consumption_rate=self.self_consumption_rate,
        )

        system_msg = (
            "You are a potential PV adopter in Germany deciding whether "
            "to install a solar PV system. You may call tools to query "
            "market data before making your decision. "
            "Respond with valid JSON only, following the AdopterDecision schema: "
            '{"will_adopt": true|false, '
            '"confidence": 0.0-1.0, '
            '"key_factor": "economic|environmental|social|policy", '
            '"reasoning": "..."}'
        )

        try:
            if self._llm_client is None:
                self._llm_client = create_llm_client()

            messages = [
                {"role": "system", "content": system_msg},
                {"role": "user", "content": full_prompt},
            ]

            # Multi-turn tool-calling loop (max 3 rounds)
            for _ in range(3):
                response = await self._llm_client.chat.completions.create(
                    model=model_name,
                    temperature=0.3,
                    messages=messages,
                    tools=tools.get_specs() if len(tools) > 0 else None,
                    tool_choice="auto" if len(tools) > 0 else None,
                )

                msg = response.choices[0].message

                if msg.tool_calls:
                    # Append assistant message with tool calls
                    messages.append(msg.model_dump())
                    for tc in msg.tool_calls:
                        args = json.loads(tc.function.arguments)
                        result = await tools.invoke(tc.function.name, args)
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tc.id,
                            "content": result,
                        })
                elif msg.content:
                    # Parse JSON from content (strip prose / code fences).
                    decision = AdopterDecision.model_validate(
                        extract_json_object(msg.content)
                    )
                    self.memory.record(0, decision, "LLM decision (with tools)")
                    return decision
                else:
                    break  # No content, no tool calls — abort

            raise ValueError("Tool loop exceeded without valid decision")

        except Exception as exc:
            print(f"[adopter:{self.agent_id}] step_llm error: {type(exc).__name__}: {exc}")
            fallback = self._formula_fallback(
                electricity_price, fit_tariff, module_price_domestic,
                module_price_foreign, bos_cost, neighbour_ratio, information, irr,
            )
            self.memory.record(0, fallback, "two-stage fallback (LLM unavailable)")
            return fallback

    def _build_llm_prompt(
        self,
        electricity_price: float,
        fit_tariff: float,
        module_price_domestic: float,
        module_price_foreign: float,
        bos_cost: float,
        neighbour_ratio: float,
        market_maturity: float,
        information: float,
        irr: float,
    ) -> str:
        type_label = self.adopter_type.value.replace("_", " ").title()
        sys_cost_dom = (module_price_domestic + bos_cost) * max(self.system_size, 0.01) * 1000
        sys_cost_for = (module_price_foreign + bos_cost) * max(self.system_size, 0.01) * 1000

        return (
            f"You are a {type_label} PV adopter in Germany.\n\n"
            f"=== Your Profile ===\n"
            f"  System size               : {self.system_size:.1f} kWp\n"
            f"  Domestic system cost      : €{sys_cost_dom:,.0f}\n"
            f"  Foreign system cost       : €{sys_cost_for:,.0f}\n"
            f"  Self-consumption rate     : {self.self_consumption_rate:.1%}\n"
            f"  Environmental awareness   : {self.environmental_awareness:.2f} / 1.0\n"
            f"  Discount rate (personal)  : {self.personal_discount_rate:.4f}\n"
            f"  Foreign PV discount       : {self.discount_foreign_pv:.4f}\n\n"
            f"=== Market Context (this month) ===\n"
            f"  Retail electricity price  : {electricity_price:.4f} €/kWh\n"
            f"  Feed-in tariff (FiT)      : {fit_tariff:.4f} €/kWh\n"
            f"  Domestic module price     : {module_price_domestic:.4f} €/W\n"
            f"  Foreign module price      : {module_price_foreign:.4f} €/W\n"
            f"  Installation (BOS) cost   : {bos_cost:.4f} €/W\n"
            f"  Information on PV (IN)    : {information:.2f} / 1.0\n"
            f"  Avg household IRR         : {irr:.1%}\n"
            f"  Neighbour adoption ratio  : {neighbour_ratio:.1%}\n"
            f"  Overall market maturity   : {market_maturity:.1%}\n\n"
            f"=== Decision Guidance (two-stage) ===\n"
            f"- First, decide whether you 'get the idea' to install PV this month\n"
            f"  (driven by peer effects, information, awareness, and IRR).\n"
            f"- If you do, evaluate economics: adopt only if the NPV of a domestic\n"
            f"  or foreign module system is non-negative; prefer domestic on a tie.\n"
            f"- High FiT + low system cost -> favourable economics.\n"
            f"- If FiT is zero or very low, adoption only makes sense with very high\n"
            f"  environmental awareness or self-consumption.\n\n"
            f"Output a single JSON object per the schema."
        )

    def _formula_fallback(
        self,
        electricity_price: float,
        fit_tariff: float,
        module_price_domestic: float,
        module_price_foreign: float,
        bos_cost: float,
        neighbour_ratio: float,
        information: float,
        irr: float,
    ) -> AdopterDecision:
        """Deterministic two-stage adoption decision when the LLM is unavailable."""
        is_residential = self.adopter_type == AdopterType.RESIDENTIAL
        outcome = evaluate_adoption(
            is_residential=is_residential,
            environmental_awareness=self.environmental_awareness,
            peer_effect=neighbour_ratio,
            information=information,
            irr=irr,
            system_size_kw=self.system_size,
            self_consumption_rate=self.self_consumption_rate,
            electricity_price=electricity_price,
            fit_tariff=fit_tariff,
            module_price_domestic=module_price_domestic,
            module_price_foreign=module_price_foreign,
            bos_cost=bos_cost,
            category_discount_rate=self.discount_rate,
            personal_discount_rate=self.personal_discount_rate,
            production_factor=self.pv_orientation,
            irradiation=self.irradiation,
        )

        self.ideation = outcome.ideation
        self.npv_domestic = outcome.npv_domestic
        self.npv_foreign = outcome.npv_foreign
        self.module_choice = outcome.module_choice
        self.attitude = outcome.ideation
        self.social_norm = neighbour_ratio
        self.pbc = 0.0
        self.intention = outcome.ideation

        if outcome.early_adopter:
            key_factor = "environmental"
        elif outcome.module_choice == "foreign":
            key_factor = "economic"
        elif fit_tariff > 0.10:
            key_factor = "policy"
        elif neighbour_ratio > 0.3:
            key_factor = "social"
        else:
            key_factor = "economic"

        return AdopterDecision(
            will_adopt=outcome.will_adopt,
            confidence=round(outcome.ideation, 4),
            key_factor=key_factor,
            reasoning=(
                f"two-stage: ideation={outcome.ideation:.3f}, "
                f"idea={outcome.developed_idea}, early={outcome.early_adopter}, "
                f"module={outcome.module_choice}, "
                f"NPVd={outcome.npv_domestic:,.0f}€, NPVf={outcome.npv_foreign:,.0f}€"
            ),
        )

    def update_awareness(self, media_coverage: float, assimilation_rate: float = 0.05) -> None:
        """Gradually shift environmental awareness toward current media coverage."""
        self.environmental_awareness = (
            self.environmental_awareness * (1 - assimilation_rate)
            + media_coverage * assimilation_rate
        )

    def apply_llm_decision(self, decision: AdopterDecision) -> None:
        """Apply the LLM adoption decision to this adopter."""
        self.intention = decision.confidence
        if decision.will_adopt:
            self.is_adopted = True
