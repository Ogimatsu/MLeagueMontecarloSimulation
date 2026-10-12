from app import const
from app.main import main
from unittest.mock import patch
from copy import deepcopy
from decimal import Decimal, ROUND_CEILING

# 出場チーム
TEAM_NAMES = (
    "Ａチーム",
    "Ｂチーム",
    "Ｃチーム",
    "Ｄチーム",
    "Ｅチーム",
    "Ｆチーム",
    "Ｇチーム",
    "Ｈチーム",
    "Ｉチーム",
    "Ｊチーム",
)

# レギュラー順位
REGULAR_ORDER = TEAM_NAMES
# セミファイナル順位
SEMIFINAL_ORDER = (
    "Ｃチーム",
    "Ａチーム",
    "Ｆチーム",
    "Ｂチーム",
    "Ｄチーム",
    "Ｅチーム",
)
# ファイナル順位
FINAL_ORDER = (
    "Ｆチーム",
    "Ｃチーム",
    "Ａチーム",
    "Ｂチーム",
)

# レギュラーのMリーグポイント
REGULAR_POINTS = {
    team_name: float((len(TEAM_NAMES) - rank + 1) * 100)
    for rank, team_name in enumerate(REGULAR_ORDER, start=1)
}
# セミファイナルのMリーグポイント
SEMIFINAL_POINTS = {
    team_name: float((len(SEMIFINAL_ORDER) - rank + 1) * 50)
    for rank, team_name in enumerate(SEMIFINAL_ORDER, start=1)
}
# ファイナルのMリーグポイント
FINAL_POINTS = {
    team_name: float((len(FINAL_ORDER) - rank + 1) * 25)
    for rank, team_name in enumerate(FINAL_ORDER, start=1)
}

# レギュラーの対戦スケジュール
REGULAR_SCHEDULE = [["Ａチーム", "Ｂチーム", "Ｃチーム", "Ｄチーム"]]
# セミの対戦スケジュールのデフォルト値
SEMIFINAL_PLACEHOLDER_SCHEDULE = [
    ["REGULAR_1", "REGULAR_2", "REGULAR_3", "REGULAR_4"],
    ["REGULAR_5", "REGULAR_6", "REGULAR_1", "REGULAR_2"],
]


def make_phase_result(
    team_order,
    phase,
    points_by_team,
    previous_result=None,
):
    """固定したフェーズ順位・ポイントを持つ simulate_phase の戻り値を作る。"""
    previous_data = dict(previous_result or [])
    result = []

    for rank, team_name in enumerate(team_order, start=1):
        team_data = previous_data.get(
            team_name,
            {
                "weight": 1.0,
                "point": 0.0,
                "regular_end_points": None,
                "regular_end_rank": None,
                "semifinal_start_points": None,
                "semifinal_end_points": None,
                "semifinal_end_rank": None,
                "final_start_points": None,
                "final_end_points": None,
                "final_end_rank": None,
            },
        ).copy()
        previous_phase = {
            const.SEMIFINAL_PHASE: const.REGULAR_PHASE,
            const.FINAL_PHASE: const.SEMIFINAL_PHASE,
        }.get(phase)
        if previous_phase is not None:
            # 前フェーズ終了時ポイントを持ち越し、小数第一位まで切り上げる。
            carry_over = (
                Decimal(str(team_data[f"{previous_phase}_end_points"]))
                * Decimal(str(const.CARRY_OVER_RATE))
            )
            team_data[f"{phase}_start_points"] = float(
                carry_over.quantize(Decimal("0.1"), rounding=ROUND_CEILING)
            )
        team_data["point"] = 0.0
        team_data[f"{phase}_end_points"] = points_by_team[team_name]
        team_data[f"{phase}_end_rank"] = rank
        result.append((team_name, team_data))

    return result

# レギュラーの結果
REGULAR_RESULT = make_phase_result(
    REGULAR_ORDER,
    const.REGULAR_PHASE,
    REGULAR_POINTS
)
# セミの結果
SEMIFINAL_RESULT = make_phase_result(
    SEMIFINAL_ORDER,
    const.SEMIFINAL_PHASE,
    SEMIFINAL_POINTS,
    previous_result=REGULAR_RESULT,
)
# ファイナルの結果
FINAL_RESULT = make_phase_result(
    FINAL_ORDER,
    const.FINAL_PHASE,
    FINAL_POINTS,
    previous_result=SEMIFINAL_RESULT,
)

# シーズン全体のチーム
EXPECTED_SEASON_TEAM_NAMES = set(TEAM_NAMES)
# セミ進出チーム
EXPECTED_SEMIFINALISTS = set(REGULAR_ORDER[:const.SEMIFINAL_TEAMS])
# ファイナル進出チーム
EXPECTED_FINALISTS = set(SEMIFINAL_ORDER[:const.FINAL_TEAMS])

# レギュラー敗退チーム
EXPECTED_REGULAR_ELIMINATED = set(REGULAR_ORDER[const.SEMIFINAL_TEAMS:])
# セミ敗退チーム
EXPECTED_SEMIFINAL_ELIMINATED = set(SEMIFINAL_ORDER[const.FINAL_TEAMS:])


