from unittest.mock import patch

import pytest

from app.game import game

TEST_TEAMS = {
    "A": {"point": 0.0, "weight": 1.0},
    "B": {"point": 0.0, "weight": 1.0},
    "C": {"point": 0.0, "weight": 1.0},
    "D": {"point": 0.0, "weight": 1.0},
}


def test_determination_of_ranking():
    """着順の決定が正しく行われているかのテスト"""
    # チームの重複が無く、1着～4着まで設定できていること
    with (
        patch(
            "app.game.random.choices",
            side_effect=[["B"], ["D"], ["C"]],
        ),
        patch(
            "app.game.random.gauss",
            side_effect=[35000, 20000, 5000],
        ),
    ):
        test_result = game(TEST_TEAMS)
        assert list(test_result) == ["B", "D", "C", "A"]

# 点数算出条件1回目でクリアするケース
MAKE_SCORES_CLEAR = 3
# 点数算出をやり直すケース
MAKE_SCORES_NOT_CLEAR = 6

@pytest.mark.parametrize(
    ("scores", "expected_calls"),
    [
        # 1人目の得点が上限を100点下回るケース
        ([119900, 35000, -10000], MAKE_SCORES_CLEAR),
        # 1人目の得点が上限と同じケース
        ([120000, 35000, -10000], MAKE_SCORES_CLEAR),
        # 1人目の得点が上限を100点上回るケース
        ([120100, 35000, -10000, 35000, 20000, 5000], MAKE_SCORES_NOT_CLEAR),
        # 1人目の得点が下限を100点上回るケース
        ([-59900, 15000, 50000], MAKE_SCORES_CLEAR),
        # 1人目の得点が下限と同じケース
        ([-60000, 15000, 50000], MAKE_SCORES_CLEAR),
        # 1人目の得点が下限を100点下回るケース
        ([-60100, 35000, 50000, 35000, 20000, 5000], MAKE_SCORES_NOT_CLEAR),
        # 4人目の得点が上限を100点上回るケース（4人目が120100点になる）
        ([-60000, 19900, 20000, 35000, 20000, 5000], MAKE_SCORES_NOT_CLEAR),
        # 4人目の得点が下限を100点下回るケース（4人目が-60100点になる）
        ([120000, 30000, 10100, 35000, 20000, 5000], MAKE_SCORES_NOT_CLEAR),
        # 3人目までで同じ点数が2人いる場合
        ([28000, 28000, 1000, 35000, 20000, 5000], MAKE_SCORES_NOT_CLEAR),
        # 4人目で同じ点数が2人発生する場合
        ([30000, 20000, 25000, 35000, 20000, 5000], MAKE_SCORES_NOT_CLEAR),
    ],
)
def test_make_player_scores(scores, expected_calls):
    """
    得点の生成が正しく行われているかのテスト
    """
    # 本テストケースでは、得点算出条件を満たしているケースはモックを3回呼び出す
    # また、得点算出条件を満たさず、算出をやり直すケースはモックを6回呼び出す
    with patch(
        "app.game.random.gauss", side_effect=scores
    ) as mock_gauss_point_total_range:
        game(TEST_TEAMS)
        assert mock_gauss_point_total_range.call_count == expected_calls


def test_m_league_points_total():
    """生成されたMリーグポイントが問題ないこと"""
    # 4人のMリーグポイントの合計が0になること
    with patch("app.game.random.gauss", side_effect=[35000, 20000, 5000]):
        test_result = game(TEST_TEAMS)
        assert sum(test_result.values()) == 0


def test_m_league_points():
    """着順とMリーグポイントが正しく割り振られていること"""
    with (
        patch(
            "app.game.random.choices",
            side_effect=[["B"], ["D"], ["C"]],
        ),
        patch(
            "app.game.random.gauss",
            side_effect=[35049, 20049, 5049],
        ),
    ):
        result = game(TEST_TEAMS)

    # 得点順：40,000／35,000／20,000／5,000
    expected = {
        "B": 60.0,
        "D": 15.0,
        "C": -20.0,
        "A": -55.0,
    }

    assert result == pytest.approx(expected)
    assert list(result) == ["B", "D", "C", "A"]
    assert sum(result.values()) == pytest.approx(0.0, abs=1e-9)
