from copy import deepcopy
from unittest.mock import patch

import pytest

from app import const
from app.simulate_phase import carry_over_points, round_up, simulate_phase


@pytest.mark.parametrize(
    ("prev_points", "expect_points"),
    [
        (123.1, 123.1),
        (123.11, 123.2),
        (123.15, 123.2),
        (-65.8, -65.8),
        (-65.81, -65.8),
        (-65.85, -65.8),
    ],
)
def test_round_up(prev_points, expect_points):
    """小数第二位以下について、ポイントが増える方向で調整されているか"""
    point = round_up(prev_points)
    assert point == expect_points


SEMIFINAL_CARRY_OVER_TEAMS = {
    "A": {
        "regular_end_points": 123.1,
    },
    "B": {
        "regular_end_points": -123.1,
    },
}

FINAL_CARRY_OVER_TEAMS = {
    "A": {
        "semifinal_end_points": 123.1,
    },
    "B": {
        "semifinal_end_points": -123.1,
    },
}


@pytest.mark.parametrize(
    ("next_phase", "prev_phase", "teams", "expected"),
    [
        (
            const.SEMIFINAL_PHASE,
            const.REGULAR_PHASE,
            SEMIFINAL_CARRY_OVER_TEAMS,
            {"A": 61.6, "B": -61.5},
        ),
        (
            const.FINAL_PHASE,
            const.SEMIFINAL_PHASE,
            FINAL_CARRY_OVER_TEAMS,
            {"A": 61.6, "B": -61.5},
        ),
    ],
)
def test_carry_over_points(next_phase, prev_phase, teams, expected):
    """全フェーズ終了時のMリーグポイントの50%を正しく持ち越せているか"""
    teams = deepcopy(teams)
    result_teams = carry_over_points(next_phase, prev_phase, teams)
    for team_name, team_data in result_teams.items():
        assert team_data[f"{next_phase}_start_points"] == expected[team_name]


# simulate_phase が必要とする項目だけを用意したテストデータ
REGULAR_TEAMS = {team_name: {"point": 0.0} for team_name in ("A", "B", "C", "D")}

SEMIFINAL_TEAMS = {
    "A": {"point": 0.0, "semifinal_start_points": 20.0},
    "B": {"point": 0.0, "semifinal_start_points": 100.0},
    "C": {"point": 0.0, "semifinal_start_points": -30.0},
    "D": {"point": 0.0, "semifinal_start_points": -90.0},
}

FINAL_TEAMS = {
    "A": {"point": 0.0, "final_start_points": 20.0},
    "B": {"point": 0.0, "final_start_points": 10.0},
    "C": {"point": 0.0, "final_start_points": -10.0},
    "D": {"point": 0.0, "final_start_points": -20.0},
}

SCHEDULE = [["A", "B", "C", "D"]]

GAME_RESULTS = [
    {"A": 60.0, "B": 10.0, "C": -20.0, "D": -50.0},
    {"A": -50.0, "B": 60.0, "C": 10.0, "D": -20.0},
]

EXPECTED_ORDER = ["B", "A", "C", "D"]


@pytest.mark.parametrize(
    (
        "teams",
        "phase",
        "schedule",
        "expected",
    ),
    [
        (
            REGULAR_TEAMS,
            const.REGULAR_PHASE,
            SCHEDULE,
            {"A": 10.0, "B": 70.0, "C": -10.0, "D": -70.0},
        ),
        (
            SEMIFINAL_TEAMS,
            const.SEMIFINAL_PHASE,
            SCHEDULE,
            # ポイント持越分も加算されていること
            {"A": 30.0, "B": 170.0, "C": -40.0, "D": -160.0},
        ),
        (
            FINAL_TEAMS,
            const.FINAL_PHASE,
            None,
            # ポイント持越分も加算されていること
            {"A": 30.0, "B": 80.0, "C": -20.0, "D": -90.0},
        ),
    ],
)
def test_simulate_phase(teams, phase, schedule, expected):
    """スケジュールに基づいて実行できているか"""
    teams = deepcopy(teams)
    with (
        patch(
            "app.simulate_phase.game",
            side_effect=GAME_RESULTS,
        ),
        patch(
            "app.simulate_phase.const.FINAL_GAMES_PER_TEAM",
            2,
        ),
    ):
        test_result = simulate_phase(teams, phase, schedule)
        # ポイントが想定通りについているか
        for rank, (team_name, team_data) in enumerate(test_result, start=1):
            assert team_data[f"{phase}_end_points"] == expected[team_name]
            assert team_data[f"{phase}_end_rank"] == rank
            assert team_data["point"] == 0.0

        # 順位が想定通りになっているか
        actual_order = [name for name, _ in test_result]
        assert actual_order == EXPECTED_ORDER


@pytest.mark.parametrize(
    ("phase", "start_points", "expected"),
    [
        (
            const.REGULAR_PHASE,
            {"A": 0.0, "B": 0.0, "C": 0.0, "D": 0.0, "E": 0.0, "F": 0.0},
            {"A": 40.0, "B": 70.0, "C": -10.0, "D": -70.0, "E": 40.0, "F": -70.0},
        ),
        (
            const.SEMIFINAL_PHASE,
            {"A": 20.0, "B": 100.0, "C": -30.0, "D": -90.0, "E": 40.0, "F": -40.0},
            {"A": 60.0, "B": 170.0, "C": -40.0, "D": -160.0, "E": 80.0, "F": -110.0},
        ),
    ],
)
def test_simulate_phase_with_different_card_teams(phase, start_points, expected):
    """カードごとの対戦チームだけに加算し、不参加チームのポイントを保持する。"""
    teams = {
        name: {"point": 0.0, f"{phase}_start_points": points}
        for name, points in start_points.items()
    }
    schedule = [
        ["A", "B", "C", "D"],
        ["A", "B", "E", "F"],
    ]
    game_results = [
        {"A": 60.0, "B": 10.0, "C": -20.0, "D": -50.0},
        {"A": -50.0, "B": 60.0, "C": 10.0, "D": -20.0},
        {"A": 40.0, "B": 20.0, "E": -10.0, "F": -50.0},
        {"A": -10.0, "B": -20.0, "E": 50.0, "F": -20.0},
    ]

    with patch("app.simulate_phase.game", side_effect=game_results) as mock_game:
        result = simulate_phase(teams, phase, schedule)

    # 各カードを連続2半荘ずつ実行し、カードにないチームを渡していないこと。
    assert mock_game.call_count == len(schedule) * const.GAMES_PER_CARD
    expected_game_teams = [
        set(card) for card in schedule for _ in range(const.GAMES_PER_CARD)
    ]
    assert [
        set(call.args[0]) for call in mock_game.call_args_list
    ] == expected_game_teams

    # A・Bは両カード分、C・DとE・Fは参加したカード分だけ加算されること。
    assert len(result) == len(expected)
    actual_points = {name: data[f"{phase}_end_points"] for name, data in result}
    assert actual_points == expected
    assert all(data["point"] == 0.0 for _, data in result)
