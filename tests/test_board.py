"""Tests for the board-of-directors group decision (agents/board.py)."""

import asyncio
from types import SimpleNamespace

from agents import Manufacturer, Region
from agents.board import (
    Board,
    DEFAULT_PERSONAS,
    Director,
    DirectorPersona,
    majority_quorum,
    resolve_item,
    tally_votes,
)
from schemas import DirectorVote, ManufacturerDecision


# ---------------------------------------------------------------------------
# Helpers — fake LLM clients and scripted directors
# ---------------------------------------------------------------------------


def _response(content: str):
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=content))]
    )


class FakeClient:
    """Minimal stand-in for AsyncOpenAI returning scripted content."""

    def __init__(self, contents):
        self._contents = list(contents)
        self.calls = 0

        class _Completions:
            async def create(_self, **kwargs):
                self.calls += 1
                payload = self._contents.pop(0) if self._contents else "{}"
                return _response(payload)

        self.chat = SimpleNamespace(completions=_Completions())


class BoomClient:
    """Client whose calls always fail (simulates a provider outage)."""

    class _Completions:
        async def create(self, **kwargs):
            raise RuntimeError("network down")

    def __init__(self):
        self.chat = SimpleNamespace(completions=BoomClient._Completions())


def _scripted_board(specs, region="test manufacturer"):
    """Board whose directors return the given ballots instead of calling an LLM."""
    board = Board.default_chamber(region, size=len(specs))
    for director, spec in zip(board.directors, specs):
        async def _vote(
            agenda_text,
            *,
            client,
            model_name,
            tick=0,
            temperature=None,
            _spec=spec,
            _director=director,
        ):
            return DirectorVote(
                director=_director.name,
                role=_director.role,
                **_spec,
            )

        director.deliberate = _vote
    board._client = object()  # never actually used by scripted directors
    return board


def _spec(vote="maintain", intensity=0.0, rd_focus="none", confidence=0.7, why="test"):
    return {
        "vote": vote,
        "intensity": intensity,
        "rd_focus": rd_focus,
        "confidence": confidence,
        "reasoning": why,
        "concern": "",
    }


# ---------------------------------------------------------------------------
# Voting rules
# ---------------------------------------------------------------------------


class TestVotingRules:
    def test_majority_quorum_is_strict_majority(self):
        assert majority_quorum(5) == 3
        assert majority_quorum(4) == 3
        assert majority_quorum(1) == 1
        assert majority_quorum(9) == 5

    def test_tally_counts_every_option(self):
        assert tally_votes(["expand", "expand", "reduce"]) == {
            "expand": 2,
            "reduce": 1,
        }

    def test_resolve_picks_unique_leader(self):
        votes = [
            DirectorVote(director="a", vote="expand", rd_focus="none"),
            DirectorVote(director="b", vote="expand", rd_focus="none"),
            DirectorVote(director="b", vote="reduce", rd_focus="none"),
        ]
        winner, tie = resolve_item(tally_votes(v.vote for v in votes), votes, lambda v: v.vote)
        assert winner == "expand"
        assert tie is False

    def test_resolve_tie_goes_to_senior_voter(self):
        votes = [
            DirectorVote(director="chair", vote="reduce", rd_focus="none"),
            DirectorVote(director="cfo", vote="expand", rd_focus="none"),
            DirectorVote(director="cmo", vote="expand", rd_focus="none"),
            DirectorVote(director="cto", vote="reduce", rd_focus="none"),
        ]
        winner, tie = resolve_item(tally_votes(v.vote for v in votes), votes, lambda v: v.vote)
        assert tie is True
        assert winner == "reduce"  # chair (first in roster order) breaks the tie

    def test_resolve_without_votes_returns_none(self):
        winner, tie = resolve_item({}, [], lambda v: v.vote)
        assert winner is None
        assert tie is False


# ---------------------------------------------------------------------------
# One meeting
# ---------------------------------------------------------------------------


