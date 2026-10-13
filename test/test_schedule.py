from collections import Counter

import pytest

from app import const
from app.schedule import create_schedule

REGULAR_TEAM_NAMES = {
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
}

SEMIFINAL_TEAM_NAMES = {
    "Ａチーム",
    "Ｂチーム",
    "Ｃチーム",
    "Ｄチーム",
    "Ｅチーム",
    "Ｆチーム",
}


@pytest.mark.parametrize(
    ("games_per_team", "team_count", "team_names"),
    [
        (const.REGULAR_GAMES_PER_TEAM, const.REGULAR_TEAM_COUNT, REGULAR_TEAM_NAMES),
        (const.SEMIFINAL_GAMES_PER_TEAM, const.SEMIFINAL_TEAM_COUNT, SEMIFINAL_TEAM_NAMES),
    ],
)
def test_create_schedule(games_per_team, team_count, team_names):
    result_schedule = create_schedule(games_per_team, team_count, team_names)

    # 総カード数の確認
    cards_per_team = games_per_team // const.GAMES_PER_CARD
    assert len(result_schedule) == team_count * cards_per_team // const.PLAYER_COUNT

    # 全チームが、必要なカード数を満たしているか
    actual_counts = Counter(team for card in result_schedule for team in card)
    expected_counts = {team: cards_per_team for team in team_names}
    assert actual_counts == expected_counts

    # 同一カード内にチームの重複が無いか
    assert all(len(card) == const.PLAYER_COUNT for card in result_schedule)
    assert all(len(set(card)) == len(card) for card in result_schedule)
