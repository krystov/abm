"""
Board-of-directors collective decision making for LLM-augmented manufacturers.

Instead of a single LLM call, a manufacturer convenes a board of N directors.
Every director is an independent LLM agent with its own mandate, personal bias
and conversation memory: it studies the monthly agenda and then decides how —
or whether — to vote. The resolution follows majority rule, and the complete
transcript (who voted what, why, and the tally) is kept so that the reasoning
process can be inspected afterwards.

Agenda items of the monthly meeting:
  A. Capacity decision : expand | maintain | reduce   (with intensity 0.0-0.5)
  B. R&D focus         : efficiency | cost_reduction | none

Quorum: at least `quorum` non-abstaining votes on an item. An item that fails
to reach quorum makes the whole meeting "no resolution", and the caller falls
back to the deterministic experience-curve rule — the same fallback used when
the LLM is unavailable.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Sequence

from openai import AsyncOpenAI

from agents.agent_framework import (
    ConversationMemory,
    create_llm_client,
    extract_json_object,
)
from schemas import DirectorVote, ManufacturerDecision


# ---------------------------------------------------------------------------
# Director personas
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DirectorPersona:
    """A board seat: name, title, mandate and voting bias."""

    name: str
    role: str
    mandate: str
    bias: str
    risk_appetite: str = "medium"


DEFAULT_PERSONAS: Sequence[DirectorPersona] = (
    DirectorPersona(
        name="Dr. Anna Weber",
        role="董事长 (Chair)",
        mandate="长期战略、市场份额与政策窗口；对 FiT 与政府研发支持的信号最敏感。",
        bias="需求趋势明确时主张扩产；只有在订单明显萎缩时才接受减产。",
        risk_appetite="medium",
    ),
    DirectorPersona(
        name="Markus Hoffmann",
        role="首席财务官 (CFO)",
        mandate="现金流、毛利率、库存周转与产能利用率；关注扩产带来的固定成本风险。",
        bias="对扩产要求严格的经济证据（利用率高、库存低、毛利为正）；产能闲置时倾向减产。",
        risk_appetite="low",
    ),
    DirectorPersona(
        name="Dr. Yuki Tanaka",
        role="首席技术官 (CTO)",
        mandate="技术领先与长期产品竞争力，关注模块效率与知识存量带来的学习效应。",
        bias="研发上偏好效率或成本下降；对纯规模扩张兴趣不大，但一般不反对需求驱动的扩产。",
        risk_appetite="medium",
    ),
    DirectorPersona(
        name="Sofia Rossi",
        role="首席市场官 (CMO)",
        mandate="订单积压、装机需求、FiT 政策与市场成熟度；担心产能不足丢单。",
        bias="订单积压高时强烈主张扩产；需求疲软、库存堆积时支持减产。",
        risk_appetite="high",
    ),
    DirectorPersona(
        name="Klaus Berger",
        role="可持续发展与合规总监 (CSO)",
        mandate="长期减排承诺、政策合规与供应链稳健；反对短期激进扩张。",
        bias="倾向维持现有产能或以小强度扩产；支持研发投入，尤其是能降低成本的投入。",
        risk_appetite="low",
    ),
)


# ---------------------------------------------------------------------------
# Individual director (one LLM agent per board seat)
# ---------------------------------------------------------------------------


@dataclass
class Director:
    """One board member: an LLM agent with a mandate, a bias and its own memory."""

    persona: DirectorPersona
    memory: ConversationMemory = field(default_factory=ConversationMemory)
    temperature: float = 0.6
    system_prompt: str = field(default="", init=False)

    def __post_init__(self) -> None:
        self.system_prompt = (
            f"You are {self.persona.name}, {self.persona.role} of a solar PV "
            f"module manufacturer.\n"
            f"You sit on the company's board and vote every month on the agenda.\n\n"
            f"=== Your mandate ===\n{self.persona.mandate}\n\n"
            f"=== Your known bias ===\n{self.persona.bias}\n"
            f"Risk appetite: {self.persona.risk_appetite}\n\n"
            f"=== Rules of the board ===\n"
            f"- Study the agenda, then cast YOUR OWN vote on both items.\n"
            f"- You may abstain (\"abstain\") on an item when the evidence is "
            f"genuinely insufficient, but abstaining is not a safe default.\n"
            f"- Vote according to your own mandate even when you expect the other "
            f"directors to disagree; disagreement is normal and expected.\n"
            f"- Use only the figures given in the agenda; never invent market data.\n\n"
            f"=== Output ===\n"
            f"Respond with a single JSON object and nothing else:\n"
            '{"vote": "expand|maintain|reduce|abstain", '
            '"intensity": 0.0-0.5, '
            '"rd_focus": "efficiency|cost_reduction|none|abstain", '
            '"confidence": 0.0-1.0, '
            '"reasoning": "用中文写 1-2 句，说明你依据哪些数字得出该判断", '
            '"concern": "用中文写一句你最主要的顾虑，可留空"}'
        )

    @property
    def name(self) -> str:
        return self.persona.name

    @property
    def role(self) -> str:
        return self.persona.role

    async def deliberate(
        self,
        agenda_text: str,
        *,
        client: AsyncOpenAI,
        model_name: str,
        tick: int = 0,
        temperature: Optional[float] = None,
    ) -> DirectorVote:
        """Think about the agenda and return this director's vote.

        Failures are turned into an abstention (never an exception) so a single
        broken call cannot stall the whole board meeting.
        """
        memory_ctx = self.memory.format_for_prompt()
        user_prompt = (
            agenda_text
            + "\n\n=== Your voting record (previous meetings) ===\n"
            + memory_ctx
        )

        try:
            response = await client.chat.completions.create(
                model=model_name,
                temperature=self.temperature if temperature is None else temperature,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
            raw = response.choices[0].message.content
            vote = DirectorVote.model_validate(extract_json_object(raw))
            vote.director = self.name
            vote.role = self.role
            self.memory.record(tick, vote, f"voted {vote.vote} / {vote.rd_focus}")
            return vote

        except Exception as exc:  # noqa: BLE001 - deliberately broad
            abstention = DirectorVote(
                director=self.name,
                role=self.role,
                vote="abstain",
                intensity=0.0,
                rd_focus="abstain",
                confidence=0.0,
                reasoning=f"无法完成投票（{type(exc).__name__}），本项弃权。",
                concern=str(exc)[:160],
            )
            self.memory.record(tick, abstention, "vote failed -> abstain")
            return abstention


# ---------------------------------------------------------------------------
# Meeting outcome
# ---------------------------------------------------------------------------


@dataclass
class BoardOutcome:
    """The minutes of one board meeting plus the resulting decision."""

    region_label: str
    tick: int
    year: Optional[float]
    quorum: int
    votes: List[DirectorVote]
    capacity_tally: Dict[str, int]
    rd_tally: Dict[str, int]
    action: Optional[str]
    intensity: float
    rd_focus: Optional[str]
    tie_broken: bool = False
    quorum_met: bool = False
    fallback_used: bool = False
    decision: Optional[ManufacturerDecision] = None

    @property
    def n_abstain(self) -> int:
        return sum(1 for v in self.votes if v.vote == "abstain")

    @property
    def n_dissent(self) -> int:
        """Directors who did not back the winning capacity motion."""
        if self.action is None:
            return 0
        return sum(1 for v in self.votes if v.vote not in ("abstain", self.action))

    @property
    def unanimous(self) -> bool:
        return self.quorum_met and self.n_dissent == 0 and self.n_abstain == 0

    def summary_line(self) -> str:
        """One-line resolution summary for consoles and logs."""
        if self.action is None or self.rd_focus is None:
            return "董事会未达成决议 -> 回退到经验曲线规则"
        return (
            f"议案A {self.action}（强度 {self.intensity:.2f}）| "
            f"议案B {self.rd_focus} | "
            f"弃权 {self.n_abstain} | 反对 {self.n_dissent}"
            + (" | 主席裁决打破平票" if self.tie_broken else "")
        )

    def format_minutes(self) -> str:
        """Readable transcript: every director's reasoning plus the vote tally."""
        stamp = f"{self.year:.0f}" if self.year is not None else f"tick {self.tick}"
        lines: List[str] = []
        lines.append("=" * 74)
        lines.append(
            f"  董事会会议纪要 · {stamp} · {self.region_label}（tick {self.tick}）"
        )
        lines.append("=" * 74)
        lines.append("  议案A 产能：expand 扩产 / maintain 维持 / reduce 减产")
        lines.append("  议案B 研发：efficiency 效率 / cost_reduction 降本 / none 不投")
        lines.append("-" * 74)

        for i, vote in enumerate(self.votes, 1):
            lines.append(f"  [{i}] {vote.director} — {vote.role}")
            lines.append(
                f"      投票: {vote.vote}（强度 {vote.intensity:.2f}）"
                f" | 研发: {vote.rd_focus}"
                f" | 把握: {vote.confidence:.2f}"
            )
            if vote.reasoning:
                lines.append(f"      理由: {vote.reasoning}")
            if vote.concern:
                lines.append(f"      顾虑: {vote.concern}")
            lines.append("")

        lines.append("-" * 74)
        lines.append(f"  议案A 计票: {format_tally(self.capacity_tally)}")
        lines.append(f"  议案B 计票: {format_tally(self.rd_tally)}")
        lines.append(
            f"  过半门槛: {self.quorum} 票有效（共 {len(self.votes)} 名董事）"
        )
        lines.append(f"  表决结果: {self.summary_line()}")
        if self.decision is not None:
            lines.append(
                f"  最终决议: action={self.decision.action}, "
                f"change_percentage={self.decision.change_percentage:.4f}, "
                f"rd_focus={self.decision.rd_focus}"
            )
        else:
            lines.append("  最终决议: （无）本月由经验曲线规则接管")
        lines.append("=" * 74)
        return "\n".join(lines)

    def to_record(self) -> dict:
        """Compact, JSON-serialisable record for the simulation history."""
        return {
            "tick": self.tick,
            "region": self.region_label,
            "quorum": self.quorum,
            "capacity_tally": dict(self.capacity_tally),
            "rd_tally": dict(self.rd_tally),
            "action": self.action,
            "intensity": round(self.intensity, 4),
            "rd_focus": self.rd_focus,
            "tie_broken": self.tie_broken,
            "quorum_met": self.quorum_met,
            "fallback_used": self.fallback_used,
            "n_abstain": self.n_abstain,
            "n_dissent": self.n_dissent,
            "unanimous": self.unanimous,
            "votes": [
                {
                    "director": v.director,
                    "role": v.role,
                    "vote": v.vote,
                    "intensity": v.intensity,
                    "rd_focus": v.rd_focus,
                    "confidence": v.confidence,
                    "reasoning": v.reasoning,
                    "concern": v.concern,
                }
                for v in self.votes
            ],
        }