class TestBoardMeeting:
    def _convene(self, specs):
        board = _scripted_board(specs)
        return asyncio.run(board.convene("AGENDA", model_name="fake-model", tick=3, year=2005.0))

    def test_majority_resolution_carries(self):
        outcome = self._convene([
            _spec("expand", 0.20, "cost_reduction"),
            _spec("expand", 0.10, "cost_reduction"),
            _spec("expand", 0.30, "efficiency"),
            _spec("maintain", 0.0, "cost_reduction"),
            _spec("reduce", 0.05, "none"),
        ])
        assert outcome.quorum_met is True
        assert outcome.action == "expand"
        assert outcome.rd_focus == "cost_reduction"
        # intensity = mean of the three directors who voted expand
        assert abs(outcome.intensity - 0.20) < 1e-9
        assert outcome.decision is not None
        assert isinstance(outcome.decision, ManufacturerDecision)
        assert outcome.decision.action == "expand"
        assert outcome.decision.change_percentage == 0.20
        assert outcome.n_dissent == 2
        assert outcome.n_abstain == 0
        assert outcome.unanimous is False

    def test_maintain_forces_zero_intensity(self):
        outcome = self._convene([
            _spec("maintain", 0.40, "none"),
            _spec("maintain", 0.30, "none"),
            _spec("maintain", 0.20, "none"),
            _spec("expand", 0.10, "none"),
            _spec("reduce", 0.10, "none"),
        ])
        assert outcome.action == "maintain"
        assert outcome.intensity == 0.0
        assert outcome.decision.change_percentage == 0.0

    def test_abstentions_below_quorum_block_the_resolution(self):
        outcome = self._convene([
            _spec("expand", 0.10, "abstain"),
            _spec("abstain", 0.0, "cost_reduction", why="no data"),
            _spec("abstain", 0.0, "abstain"),
            _spec("abstain", 0.0, "abstain"),
            _spec("abstain", 0.0, "abstain"),
        ])
        assert outcome.quorum_met is False
        assert outcome.decision is None  # caller must fall back
        assert outcome.n_abstain == 4

    def test_tie_is_broken_by_the_chair(self):
        outcome = self._convene([
            _spec("reduce", 0.05, "none"),   # chair
            _spec("expand", 0.10, "none"),
            _spec("expand", 0.10, "none"),
            _spec("reduce", 0.05, "none"),
            _spec("abstain", 0.0, "abstain"),
        ])
        assert outcome.tie_broken is True
        assert outcome.action == "reduce"

    def test_minutes_show_every_director_and_the_tally(self):
        outcome = self._convene([
            _spec("expand", 0.10, "cost_reduction", why="订单积压上升，应扩产"),
            _spec("reduce", 0.05, "none", why="产能利用率偏低"),
            _spec("maintain", 0.0, "efficiency", why="技术优先"),
            _spec("expand", 0.10, "cost_reduction", why="FiT 支持需求"),
            _spec("abstain", 0.0, "abstain", why="证据不足"),
        ])
        minutes = outcome.format_minutes()
        for director in outcome.votes:
            assert director.director in minutes
        assert "订单积压上升，应扩产" in minutes
        assert "议案A 计票" in minutes
        assert "expand" in minutes
        record = outcome.to_record()
        assert len(record["votes"]) == 5
        assert record["n_abstain"] == 1

    def test_board_roster_uses_five_default_personas(self):
        board = Board.default_chamber("manufacturer", size=5)
        assert len(board.directors) == 5
        assert board.quorum == 3
        assert len(set(board.roster())) == 5
        assert board.roster()[0] == DEFAULT_PERSONAS[0].name

    def test_board_scales_beyond_default_personas(self):
        board = Board.default_chamber("manufacturer", size=7)
        assert len(board.directors) == 7
        assert board.quorum == 4
        assert len(set(board.roster())) == 7  # duplicated seats get a suffix


# ---------------------------------------------------------------------------
# Director-level behaviour (LLM contract + failure handling)
# ---------------------------------------------------------------------------


class TestDirector:
    def test_director_parses_json_wrapped_in_prose_and_fences(self):
        director = Director(persona=DEFAULT_PERSONAS[0])
        client = FakeClient([
            'Let me think.\n```json\n{"vote": "expand", "intensity": 0.12, '
            '"rd_focus": "cost_reduction", "confidence": 0.8, '
            '"reasoning": "需求强", "concern": "库存"}\n```'
        ])
        vote = asyncio.run(
            director.deliberate("AGENDA", client=client, model_name="fake", tick=1)
        )
        assert vote.vote == "expand"
        assert vote.intensity == 0.12
        assert vote.rd_focus == "cost_reduction"
        assert vote.director == director.name   # filled in by the board, not the LLM
        assert vote.role == director.role
        assert len(director.memory) == 1        # the vote is remembered

    def test_failed_call_becomes_an_abstention(self):
        director = Director(persona=DEFAULT_PERSONAS[1])
        vote = asyncio.run(
            director.deliberate("AGENDA", client=BoomClient(), model_name="fake", tick=2)
        )
        assert vote.vote == "abstain"
        assert vote.rd_focus == "abstain"
        assert vote.confidence == 0.0
        assert "RuntimeError" in vote.reasoning

    def test_directors_keep_separate_memories(self):
        board = Board.default_chamber("manufacturer", size=5)
        for director in board.directors:
            director.memory.record(0, {"vote": "expand"}, "voted")
        assert all(len(d.memory) == 1 for d in board.directors)
        assert len({id(d.memory) for d in board.directors}) == 5