def test_main():
    """シーズンを通して正しく実行されているか"""
    phase_calls = []
    phase_results = iter(deepcopy(
        [REGULAR_RESULT, SEMIFINAL_RESULT, FINAL_RESULT]
    ))

    def fake_simulate_phase(teams, phase, schedule=None):
        # 後続処理で辞書が変更されても、呼び出し時点の値を確認できるようにする。
        phase_calls.append(deepcopy((teams, phase, schedule)))
        return next(phase_results)

    with (
        patch(
            "app.main.create_schedule",
            side_effect=deepcopy(
                [REGULAR_SCHEDULE, SEMIFINAL_PLACEHOLDER_SCHEDULE]
            )
        ) as mock_create_schedule,
        patch(
            "app.main.simulate_phase",
            side_effect=fake_simulate_phase,
        ) as mock_simulate_phase,
    ):
        test_result = main()
        assert mock_simulate_phase.call_count == len(phase_calls) == 3
        regular_call, semifinal_call, final_call = mock_simulate_phase.call_args_list

        # 規定の引数でスケジュールを作成し、レギュラーを実行していること
        assert mock_create_schedule.call_count == 2
        regular_schedule_call, semifinal_schedule_call = mock_create_schedule.call_args_list
        assert regular_schedule_call.args[:2] == (
            const.REGULAR_GAMES_PER_TEAM, const.REGULAR_TEAMS
        )
        assert set(regular_schedule_call.args[2]) == EXPECTED_SEASON_TEAM_NAMES
        assert semifinal_schedule_call.args[:2] == (
            const.SEMIFINAL_GAMES_PER_TEAM, const.SEMIFINAL_TEAMS
        )
        assert semifinal_schedule_call.args[2] == [
            f"REGULAR_{rank}" for rank in range(1, const.SEMIFINAL_TEAMS + 1)
        ]
        assert set(regular_call.args[0]) == EXPECTED_SEASON_TEAM_NAMES
        assert regular_call.args[1] == const.REGULAR_PHASE
        assert regular_call.args[2] == REGULAR_SCHEDULE

        # レギュラー上位6チームをセミファイナルへ渡していること
        regular_passed_teams = semifinal_call.args[0]
        regular_passed_phase = semifinal_call.args[1]
        assert set(regular_passed_teams) == EXPECTED_SEMIFINALISTS
        assert regular_passed_phase == const.SEMIFINAL_PHASE

        # セミファイナルの仮チーム名を実際の名前へ置き換えること
        assert semifinal_call.args[2] == [
            ["Ａチーム", "Ｂチーム", "Ｃチーム", "Ｄチーム"],
            ["Ｅチーム", "Ｆチーム", "Ａチーム", "Ｂチーム"],
        ]

        # セミファイナル上位4チームをファイナルへ渡すこと
        semifinal_passed_teams = final_call.args[0]
        semifinal_passed_phase = final_call.args[1]
        assert set(semifinal_passed_teams) == EXPECTED_FINALISTS
        assert semifinal_passed_phase == const.FINAL_PHASE
        # ファイナルにはスケジュールを渡さないこと
        assert len(final_call.args) == 2
        assert final_call.kwargs == {}

        # 次フェーズに進む前に持ち越し処理を行うこと
        semifinal_input, _, _ = phase_calls[1]
        final_input, _, _ = phase_calls[2]
        expected_semifinal_result = dict(SEMIFINAL_RESULT)
        expected_final_result = dict(FINAL_RESULT)
        for team_name, team_data in semifinal_input.items():
            assert team_data["regular_end_points"] == REGULAR_POINTS[team_name]
            assert team_data["semifinal_start_points"] == (
                expected_semifinal_result[team_name]["semifinal_start_points"]
            )
        for team_name, team_data in final_input.items():
            assert team_data["semifinal_end_points"] == SEMIFINAL_POINTS[team_name]
            assert team_data["final_start_points"] == (
                expected_final_result[team_name]["final_start_points"]
            )

        # 最後に敗退チームも含めて集約していること
        assert set(test_result) == EXPECTED_SEASON_TEAM_NAMES
        expected_regular_result = dict(REGULAR_RESULT)
        for team_name in EXPECTED_REGULAR_ELIMINATED:
            assert test_result[team_name] == expected_regular_result[team_name]
        for team_name in EXPECTED_SEMIFINAL_ELIMINATED:
            assert test_result[team_name] == expected_semifinal_result[team_name]
        for team_name in EXPECTED_FINALISTS:
            assert test_result[team_name] == expected_final_result[team_name]

        # 未進出フェーズの成績を保持していること
        for team_name in EXPECTED_REGULAR_ELIMINATED:
            for phase in (const.SEMIFINAL_PHASE, const.FINAL_PHASE):
                assert test_result[team_name][f"{phase}_start_points"] is None
                assert test_result[team_name][f"{phase}_end_points"] is None
                assert test_result[team_name][f"{phase}_end_rank"] is None
        for team_name in EXPECTED_SEMIFINAL_ELIMINATED:
            assert test_result[team_name]["final_start_points"] is None
            assert test_result[team_name]["final_end_points"] is None
            assert test_result[team_name]["final_end_rank"] is None
