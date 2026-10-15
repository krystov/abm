"""End-to-end test of board mode with a stubbed LLM client (no network)."""

import asyncio
from types import SimpleNamespace

import agents.board as board_module
import agents.manufacturer as manufacturer_module
from analysis.metrics import compute_metrics
from model.solar_model import SolarModel


BALLOTS = [
    {"vote": "expand", "intensity": 0.20, "rd_focus": "cost_reduction"},
    {"vote": "expand", "intensity": 0.10, "rd_focus": "cost_reduction"},
    {"vote": "expand", "intensity": 0.10, "rd_focus": "efficiency"},
    {"vote": "maintain", "intensity": 0.0, "rd_focus": "cost_reduction"},
    {"vote": "maintain", "intensity": 0.0, "rd_focus": "none"},
]


class StubClient:
    """AsyncOpenAI stand-in that returns a fixed rotation of board ballots."""

    def __init__(self, ballots=BALLOTS):
        self._ballots = ballots
        self._i = 0

        class _Completions:
            async def create(_self, **kwargs):
                ballot = self._ballots[self._i % len(self._ballots)]
                self._i += 1
                payload = (
                    '{"vote": "%s", "intensity": %.2f, "rd_focus": "%s", '
                    '"confidence": 0.75, "reasoning": "stub ballot", "concern": ""}'
                    % (ballot["vote"], ballot["intensity"], ballot["rd_focus"])
                )
                return SimpleNamespace(
                    choices=[SimpleNamespace(message=SimpleNamespace(content=payload))]
                )

        self.chat = SimpleNamespace(completions=_Completions())


def test_board_mode_runs_end_to_end_with_stubbed_llm(tmp_path, monkeypatch):
    stub = StubClient()
    monkeypatch.setattr(board_module, "create_llm_client", lambda: stub)
    monkeypatch.setattr(manufacturer_module, "create_llm_client", lambda: stub)

    minutes_path = tmp_path / "board_minutes.md"
    model = SolarModel(
        n_ticks=2,
        n_adopters=30,
        seed=3,
        use_llm=True,
        use_board=True,
        board_size=5,
        board_temperature=0.0,
        board_verbose=False,
        board_log_path=str(minutes_path),
        llm_adopter_fraction=0.0,  # keep adopters on the formula path (no API calls)
    )
    initial = {
        key: (mfg.capacity, mfg.production_cost)
        for key, mfg in model.manufacturers.items()
    }

    history = asyncio.run(model.run(verbose=False))

    assert len(history) == 2
    for record in history:
        for key in ("domestic_board", "foreign_board"):
            board = record[key]
            assert board is not None
            assert len(board["votes"]) == 5
            assert board["quorum"] == 3
            assert board["quorum_met"] is True
            assert board["fallback_used"] is False
            assert board["action"] == "expand"          # 3 expand vs 2 maintain
            assert board["rd_focus"] == "cost_reduction"  # 3 vs 1 efficiency + 1 none

    # The board resolution is what drives the manufacturer's state.
    for key in ("domestic", "foreign"):
        mfg = model.manufacturers[key]
        cap_before, cost_before = initial[key]
        assert mfg.capacity > cap_before          # expand motion was carried out
        assert mfg.production_cost < cost_before  # cost_reduction ran the curve

    # Minutes were written and contain every director plus the tally.
    text = minutes_path.read_text(encoding="utf-8")
    assert text.count("董事会会议纪要") == 4  # 2 ticks x 2 manufacturers
    assert "议案A 计票" in text
    assert "Dr. Anna Weber" in text

    stats = compute_metrics(history)["board_stats"]
    assert stats["meetings"] == 4
    assert stats["fallback_meetings"] == 0
    assert stats["avg_dissent"] == 2.0  # the two 'maintain' directors every meeting
    assert stats["actions"]["expand"] == 4