# ---------------------------------------------------------------------------
# Manufacturer integration
# ---------------------------------------------------------------------------


def _make_manufacturer(**overrides):
    params = dict(
        manufacturer_id=1,
        region=Region.DOMESTIC,
        capacity=500.0,
        module_efficiency=0.15,
        production_cost=1.50,
        price=2.25,
        knowledge_stock=100.0,
        cumulative_production=500.0,
        sales=10.0,
        stock=20.0,
        employees=2000,
        mark_up=0.50,
        rd_spending=1000.0,
        cp_initial=500.0,
        ks_initial=100.0,
        experience_curve_intercept=2.882,
        beta_learning_by_doing=-0.074,
        beta_learning_by_research=-0.814,
    )
    params.update(overrides)
    return Manufacturer(**params)


class TestManufacturerBoard:
    def test_agenda_carries_the_figures_directors_need(self):
        mfg = _make_manufacturer()
        agenda = mfg._build_board_agenda(
            electricity_price=0.25,
            fit_tariff=0.40,
            order_backlog=600.0,
            tech_push_level=3.0,
            tick=12,
            year=1992.0,
        )
        for token in ("议案A", "议案B", "产能利用率", "生产成本", "订单积压", "1992"):
            assert token in agenda

    def test_step_board_resolves_and_does_not_touch_state(self):
        mfg = _make_manufacturer()
        mfg.board = _scripted_board([
            _spec("expand", 0.20, "cost_reduction"),
            _spec("expand", 0.10, "cost_reduction"),
            _spec("expand", 0.10, "efficiency"),
            _spec("maintain", 0.0, "cost_reduction"),
            _spec("reduce", 0.05, "none"),
        ], region=mfg._region_label())

        capacity_before = mfg.capacity
        cost_before = mfg.production_cost
        outcome = asyncio.run(mfg.step_board(
            electricity_price=0.25,
            fit_tariff=0.40,
            order_backlog=600.0,
            tech_push_level=3.0,
            tick=12,
            year=1992.0,
        ))

        assert outcome.fallback_used is False
        assert outcome.decision.action == "expand"
        # step_board only decides — the caller applies it
        assert mfg.capacity == capacity_before
        assert mfg.production_cost == cost_before

        mfg.apply_llm_decision(outcome.decision)
        assert mfg.capacity > capacity_before
        assert mfg.production_cost < cost_before

    def test_step_board_falls_back_when_the_board_is_deadlocked(self):
        mfg = _make_manufacturer()
        mfg.board = _scripted_board([
            _spec("abstain", 0.0, "abstain"),
            _spec("abstain", 0.0, "abstain"),
            _spec("abstain", 0.0, "abstain"),
            _spec("abstain", 0.0, "abstain"),
            _spec("abstain", 0.0, "abstain"),
        ], region=mfg._region_label())

        outcome = asyncio.run(mfg.step_board(
            electricity_price=0.25,
            fit_tariff=0.40,
            order_backlog=600.0,
        ))

        assert outcome.fallback_used is True
        assert outcome.decision is not None
        assert outcome.decision.action in ("expand", "maintain", "reduce")

    def test_experience_curve_fallback_can_be_computed_without_applying(self):
        mfg = _make_manufacturer()
        capacity_before = mfg.capacity
        cumulative_before = mfg.cumulative_production

        decision = mfg._experience_curve_fallback(
            0.25, 0.40, 600.0, apply=False
        )
        assert isinstance(decision, ManufacturerDecision)
        assert mfg.capacity == capacity_before
        assert mfg.cumulative_production == cumulative_before

    def test_experience_curve_fallback_applies_in_formula_mode(self):
        mfg = _make_manufacturer()
        cost_before = mfg.production_cost
        decision = mfg._experience_curve_fallback(0.25, 0.40, 600.0)
        assert isinstance(decision, ManufacturerDecision)
        assert mfg.production_cost <= cost_before