def format_tally(tally: Dict[str, int]) -> str:
    """Render a tally such as 'expand 3 票 / maintain 1 票'."""
    if not tally:
        return "（无有效票）"
    return " ▪ ".join(
        f"{option} {count} 票"
        for option, count in sorted(tally.items(), key=lambda kv: (-kv[1], kv[0]))
    )


# ---------------------------------------------------------------------------
# The board itself
# ---------------------------------------------------------------------------


@dataclass
class Board:
    """A chamber of directors that resolves the monthly agenda by majority vote."""

    directors: List[Director]
    region_label: str = "manufacturer"
    quorum: Optional[int] = None
    _client: Optional[AsyncOpenAI] = field(default=None, repr=False, compare=False)

    def __post_init__(self) -> None:
        if not self.directors:
            raise ValueError("A board needs at least one director")
        if self.quorum is None:
            self.quorum = majority_quorum(len(self.directors))

    @classmethod
    def default_chamber(
        cls,
        region_label: str,
        size: int = 5,
        temperature: float = 0.6,
    ) -> "Board":
        """Build a board of `size` seats from the default director personas."""
        seats: List[DirectorPersona] = []
        for i in range(size):
            base = DEFAULT_PERSONAS[i % len(DEFAULT_PERSONAS)]
            if i < len(DEFAULT_PERSONAS):
                seats.append(base)
            else:
                duplicate = i // len(DEFAULT_PERSONAS) + 1
                seats.append(
                    DirectorPersona(
                        name=f"{base.name} ({duplicate})",
                        role=base.role,
                        mandate=base.mandate,
                        bias=base.bias,
                        risk_appetite=base.risk_appetite,
                    )
                )
        return cls(
            directors=[Director(persona=s, temperature=temperature) for s in seats],
            region_label=region_label,
        )

    def _get_client(self) -> AsyncOpenAI:
        if self._client is None:
            self._client = create_llm_client()
        return self._client

    def roster(self) -> List[str]:
        """Director names in seniority order (index 0 = chair)."""
        return [d.name for d in self.directors]

    async def convene(
        self,
        agenda_text: str,
        *,
        model_name: str,
        tick: int = 0,
        year: Optional[float] = None,
        temperature: Optional[float] = None,
    ) -> BoardOutcome:
        """Run one meeting: every director votes concurrently, then tally."""
        client = self._get_client()
        votes = list(
            await asyncio.gather(
                *(
                    d.deliberate(
                        agenda_text,
                        client=client,
                        model_name=model_name,
                        tick=tick,
                        temperature=temperature,
                    )
                    for d in self.directors
                )
            )
        )

        capacity_voters = [v for v in votes if v.vote != "abstain"]
        rd_voters = [v for v in votes if v.rd_focus != "abstain"]

        capacity_tally = tally_votes(v.vote for v in capacity_voters)
        rd_tally = tally_votes(v.rd_focus for v in rd_voters)

        action, cap_tie = resolve_item(capacity_tally, capacity_voters, lambda v: v.vote)
        rd_focus, rd_tie = resolve_item(rd_tally, rd_voters, lambda v: v.rd_focus)
        tie_broken = cap_tie or rd_tie

        quorum_met = (
            action is not None
            and rd_focus is not None
            and len(capacity_voters) >= self.quorum
            and len(rd_voters) >= self.quorum
        )

        intensity = 0.0
        if action in ("expand", "reduce"):
            supporting = [v.intensity for v in capacity_voters if v.vote == action]
            if supporting:
                intensity = sum(supporting) / len(supporting)
            intensity = max(0.0, min(0.5, intensity))

        decision: Optional[ManufacturerDecision] = None
        if quorum_met:
            carried = capacity_tally.get(action, 0)
            decision = ManufacturerDecision(
                action=action,
                change_percentage=round(intensity, 4),
                rd_focus=rd_focus,
                reasoning=(
                    f"董事会表决 {carried}/{len(votes)} 通过 {action}"
                    f"（强度 {intensity:.2f}），研发重点 {rd_focus}"
                    + ("；平票由主席裁决" if tie_broken else "")
                ),
            )

        return BoardOutcome(
            region_label=self.region_label,
            tick=tick,
            year=year,
            quorum=self.quorum,
            votes=votes,
            capacity_tally=capacity_tally,
            rd_tally=rd_tally,
            action=action,
            intensity=round(intensity, 4),
            rd_focus=rd_focus,
            tie_broken=tie_broken,
            quorum_met=quorum_met,
            decision=decision,
        )


# ---------------------------------------------------------------------------
# Voting rules (pure functions, easy to unit-test)
# ---------------------------------------------------------------------------


def majority_quorum(n_directors: int) -> int:
    """Smallest number of non-abstaining votes that carries a motion."""
    return n_directors // 2 + 1


def tally_votes(options: Iterable[str]) -> Dict[str, int]:
    """Count votes per option."""
    tally: Dict[str, int] = {}
    for option in options:
        tally[option] = tally.get(option, 0) + 1
    return tally


def resolve_item(tally: Dict[str, int], voters: List[DirectorVote], getter):
    """Pick the winning option; a tie is settled by the most senior voter.

    Returns ``(winner_or_None, tie_broken)``. ``None`` means the item has no
    valid resolution at all (no votes cast) and the caller must fall back.
    """
    if not tally or not voters:
        return None, False
    best = max(tally.values())
    leaders = [option for option, count in tally.items() if count == best]
    if len(leaders) == 1:
        return leaders[0], False
    for voter in voters:  # roster order == seniority order (index 0 is chair)
        if getter(voter) in leaders:
            return getter(voter), True
    return None, True
